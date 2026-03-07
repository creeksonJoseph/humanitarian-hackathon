"""Seed the database with Nyamira County locations.

Run via Flask CLI:
    flask seed-db

This inserts core stages, villages, and the county referral hospital that
the demo uses. Safe to run multiple times (skips existing records).
"""
import logging

from . import db
from .models import Location

logger = logging.getLogger("app.seed")

# Nyamira County seed data
# type choices: STAGE, VILLAGE, HOSPITAL
LOCATIONS = [
    # Main Referral Hospital
    {"code": "0001", "name": "Nyamira County Referral Hospital", "type": "HOSPITAL"},

    # Boda-boda stages
    {"code": "1001", "name": "Nyamaiya Stage", "type": "STAGE"},
    {"code": "1002", "name": "Miruka Stage", "type": "STAGE"},
    {"code": "1003", "name": "Nyamira Town Stage", "type": "STAGE"},
    {"code": "1004", "name": "Tombe Stage", "type": "STAGE"},
    {"code": "1005", "name": "Manga Stage", "type": "STAGE"},

    # Villages
    {"code": "4050", "name": "Ekerenyo", "type": "VILLAGE"},
    {"code": "4051", "name": "Gesima", "type": "VILLAGE"},
    {"code": "4052", "name": "Magwagwa", "type": "VILLAGE"},
    {"code": "4053", "name": "Nyansiongo", "type": "VILLAGE"},
    {"code": "4054", "name": "Rigoma", "type": "VILLAGE"},
    {"code": "4055", "name": "Bosamaro", "type": "VILLAGE"},
    {"code": "4056", "name": "Gesicho", "type": "VILLAGE"},
]


def seed_locations() -> int:
    """Insert location records that don't already exist. Returns count inserted."""
    inserted = 0
    for data in LOCATIONS:
        if not db.session.get(Location, data["code"]):
            db.session.add(Location(**data))
            inserted += 1
    db.session.commit()
    logger.info("seed_locations: inserted %d locations", inserted)
    return inserted


# Three verified demo riders spread across Nyamira stages
RIDERS = [
    {
        "phone_number": "+254711000001",
        "name": "Otieno Mwangi",
        "home_stage_code": "1001",   # Nyamaiya Stage
        "last_known_location_code": "1001",
        "is_verified": True,
        "status": "AVAILABLE",
    },
    {
        "phone_number": "+254722000002",
        "name": "Akinyi Moraa",
        "home_stage_code": "1003",   # Nyamira Town Stage
        "last_known_location_code": "1003",
        "is_verified": True,
        "status": "AVAILABLE",
    },
    {
        "phone_number": "+254733000003",
        "name": "Bosire Nyamweya",
        "home_stage_code": "1005",   # Manga Stage
        "last_known_location_code": "1005",
        "is_verified": True,
        "status": "AVAILABLE",
    },
]


def seed_riders() -> int:
    """Insert demo riders that don't already exist. Returns count inserted."""
    from .models import Rider
    inserted = 0
    for data in RIDERS:
        if not db.session.get(Rider, data["phone_number"]):
            db.session.add(Rider(**data))
            inserted += 1
    db.session.commit()
    logger.info("seed_riders: inserted %d riders", inserted)
    return inserted

