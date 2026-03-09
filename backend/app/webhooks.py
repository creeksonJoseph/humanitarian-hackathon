"""SMS inbound and health-check blueprint."""
import re
import logging

from flask import Blueprint, request, jsonify, make_response
from sqlalchemy import text as sql_text

from . import db
from .models import EmergencyJob, Rider

logger = logging.getLogger("app.webhooks")
ussd_logger = logging.getLogger("app.ussd")

bp = Blueprint("webhooks", __name__)

# Jobs in these statuses can still be claimed by a rider
CLAIMABLE_STATUSES = {"BROADCASTING", "ESCALATED"}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@bp.route("/health")
def health_check():
    """Lightweight health-check for monitoring / uptime services."""
    try:
        db.session.execute(sql_text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        db_status = f"error: {exc}"

    return jsonify(
        {
            "status": "ok" if db_status == "ok" else "degraded",
            "database": db_status,
            "version": "1.0.0",
        }
    )


# ---------------------------------------------------------------------------
# SMS Delivery Report Webhook
# ---------------------------------------------------------------------------

@bp.route("/sms/delivery", methods=["POST"])
def sms_delivery_report():
    """Receive SMS delivery status callbacks from Africa's Talking.

    Set this URL in AT dashboard → SMS → Delivery Reports callback.
    AT retries every minute for up to 12 hours until it gets HTTP 200.
    """
    msg_id     = request.values.get("id", "unknown")
    status     = request.values.get("status", "unknown")
    phone      = request.values.get("phoneNumber", "unknown")
    network    = request.values.get("networkCode", "unknown")
    failure    = request.values.get("failureReason", "")

    if status.lower() in ("success", "delivered"):
        logger.info(
            "[DELIVERY OK] msgId=%s to=%s network=%s",
            msg_id, phone, network
        )
    else:
        logger.warning(
            "[DELIVERY FAILED] msgId=%s to=%s status=%s reason=%s network=%s",
            msg_id, phone, status, failure, network
        )

    # Must return 200 — AT retries until it gets 200
    return ("", 200)


# ---------------------------------------------------------------------------
# Inbound SMS Webhook
# ---------------------------------------------------------------------------

@bp.route("/sms", methods=["POST"])
def sms_callback():
    """Handle inbound SMS from Africa's Talking.

    Supported commands (case-insensitive):
        YES              – claim the most recent claimable job
        ACCEPT <job_id>  – claim a specific job by ID
        DROP <job_id>    – surrender a claimed job so it re-broadcasts
    """
    from_number = request.values.get("from", "").strip()
    text = request.values.get("text", "").strip().upper()

    logger.info(
        "[INBOUND SMS] from=%s text='%s' (Full Payload: %s)",
        from_number, text, dict(request.values)
    )

    if text == "YES":
        # Fix #2: accept jobs in BROADCASTING or ESCALATED state
        job = (
            EmergencyJob.query
            .filter(EmergencyJob.status.in_(CLAIMABLE_STATUSES))
            .order_by(EmergencyJob.created_at.desc())
            .first()
        )
        if job:
            _handle_accept(from_number, job.job_id)
        else:
            from .sms import send_sms
            # If no broadcasting job exists, check if there's a recently CLAIMED one
            recently_claimed = (
                EmergencyJob.query
                .filter(EmergencyJob.status.in_(["CLAIMED", "RESOLVED"]))
                .order_by(EmergencyJob.created_at.desc())
                .first()
            )
            # If there was a job in the last few hours, it was probably the one they were replying to
            if recently_claimed:
                send_sms(from_number, "OkoaRoute: This rescue has already been claimed by another rider. Thank you for responding.")
            else:
                send_sms(from_number, "OkoaRoute: No active emergencies right now. Thank you for being ready.")

    elif re.match(r"^ACCEPT\s+(\d+)$", text):
        job_id = int(re.match(r"^ACCEPT\s+(\d+)$", text).group(1))
        _handle_accept(from_number, job_id)

    elif re.match(r"^DROP\s+(\d+)$", text):
        job_id = int(re.match(r"^DROP\s+(\d+)$", text).group(1))
        _handle_drop(from_number, job_id)

    return ("", 200)


def _handle_accept(rider_phone: str, job_id: int):
    """Atomically claim a job for the first rider who replies YES/ACCEPT."""
    from .sms import send_sms
    from .dispatch import send_handshake

    job = db.session.get(EmergencyJob, job_id)
    if not job:
        send_sms(rider_phone, "OkoaRoute: Job not found or has already been resolved.")
        return

    # Fix #2: accept BROADCASTING or ESCALATED jobs
    if job.status not in CLAIMABLE_STATUSES:
        send_sms(rider_phone, "OkoaRoute: This rescue has already been claimed by another rider. Thank you for responding.")
        return

    rider = db.session.get(Rider, rider_phone)
    if not rider:
        send_sms(rider_phone, "OkoaRoute: Your number is not registered as a rider. Contact admin.")
        return

    # Fix #1: block ON_JOB riders from claiming a second job
    if rider.status != "AVAILABLE":
        send_sms(
            rider_phone,
            f"OkoaRoute: You are currently {rider.status.lower().replace('_', ' ')}. "
            f"Complete your current job before accepting a new rescue."
        )
        return

    # Concurrency lock – first writer wins
    try:
        job.assigned_rider = rider_phone
        job.status = "CLAIMED"
        rider.status = "ON_JOB"
        db.session.commit()
    except Exception:
        db.session.rollback()
        send_sms(rider_phone, "OkoaRoute: This rescue was just taken by another rider. Better luck next time.")
        return

    send_handshake(job)
    logger.info("Job %s claimed by %s", job_id, rider_phone)


def _handle_drop(rider_phone: str, job_id: int):
    """Release a claimed job back to BROADCASTING."""
    from .sms import send_sms
    from .dispatch import notify_candidates

    job = db.session.get(EmergencyJob, job_id)
    if not job or job.assigned_rider != rider_phone:
        return

    try:
        job.assigned_rider = None
        job.status = "BROADCASTING"
        rider = db.session.get(Rider, rider_phone)
        if rider:
            rider.status = "AVAILABLE"
        db.session.commit()
    except Exception:
        db.session.rollback()
        return

    notify_candidates(job)
    send_sms(rider_phone, "OkoaRoute: You have dropped this rescue. Another rider will be dispatched.")
    logger.info("Job %s dropped by %s and re-broadcast", job_id, rider_phone)


# ---------------------------------------------------------------------------
# USSD Webhook  – Africa's Talking calls this on every keypress
# ---------------------------------------------------------------------------

@bp.route("/ussd", methods=["POST"])
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
        from .models import Location
        from .dispatch import notify_candidates
        
        parts = text.split("*")
        emergency_type_map = {"1": "MATERNITY", "2": "INJURY", "3": "OTHER"}
        selected_type = emergency_type_map.get(parts[1], "OTHER")
        village_code = parts[2]
        try:
            if not db.session.get(Location, village_code):
                response = (
                    f"END Invalid village code '{village_code}'. "
                    f"Please check the code and try again."
                )
            else:
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
                    ussd_logger.info(
                        "[SOS CREATED] Job %s | type=%s village=%s caller=%s",
                        new_job.job_id, selected_type, village_code, phone_number
                    )
                    reached = notify_candidates(new_job)
                    ussd_logger.info(
                        "[SOS DISPATCHED] Job %s | sent to %d rider(s): %s",
                        new_job.job_id,
                        len(reached),
                        ", ".join(r[0] for r in reached) if reached else "none"
                    )
                    if reached:
                        response = (
                            "END SOS sent. Nearest riders have been notified. "
                            "You will receive an SMS with details shortly."
                        )
                    else:
                        ussd_logger.warning("[SOS NO RIDERS] Job %s — no AVAILABLE riders found", new_job.job_id)
                        response = (
                            "END SOS sent. No riders are nearby right now — "
                            "we will keep searching and alert you by SMS."
                        )
        except Exception as exc:
            db.session.rollback()
            ussd_logger.exception("[SOS ERROR] caller=%s village=%s error=%s", phone_number, village_code if 'village_code' in dir() else '?', exc)
            response = "END Error processing request. Please try again."


    # --- BRANCH 2: REPORT HAZARD ---
    elif text == "2":
        response = "CON Select Hazard Type:\n"
        response += "1. Floods\n"
        response += "2. Downed Power Lines\n"
        response += "3. Road Block\n"
        response += "4. Other"

    elif text in ["2*1", "2*2", "2*3", "2*4"]:
        response = "CON Enter 4-digit code of the hazardous route:"

    elif len(text.split("*")) == 3 and text.startswith("2*"):
        from .models import HazardReport
        from datetime import datetime, timezone
        
        parts = text.split("*")
        hazard_type_map = {"1": "FLOOD", "2": "POWER_LINES", "3": "ROAD_BLOCK", "4": "OTHER"}
        hazard_type = hazard_type_map.get(parts[1], "OTHER")
        route_code = parts[2]
        try:
            rider = db.session.get(Rider, phone_number)
            status = "ACTIVE" if (rider and rider.is_verified) else "UNVERIFIED"
            if rider:
                rider.last_known_location_code = route_code

            hr = HazardReport(hazard_type=hazard_type, route_description=route_code, reported_by_number=phone_number, status=status)
            db.session.add(hr)
            db.session.commit()

            if status == "UNVERIFIED":
                now = datetime.now(timezone.utc)
                existing = HazardReport.query.filter(
                    HazardReport.route_description == route_code,
                    HazardReport.status == "UNVERIFIED",
                    HazardReport.reported_by_number != phone_number,
                    HazardReport.expires_at > now,
                ).first()
                if existing:
                    HazardReport.query.filter(
                        HazardReport.route_description == route_code,
                        HazardReport.status == "UNVERIFIED",
                    ).update({"status": "ACTIVE"})
                    db.session.commit()

            response = f"END Thank you. Hazard reported for route {route_code}."
        except Exception:
            db.session.rollback()
            response = "END Error saving hazard report."


    # --- BRANCH 3: RIDER PORTAL ---
    elif text == "3":
        response = "CON Rider Portal:\n"
        response += "1. Check in current location\n"
        response += "2. Register as a Rider"
        
    # --- BRANCH 3.1: RIDER CHECK-IN ---
    elif text == "3*1":
        response = "CON Enter your 4-digit Stage Code to check in:"

    elif len(text.split("*")) == 3 and text.startswith("3*1*"):
        parts = text.split("*")
        stage_code = parts[2]
        try:
            rider = db.session.get(Rider, phone_number)
            if rider:
                rider.last_known_location_code = stage_code
                rider.status = "AVAILABLE"
                db.session.commit()
                response = f"END Check-in successful. Stage: {stage_code}. You will receive SOS alerts."
            else:
                response = "END You are not registered. Dial again and select 'Register as a Rider'."
        except Exception:
            db.session.rollback()
            response = "END Error processing check-in. Please try again."

    # --- BRANCH 3.2: RIDER REGISTRATION ---
    elif text == "3*2":
        response = "CON Enter your Full Name:"
        
    elif len(text.split("*")) == 3 and text.startswith("3*2*"):
        response = "CON Enter your 4-digit Home Stage Code:"
        
    elif len(text.split("*")) == 4 and text.startswith("3*2*"):
        parts = text.split("*")
        name = parts[2]
        stage_code = parts[3]
        try:
            rider = db.session.get(Rider, phone_number)
            if rider:
                response = "END You are already registered as a rider."
            else:
                new_rider = Rider(
                    phone_number=phone_number,
                    name=name,          
                    home_stage_code=stage_code,
                    last_known_location_code=stage_code,
                    is_verified=False,
                    status="AVAILABLE",
                )
                db.session.add(new_rider)
                db.session.commit()
                response = (
                    f"END You have successfully registered pending approval."
                )
        except Exception:
            db.session.rollback()
            response = "END Error processing registration. Please try again."

    # --- BRANCH 4: CHECK ROUTE SAFETY ---
    elif text == "4":
        response = "CON Enter 4-digit route code to check (e.g., 4050 for Ekerenyo):"

    elif len(text.split("*")) == 2 and text.startswith("4*"):
        from datetime import datetime, timezone
        from .models import HazardReport
        
        route_code = text.split("*")[1]

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
        from .dispatch import notify_candidates
        
        job = EmergencyJob.query.filter(
            EmergencyJob.caller_number == phone_number,
            EmergencyJob.status.in_(["BROADCASTING", "ESCALATED", "CLAIMED"]),
        ).order_by(EmergencyJob.created_at.desc()).first()

        if not job:
            response = "END No active job found for your number. Select option 1 to call for help."
        else:
            try:
                if job.status == "CLAIMED":
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
                ussd_logger.exception("[OPTION 5 ERROR] caller=%s error=%s", phone_number, exc)
                response = "END Error processing. Please try again."

    else:
        response = "END Invalid input. Please try again."

    r = make_response(response, 200)
    r.headers["Content-Type"] = "text/plain"
    return r
