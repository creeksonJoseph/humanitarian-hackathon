"""Tests for the inbound SMS webhook (/sms) – ACCEPT and DROP flows."""
import os
from app import create_app, db
from app.models import Rider, Location, EmergencyJob


def make_app():
    return create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "API_KEY": "test-key",
        "AT_API_KEY": "",  # force stub
    })


def _seed(app):
    """Insert a location, rider, and broadcasting job."""
    with app.app_context():
        db.create_all()
        loc = Location(code="4050", name="Ekerenyo", type="VILLAGE")
        db.session.add(loc)
        rider = Rider(
            phone_number="+254700000001",
            name="Test Rider",
            home_stage_code="4050",
            last_known_location_code="4050",
            is_verified=True,
            status="AVAILABLE",
        )
        db.session.add(rider)
        job = EmergencyJob(
            caller_number="+254700000002",
            village_code="4050",
            emergency_type="MATERNITY",
            status="BROADCASTING",
        )
        db.session.add(job)
        db.session.commit()
        return job.job_id


def test_accept_claims_job():
    app = make_app()
    job_id = _seed(app)
    client = app.test_client()

    resp = client.post("/sms", data={"from": "+254700000001", "text": f"ACCEPT {job_id}"})
    assert resp.status_code == 200

    with app.app_context():
        job = db.session.get(EmergencyJob, job_id)
        assert job.status == "CLAIMED"
        assert job.assigned_rider == "+254700000001"
        rider = db.session.get(Rider, "+254700000001")
        assert rider.status == "ON_JOB"


def test_second_accept_is_rejected():
    """The second rider to reply ACCEPT should NOT take over the job."""
    app = make_app()
    job_id = _seed(app)
    client = app.test_client()

    # Add a second rider
    with app.app_context():
        r2 = Rider(
            phone_number="+254700000003",
            name="Second Rider",
            home_stage_code="4050",
            last_known_location_code="4050",
            is_verified=True,
            status="AVAILABLE",
        )
        db.session.add(r2)
        db.session.commit()

    client.post("/sms", data={"from": "+254700000001", "text": f"ACCEPT {job_id}"})
    client.post("/sms", data={"from": "+254700000003", "text": f"ACCEPT {job_id}"})

    with app.app_context():
        job = db.session.get(EmergencyJob, job_id)
        assert job.assigned_rider == "+254700000001"  # first winner unchanged


def test_drop_releases_job():
    app = make_app()
    job_id = _seed(app)
    client = app.test_client()

    client.post("/sms", data={"from": "+254700000001", "text": f"ACCEPT {job_id}"})
    client.post("/sms", data={"from": "+254700000001", "text": f"DROP {job_id}"})

    with app.app_context():
        job = db.session.get(EmergencyJob, job_id)
        assert job.status == "BROADCASTING"
        assert job.assigned_rider is None
        rider = db.session.get(Rider, "+254700000001")
        assert rider.status == "AVAILABLE"


def test_unknown_rider_accept_is_rejected():
    """An unregistered number should not be able to claim a job."""
    app = make_app()
    job_id = _seed(app)
    client = app.test_client()

    client.post("/sms", data={"from": "+254799999999", "text": f"ACCEPT {job_id}"})

    with app.app_context():
        job = db.session.get(EmergencyJob, job_id)
        assert job.status == "BROADCASTING"
        assert job.assigned_rider is None


def test_accept_nonexistent_job():
    """Accepting a job that doesn't exist should return 200 (AT ignores body)."""
    app = make_app()
    _seed(app)
    client = app.test_client()
    resp = client.post("/sms", data={"from": "+254700000001", "text": "ACCEPT 99999"})
    assert resp.status_code == 200
