"""SMS inbound and health-check blueprint."""
import re
import logging

from flask import Blueprint, request, jsonify
from sqlalchemy import text as sql_text

from . import db
from .models import EmergencyJob, Rider

logger = logging.getLogger("app.webhooks")

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
        send_sms(rider_phone, f"OkoaRoute: Job {job_id} not found.")
        return

    # Fix #2: accept BROADCASTING or ESCALATED jobs
    if job.status not in CLAIMABLE_STATUSES:
        send_sms(rider_phone, f"OkoaRoute: Job {job_id} already claimed. Thank you for responding.")
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
        send_sms(rider_phone, f"OkoaRoute: Job {job_id} was just taken. Better luck next time.")
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
    send_sms(rider_phone, f"OkoaRoute: Job {job_id} released. Another rider will be dispatched.")
    logger.info("Job %s dropped by %s and re-broadcast", job_id, rider_phone)
