import tempfile
import uuid
from datetime import timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.schemas.incident import (
    IncidentOut,
    BatchSeverityResponse,
    VideoSeverityResult,
)
from app.services.cv_service import (
    assess_flood_severity,
    assess_flood_severity_batch,
    assess_flood_severity_video,
)
from app.services.gemini_service import analyze_image, chat_with_gemini


# main.py already adds /incidents
router = APIRouter()

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
IMAGE_DIR = MEDIA_DIR / "images"

ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_AUDIO = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4"}
ALLOWED_VIDEO = {"video/mp4", "video/webm", "video/quicktime"}

MAX_IMAGE_MB = 5
MAX_AUDIO_MB = 15
MAX_VIDEO_MB = 50
MAX_BATCH_IMAGES = 10


def _validate_image(file: UploadFile):
    if file.content_type not in ALLOWED_IMAGES:
        raise HTTPException(
            400,
            "Only JPEG, PNG or WEBP images are allowed."
        )


async def _save_optional_media(
    file: Optional[UploadFile],
    kind: str,
    allowed_types: set,
    max_size_mb: int,
):
    if not file:
        return None

    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Unsupported {kind} file type.")

    data = await file.read()

    if len(data) > max_size_mb * 1024 * 1024:
        raise HTTPException(400, f"{kind} file is too large.")

    folder = MEDIA_DIR / kind
    folder.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or "").suffix or ".bin"
    name = f"{uuid.uuid4()}{ext}"
    path = folder / name
    path.write_bytes(data)

    return f"/media/{kind}/{name}"


async def _read_images(files: List[UploadFile]):
    if not files:
        raise HTTPException(400, "At least one image is required.")

    if len(files) > MAX_BATCH_IMAGES:
        raise HTTPException(
            400,
            f"Maximum {MAX_BATCH_IMAGES} images allowed."
        )

    images = []

    for file in files:
        _validate_image(file)

        data = await file.read()

        if len(data) > MAX_IMAGE_MB * 1024 * 1024:
            raise HTTPException(
                400,
                f"{file.filename} exceeds {MAX_IMAGE_MB} MB.",
            )

        images.append(
            {
                "filename": file.filename or "image",
                "content": data,
            }
        )

    return images


def _save_incident_images(incident_id: int, images):
    folder = IMAGE_DIR / str(incident_id)
    folder.mkdir(parents=True, exist_ok=True)

    urls = []

    for image in images:
        ext = Path(image["filename"]).suffix or ".jpg"
        name = f"{uuid.uuid4()}{ext}"

        (folder / name).write_bytes(image["content"])

        urls.append(
            f"/media/images/{incident_id}/{name}"
        )

    return urls


def _get_incident_images(incident_id: int):
    folder = IMAGE_DIR / str(incident_id)

    if not folder.exists():
        return []

    return [
        f"/media/images/{incident_id}/{file.name}"
        for file in sorted(folder.iterdir())
        if file.is_file()
    ]


def _as_utc(value):
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _to_incident_out(
    db_incident,
    severity=None,
    ai_assessment=None,
):
    return IncidentOut(
        id=db_incident.id,
        latitude=db_incident.latitude,
        longitude=db_incident.longitude,
        description=db_incident.description,
        severity=severity or {
            "severity_level": db_incident.severity_level,
            "flood_coverage_pct": db_incident.flood_coverage_pct,
            "severity_score": db_incident.confidence,
        },
        image_urls=_get_incident_images(db_incident.id),
        audio_url=db_incident.audio_path,
        video_url=db_incident.video_path,
        ai_assessment=ai_assessment or db_incident.ai_assessment,
        created_at=_as_utc(db_incident.created_at),
    )


@router.post("/assess")
async def assess_incident(
    file: UploadFile = File(...),
):
    _validate_image(file)

    data = await file.read()

    if len(data) > MAX_IMAGE_MB * 1024 * 1024:
        raise HTTPException(
            400,
            "Image exceeds 5 MB."
        )

    return assess_flood_severity(data)


