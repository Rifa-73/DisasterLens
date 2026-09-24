from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SeverityResult(BaseModel):
    severity_level: str
    flood_coverage_pct: float
    severity_score: float


class GeminiAssessment(BaseModel):
    disaster_type: str
    likelihood: str
    priority: str
    reason: str
    needs_human_verification: bool


class IncidentCreate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    description: Optional[str] = Field(None, max_length=500)


class BatchImageResult(BaseModel):
    filename: str
    rank: int
    severity: SeverityResult


class BatchSeverityResponse(BaseModel):
    total_images: int
    results: list[BatchImageResult]
    highest_severity: BatchImageResult


class VideoSeverityResult(BaseModel):
    frames_analyzed: int
    fps: float
    average_flood_coverage_pct: float
    peak_flood_coverage_pct: float
    peak_frame: int
    peak_severity: str
    severity_level: str
    high_frames: int
    medium_frames: int
    low_frames: int


class IncidentOut(BaseModel):
    id: int
    latitude: float
    longitude: float
    description: Optional[str] = None

    severity: SeverityResult

    image_urls: list[str] = []

    audio_url: Optional[str] = None
    video_url: Optional[str] = None

    ai_assessment: Optional[GeminiAssessment] = None
    created_at: Optional[datetime] = None