"""Application entry-point.

Run in development:
    python app.py

Run with gunicorn (production):
    gunicorn app:app

All routes (/ussd, /sms, /health, /api/*) are registered inside
`create_app()` via blueprints so they are available both here and in tests.
"""
from flask import request, make_response

from app import create_app, db
from app.models import EmergencyJob, Rider, HazardReport
from app.dispatch import notify_candidates

app = create_app()


# ---------------------------------------------------------------------------
# USSD Webhook  – Africa's Talking calls this on every keypress
# ---------------------------------------------------------------------------

@app.route("/ussd", methods=["POST"])
def ussd_callback():
    """Handle HTTP POST requests from Africa's Talking USSD gateway."""
    phone_number = request.values.get("phoneNumber", None)
    text = request.values.get("text", "")

    response = ""

    # --- MAIN MENU ---
    if text == "":
        response = "CON Welcome to OkoaRoute Emergency\n"
        response += "1. Request Emergency Boda\n"
        response += "2. Report Road Hazard\n"
        response += "3. Rider Check-in\n"
        response += "4. Check Route Safety"

    # --- BRANCH 1: REQUEST EMERGENCY ---
    elif text == "1":
        response = "CON Select Emergency Type:\n"
        response += "1. Maternity\n"
        response += "2. Severe Injury\n"
        response += "3. Other Medical"

    elif text in ["1*1", "1*2", "1*3"]:
        response = "CON Enter your 4-digit Village Code (e.g., 4050 for Ekerenyo):"

    elif len(text.split("*")) == 3 and text.startswith("1*"):
        parts = text.split("*")
        emergency_type_map = {"1": "MATERNITY", "2": "INJURY", "3": "OTHER"}
        selected_type = emergency_type_map.get(parts[1], "OTHER")
        village_code = parts[2]
        try:
            new_job = EmergencyJob(
                caller_number=phone_number,
                village_code=village_code,
                emergency_type=selected_type,
                status="BROADCASTING",
            )
            db.session.add(new_job)
            db.session.commit()
            notify_candidates(new_job)
            response = f"END SOS Sent. Dispatching nearest vetted rider to village {village_code}. You will receive an SMS shortly."
        except Exception:
            db.session.rollback()
            response = "END Error processing request. Please ensure the village code is correct."

    # --- BRANCH 2: REPORT HAZARD ---
    elif text == "2":
        response = "CON Enter 4-digit code of the hazardous route:"

    elif len(text.split("*")) == 2 and text.startswith("2*"):
        parts = text.split("*")
        route_code = parts[1]
        try:
            rider = db.session.get(Rider, phone_number)
            status = "ACTIVE" if (rider and rider.is_verified) else "UNVERIFIED"
            if rider:
                rider.last_known_location_code = route_code
            hr = HazardReport(route_description=route_code, reported_by_number=phone_number, status=status)
            db.session.add(hr)
            db.session.commit()
            response = f"END Thank you. Hazard reported for route {route_code}."
        except Exception:
            db.session.rollback()
            response = "END Error saving hazard report."

    # --- BRANCH 3: RIDER CHECK-IN ---
    elif text == "3":
        response = "CON Enter your 4-digit Stage Code to check in:"

    elif len(text.split("*")) == 2 and text.startswith("3*"):
        parts = text.split("*")
        stage_code = parts[1]
        try:
            rider = db.session.get(Rider, phone_number)
            if rider:
                rider.last_known_location_code = stage_code
                db.session.commit()
                response = f"END Check-in successful. Current stage: {stage_code}."
            else:
                response = "END Error. Number not recognized as a registered rider."
        except Exception:
            db.session.rollback()
            response = "END Error processing check-in."

    # --- BRANCH 4: CHECK ROUTE SAFETY ---
    elif text == "4":
        response = "CON Enter 4-digit route code to check (e.g., 4050 for Ekerenyo):"

    # --- USSD: route code entered (e.g., '4*4050') ---
    elif len(text.split("*")) == 2 and text.startswith("4*"):
        from datetime import datetime, timezone
        route_code = text.split("*")[1]
        now = datetime.now(timezone.utc)
        active_hazards = HazardReport.query.filter(
            HazardReport.route_description == route_code,
            HazardReport.status.in_(["ACTIVE", "UNVERIFIED"]),
            HazardReport.expires_at > now,
        ).all()
        if not active_hazards:
            response = f"END Route {route_code}: No reported hazards. Route appears safe."
        else:
            hazard_lines = []
            for h in active_hazards:
                trust = "Verified" if h.status == "ACTIVE" else "Unverified report"
                hazard_lines.append(f"{trust}: {h.route_description}")
            response = "END HAZARD ALERT for route {}:\n{}".format(
                route_code, "\n".join(hazard_lines)
            )

    else:
        response = "END Invalid input. Please try again."

    r = make_response(response, 200)
    r.headers["Content-Type"] = "text/plain"
    return r


if __name__ == "__main__":
    app.run(port=8000, debug=True)