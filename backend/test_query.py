from app import create_app, db
from app.models import HazardReport, EmergencyJob
from datetime import datetime, timezone

app = create_app()

with app.app_context():
    try:
        now = datetime.now(timezone.utc)
        place = "4050"

        print("Testing Hazards API logic...")
        hazard_query = HazardReport.query.filter(HazardReport.status.in_(["ACTIVE", "UNVERIFIED"]), HazardReport.expires_at > now)
        hazard_query = hazard_query.filter(HazardReport.route_description.contains(place))
        print("Hazards Count:", hazard_query.count())
        
        print("Hazards Query compiled successfully.")
        
    except Exception as e:
        import traceback
        traceback.print_exc()

