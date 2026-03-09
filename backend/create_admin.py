import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))

from app import create_app, db
from app.models.admin import Admin

app = create_app()

with app.app_context():
    # Only create tables that don't exist yet, avoiding overriding existing ones
    db.create_all()

    admin = Admin.query.filter_by(username="admin").first()
    if not admin:
        admin = Admin(username="admin")
        admin.set_password("admin")
        db.session.add(admin)
        db.session.commit()
        print("Admin user created (admin / admin).")
    else:
        print("Admin user already exists.")
