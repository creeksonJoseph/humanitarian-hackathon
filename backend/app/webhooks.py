"""SMS inbound and health-check blueprint."""
import re
import logging

from flask import Blueprint, request, jsonify
from sqlalchemy import text as sql_text

from . import db
from .models import EmergencyJob, Rider

logger = logging.getLogger("app.webhooks")

bp = Blueprint("webhooks", __name__)


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
# Inbound SMS Webhook
# ---------------------------------------------------------------------------

@bp.route("/sms", methods=["POST"])
def sms_callback():
    """Handle inbound SMS from Africa's Talking.

    Supported commands (case-insensitive):
        YES              – claim the most recent BROADCASTING job (simple, natural)
        ACCEPT <job_id>  – claim a specific job by ID (fallback, useful when rider
                           received multiple broadcasts)
        DROP <job_id>    – surrender a job so it re-broadcasts
    """
    from_number = request.values.get("from", "").strip()
    text = request.values.get("text", "").strip().upper()

    # Simple "YES" reply – find the most recent BROADCASTING job
    if text == "YES":
        job = (
            EmergencyJob.query
            .filter_by(status="BROADCASTING")
            .order_by(EmergencyJob.created_at.desc())
            .first()
        )
        if job:
            _handle_accept(from_number, job.job_id)
        else:
            from .sms import send_sms
            send_sms(from_number, "OkoaRoute: No active emergencies right now. Thank you for being ready.")

    # Specific "ACCEPT <id>" – for riders who received multiple broadcasts
    elif re.match(r"^ACCEPT\s+(\d+)$", text):
        job_id = int(re.match(r"^ACCEPT\s+(\d+)$", text).group(1))
        _handle_accept(from_number, job_id)

    # Drop a job
    elif re.match(r"^DROP\s+(\d+)$", text):
        job_id = int(re.match(r"^DROP\s+(\d+)$", text).group(1))
        _handle_drop(from_number, job_id)

    # Africa's Talking ignores the response body – always return 200
    return ("", 200)


def _handle_accept(rider_phone: str, job_id: int):
    """Atomically claim a job for the first rider who replies YES/ACCEPT."""
    from .sms import send_sms
    from .dispatch import send_handshake

    job = db.session.get(EmergencyJob, job_id)
    if not job:
        send_sms(rider_phone, f"OkoaRoute: Job {job_id} not found.")
        return

    if job.status != "BROADCASTING":
        send_sms(rider_phone, f"OkoaRoute: Job {job_id} already claimed. Thank you for responding.")
        return

    rider = db.session.get(Rider, rider_phone)
    if not rider:
        send_sms(rider_phone, "OkoaRoute: Your number is not registered as a rider. Contact admin.")
        return

    # Concurrency lock – first writer wins
    try:
        job.assigned_rider = rider_phone
        job.status = "CLAIMED"
        rider.status = "ON_JOB"
        db.session.commit()
    except Exception:
        db.session.rollback()
        send_sms(rider_phone, f"OkoaRoute: Job {job_id} was just taken. Better luck next time.")
        return

    # Send full contact details to both parties
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
    send_sms(rider_phone, f"OkoaRoute: Job {job_id} released. Another rider will be dispatched.")
    logger.info("Job %s dropped by %s and re-broadcast", job_id, rider_phone)
