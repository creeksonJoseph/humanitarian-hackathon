from flask import request, make_response

# Use the app factory
from app import create_app, db
from app.models import EmergencyJob, Location, Rider, HazardReport
from app.dispatch import notify_candidates

app = create_app()



@app.route("/ussd", methods=["POST"])
def ussd_callback():
    """Handle HTTP POST requests from Africa's Talking USSD gateway."""
    session_id = request.values.get("sessionId", None)
    service_code = request.values.get("serviceCode", None)
    phone_number = request.values.get("phoneNumber", None)
    text = request.values.get("text", "")

    response = ""

    # --- MAIN MENU ---
    if text == "":
        response = "CON Welcome to OkoaRoute Emergency\n"
        response += "1. Request Emergency Boda\n"
        response += "2. Report Road Hazard\n"
        response += "3. Rider Check-in"

    # --- BRANCH 1: REQUEST EMERGENCY ---
    elif text == "1":
        response = "CON Select Emergency Type:\n"
        response += "1. Maternity\n"
        response += "2. Severe Injury\n"
        response += "3. Other Medical"

    elif text in ["1*1", "1*2", "1*3"]:
        response = "CON Enter your 4-digit Village Code (e.g., 4050 for Ekerenyo):"

    elif len(text.split("*")) == 3 and text.startswith("1*"):
        # User entered their village code. Example text: '1*1*4050'
        parts = text.split("*")
        emergency_type_map = {"1": "MATERNITY", "2": "INJURY", "3": "OTHER"}
        selected_type = emergency_type_map.get(parts[1], "OTHER")
        village_code = parts[2]

        # Save the SOS to the database
        try:
            new_job = EmergencyJob(
                caller_number=phone_number,
                village_code=village_code,
                emergency_type=selected_type,
                status="BROADCASTING",
            )
            db.session.add(new_job)
            db.session.commit()

            # TODO: Trigger the SMS broadcast out to the riders via sms_engine
            # broadcast_sos_to_riders(new_job.job_id, village_code)

            response = f"END SOS Sent. We are dispatching the nearest vetted rider to village {village_code}. You will receive an SMS shortly."
from flask import request, make_response

# Use the app factory
from app import create_app, db
from app.models import EmergencyJob, Location, Rider, HazardReport
from app.dispatch import notify_candidates

app = create_app()



@app.route("/ussd", methods=["POST"])
def ussd_callback():
    """Handle HTTP POST requests from Africa's Talking USSD gateway."""
    session_id = request.values.get("sessionId", None)
    service_code = request.values.get("serviceCode", None)
    phone_number = request.values.get("phoneNumber", None)
    text = request.values.get("text", "")

    response = ""

    # --- MAIN MENU ---
    if text == "":
        response = "CON Welcome to OkoaRoute Emergency\n"
        response += "1. Request Emergency Boda\n"
        response += "2. Report Road Hazard\n"
        response += "3. Rider Check-in"

    # --- BRANCH 1: REQUEST EMERGENCY ---
    elif text == "1":
        response = "CON Select Emergency Type:\n"
        response += "1. Maternity\n"
        response += "2. Severe Injury\n"
        response += "3. Other Medical"

    elif text in ["1*1", "1*2", "1*3"]:
        response = "CON Enter your 4-digit Village Code (e.g., 4050 for Ekerenyo):"

    elif len(text.split("*")) == 3 and text.startswith("1*"):
        # User entered their village code. Example text: '1*1*4050'
        parts = text.split("*")
        emergency_type_map = {"1": "MATERNITY", "2": "INJURY", "3": "OTHER"}
        selected_type = emergency_type_map.get(parts[1], "OTHER")
        village_code = parts[2]

        # Save the SOS to the database
        try:
            new_job = EmergencyJob(
                caller_number=phone_number,
                village_code=village_code,
                emergency_type=selected_type,
                status="BROADCASTING",
            )
            db.session.add(new_job)
            db.session.commit()

            # TODO: Trigger the SMS broadcast out to the riders via sms_engine
            # broadcast_sos_to_riders(new_job.job_id, village_code)

            response = f"END SOS Sent. We are dispatching the nearest vetted rider to village {village_code}. You will receive an SMS shortly."

        except Exception:
            db.session.rollback()
            # Failsafe if the village code doesn't exist in the Locations table
            response = "END Error processing request. Please ensure the village code is correct."

    # --- BRANCH 2 & 3 PLACEHOLDERS ---
    elif text == "2":
        response = "CON Enter 4-digit code of the hazardous route:"
        # Logic handled when user supplies the code below

    elif text == "3":
        response = "CON Enter your 4-digit Stage Code to check in:"
        # Logic handled when user supplies the code below

    # --- USSD: hazard code entered (e.g., '2*4050') ---
    elif len(text.split("*")) == 2 and text.startswith("2*"):
        parts = text.split("*")
        route_code = parts[1]
        try:
            # If phone belongs to a vetted rider mark ACTIVE, else UNVERIFIED
            rider = db.session.get(Rider, phone_number)
            status = "ACTIVE" if rider and rider.is_verified else "UNVERIFIED"
            hr = HazardReport(route_description=route_code, reported_by_number=phone_number, status=status)
            db.session.add(hr)
            db.session.commit()
            response = f"END Thank you. Hazard reported for route {route_code}."
        except Exception:
            db.session.rollback()
            response = "END Error saving hazard report."

    # --- USSD: rider check-in provided (e.g., '3*4050') ---
    elif len(text.split("*")) == 2 and text.startswith("3*"):
        parts = text.split("*")
        stage_code = parts[1]
        try:
            rider = db.session.get(Rider, phone_number)
            if rider:
                rider.last_known_location_code = stage_code
            else:
                # create a minimal rider record
                rider = Rider(phone_number=phone_number, name="", home_stage_code=stage_code, last_known_location_code=stage_code, is_verified=False, status="AVAILABLE")
                db.session.add(rider)
            db.session.commit()
            response = f"END Check-in successful. Current stage: {stage_code}."
        except Exception:
            db.session.rollback()
            response = "END Error processing check-in."

    else:
        response = "END Invalid input. Please try again."

    # Africa's Talking requires a plain text response
    r = make_response(response, 200)
    r.headers["Content-Type"] = "text/plain"
    return r


if __name__ == "__main__":
    # Run the server on port 8000
    app.run(port=8000, debug=True)
