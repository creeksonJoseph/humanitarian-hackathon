from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from werkzeug.exceptions import HTTPException
from flask import request, jsonify, current_app
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from .errors import ApplicationError, format_error, http_exception_to_dict

# Module-level SQLAlchemy object. Initialize with `db.init_app(app)` in your
# application factory. Models import `db` from here.
db = SQLAlchemy()


def create_app(test_config=None):
	"""Create and configure the Flask application."""
	app = Flask(__name__, instance_relative_config=True)

	# ensure the instance folder exists early so we can build an absolute DB path
	try:
		os.makedirs(app.instance_path, exist_ok=True)
	except OSError:
		pass

	# Default config - use an absolute path to the SQLite file inside the instance folder
	db_path = os.path.join(app.instance_path, "okoaroute.db")
	app.config.from_mapping(
		SECRET_KEY="dev",
		SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
		SQLALCHEMY_TRACK_MODIFICATIONS=False,
		# Africa's Talking credentials – set AT_API_KEY to switch from stub to real
		AT_USERNAME=os.getenv("AFRICAS_TALKING_USERNAME", "sandbox"),
		AT_API_KEY=os.getenv("AFRICAS_TALKING_API_KEY", ""),
		# Internal API key for protected endpoints
		API_KEY=os.getenv("API_KEY", "dev-api-key"),
	)

	if test_config is not None:
		app.config.update(test_config)

	# Initialize extensions
	db.init_app(app)

	# Initialize Flask-Migrate (Alembic integration)
	Migrate(app, db)

	# CORS – allows the frontend dashboard to call /api/* endpoints
	try:
		from flask_cors import CORS  # type: ignore[import]
		origins = os.getenv("CORS_ORIGINS", "*").split(",")
		CORS(app, resources={r"/api/*": {"origins": origins}})
	except ImportError:
		app.logger.warning("flask-cors not installed; CORS headers will not be sent")

	# Add a CLI helper to create the database tables in a controlled way
	@app.cli.command("init-db")
	def init_db_command():
		"""Create database tables (development only)."""
		with app.app_context():
			db.create_all()
			print("Initialized the database.")

	# Seed Nyamira locations
	@app.cli.command("seed-db")
	def seed_db_command():
		"""Insert seed locations for Nyamira County."""
		from .seed import seed_locations
		with app.app_context():
			count = seed_locations()
			print(f"Seeded {count} new locations.")

	# Background task runner (intended for cron)
	import click

	@app.cli.command("run-tasks")
	@click.argument("task", type=click.Choice(["stale-jobs", "reset-locations", "expire-hazards", "all"]))
	def run_tasks_command(task):
		"""Run a maintenance background task."""
		from .tasks import auto_resolve_stale_jobs, reset_rider_locations, expire_old_hazards
		with app.app_context():
			if task in ("stale-jobs", "all"):
				n = auto_resolve_stale_jobs()
				print(f"auto_resolve_stale_jobs: {n} jobs resolved")
			if task in ("reset-locations", "all"):
				n = reset_rider_locations()
				print(f"reset_rider_locations: {n} riders reset")
			if task in ("expire-hazards", "all"):
				n = expire_old_hazards()
				print(f"expire_old_hazards: {n} hazards expired")

	# Register blueprints (api will be added later)
	from . import api  # noqa: E402,F401
	app.register_blueprint(api.bp)

	from . import webhooks  # noqa: E402,F401
	app.register_blueprint(webhooks.bp)

	# Centralized error handlers that produce JSON for API requests.
	# We scope JSON responses to requests that accept JSON or to API paths.

	def wants_json():
		# prefer JSON for requests that ask for it or for /api routes
		return request.accept_mimetypes.best == 'application/json' or request.path.startswith('/api')


	@app.errorhandler(ApplicationError)
	def handle_application_error(err):
		payload = format_error(err.code, err.message, status=err.status_code, details=err.details)
		if wants_json():
			return jsonify(payload), err.status_code
		# fallback to plain text for non-API callers
		return (err.message, err.status_code)


	@app.errorhandler(HTTPException)
	def handle_http_exception(err):
		payload = http_exception_to_dict(err)
		if wants_json():
			return jsonify(payload), err.code
		return (err.description or err.name, err.code)


	@app.errorhandler(Exception)
	def handle_unexpected_error(err):
		current_app.logger.exception('Unhandled exception')
		payload = format_error('internal_server_error', 'An internal error occurred', status=500)
		if wants_json():
			return jsonify(payload), 500
		return ('Internal Server Error', 500)

	# Marshmallow validation errors (schema load/dump)
	@app.errorhandler(ValidationError)
	def handle_validation_error(err):
		current_app.logger.debug('Validation error: %s', getattr(err, 'messages', err))
		payload = format_error('validation_error', 'Invalid input', status=400, details=getattr(err, 'messages', None) or {})
		if wants_json():
			return jsonify(payload), 400
		return (str(err), 400)

	# Database errors
	@app.errorhandler(SQLAlchemyError)
	def handle_db_error(err):
		current_app.logger.exception('Database error')
		payload = format_error('database_error', 'A database error occurred', status=500)
		if wants_json():
			return jsonify(payload), 500
		return ('Database Error', 500)

	return app


__all__ = ["db", "create_app"]
