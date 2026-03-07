from app import create_app, db
from app.models import Rider
import os

def test_smoke():
    app = create_app({"TESTING": True, "API_KEY": "testkey"})

    with app.app_context():
        # Ensure tables exist
        db.create_all()

        # Clear previous SMS log
        sms_log = os.path.join(app.instance_path, "sms.log")
        try:
            open(sms_log, "w").close()
        except Exception as e:
            print("Warning: could not reset sms.log:", e)

        # Ensure there's an available rider
        rider_phone = "+254700000001"
        rider = db.session.get(Rider, rider_phone)
        if not rider:
            rider = Rider(
                phone_number=rider_phone,
                name="Smoke Rider",
                home_stage_code="4050",
                last_known_location_code="4050",
                is_verified=True,
                status="AVAILABLE",
            )
            db.session.add(rider)
            db.session.commit()

    # Use test client to call endpoints
    client = app.test_client()

    print("--- POST /api/hazards ---")
    resp = client.post("/api/hazards", json={
        "route_description": "4050",
        "reported_by_number": "+254700000000",
    })
    print(resp.status_code, resp.get_json())
    assert resp.status_code == 201

    print("--- POST /api/jobs ---")
    resp = client.post("/api/jobs", json={
        "caller_number": "+254700000000",
        "village_code": "4050",
        "emergency_type": "MATERNITY",
    })
    print(resp.status_code, resp.get_json())
    assert resp.status_code == 201
    job_id = resp.get_json().get("job_id")
    assert job_id is not None

    print("--- Check sms log ---")
    with open(os.path.join(app.instance_path, "sms.log"), "r") as f:
        sms_content = f.read()
        print(sms_content)
        assert "OkoaRoute SOS" in sms_content

    if job_id:
        print("--- POST /api/jobs/{}/claim ---".format(job_id))
        resp = client.post(f"/api/jobs/{job_id}/claim", json={"rider_phone": rider_phone}, headers={"X-API-Key": "testkey"})
        print(resp.status_code, resp.get_json())
        assert resp.status_code == 200
        assert resp.get_json().get("status") == "claimed"
    else:
        assert False, "No job_id returned"
