from datetime import datetime, timedelta, timezone
from app import db


class HazardReport(db.Model):
    __tablename__ = "hazard_reports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hazard_type = db.Column(db.String, nullable=False, server_default="OTHER", comment="E.g., FLOOD, ROAD_BLOCK, ACCIDENT")
    route_description = db.Column(db.String, nullable=False)
    reported_by_number = db.Column(db.String, nullable=False, comment="Can be anyone, not just a vetted rider")
    status = db.Column(db.String, nullable=False, comment="ACTIVE (if rider), UNVERIFIED (if public), CLEARED")
    reported_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(hours=12),
        nullable=False,
        comment="reported_at + 12 hours",
    )

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return f"<HazardReport(id={self.id}, status={self.status!r})>"
