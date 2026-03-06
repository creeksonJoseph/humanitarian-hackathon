from app.sms import send_sms
import os


def test_send_sms_writes_log(tmp_path):
    # Ensure instance folder exists
    os.makedirs("instance", exist_ok=True)
    ok = send_sms("+254700000001", "test message")
    assert ok is True
    # check sms.log contains entry
    with open(os.path.join("instance", "sms.log"), "r", encoding="utf-8") as fh:
        data = fh.read()
    assert "test message" in data
