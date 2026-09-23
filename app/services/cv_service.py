"""
Connects the FastAPI backend to the teammate's trained FloodNet U-Net model
(see cvdl/src/predict_api.py and cvdl/models/cvdl_model.py).

Folder layout this expects (repo root):
    DisasterLens/
        app/            <- this backend
        cvdl/
            models/cvdl_model.py
            src/predict_api.py
            outputs/best_model_weighted.pth   <- trained weights (confirmed best by CV teammate)
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CVDL_SRC = REPO_ROOT / "cvdl" / "src"
if str(CVDL_SRC) not in sys.path:
    sys.path.insert(0, str(CVDL_SRC))

from predict_api import FloodPredictor  # teammate's inference class
from predict_video import FloodVideoPredictor  # teammate's video inference class

from app.schemas.incident import SeverityResult

MODEL_PATH = REPO_ROOT / "cvdl" / "outputs" / "best_model_weighted.pth"

# Load the model ONCE when the server starts, not on every request.
_predictor = FloodPredictor(str(MODEL_PATH))

_SEVERITY_MAP = {
    "None": "low",
    "Low": "low",
    "Medium": "moderate",
    "High": "severe",
}

FLOOD_RELATED_CLASSES = ["Building-Flooded", "Road-Flooded", "Water"]


def assess_flood_severity(image_bytes: bytes) -> SeverityResult:
    result = _predictor.predict(image_bytes)

    flood_coverage_pct = round(
        sum(result["class_percentages"].get(c, 0.0) for c in FLOOD_RELATED_CLASSES),
        2,
    )

    return SeverityResult(
        severity_level=_SEVERITY_MAP.get(result["severity_label"], "low"),
        flood_coverage_pct=flood_coverage_pct,
        severity_score=result["severity_score"],
    )


def assess_flood_severity_batch(images: list[bytes]) -> list[SeverityResult]:
    """
    Runs each image through the same loaded model, one at a time.
    Order of results matches the order of the input list.
    """
    return [assess_flood_severity(image_bytes) for image_bytes in images]


# ------------------------------------------------------------------
# Video analysis
# ------------------------------------------------------------------
# Loaded lazily (only the first time a video is actually analyzed),
# since most requests are just images and don't need this in memory.
_video_predictor: FloodVideoPredictor | None = None


def _get_video_predictor() -> FloodVideoPredictor:
    global _video_predictor
    if _video_predictor is None:
        _video_predictor = FloodVideoPredictor(str(MODEL_PATH))
    return _video_predictor


def assess_flood_severity_video(video_path: str) -> dict:
    """
    Runs a video frame-by-frame through the U-Net model and returns
    aggregated stats (average/peak flood coverage, per-frame severity
    counts). Unlike images, this needs a real file path on disk - OpenCV
    can't read video straight from bytes - so the caller must save the
    upload to a temp file first and pass that path in.
    """
    predictor = _get_video_predictor()
    result = predictor.predict_video(video_path)
    result["severity_level"] = _SEVERITY_MAP.get(result["peak_severity"], "low")
    return result