"""SMS package – automatically selects the right backend.

- If AT_API_KEY is set in the Flask app config, uses the real
  Africa's Talking SDK (at_client.py).
- Otherwise falls back to the stub that writes to instance/sms.log.

Callers always use: `from app.sms import send_sms`
No changes needed in callers when switching environments.
"""
import logging

logger = logging.getLogger("app.sms")


def send_sms(number, message: str) -> bool:
    """Send an SMS (to a string or list of strings), routing to the real AT client or stub based on config."""
    # Import here to avoid a circular import at module load time
    try:
        from flask import current_app
        api_key  = current_app.config.get("AT_API_KEY", "")
        username = current_app.config.get("AT_USERNAME", "sandbox")
        sender   = current_app.config.get("AT_SENDER_ID", "") or None
    except RuntimeError:
        # Outside application context (unit tests without app) – use stub
        api_key  = ""
        username = "sandbox"
        sender   = None

    if api_key:
        from .at_client import send_sms as _at_send
        return _at_send(number, message, username=username, api_key=api_key, sender_id=sender)

    from .stub import send_sms as _stub_send
    return _stub_send(number, message)


__all__ = ["send_sms"]
