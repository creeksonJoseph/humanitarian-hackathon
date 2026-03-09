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

	# Use an absolute path to the SQLite file inside the backend folder explicitly
	basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
	instance_dir = os.path.join(basedir, "instance")
	
	try:
		os.makedirs(instance_dir, exist_ok=True)
	except OSError:
		pass

	db_path = os.path.join(instance_dir, "okoaroute.db")
	database_url = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

	app.config.from_mapping(
		SECRET_KEY="dev",
		SQLALCHEMY_DATABASE_URI=database_url,
		SQLALCHEMY_TRACK_MODIFICATIONS=False,
		# Africa's Talking credentials – set AT_API_KEY to switch from stub to real
		AT_USERNAME=os.getenv("AFRICAS_TALKING_USERNAME", "sandbox"),
		AT_API_KEY=os.getenv("AFRICAS_TALKING_API_KEY", ""),
		AT_SENDER_ID=os.getenv("AT_SENDER_ID", ""),  # shortcode e.g. 28899
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

	@app.cli.command("clean-db")
	def clean_db_command():
		"""Drop all database tables (useful for complete resets)."""
		with app.app_context():
			db.drop_all()
			print("Dropped all tables in the database.")

	# Seed Nyamira locations
	@app.cli.command("seed-db")
	def seed_db_command():
		"""Insert seed locations and demo riders for Nyamira County."""
		from .seed import seed_locations, seed_riders
		with app.app_context():
			loc_count = seed_locations()
			rider_count = seed_riders()
			print(f"Seeded {loc_count} new locations and {rider_count} new riders.")

	# Background task runner (intended for cron)
	import click

	@app.cli.command("run-tasks")
	@click.argument("task", type=click.Choice(["stale-jobs", "reset-locations", "expire-hazards", "escalate", "all"]))
	def run_tasks_command(task):
		"""Run a maintenance background task."""
		from .tasks import auto_resolve_stale_jobs, reset_rider_locations, expire_old_hazards, escalate_unanswered_jobs
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
			if task in ("escalate", "all"):
				n = escalate_unanswered_jobs()
				print(f"escalate_unanswered_jobs: {n} jobs escalated")

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

	# -------------------------------------------------------------------------
	# Status endpoints
	# -------------------------------------------------------------------------

	@app.route("/")
	def index():
		"""Base route returning HTML status page to confirm server status."""
		html = '''<!DOCTYPE html>\n\n<html lang="en"><head>\n<meta charset="utf-8"/>\n<meta content="width=device-width, initial-scale=1.0" name="viewport"/>\n<title>OkoaRoute | Status</title>\n<!-- Tailwind CSS CDN -->\n<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>\n<!-- Google Fonts: Oswald -->\n<link href="https://fonts.googleapis.com" rel="preconnect"/>\n<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>\n<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@200..700&display=swap" rel="stylesheet"/>\n<script>\n    tailwind.config = {\n      theme: {\n        extend: {\n          colors: {\n            slate: {\n              950: '#0f172a',\n            },\n            emerald: {\n              400: '#34d399',\n              500: '#10b981',\n            }\n          },\n          fontFamily: {\n            oswald: ['Oswald', 'sans-serif'],\n          },\n          animation: {\n            'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',\n          }\n        }\n      }\n    }\n  </script>\n<style data-purpose="typography">\n    body {\n      font-family: 'Oswald', sans-serif;\n      letter-spacing: 0.05em;\n      text-transform: uppercase;\n    }\n  </style>\n<style data-purpose="glow-effects">\n    .glow-emerald {\n      box-shadow: 0 0 15px rgba(16, 185, 129, 0.6);\n    }\n    /* Subtle scanline effect for Command Center aesthetic */\n    .scanline-overlay {\n      background: linear-gradient(\n        to bottom,\n        rgba(255, 255, 255, 0) 50%,\n        rgba(0, 0, 0, 0.05) 50%\n      );\n      background-size: 100% 4px;\n      pointer-events: none;\n    }\n  </style>\n</head>\n<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col justify-between overflow-hidden">\n<!-- BEGIN: Navigation / Logo Section -->\n<header class="p-8 md:p-12 w-full flex justify-center items-center">\n<div class="flex items-center gap-4" data-purpose="brand-identity">\n<!-- Medical/Emergency Icon -->\n<svg class="w-10 h-10 text-red-600" fill="none" stroke="currentColor" stroke-width="1.5" viewbox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">\n<path d="M12 9v6m3-3H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke-linecap="round" stroke-linejoin="round"></path>\n</svg>\n<h1 class="text-4xl font-bold tracking-widest">OkoaRoute</h1>\n</div>\n</header>\n<!-- END: Navigation / Logo Section -->\n<!-- BEGIN: Main Content -->\n<main class="flex-grow flex flex-col items-center justify-center px-4 relative">\n<!-- Visual background element for Command Center feel -->\n<div class="absolute inset-0 scanline-overlay opacity-20"></div>\n<div class="text-center z-10" data-purpose="status-display">\n<!-- Status Indicator Container -->\n<div class="mb-8 flex flex-col items-center">\n<div class="flex items-center gap-3 bg-slate-900/50 border border-slate-800 px-8 py-4 rounded-sm shadow-2xl">\n<!-- The Glowing Emerald Indicator -->\n<span class="relative flex h-4 w-4">\n<span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>\n<span class="relative inline-flex rounded-full h-4 w-4 bg-emerald-500 glow-emerald"></span>\n</span>\n<h2 class="text-2xl md:text-3xl font-medium tracking-widest text-emerald-400">\n            SERVER STATUS: HEALTHY\n          </h2>\n</div>\n</div>\n<!-- Information Text -->\n<p class="text-slate-400 text-sm tracking-[0.2em] max-w-md mx-auto leading-relaxed">\n        OPERATIONAL SYSTEMS NOMINAL // GLOBAL ROUTING ACTIVE // EMERGENCY CHANNELS OPEN\n      </p>\n</div>\n</main>\n<!-- END: Main Content -->\n<!-- BEGIN: Footer -->\n<footer class="p-8 md:p-12 text-center w-full">\n<div class="border-t border-slate-800/50 pt-8 inline-block px-12">\n<p class="text-slate-500 text-xs tracking-widest uppercase">\n        Crafted by <span class="text-slate-300 font-medium">Creekson Joseph</span>\n</p>\n</div>\n</footer>\n<!-- END: Footer -->\n</body></html>'''
		return html, 200, {'Content-Type': 'text/html'}

	@app.route("/health")
	def health():
		"""Health check endpoint returning 200 OK."""
		return jsonify({"status": "server is up and running"}), 200

	return app


__all__ = ["db", "create_app"]
