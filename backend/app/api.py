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


@bp.route("/riders/<phone>/verify", methods=["POST"])
def verify_rider(phone):
    """Verify a rider from the Command Center and send SMS notification."""
    from .sms import send_sms
    
    rider = db.session.get(Rider, phone)
    if not rider:
        raise ApplicationError(status_code=404, code="rider_not_found", message="Rider not found")

    if rider.is_verified:
        return jsonify({"success": True, "message": "Rider is already verified"}), 200

    rider.is_verified = True
    db.session.commit()

    # Send notification SMS
    content = f"Dear {rider.name}, you have been approved as a rescue rider. Be ready to accept SOS alerts securely."
    try:
        send_sms(rider.phone_number, content)
    except Exception as e:
        current_app.logger.error(f"Failed to send verification SMS to {phone}: {e}")

    return jsonify({"success": True, "message": f"Rider {rider.name} verified successfully."}), 200


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
    place = request.args.get("place")
    
    sos_query = EmergencyJob.query
    rider_query = Rider.query
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    hazard_query = HazardReport.query.filter(HazardReport.expires_at > now_naive)

    if place:
        sos_query = sos_query.filter_by(village_code=place)
        rider_query = rider_query.filter_by(last_known_location_code=place)
        hazard_query = hazard_query.filter(HazardReport.route_description.ilike(f"%{place}%"))

    active_hazards = hazard_query.filter(HazardReport.status.in_(["ACTIVE", "UNVERIFIED"])).count()

    return jsonify(
        {
            "active_sos": sos_query.filter(EmergencyJob.status.in_(["BROADCASTING", "CLAIMED"])).count(),
            "total_sos": sos_query.count(),
            "available_riders": rider_query.filter_by(status="AVAILABLE").count(),
            "total_riders": rider_query.count(),
            "pending_riders": rider_query.filter_by(is_verified=False).count(),
            "active_hazards": hazard_query.filter(HazardReport.status.in_(["ACTIVE", "UNVERIFIED"])).count(),
            "unverified_hazards": hazard_query.filter_by(status="UNVERIFIED").count(),
        }
    )


@bp.route("/hazards", methods=["GET"])
def list_hazards():
    """Return all non-expired hazard reports, paginated, newest first."""
    place = request.args.get("place")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    
    query = HazardReport.query.filter(HazardReport.status.in_(["ACTIVE", "UNVERIFIED"]), HazardReport.expires_at > now_naive)
    
    if place:
        query = query.filter(HazardReport.route_description.ilike(f"%{place}%"))
        
    total_count = query.count()
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
    
    hazards = query.order_by(HazardReport.reported_at.desc()).offset((page - 1) * limit).limit(limit).all()

    data = [
        {
            "id": h.id,
            "hazard_type": h.hazard_type,
            "route_description": h.route_description,
            "reported_by_number": h.reported_by_number,
            "status": h.status,
            "reported_at": h.reported_at.isoformat() if h.reported_at else None,
            "expires_at": h.expires_at.isoformat() if h.expires_at else None,
        }
        for h in hazards
    ]
    return jsonify({
        "data": data,
        "current_page": page,
        "total_pages": total_pages,
        "total_count": total_count
    })


@bp.route("/hazards/<int:hazard_id>/clear", methods=["POST"])
def clear_hazard(hazard_id):
    """Admin override to manually clear a hazard."""
    hazard = db.session.get(HazardReport, hazard_id)
    if not hazard:
        raise ApplicationError(status_code=404, code="not_found", message="Hazard not found")
        
    hazard.status = "CLEARED"
    db.session.commit()
    return jsonify({"success": True, "message": f"Hazard {hazard_id} cleared."})


@bp.route("/sos", methods=["GET"])
def list_sos():
    """Return the recent emergency jobs for the dashboard live feed, paginated."""
    tab = request.args.get("tab", "all")
    place = request.args.get("place")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)
    
    query = EmergencyJob.query

    if tab == "active":
        query = query.filter(EmergencyJob.status.in_(["BROADCASTING", "CLAIMED"]))
    if place:
        query = query.filter_by(village_code=place)

    total_count = query.count()
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    jobs = query.order_by(EmergencyJob.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for job in jobs:
        loc = db.session.get(Location, job.village_code)
        rider = db.session.get(Rider, job.assigned_rider) if job.assigned_rider else None
        
        result.append({
            "id": job.job_id,
            "caller": job.caller_number,
            "type": job.emergency_type,
            "status": job.status,
            "village": loc.name if loc else job.village_code,
            "village_code": job.village_code,
            "assigned_rider": rider.name if rider else job.assigned_rider,
            "rider_phone": job.assigned_rider,
            "time": job.created_at.isoformat() if job.created_at else None
        })
        
    return jsonify({
        "data": result,
        "current_page": page,
        "total_pages": total_pages,
        "total_count": total_count
    })


@bp.route("/riders", methods=["GET"])
def list_riders():
    """Return the rider roster, paginated."""
    tab = request.args.get("tab", "all")
    place = request.args.get("place")
    search = request.args.get("search")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)
    
    query = Rider.query

    if tab == "available":
        query = query.filter_by(status="AVAILABLE")
    elif tab == "pending":
        query = query.filter_by(is_verified=False)
        
    if place:
        query = query.filter_by(last_known_location_code=place)
        
    if search:
        query = query.filter(
            (Rider.name.ilike(f"%{search}%")) | (Rider.phone_number.ilike(f"%{search}%"))
        )

    total_count = query.count()
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    riders = query.offset((page - 1) * limit).limit(limit).all()
    
    result = []
    for rider in riders:
        loc = db.session.get(Location, rider.last_known_location_code)
        result.append({
            "phone": rider.phone_number,
            "name": rider.name,
            "status": rider.status,
            "current_location": loc.name if loc else rider.last_known_location_code,
            "location_code": rider.last_known_location_code,
            "is_verified": rider.is_verified
        })
        
    return jsonify({
        "data": result,
        "current_page": page,
        "total_pages": total_pages,
        "total_count": total_count
    })

@bp.route("/locations", methods=["GET"])
def list_locations():
    """Return all known locations (villages/stages) for filtering."""
    locations = Location.query.all()
    return jsonify([{"code": l.code, "name": l.name, "type": l.type} for l in locations])
