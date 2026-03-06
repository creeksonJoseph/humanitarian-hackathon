from app import db


class Rider(db.Model):
    __tablename__ = "riders"

    phone_number = db.Column(db.String, primary_key=True, comment="e.g., +2547XXXXXXXX")
    name = db.Column(db.String, nullable=False)
    home_stage_code = db.Column(db.String, db.ForeignKey("locations.code"), nullable=False)
    last_known_location_code = db.Column(
        db.String,
        db.ForeignKey("locations.code"),
        nullable=True,
        comment="Updated only when they manually check-in or report a hazard",
    )
    is_verified = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String, nullable=False, comment="AVAILABLE, ON_JOB, OFFLINE")

    # relationships to Location (two FKs to same table require foreign_keys)
    home_stage = db.relationship("Location", foreign_keys=[home_stage_code], backref="home_riders")
    last_known_location = db.relationship(
        "Location", foreign_keys=[last_known_location_code], backref="last_known_riders"
    )

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return f"<Rider(phone_number={self.phone_number!r}, name={self.name!r})>"
