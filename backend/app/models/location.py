from app import db


class Location(db.Model):
    __tablename__ = "locations"

    code = db.Column(db.String, primary_key=True, index=True, comment="e.g., 4050")
    name = db.Column(db.String, nullable=False, comment="e.g., Ekerenyo")
    type = db.Column(db.String, nullable=False, comment="STAGE, VILLAGE, HOSPITAL")

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return f"<Location(code={self.code!r}, name={self.name!r})>"
