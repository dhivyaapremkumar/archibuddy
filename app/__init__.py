from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database import Base


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    frontage_ft = Column(Float, nullable=False)
    depth_ft = Column(Float, nullable=False)
    road_ft = Column(Float, nullable=False)
    floors = Column(String, nullable=False)

    front_m = Column(Float, nullable=False)
    side_m = Column(Float, nullable=False)
    rear_m = Column(Float, nullable=False)
    plot_sqft = Column(Float, nullable=False)
    max_fsi_sqft = Column(Float, nullable=False)
    buildable_sqft = Column(Float, nullable=False)
    parking = Column(Integer, nullable=False)
    warning = Column(String, nullable=True)
    rules_version = Column(String, nullable=False)
