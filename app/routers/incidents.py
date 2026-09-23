import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel
from app.services.gemini_service import chat_with_gemini
from app.services.gemini_service import analyze_image

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, Query
from sqlalchemy.orm import Session

from app.services.cv_service import (
    assess_flood_severity,
    assess_flood_severity_batch,
    assess_flood_severity_video,
)
from app.schemas.incident import (
    SeverityResult,
    IncidentOut,
    BatchImageResult,
    BatchSeverityResponse,
    VideoSeverityResult,
)
from app.database import get_db
from app.models.incident import Incident

router = APIRouter()

# ------------------------------------------------------------------
# Image validation (used by the AI severity assessment)
# ------------------------------------------------------------------
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

# Batch endpoint - cap the count so one request can't tie up the model
# for minutes (each image runs through the full U-Net forward pass).
MAX_BATCH_IMAGES = 10

# ------------------------------------------------------------------
# Audio/video validation (NOT analyzed by the AI model - saved as
# extra evidence/context alongside the incident report)
# ------------------------------------------------------------------
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/webm", "audio/mp4", "audio/x-m4a"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_AUDIO_SIZE_MB = 15
MAX_VIDEO_SIZE_MB = 50

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"


def _validate_image(file: UploadFile, image_bytes: bytes) -> None:
    """Checks for the required image upload."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Image must be one of: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"Image must be under {MAX_IMAGE_SIZE_MB}MB")
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")


async def _save_optional_media(
    file: Optional[UploadFile],
    kind: str,  # "audio" or "video"
    allowed_types: set,
    max_size_mb: int,
) -> Optional[str]:
    """
    Validates and saves an optional audio/video file to disk.
    Returns the relative path to store in the DB (e.g. "media/audio/xyz.mp3"),
    or None if no file was provided.
    """
    if file is None or file.filename == "":
        return None

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"{kind.capitalize()} must be one of: {', '.join(allowed_types)}",
        )

    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail=f"Uploaded {kind} is empty")
    if len(file_bytes) > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"{kind.capitalize()} must be under {max_size_mb}MB")

    # Use a random filename so two people uploading "recording.mp3" don't collide.
    extension = Path(file.filename).suffix or ""
    unique_name = f"{uuid.uuid4().hex}{extension}"
    save_path = MEDIA_DIR / kind / unique_name

    with open(save_path, "wb") as f:
        f.write(file_bytes)

    return f"media/{kind}/{unique_name}"


def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    SQLite returns naive datetimes (stored in UTC). Attach UTC explicitly so
    the API returns '...+00:00' and the frontend converts to local time
    (e.g. IST) correctly instead of treating it as already-local.
    """
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _to_incident_out(db_incident: Incident, severity: SeverityResult, ai_assessment=None) -> IncidentOut:
    return IncidentOut(
        id=db_incident.id,
        latitude=db_incident.latitude,
        longitude=db_incident.longitude,
        description=db_incident.description,
        severity=severity,
        audio_url=f"/{db_incident.audio_path}" if db_incident.audio_path else None,
        video_url=f"/{db_incident.video_path}" if db_incident.video_path else None,
        ai_assessment=ai_assessment,
        created_at=_as_utc(db_incident.created_at),
    )


@router.post("/assess", response_model=SeverityResult)
async def assess_image(file: UploadFile = File(...)):
    """
    Run an uploaded image through the CV model and return severity only.
    Doesn't save anything - use /incidents/report to save an assessed incident.
    """
    image_bytes = await file.read()
    _validate_image(file, image_bytes)
    return assess_flood_severity(image_bytes)


