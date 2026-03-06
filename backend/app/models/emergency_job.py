from datetime import datetime, timezone
from app import db


class EmergencyJob(db.Model):
    __tablename__ = "emergency_jobs"

    job_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    caller_number = db.Column(db.String, nullable=False)
    village_code = db.Column(db.String, db.ForeignKey("locations.code"), nullable=False)
    landmark_hint = db.Column(db.String, nullable=True)
    emergency_type = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False, comment="BROADCASTING, CLAIMED, RESOLVED, CANCELLED")
    assigned_rider = db.Column(db.String, db.ForeignKey("riders.phone_number"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True, comment="Updated only if user/rider manually closes the job")
    cancellation_reason = db.Column(db.String, nullable=True)

    village = db.relationship("Location", backref="emergency_jobs")
    rider = db.relationship("Rider", backref="assigned_jobs")

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return f"<EmergencyJob(job_id={self.job_id}, status={self.status!r})>"
