"""Application entry-point.

Run in development:
    python app.py

Run with gunicorn (production):
    gunicorn app:app

All routes (/ussd, /sms, /health, /api/*) are registered inside
`create_app()` via blueprints so they are available both here and in tests.
"""
import os
import logging
from dotenv import load_dotenv

# Show INFO-level logs from all app.* loggers in the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)

# Load config/.env so AT_API_KEY and other secrets are available to create_app()
load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))

from flask import request, make_response

from app import create_app, db
from app.models import EmergencyJob, Rider, HazardReport
from app.dispatch import notify_candidates

app = create_app()
logger = logging.getLogger("app.ussd")


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
        # Show option 5 if this caller has ANY active job (searching or rider assigned)
        has_active_job = EmergencyJob.query.filter(
            EmergencyJob.caller_number == phone_number,
            EmergencyJob.status.in_(["BROADCASTING", "ESCALATED", "CLAIMED"]),
        ).first()
        if has_active_job:
            response += "\n5. Report Rider No-Show / Re-send SOS"

    # --- BRANCH 1: REQUEST EMERGENCY ---
    elif text == "1":
        # Check immediately if this caller already has an active job
        active_job = EmergencyJob.query.filter(
            EmergencyJob.caller_number == phone_number,
            EmergencyJob.status.in_(["BROADCASTING", "ESCALATED", "CLAIMED"]),
        ).order_by(EmergencyJob.created_at.desc()).first()

        if active_job:
            if active_job.status == "CLAIMED":
                response = (
                    "END A rider has already been dispatched to you. "
                    "Please wait. If the rider has not arrived, dial again and select 5."
                )
            else:
                response = (
                    "END Your SOS is active and we are still searching for a rider. "
                    "Please wait."
                )
        else:
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
                    if existing.status == "CLAIMED":
                        response = (
                            f"END Your SOS is already active "
                            f"and claimed by a rider. We are monitoring the situation."
                        )
                    else:
                        response = (
                            f"END Your SOS is currently active. "
                            f"We are still searching for an available rider."
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
                    logger.info(
                        "[SOS CREATED] Job %s | type=%s village=%s caller=%s",
                        new_job.job_id, selected_type, village_code, phone_number
                    )
                    reached = notify_candidates(new_job)
                    logger.info(
                        "[SOS DISPATCHED] Job %s | sent to %d rider(s): %s",
                        new_job.job_id,
                        len(reached),
                        ", ".join(r[0] for r in reached) if reached else "none"
                    )
                    # Fix #3: tell caller honestly if no riders were notified
                    if reached:
                        response = (
                            "END SOS sent. Nearest riders have been notified. "
                            "You will receive an SMS with details shortly."
                        )
                    else:
                        logger.warning("[SOS NO RIDERS] Job %s — no AVAILABLE riders found", new_job.job_id)
                        response = (
                            "END SOS sent. No riders are nearby right now — "
                            "we will keep searching and alert you by SMS."
                        )
        except Exception as exc:
            db.session.rollback()
            logger.exception("[SOS ERROR] caller=%s village=%s error=%s", phone_number, village_code if 'village_code' in dir() else '?', exc)
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
                # Existing rider — update location
                rider.last_known_location_code = stage_code
                rider.status = "AVAILABLE"  # re-activate if they'd gone offline
                db.session.commit()
                response = f"END Check-in successful. Stage: {stage_code}. You will receive SOS alerts."
            else:
                # Self-registration: anyone can volunteer during a disaster.
                # Name defaults to their phone number — admin can update later.
                new_rider = Rider(
                    phone_number=phone_number,
                    name=phone_number,          # placeholder name
                    home_stage_code=stage_code,
                    last_known_location_code=stage_code,
                    is_verified=False,          # unverified until admin confirms
                    status="AVAILABLE",
                )
                db.session.add(new_rider)
                db.session.commit()
                response = (
                    f"END Registered & checked in at stage {stage_code}. "
                    f"You will receive SOS rescue alerts. Thank you for volunteering."
                )
        except Exception:
            db.session.rollback()
            response = "END Error processing check-in. Please try again."

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
                verified = sum(1 for h in active_hazards if h.status == "ACTIVE")
                unverified = len(active_hazards) - verified
                # Show the most recently reported time
                latest = max(active_hazards, key=lambda h: h.reported_at or h.expires_at)
                reported_str = latest.reported_at.strftime("%d %b %H:%M") if latest.reported_at else "recently"

                parts = []
                if verified:
                    parts.append(f"{verified} verified report{'s' if verified > 1 else ''}")
                if unverified:
                    parts.append(f"{unverified} unverified report{'s' if unverified > 1 else ''}")

                response = (
                    f"END ⚠️ HAZARD ALERT: Route {route_code}\n"
                    f"{', '.join(parts)}.\n"
                    f"Last reported: {reported_str}.\n"
                    f"Use caution or find an alternative route."
                )

    # --- BRANCH 5: REPORT NO-SHOW / RE-SEND SOS ---
    elif text == "5":
        job = EmergencyJob.query.filter(
            EmergencyJob.caller_number == phone_number,
            EmergencyJob.status.in_(["BROADCASTING", "ESCALATED", "CLAIMED"]),
        ).order_by(EmergencyJob.created_at.desc()).first()

        if not job:
            response = "END No active job found for your number. Select option 1 to call for help."
        else:
            try:
                if job.status == "CLAIMED":
                    # Rider assigned but hasn't arrived — free them and re-broadcast
                    ghost_rider_phone = job.assigned_rider
                    job.assigned_rider = None
                    job.status = "BROADCASTING"
                    job.cancellation_reason = "RIDER_NO_SHOW"
                    if ghost_rider_phone:
                        ghost_rider = db.session.get(Rider, ghost_rider_phone)
                        if ghost_rider:
                            ghost_rider.status = "AVAILABLE"
                    db.session.commit()
                    notify_candidates(job)
                    response = (
                        f"END Noted. Finding you a new rider. "
                        f"You will receive an SMS shortly."
                    )
                else:
                    # Still searching — force immediate surge to all available riders
                    job.status = "BROADCASTING"
                    db.session.commit()
                    reached = notify_candidates(job, surge=True)
                    if reached:
                        response = (
                            f"END Re-sending SOS to all available riders. "
                            f"You will receive an SMS confirmation."
                        )
                    else:
                        response = (
                            f"END No riders available right now. "
                            f"Please call a health facility directly."
                        )
            except Exception as exc:
                db.session.rollback()
                logger.exception("[OPTION 5 ERROR] caller=%s error=%s", phone_number, exc)
                response = "END Error processing. Please try again."

    else:
        response = "END Invalid input. Please try again."

    r = make_response(response, 200)
    r.headers["Content-Type"] = "text/plain"
    return r


if __name__ == "__main__":
    app.run(port=8000, debug=True)