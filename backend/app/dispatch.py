"""Dispatch logic – finding riders and sending SMS comms."""
import logging
from datetime import datetime, timezone

from .models import Rider, EmergencyJob, HazardReport
from .sms import send_sms
from . import db

logger = logging.getLogger("app.dispatch")


def _get_active_hazard_note() -> str:
    """Return a short warning string if there are active hazards, else empty string."""
    now = datetime.now(timezone.utc)
    hazards = HazardReport.query.filter(
        HazardReport.status.in_(["ACTIVE", "UNVERIFIED"]),
        HazardReport.expires_at > now,
    ).all()
    if not hazards:
        return ""
    # Summarise: show first two at most so SMS stays short
    descriptions = [h.route_description for h in hazards[:2]]
    label = "HAZARD WARNING" if any(h.status == "ACTIVE" for h in hazards[:2]) else "UNVERIFIED REPORT"
    return f" ⚠️ {label}: {', '.join(descriptions)} may be impassable."


def notify_candidates(job: EmergencyJob) -> list:
    """Find available riders and blast the SOS broadcast SMS.

    The broadcast message:
    - Tells the rider what type of emergency it is and where
    - Includes any active hazard warning so they know about route risks upfront
    - Tells them to reply YES to claim the job (simple, natural language)
    """
    candidates = Rider.query.filter_by(status="AVAILABLE").all()
    if not candidates:
        logger.warning("notify_candidates: no available riders for job %s", job.job_id)
        return []

    hazard_note = _get_active_hazard_note()

    messages = []
    for rider in candidates:
        msg = (
            f"OkoaRoute SOS [Job {job.job_id}]: "
            f"{job.emergency_type} emergency at village {job.village_code}."
            f"{hazard_note} "
            f"Reply YES to accept this rescue and get full contact details."
        )
        send_sms(rider.phone_number, msg)
        messages.append((rider.phone_number, msg))
        logger.info("SOS broadcast sent to %s for job %s", rider.phone_number, job.job_id)

    return messages


def send_handshake(job: EmergencyJob) -> bool:
    """Exchange phone numbers + rider name between caller and assigned rider.

    - Caller gets: rider name + phone number (so they know who's coming)
    - Rider gets: caller's number + any active hazard/route warning
    """
    if not job.assigned_rider or not job.caller_number:
        logger.error("send_handshake: job %s missing rider or caller", job.job_id)
        return False

    rider = db.session.get(Rider, job.assigned_rider)
    rider_name = rider.name if rider else "Your rider"
    rider_number = job.assigned_rider
    caller_number = job.caller_number

    hazard_note = _get_active_hazard_note()

    msg_to_caller = (
        f"OkoaRoute [Job {job.job_id}]: {rider_name} is on the way to you. "
        f"Call them at {rider_number} to give your exact location."
    )
    msg_to_rider = (
        f"OkoaRoute [Job {job.job_id}] CONFIRMED. "
        f"Call the patient/proxy at {caller_number} for the exact location."
        f"{hazard_note}"
    )

    ok1 = send_sms(caller_number, msg_to_caller)
    ok2 = send_sms(rider_number, msg_to_rider)
    logger.info("Handshake sent for job %s (caller=%s, rider=%s)", job.job_id, ok1, ok2)
    return ok1 and ok2
