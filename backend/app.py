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
        # Only show option 5 if this caller has an active CLAIMED job
        has_claimed_job = EmergencyJob.query.filter(
            EmergencyJob.caller_number == phone_number,
            EmergencyJob.status == "CLAIMED",
        ).first()
        if has_claimed_job:
            response += "\n5. Report Rider No-Show"

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
            # Fix #4: validate village code exists in Location table
            from app.models import Location
            if not db.session.get(Location, village_code):
                response = (
                    f"END Invalid village code '{village_code}'. "
                    f"Please check the code and try again."
                )
            else:
                # Duplicate SOS guard: don't let same caller open two active jobs
                existing = EmergencyJob.query.filter(
                    EmergencyJob.caller_number == phone_number,
                    EmergencyJob.status.in_(["BROADCASTING", "ESCALATED", "CLAIMED"]),
                ).first()
                if existing:
                    response = (
                        f"END Your SOS [Job {existing.job_id}] is already active "
                        f"and a rider has been notified. Please wait."
                    )
                else:
                    new_job = EmergencyJob(
                        caller_number=phone_number,
                        village_code=village_code,
                        emergency_type=selected_type,
                        status="BROADCASTING",
                    )
                    db.session.add(new_job)
                    db.session.commit()
                    reached = notify_candidates(new_job)
                    # Fix #3: tell caller honestly if no riders were notified
                    if reached:
                        response = (
                            f"END SOS logged [Job {new_job.job_id}]. "
                            f"Notifying nearest riders. You will receive an SMS with details shortly."
                        )
                    else:
                        response = (
                            f"END SOS logged [Job {new_job.job_id}]. "
                            f"No riders are nearby right now — we will keep searching and alert you."
                        )
        except Exception:
            db.session.rollback()
            response = "END Error processing request. Please try again."


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

            # Corroboration rule: if a second DIFFERENT number reports the same
            # route as UNVERIFIED, upgrade all UNVERIFIED reports on that route to ACTIVE.
            if status == "UNVERIFIED":
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                existing = HazardReport.query.filter(
                    HazardReport.route_description == route_code,
                    HazardReport.status == "UNVERIFIED",
                    HazardReport.reported_by_number != phone_number,
                    HazardReport.expires_at > now,
                ).first()
                if existing:
                    # Two independent strangers agree → mark all UNVERIFIED on this route as ACTIVE
                    HazardReport.query.filter(
                        HazardReport.route_description == route_code,
                        HazardReport.status == "UNVERIFIED",
                    ).update({"status": "ACTIVE"})
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

    elif len(text.split("*")) == 2 and text.startswith("4*"):
        from datetime import datetime, timezone
        route_code = text.split("*")[1]

        # Fix #7: validate the route code before querying
        if not route_code.isdigit() or len(route_code) != 4:
            response = "END Invalid route code. Please enter a 4-digit code (e.g., 4050)."
        else:
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

    # --- BRANCH 5: REPORT RIDER NO-SHOW ---
    elif text == "5":
        # Look up the caller's most recent CLAIMED job by their phone number
        job = EmergencyJob.query.filter(
            EmergencyJob.caller_number == phone_number,
            EmergencyJob.status == "CLAIMED",
        ).order_by(EmergencyJob.created_at.desc()).first()

        if not job:
            response = "END No active claimed job found for your number. If you still need help, select option 1."
        else:
            try:
                ghost_rider_phone = job.assigned_rider

                # Release the job for re-dispatch
                job.assigned_rider = None
                job.status = "BROADCASTING"
                job.cancellation_reason = "RIDER_NO_SHOW"

                # Free the rider back to AVAILABLE — they may just be stuck in mud.
                # It's on them not to accept another job they can't fulfil.
                if ghost_rider_phone:
                    ghost_rider = db.session.get(Rider, ghost_rider_phone)
                    if ghost_rider:
                        ghost_rider.status = "AVAILABLE"

                db.session.commit()

                # Re-broadcast to all remaining available riders
                notify_candidates(job)

                response = (
                    f"END Noted. Finding you a new rider for Job {job.job_id}. "
                    f"You will receive an SMS shortly. The previous rider has been flagged."
                )
            except Exception:
                db.session.rollback()
                response = "END Error processing your report. Please try again."

    else:
        response = "END Invalid input. Please try again."

    r = make_response(response, 200)
    r.headers["Content-Type"] = "text/plain"
    return r


if __name__ == "__main__":
    app.run(port=8000, debug=True)