from pydantic import BaseModel, Field
from typing import Optional


class SeverityResult(BaseModel):
    """What we return after running an uploaded image through the CV model."""
    severity_level: str          # e.g. "low", "moderate", "severe"
    flood_coverage_pct: float    # % of image classified as flooded, from U-Net mask
    severity_score: float


class GeminiAssessment(BaseModel):

    disaster_type: str
    likelihood: str
    priority: str
    reason: str
    needs_human_verification: bool


class IncidentCreate(BaseModel):
    """What a client sends when reporting/creating an incident."""
    # Real latitude/longitude ranges - anything outside this is not a real location.
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    # Cap description length so someone can't send a huge block of text.
    description: Optional[str] = Field(None, max_length=500)


class IncidentOut(BaseModel):
    """What we return once an incident is stored + assessed."""
    id: int
    latitude: float
    longitude: float
    description: Optional[str] = None
    severity: SeverityResult
    # URLs the frontend can use to play back the uploaded audio/video, if any.
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    ai_assessment: Optional[GeminiAssessment] = None