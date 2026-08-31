from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, Query
from sqlalchemy.orm import Session

from app.services.cv_service import assess_flood_severity
from app.schemas.incident import SeverityResult, IncidentOut
from app.database import get_db
from app.models.incident import Incident

router = APIRouter()

# Only accept these image types - keeps out random file uploads pretending to be images.
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


def _validate_image(file: UploadFile, image_bytes: bytes) -> None:
    """Shared checks for any endpoint that accepts an image upload."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File must be one of: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Image must be under {MAX_IMAGE_SIZE_MB}MB",
        )
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")


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
    # ge/le = real-world latitude/longitude ranges; anything outside is rejected
    # automatically by FastAPI before this function even runs.
    latitude: float = Form(..., ge=-90, le=90),
    longitude: float = Form(..., ge=-180, le=180),
    description: Optional[str] = Form(None, max_length=500),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Full flow: upload an image with location -> assess severity -> save to DB.
    This is what the frontend's "report an incident" form should call.
    """
    image_bytes = await file.read()
    _validate_image(file, image_bytes)

    severity = assess_flood_severity(image_bytes)

    db_incident = Incident(
        latitude=latitude,
        longitude=longitude,
        description=description,
        severity_level=severity.severity_level,
        flood_coverage_pct=severity.flood_coverage_pct,
        confidence=severity.confidence,
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    return IncidentOut(
        id=db_incident.id,
        latitude=db_incident.latitude,
        longitude=db_incident.longitude,
        description=db_incident.description,
        severity=severity,
    )


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
        IncidentOut(
            id=r.id,
            latitude=r.latitude,
            longitude=r.longitude,
            description=r.description,
            severity=SeverityResult(
                severity_level=r.severity_level,
                flood_coverage_pct=r.flood_coverage_pct,
                confidence=r.confidence,
            ),
        )
        for r in rows
    ]
