"""Dispatch logic – finding riders and sending SMS comms."""
import logging
from datetime import datetime, timezone

from .models import Rider, EmergencyJob, HazardReport
from .sms import send_sms
from . import db

logger = logging.getLogger("app.dispatch")

# How many local riders to blast in the first wave
LOCAL_BLAST_LIMIT = 5


def _get_active_hazard_note() -> str:
    """Return a short warning string if there are active hazards, else empty string."""
    now = datetime.now(timezone.utc)
    hazards = HazardReport.query.filter(
        HazardReport.status.in_(["ACTIVE", "UNVERIFIED"]),
        HazardReport.expires_at > now,
    ).all()
    if not hazards:
        return ""
    descriptions = [h.route_description for h in hazards[:2]]
    label = "HAZARD WARNING" if any(h.status == "ACTIVE" for h in hazards[:2]) else "UNVERIFIED REPORT"
    return f" ⚠️ {label}: {', '.join(descriptions)} may be impassable."


def _build_sos_message(job: EmergencyJob, hazard_note: str, surge: bool = False) -> str:
    prefix = "🚨 URGENT SOS" if surge else "OkoaRoute SOS"
    return (
        f"{prefix} [Job {job.job_id}]: "
        f"{job.emergency_type} emergency at village {job.village_code}."
        f"{hazard_note} "
        f"Reply YES to accept this rescue and get full contact details."
    )


def notify_candidates(job: EmergencyJob, surge: bool = False) -> list:
    """Broadcast SOS to riders using a proximity-first strategy.

    Wave 1 (initial dispatch):
        Query riders whose last_known_location_code matches the job's village_code.
        If fewer than LOCAL_BLAST_LIMIT are found, fill up to the limit from
        riders at any location (ordered by availability).
        This ensures local riders are always preferred.

    Wave 2 (escalation — called by escalate_unanswered_jobs task after 3 min):
        surge=True → blast ALL remaining AVAILABLE riders with a surge bonus message.
    """
    hazard_note = _get_active_hazard_note()
    msg = _build_sos_message(job, hazard_note, surge=surge)

    if surge:
        # Escalation: blast everyone who hasn't already been notified
        # (job is still BROADCASTING, so assigned_rider is None)
        candidates = Rider.query.filter_by(status="AVAILABLE").all()
    else:
        # Wave 1: local riders first
        local_riders = (
            Rider.query
            .filter_by(status="AVAILABLE", last_known_location_code=job.village_code)
            .limit(LOCAL_BLAST_LIMIT)
            .all()
        )
        if len(local_riders) < LOCAL_BLAST_LIMIT:
            # Not enough local — top up from anywhere
            local_phones = [r.phone_number for r in local_riders]
            extras = (
                Rider.query
                .filter(
                    Rider.status == "AVAILABLE",
                    Rider.phone_number.notin_(local_phones),
                )
                .limit(LOCAL_BLAST_LIMIT - len(local_riders))
                .all()
            )
            candidates = local_riders + extras
        else:
            candidates = local_riders

    if not candidates:
        logger.warning("notify_candidates: no available riders for job %s (surge=%s)", job.job_id, surge)
        return []

    messages = []
    for rider in candidates:
        send_sms(rider.phone_number, msg)
        messages.append((rider.phone_number, msg))
        logger.info("SOS broadcast sent to %s for job %s (surge=%s)", rider.phone_number, job.job_id, surge)

    return messages


def send_handshake(job: EmergencyJob) -> bool:
    """Exchange phone numbers + rider name between caller and assigned rider."""
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
