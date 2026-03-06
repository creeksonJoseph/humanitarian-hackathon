from flask_sqlalchemy import SQLAlchemy

# Module-level SQLAlchemy object. Initialize with `db.init_app(app)` in your
# application factory or script and call `with app.app_context(): db.create_all()`
# to create tables for development/testing.
db = SQLAlchemy()

__all__ = ["db"]
