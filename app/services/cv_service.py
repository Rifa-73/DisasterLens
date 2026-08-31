"""
This is the seam between your backend and the CV/DL teammate's work.

Right now assess_flood_severity() is a stub that returns fake data so you can
build and test the API without waiting on the trained U-Net model. Once the
model is ready, replace the inside of this function with the real inference
call (load model once at startup, not per-request — see note below).
"""

import random
from app.schemas.incident import SeverityResult


def assess_flood_severity(image_bytes: bytes) -> SeverityResult:
    # TODO: replace with real U-Net inference, e.g.:
    #   mask = unet_model.predict(preprocess(image_bytes))
    #   coverage = mask.sum() / mask.size * 100
    coverage = round(random.uniform(0, 100), 2)

    if coverage < 20:
        level = "low"
    elif coverage < 60:
        level = "moderate"
    else:
        level = "severe"

    return SeverityResult(
        severity_level=level,
        flood_coverage_pct=coverage,
        confidence=round(random.uniform(0.7, 0.99), 2),
    )
