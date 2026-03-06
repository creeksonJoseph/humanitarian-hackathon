from .models import Rider
from .sms import send_sms
from . import db


def notify_candidates(job):
    """Select available riders and notify them via SMS (stub)"""
    # Simple selection: all available riders. In real app, filter by proximity.
    candidates = Rider.query.filter_by(status="AVAILABLE").all()
    if not candidates:
        return []

    messages = []
    for r in candidates:
        msg = f"URGENT SOS: {job.emergency_type} at {job.village_code}. Reply ACCEPT {job.job_id}"
        send_sms(r.phone_number, msg)
        messages.append((r.phone_number, msg))

    return messages
