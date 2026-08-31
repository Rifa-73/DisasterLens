from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
def health_check():
    """Simple liveness check - hit this first to confirm the server works."""
    return {"status": "ok"}
