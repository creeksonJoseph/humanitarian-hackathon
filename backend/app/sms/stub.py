import logging
import os

logger = logging.getLogger("app.sms.stub")


def send_sms(number: str, message: str) -> bool:
    """Stub implementation: log the message and append to a local file for inspection."""
    logger.info("STUB SMS to %s: %s", number, message)
    # ensure instance folder
    try:
        os.makedirs("instance", exist_ok=True)
        with open(os.path.join("instance", "sms.log"), "a", encoding="utf-8") as fh:
            fh.write(f"TO:{number} MSG:{message}\n")
    except Exception:
        logger.exception("failed to write sms log")
    return True