@router.post(
    "/assess-batch",
    response_model=BatchSeverityResponse
)
async def assess_batch(
    files: List[UploadFile] = File(...),
):
    images = await _read_images(files)

    severity_results = assess_flood_severity_batch(
        [item["content"] for item in images]
    )

    results = []

    for index, severity in enumerate(severity_results):
        results.append(
            {
                "filename": images[index]["filename"],
                "rank": 0,
                "severity": severity.model_dump(),
            }
        )

    results.sort(
        key=lambda x: x["severity"]["flood_coverage_pct"],
        reverse=True,
    )

    for index, result in enumerate(results):
        result["rank"] = index + 1

    return {
        "total_images": len(results),
        "results": results,
        "highest_severity": results[0],
    }


@router.post(
    "/assess-video",
    response_model=VideoSeverityResult
)
async def assess_video(
    file: UploadFile = File(...),
):
    if file.content_type not in ALLOWED_VIDEO:
        raise HTTPException(
            400,
            "Unsupported video type."
        )

    data = await file.read()

    if len(data) > MAX_VIDEO_MB * 1024 * 1024:
        raise HTTPException(
            400,
            "Video exceeds 50 MB."
        )

    suffix = Path(file.filename or "").suffix or ".mp4"

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp:
        temp.write(data)
        temp_path = temp.name

    try:
        return assess_flood_severity_video(temp_path)
    finally:
        Path(temp_path).unlink(missing_ok=True)


@router.post(
    "/report",
    response_model=IncidentOut
)
async def create_report(
    latitude: float = Form(...),
    longitude: float = Form(...),
    description: Optional[str] = Form(None),

    files: List[UploadFile] = File(default=[]),
    file: Optional[UploadFile] = File(None),

    audio: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db),
):
    # Backward compatibility with old frontend
    if not files and file:
        files = [file]

    images = await _read_images(files)

    contents = [
        item["content"]
        for item in images
    ]

    names = [
        item["filename"]
        for item in images
    ]

    severity_results = assess_flood_severity_batch(
        contents
    )

    batch = []

    for index, severity in enumerate(severity_results):
        batch.append(
            {
                "filename": names[index],
                "original_index": index,
                "rank": 0,
                "severity": severity.model_dump(),
            }
        )

    batch.sort(
        key=lambda x: x["severity"]["flood_coverage_pct"],
        reverse=True,
    )

    for index, result in enumerate(batch):
        result["rank"] = index + 1

    highest = batch[0]

    # Use the original image index after sorting.
    primary_image = contents[highest["original_index"]]

    # analyze_image() is synchronous, so do not await it.
    ai = analyze_image(primary_image)

    audio_url = await _save_optional_media(
        audio,
        "audio",
        ALLOWED_AUDIO,
        MAX_AUDIO_MB,
    )

    video_url = await _save_optional_media(
        video,
        "video",
        ALLOWED_VIDEO,
        MAX_VIDEO_MB,
    )

    incident = Incident(
        latitude=latitude,
        longitude=longitude,
        description=description,
        severity_level=highest["severity"]["severity_level"],
        flood_coverage_pct=highest["severity"]["flood_coverage_pct"],
        confidence=highest["severity"]["severity_score"],
        audio_path=audio_url,
        video_path=video_url,
        ai_assessment=ai,
    )

    db.add(incident)
    db.flush()

    image_urls = _save_incident_images(
        incident.id,
        images,
    )

    db.commit()
    db.refresh(incident)

    result = _to_incident_out(
        incident,
        severity=highest["severity"],
        ai_assessment=ai,
    )

    result.image_urls = image_urls

    return result


@router.get(
    "/",
    response_model=List[IncidentOut]
)
def get_incidents(
    db: Session = Depends(get_db),
):
    incidents = (
        db.query(Incident)
        .order_by(Incident.created_at.desc())
        .all()
    )

    return [
        _to_incident_out(incident)
        for incident in incidents
    ]


@router.post("/chat")
async def chat(
    message: str = Form(...),
):
    return await chat_with_gemini(message)