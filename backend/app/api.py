from flask import Blueprint, request, jsonify, current_app
from . import db
from .models import HazardReport, EmergencyJob, Rider, Location
from .dispatch import notify_candidates
from .auth import require_api_key
from .schemas import HazardReportSchema, JobCreateSchema, RiderCheckinSchema, ClaimJobSchema
from .errors import ApplicationError

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/hazards", methods=["POST"])  # create hazard report
def create_hazard():
    payload = HazardReportSchema().load(request.get_json() or {})

    report = HazardReport(**payload)
    db.session.add(report)
    db.session.commit()
    return jsonify({"id": report.id}), 201


@bp.route("/jobs", methods=["POST"])  # create emergency job
def create_job():
    payload = JobCreateSchema().load(request.get_json() or {})

    job = EmergencyJob(caller_number=payload["caller_number"], village_code=payload["village_code"], emergency_type=payload["emergency_type"], status="BROADCASTING")
    db.session.add(job)
    db.session.commit()

    # trigger dispatch (synchronous for MVP)
    try:
        notify_candidates(job)
    except Exception:
        current_app.logger.exception("dispatch failed")

    return jsonify({"job_id": job.job_id}), 201


@bp.route("/riders/<phone>/checkin", methods=["POST"])  # rider check-in
def rider_checkin(phone):
    payload = RiderCheckinSchema().load(request.get_json() or {})

    stage = payload["stage_code"]
    rider = db.session.get(Rider, phone)
    if not rider:
        raise ApplicationError(status_code=404, code="rider_not_found", message="Rider not found")

    rider.last_known_location_code = stage
    db.session.commit()
    return jsonify({"status": "ok"})


@bp.route("/jobs/<int:job_id>/claim", methods=["POST"])  # claim a job by rider
@require_api_key
def claim_job(job_id):
    payload = ClaimJobSchema().load(request.get_json() or {})

    rider_phone = payload["rider_phone"]
    job = db.session.get(EmergencyJob, job_id)
    if not job:
        raise ApplicationError(status_code=404, code="job_not_found", message="Job not found")
    if job.status != "BROADCASTING":
        raise ApplicationError(status_code=400, code="job_not_available", message="Job not available")
    job.assigned_rider = rider_phone
    job.status = "CLAIMED"
    db.session.commit()
    return jsonify({"status": "claimed"})
