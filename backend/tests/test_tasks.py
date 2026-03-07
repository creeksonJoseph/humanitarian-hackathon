"""Unit tests for background task functions in app/tasks.py."""
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models import Rider, Location, EmergencyJob, HazardReport
from app import tasks as task_module


def make_app():
    return create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })


def _base_seed(app):
    with app.app_context():
        db.create_all()
        loc = Location(code="4050", name="Ekerenyo", type="VILLAGE")
        db.session.add(loc)
        rider = Rider(
            phone_number="+254700000001",
            name="Task Rider",
            home_stage_code="4050",
            last_known_location_code="4050",
            is_verified=True,
            status="AVAILABLE",
        )
        db.session.add(rider)
        db.session.commit()


# ---- auto_resolve_stale_jobs -----------------------------------------------

def test_auto_resolve_old_claimed_job():
    app = make_app()
    _base_seed(app)

    with app.app_context():
        old_time = datetime.now(timezone.utc) - timedelta(hours=4)
        job = EmergencyJob(
            caller_number="+254700000002",
            village_code="4050",
            emergency_type="MATERNITY",
            status="CLAIMED",
            assigned_rider="+254700000001",
            created_at=old_time,
        )
        db.session.add(job)
        # Set rider ON_JOB
        rider = db.session.get(Rider, "+254700000001")
        rider.status = "ON_JOB"
        db.session.commit()

        job_id = job.job_id

    with app.app_context():
        count = task_module.auto_resolve_stale_jobs()
        assert count == 1
        job = db.session.get(EmergencyJob, job_id)
        assert job.status == "AUTO_RESOLVED"
        assert job.cancellation_reason == "SYSTEM_TIMEOUT"
        rider = db.session.get(Rider, "+254700000001")
        assert rider.status == "AVAILABLE"


def test_recent_claimed_job_not_resolved():
    app = make_app()
    _base_seed(app)

    with app.app_context():
        job = EmergencyJob(
            caller_number="+254700000002",
            village_code="4050",
            emergency_type="MATERNITY",
            status="CLAIMED",
            assigned_rider="+254700000001",
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.job_id

    with app.app_context():
        count = task_module.auto_resolve_stale_jobs()
        assert count == 0
        job = db.session.get(EmergencyJob, job_id)
        assert job.status == "CLAIMED"  # untouched


# ---- reset_rider_locations --------------------------------------------------

def test_reset_rider_locations():
    app = make_app()
    _base_seed(app)

    with app.app_context():
        # Move rider away from home
        rider = db.session.get(Rider, "+254700000001")
        rider.last_known_location_code = "4051"  # somewhere else
        db.session.commit()

    with app.app_context():
        count = task_module.reset_rider_locations()
        assert count == 1
        rider = db.session.get(Rider, "+254700000001")
        assert rider.last_known_location_code == rider.home_stage_code


# ---- expire_old_hazards -----------------------------------------------------

def test_expire_old_hazards():
    app = make_app()
    _base_seed(app)

    with app.app_context():
        old_time = datetime.now(timezone.utc) - timedelta(hours=13)
        hazard = HazardReport(
            route_description="4050",
            reported_by_number="+254700000001",
            status="ACTIVE",
            expires_at=old_time,
        )
        db.session.add(hazard)
        db.session.commit()
        hazard_id = hazard.id

    with app.app_context():
        count = task_module.expire_old_hazards()
        assert count == 1
        h = db.session.get(HazardReport, hazard_id)
        assert h.status == "EXPIRED"


def test_fresh_hazard_not_expired():
    app = make_app()
    _base_seed(app)

    with app.app_context():
        # expires_at defaults to utcnow + 12h
        hazard = HazardReport(
            route_description="4050",
            reported_by_number="+254700000001",
            status="ACTIVE",
        )
        db.session.add(hazard)
        db.session.commit()
        hazard_id = hazard.id

    with app.app_context():
        count = task_module.expire_old_hazards()
        assert count == 0
        h = db.session.get(HazardReport, hazard_id)
        assert h.status == "ACTIVE"
