from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(String, nullable=True)

    severity_level = Column(String, nullable=False)
    flood_coverage_pct = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
