"""Background maintenance tasks for OkoaRoute.

These are meant to be called from cron jobs or Flask CLI commands.
Each function is self-contained and returns the count of modified rows.

Cron setup example:
    # auto-resolve stale jobs every 15 minutes
    */15 * * * * cd /path/to/backend && .venv/bin/flask run-tasks stale-jobs

    # nightly location reset at 3 AM
    0 3 * * * cd /path/to/backend && .venv/bin/flask run-tasks reset-locations

    # expire old hazards every 30 minutes
    */30 * * * * cd /path/to/backend && .venv/bin/flask run-tasks expire-hazards
"""
import logging
from datetime import datetime, timedelta, timezone

from . import db
from .models import EmergencyJob, HazardReport, Rider

logger = logging.getLogger("app.tasks")


def escalate_unanswered_jobs() -> int:
    """Re-broadcast BROADCASTING jobs that have had no rider accept for 3+ minutes.

    Fix #2: after escalating, sets status to ESCALATED so this function won't
    re-process the same job on the next cron run — preventing broadcast spam.

    Fix #5: if the surge blast also finds zero riders, sends the caller a final
    "no riders available" SMS so they aren't left waiting in silence.

    Run via cron every 3 minutes:
        */3 * * * * flask run-tasks escalate
    """
    from .dispatch import notify_candidates
    from .sms import send_sms

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=3)
    # Only escalate pure BROADCASTING jobs (not already ESCALATED, CLAIMED, etc.)
    unanswered = EmergencyJob.query.filter(
        EmergencyJob.status == "BROADCASTING",
        EmergencyJob.created_at < cutoff,
    ).all()

    count = 0
    for job in unanswered:
        # Notify the caller that we're expanding the search
        send_sms(
            job.caller_number,
            f"OkoaRoute [Job {job.job_id}]: No rider nearby yet. "
            f"Expanding search to surrounding areas. Please stand by."
        )

        # Surge blast to riders outside the local area (local already got wave 1)
        reached = notify_candidates(job, surge=True)

        if not reached:
            # Fix #5: no riders at all — don't leave caller hanging
            send_sms(
                job.caller_number,
                f"OkoaRoute [Job {job.job_id}]: We could not find an available rider "
                f"at this time. Please call your nearest health facility directly or "
                f"try again shortly."
            )
            job.status = "CANCELLED"
            job.cancellation_reason = "NO_RIDERS_AVAILABLE"
        else:
            # Fix #2: mark as escalated so cron won't re-broadcast
            job.status = "ESCALATED"

        db.session.commit()
        count += 1
        logger.info("Escalated job %s (reached %d riders)", job.job_id, len(reached))

    return count



def auto_resolve_stale_jobs() -> int:
    """Auto-resolve CLAIMED jobs older than 3 hours.

    Frees up the assigned rider and stamps the job as AUTO_RESOLVED so
    the fleet doesn't silently shrink because riders never confirm delivery.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=3)
    stale_jobs = (
        EmergencyJob.query.filter(
            EmergencyJob.status == "CLAIMED",
            EmergencyJob.created_at < cutoff,
        ).all()
    )

    for job in stale_jobs:
        job.status = "AUTO_RESOLVED"
        job.resolved_at = datetime.now(timezone.utc)
        job.cancellation_reason = "SYSTEM_TIMEOUT"

        # Free up the rider so they can receive future dispatches
        if job.assigned_rider:
            rider = db.session.get(Rider, job.assigned_rider)
            if rider:
                rider.status = "AVAILABLE"

    db.session.commit()
    if stale_jobs:
        logger.info("auto_resolve_stale_jobs: resolved %d stale jobs", len(stale_jobs))
    return len(stale_jobs)


def reset_rider_locations() -> int:
    """Reset all riders' last_known_location_code to their home_stage_code.

    Run at 3 AM daily. Boda riders go home overnight, so starting every day
    from their home stage keeps the dispatch engine accurate.
    """
    riders = Rider.query.all()
    for rider in riders:
        rider.last_known_location_code = rider.home_stage_code
    db.session.commit()
    logger.info("reset_rider_locations: reset %d riders to home stage", len(riders))
    return len(riders)


def expire_old_hazards() -> int:
    """Mark hazard reports whose 12-hour TTL has elapsed as EXPIRED.

    Keeps the routing engine from blocking routes based on stale data.
    """
    now = datetime.now(timezone.utc)
    expired = HazardReport.query.filter(
        HazardReport.expires_at < now,
        HazardReport.status.in_(["ACTIVE", "UNVERIFIED"]),
    ).all()

    for hazard in expired:
        hazard.status = "EXPIRED"

    db.session.commit()
    if expired:
        logger.info("expire_old_hazards: expired %d hazard reports", len(expired))
    return len(expired)
