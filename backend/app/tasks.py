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

    The initial dispatch only contacts local riders. If none accept within 3 minutes,
    this function fires a surge broadcast to ALL available riders with a bonus message,
    and sends the caller a status update so they know the search is expanding.

    Run via cron every 3 minutes:
        */3 * * * * flask run-tasks escalate
    """
    from .dispatch import notify_candidates
    from .sms import send_sms

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=3)
    unanswered = EmergencyJob.query.filter(
        EmergencyJob.status == "BROADCASTING",
        EmergencyJob.created_at < cutoff,
    ).all()

    count = 0
    for job in unanswered:
        # Notify the caller that we're expanding the search
        send_sms(
            job.caller_number,
            f"OkoaRoute [Job {job.job_id}]: No rider available nearby yet. "
            f"Expanding search to riders from surrounding areas. Please stand by."
        )
        # Surge broadcast to ALL available riders
        notify_candidates(job, surge=True)
        count += 1
        logger.info("Escalated job %s to surge broadcast", job.job_id)

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