@router.post("/assess-batch", response_model=BatchSeverityResponse)
async def assess_images_batch(files: List[UploadFile] = File(...)):
    """
    Run multiple uploaded images through the CV model in one request and
    rank them by flood coverage - highest first. Useful for comparing
    several photos of the same or nearby areas to see which is worst hit.
    Doesn't save anything to the DB (same as /assess).
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one image is required")
    if len(files) > MAX_BATCH_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Max {MAX_BATCH_IMAGES} images per batch request",
        )

    filenames = []
    image_bytes_list = []
    for f in files:
        image_bytes = await f.read()
        _validate_image(f, image_bytes)
        filenames.append(f.filename or "unnamed")
        image_bytes_list.append(image_bytes)

    severities = assess_flood_severity_batch(image_bytes_list)

    # Pair each filename with its result, then sort worst-to-best by
    # flood coverage so the most urgent images surface first.
    paired = list(zip(filenames, severities))
    paired.sort(key=lambda pair: pair[1].flood_coverage_pct, reverse=True)

    results = [
        BatchImageResult(filename=name, rank=rank, severity=severity)
        for rank, (name, severity) in enumerate(paired, start=1)
    ]

    return BatchSeverityResponse(
        total_images=len(results),
        results=results,
        highest_severity=results[0],
    )


@router.post("/assess-video", response_model=VideoSeverityResult)
async def assess_video(file: UploadFile = File(...)):
    """
    Run an uploaded flood video frame-by-frame through the U-Net model
    and return aggregated severity stats (average/peak flood coverage,
    plus how many frames fell into each severity band).

    Unlike images, OpenCV needs a real file on disk to read video, so
    the upload is written to a temp file first and deleted once analysis
    finishes (even if it fails). Doesn't save anything to the DB.
    """
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Video must be one of: {', '.join(ALLOWED_VIDEO_TYPES)}",
        )

    video_bytes = await file.read()

    if len(video_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded video is empty")
    if len(video_bytes) > MAX_VIDEO_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail=f"Video must be under {MAX_VIDEO_SIZE_MB}MB"
        )

    suffix = Path(file.filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        result = assess_flood_severity_video(tmp_path)
    finally:
        # Always clean up the temp file, even if analysis raised.
        Path(tmp_path).unlink(missing_ok=True)

    return VideoSeverityResult(
        frames_analyzed=result["frames_analyzed"],
        fps=result["fps"],
        average_flood_coverage_pct=result["average_flood_coverage_pct"],
        peak_flood_coverage_pct=result["peak_flood_coverage_pct"],
        peak_frame=result["peak_frame"],
        peak_severity=result["peak_severity"],
        severity_level=result["severity_level"],
        high_frames=result["high_frames"],
        medium_frames=result["medium_frames"],
        low_frames=result["low_frames"],
    )


@router.post("/report", response_model=IncidentOut)
async def report_incident(
    latitude: float = Form(..., ge=-90, le=90),
    longitude: float = Form(..., ge=-180, le=180),
    description: Optional[str] = Form(None, max_length=500),
    file: UploadFile = File(...),
    audio: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Full flow: upload an image (required) with location -> assess severity ->
    save to DB. Audio and video are optional extra evidence - they are saved
    alongside the incident but are NOT analyzed by the AI model (which only
    understands images). A Gemini-based assessment also runs on the image.
    """
    image_bytes = await file.read()
    _validate_image(file, image_bytes)

    severity = assess_flood_severity(image_bytes)
    ai_assessment = analyze_image(image_bytes, description or "")

    audio_path = await _save_optional_media(audio, "audio", ALLOWED_AUDIO_TYPES, MAX_AUDIO_SIZE_MB)
    video_path = await _save_optional_media(video, "video", ALLOWED_VIDEO_TYPES, MAX_VIDEO_SIZE_MB)

    db_incident = Incident(
        latitude=latitude,
        longitude=longitude,
        description=description,
        severity_level=severity.severity_level,
        flood_coverage_pct=severity.flood_coverage_pct,
        confidence=severity.severity_score,
        audio_path=audio_path,
        video_path=video_path,
        ai_assessment=ai_assessment,
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    return _to_incident_out(db_incident, severity, ai_assessment)


@router.get("/", response_model=list[IncidentOut])
def list_incidents(
    db: Session = Depends(get_db),
    severity: Optional[str] = Query(
        None, description="Filter by severity_level: low, moderate, or severe"
    ),
    limit: int = Query(50, ge=1, le=200, description="Max number of results"),
):
    """
    Returns saved incidents - what the map/dashboard would call.
    Supports optional filtering, e.g. GET /incidents/?severity=severe&limit=10
    Most recent incidents are returned first.
    """
    query = db.query(Incident)

    if severity:
        query = query.filter(Incident.severity_level == severity.lower())

    rows = query.order_by(Incident.id.desc()).limit(limit).all()

    return [
        _to_incident_out(
            r,
            SeverityResult(
                severity_level=r.severity_level,
                flood_coverage_pct=r.flood_coverage_pct,
                severity_score=r.confidence,
            ),
            r.ai_assessment,
        )
        for r in rows
    ]


class ChatRequest(BaseModel):
    question: str
    incident: dict


@router.post("/chat")
def chat(request: ChatRequest):
    return {
        "answer": chat_with_gemini(
            request.question,
            request.incident
        )
    }