"""Application entry-point.

Run in development:
    python app.py

Run with gunicorn (production):
    gunicorn app:app

All routes (/ussd, /sms, /health, /api/*) are registered inside
`create_app()` via blueprints so they are available both here and in tests.
"""
import os
import logging
from dotenv import load_dotenv

# Show INFO-level logs from all app.* loggers in the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)

# Load config/.env so AT_API_KEY and other secrets are available to create_app()
load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))

from flask import request, make_response

from app import create_app, db
from app.models import EmergencyJob, Rider, HazardReport
from app.dispatch import notify_candidates

app = create_app()


if __name__ == "__main__":
    app.run(port=8000, debug=True)