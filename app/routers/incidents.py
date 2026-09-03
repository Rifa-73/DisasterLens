import uuid
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from app.services.gemini_service import chat_with_gemini
from app.services.gemini_service import analyze_image

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, Query
from sqlalchemy.orm import Session

from app.services.cv_service import assess_flood_severity
from app.schemas.incident import SeverityResult, IncidentOut
from app.database import get_db
from app.models.incident import Incident

router = APIRouter()

# ------------------------------------------------------------------
# Image validation (used by the AI severity assessment)
# ------------------------------------------------------------------
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

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