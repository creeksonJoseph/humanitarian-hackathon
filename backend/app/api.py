from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import text as sql_text

from . import db
from .models import HazardReport, EmergencyJob, Rider, Location
from .dispatch import notify_candidates
from .auth import require_api_key
from .schemas import HazardReportSchema, JobCreateSchema, RiderCheckinSchema, ClaimJobSchema
from .errors import ApplicationError

bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# Write endpoints (create resources)
# ---------------------------------------------------------------------------

@bp.route("/hazards", methods=["POST"])
def create_hazard():
    """Create a new hazard report. Anyone with a phone number can report."""
    payload = HazardReportSchema().load(request.get_json() or {})
    report = HazardReport(**payload)
    db.session.add(report)
    db.session.commit()
    return jsonify({"id": report.id}), 201


@bp.route("/jobs", methods=["POST"])
def create_job():
    """Create an emergency job and immediately broadcast to nearby riders."""
    payload = JobCreateSchema().load(request.get_json() or {})

    job = EmergencyJob(
        caller_number=payload["caller_number"],
        village_code=payload["village_code"],
        emergency_type=payload["emergency_type"],
        status="BROADCASTING",
    )
    db.session.add(job)
    db.session.commit()

    # Trigger dispatch (synchronous for MVP)
    try:
        notify_candidates(job)
    except Exception:
        current_app.logger.exception("dispatch failed")

    return jsonify({"job_id": job.job_id}), 201


@bp.route("/riders/<phone>/checkin", methods=["POST"])
def rider_checkin(phone):
    """Manual rider check-in – updates last_known_location_code."""
    payload = RiderCheckinSchema().load(request.get_json() or {})

    stage = payload["stage_code"]
    rider = db.session.get(Rider, phone)
    if not rider:
        raise ApplicationError(status_code=404, code="rider_not_found", message="Rider not found")

    rider.last_known_location_code = stage
    db.session.commit()
    return jsonify({"status": "ok"})


@bp.route("/jobs/<int:job_id>/claim", methods=["POST"])
@require_api_key
def claim_job(job_id):
    """Claim a broadcasting job on behalf of a rider (used internally by /sms handler)."""
    payload = ClaimJobSchema().load(request.get_json() or {})

    rider_phone = payload["rider_phone"]
    job = db.session.get(EmergencyJob, job_id)
    if not job:
        raise ApplicationError(status_code=404, code="job_not_found", message="Job not found")
    if job.status != "BROADCASTING":
        raise ApplicationError(status_code=409, code="job_not_available", message="Job already claimed")
    job.assigned_rider = rider_phone
    job.status = "CLAIMED"
    db.session.commit()
    return jsonify({"status": "claimed"})


# ---------------------------------------------------------------------------
# Read endpoints (dashboard data)
# ---------------------------------------------------------------------------

@bp.route("/stats", methods=["GET"])
def get_stats():
    """Live counter stats for the judge command-center dashboard."""
    active_hazards = HazardReport.query.filter(
        HazardReport.status.in_(["ACTIVE", "UNVERIFIED"]),
        HazardReport.expires_at > datetime.now(timezone.utc),
    ).count()

    return jsonify(
        {
            "jobs": {
                "broadcasting": EmergencyJob.query.filter_by(status="BROADCASTING").count(),
                "claimed": EmergencyJob.query.filter_by(status="CLAIMED").count(),
                "resolved": EmergencyJob.query.filter(
                    EmergencyJob.status.in_(["RESOLVED", "AUTO_RESOLVED"])
                ).count(),
                "cancelled": EmergencyJob.query.filter_by(status="CANCELLED").count(),
            },
            "riders": {
                "total": Rider.query.count(),
                "available": Rider.query.filter_by(status="AVAILABLE").count(),
                "on_job": Rider.query.filter_by(status="ON_JOB").count(),
                "offline": Rider.query.filter_by(status="OFFLINE").count(),
            },
            "hazards": {
                "active": active_hazards,
            },
        }
    )


@bp.route("/hazards", methods=["GET"])
def list_hazards():
    """Return all non-expired hazard reports, newest first."""
    now = datetime.now(timezone.utc)
    hazards = (
        HazardReport.query
        .filter(HazardReport.expires_at > now)
        .order_by(HazardReport.reported_at.desc())
        .limit(50)
        .all()
    )
    return jsonify(
        [
            {
                "id": h.id,
                "route_description": h.route_description,
                "reported_by_number": h.reported_by_number,
                "status": h.status,
                "reported_at": h.reported_at.isoformat() if h.reported_at else None,
                "expires_at": h.expires_at.isoformat() if h.expires_at else None,
            }
            for h in hazards
        ]
    )


@bp.route("/jobs", methods=["GET"])
def list_jobs():
    """Return the 50 most recent emergency jobs for the dashboard live feed."""
    jobs = (
        EmergencyJob.query
        .order_by(EmergencyJob.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify(
        [
            {
                "job_id": j.job_id,
                "caller_number": j.caller_number,
                "village_code": j.village_code,
                "emergency_type": j.emergency_type,
                "status": j.status,
                "assigned_rider": j.assigned_rider,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "resolved_at": j.resolved_at.isoformat() if j.resolved_at else None,
                "cancellation_reason": j.cancellation_reason,
            }
            for j in jobs
        ]
    )
