import json
import os
from app import create_app, db


def setup_app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "API_KEY": "test-key"})
    return app


def test_create_hazard_and_job_and_claim(tmp_path):
    app = setup_app()
    with app.app_context():
        db.create_all()
        client = app.test_client()

        # create a rider
        from app.models import Rider

        r = Rider(phone_number="+254700000001", name="Test Rider", home_stage_code="4050", is_verified=True, status="AVAILABLE")
        db.session.add(r)
        db.session.commit()

        # create hazard
        rv = client.post("/api/hazards", json={"route_description": "bridge-1", "reported_by_number": "+254700000001"})
        assert rv.status_code == 201

        # create job
        rv = client.post("/api/jobs", json={"caller_number": "+254700000002", "village_code": "4050", "emergency_type": "MATERNITY"})
        assert rv.status_code == 201
        job_id = rv.get_json()["job_id"]

        # claim job with API key
        rv = client.post(f"/api/jobs/{job_id}/claim", json={"rider_phone": "+254700000001"}, headers={"X-API-Key": "test-key"})
        assert rv.status_code == 200
        assert rv.get_json()["status"] == "claimed"
