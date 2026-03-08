"""Tests for read-only dashboard endpoints: GET /api/stats, /api/hazards, /api/jobs, /health."""
from app import create_app, db
from app.models import Rider, Location, EmergencyJob, HazardReport


def make_app():
    return create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "API_KEY": "test-key",
    })


def _seed(app):
    with app.app_context():
        db.create_all()
        loc = Location(code="4050", name="Ekerenyo", type="VILLAGE")
        db.session.add(loc)
        rider = Rider(
            phone_number="+254700000001",
            name="Dashboard Rider",
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
        hazard = HazardReport(
            route_description="Ekerenyo Main Bridge",
            reported_by_number="+254700000001",
            status="ACTIVE",
        )
        db.session.add(hazard)
        db.session.commit()


# ---- /health ----------------------------------------------------------------

def test_health_ok():
    app = make_app()
    _seed(app)
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert "version" in data


# ---- GET /api/stats ---------------------------------------------------------

def test_get_stats():
    app = make_app()
    _seed(app)
    client = app.test_client()
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "active_sos" in data
    assert "total_sos" in data
    assert "available_riders" in data
    assert "total_riders" in data
    assert "active_hazards" in data
    assert data["active_sos"] >= 1
    assert data["available_riders"] >= 1
    assert data["active_hazards"] >= 1


# ---- GET /api/hazards -------------------------------------------------------

def test_list_hazards():
    app = make_app()
    _seed(app)
    client = app.test_client()
    resp = client.get("/api/hazards")
    assert resp.status_code == 200
    hazards = resp.get_json()
    assert isinstance(hazards, list)
    assert len(hazards) >= 1
    assert "route_description" in hazards[0]
    assert "status" in hazards[0]


# ---- GET /api/sos ----------------------------------------------------------

def test_list_sos():
    app = make_app()
    _seed(app)
    client = app.test_client()
    resp = client.get("/api/sos")
    assert resp.status_code == 200
    jobs = resp.get_json()
    assert isinstance(jobs, list)
    assert len(jobs) >= 1
    assert "id" in jobs[0]
    assert "status" in jobs[0]
    assert "type" in jobs[0]

# ---- GET /api/riders -------------------------------------------------------

def test_list_riders():
    app = make_app()
    _seed(app)
    client = app.test_client()
    resp = client.get("/api/riders")
    assert resp.status_code == 200
    riders = resp.get_json()
    assert isinstance(riders, list)
    assert len(riders) >= 1
    assert "phone" in riders[0]
    assert "status" in riders[0]
