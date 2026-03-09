"""Africa's Talking SMS client.

Used when AT_API_KEY is set in the Flask config. Falls back to the stub
in development/testing when no key is provided.
"""
import logging

logger = logging.getLogger("app.sms.at_client")


def send_sms(number, message: str, *, username: str, api_key: str, sender_id: str = None) -> bool:
    """Send an SMS via the Africa's Talking SDK."""
    try:
        import africastalking  # type: ignore[import]
    except ImportError:
        logger.error(
            "africastalking package not installed. Run: pip install africastalking"
        )
        return False

    africastalking.initialize(username, api_key)
    sms = africastalking.SMS
    
    recipients = [number] if isinstance(number, str) else number
    
    try:
        kwargs = {}
        if sender_id:
            kwargs["sender_id"] = sender_id
        response = sms.send(message, recipients, **kwargs)
        logger.info("AT SMS sent to %s: %s", recipients, response)
        return True
    except Exception:
        logger.exception("Africa's Talking SMS failed for %s", recipients)
        return False
