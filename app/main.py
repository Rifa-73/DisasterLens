"""
DisasterLens Backend - FastAPI entrypoint

Architecture (matches project design):
  Frontend (React) -> FastAPI (this layer) -> CV/DL models (U-Net severity, YOLO detection)
                                            -> Database (incidents, users)
                                            -> Geospatial / real-time layer
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import incidents, health
from app.database import Base, engine
from app.models import incident as incident_model  # noqa: F401 - registers the table

# Creates disasterlens.db and the incidents table if they don't exist yet.
# Fine for dev; for real schema changes later you'd move to Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DisasterLens API",
    description="AI-powered flood detection and severity assessment backend",
    version="0.1.0",
)

# Allow the React frontend to call this API during development.
# Tighten allow_origins before deploying anywhere public.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(incidents.router, prefix="/incidents", tags=["incidents"])


@app.get("/")
def root():
    return {"message": "DisasterLens API is running"}
