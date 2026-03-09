import os
from sqlalchemy import text
from app import create_app, db
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))

app = create_app()

with app.app_context():
    database_url = app.config.get("SQLALCHEMY_DATABASE_URI")
    print(f"Connecting to database: {database_url}")
    
    engine = db.engine
    
    with engine.connect() as conn:
        print("Checking if hazard_type column exists...")
        try:
            conn.execute(text("SELECT hazard_type FROM hazard_reports LIMIT 1"))
            print("The hazard_type column already exists.")
        except Exception as e:
            print("The hazard_type column does not exist. Adding it now...")
            try:
                pass
            except Exception:
                pass
                
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE hazard_reports ADD COLUMN hazard_type VARCHAR(255) DEFAULT 'OTHER' NOT NULL"))
            print("Successfully added hazard_type column to hazard_reports table!")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column already exists or was created.")
            else:
                print(f"Error executing ALTER TABLE: {e}")
                print("\nYou can also run this SQL manually in your database:")
                print("ALTER TABLE hazard_reports ADD COLUMN hazard_type VARCHAR DEFAULT 'OTHER' NOT NULL;")

print("Database patch complete.")
