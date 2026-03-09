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
        f"{prefix}: "
        f"{job.emergency_type} emergency at village {job.village_code}."
        f"{hazard_note} "
        f"Reply YES to accept this rescue and get full contact details."
    )


def notify_candidates(job: EmergencyJob, surge: bool = False) -> list:
    """Broadcast SOS to riders using a proximity-first strategy.

    Wave 1 (surge=False):
        Local riders (last_known_location_code == village_code) up to LOCAL_BLAST_LIMIT.
        Topped up from anywhere if not enough local riders available.

    Wave 2 / Escalation (surge=True):
        Fix #6 — only contacts riders NOT in the local area, so local riders
        don't receive a duplicate. They already got wave 1.
        Genuinely new riders from surrounding areas get the message for the first time.
    """
    hazard_note = _get_active_hazard_note()
    msg = _build_sos_message(job, hazard_note, surge=surge)

    if surge:
        # Fix #6: Exclude riders who were already in the local blast (same location)
        # to avoid sending the same SOS twice to the same person.
        candidates = (
            Rider.query
            .filter(
                Rider.status == "AVAILABLE",
                Rider.last_known_location_code != job.village_code,
            )
            .all()
        )
    else:
        # Wave 1: local riders first (no maximum limit, alert everyone locally)
        local_riders = (
            Rider.query
            .filter_by(status="AVAILABLE", last_known_location_code=job.village_code)
            .all()
        )
        if len(local_riders) < LOCAL_BLAST_LIMIT:
            local_phones = [r.phone_number for r in local_riders]
            extras = (
                Rider.query
                .filter(
                    Rider.status == "AVAILABLE",
                    Rider.phone_number.notin_(local_phones) if local_phones else True,
                )
                .limit(LOCAL_BLAST_LIMIT - len(local_riders))
                .all()
            )
            candidates = local_riders + extras
        else:
            candidates = local_riders

    messages = []
    if candidates:
        phones = [rider.phone_number for rider in candidates]
        send_sms(phones, msg)
        for phone in phones:
            messages.append((phone, msg))
            logger.info("SOS broadcast sent to %s for job %s (surge=%s)", phone, job.job_id, surge)
    else:
        logger.warning("notify_candidates: no available riders for job %s (surge=%s)", job.job_id, surge)

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
        f"OkoaRoute: {rider_name} is on the way to you. "
        f"Call them at {rider_number} to give your exact location."
    )
    msg_to_rider = (
        f"OkoaRoute CONFIRMED. "
        f"Call the patient/proxy at {caller_number} for the exact location."
        f"{hazard_note}"
    )

    ok1 = send_sms(caller_number, msg_to_caller)
    ok2 = send_sms(rider_number, msg_to_rider)
    logger.info("Handshake sent for job %s (caller=%s, rider=%s)", job.job_id, ok1, ok2)
    return ok1 and ok2
