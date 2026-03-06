# OkoaRoute Production Readiness Checklist

## ✅ Completed

- [x] Environment variables template (`.env.example`)
- [x] Updated `.gitignore` for production
- [x] Organized test files in `/tests` folder
- [x] Created deployment documentation
- [x] Production requirements file
- [x] Configuration management module
- [x] Removed root-level database files

## 🚧 Critical Items to Implement

### 1. Background Task System (HIGH PRIORITY)
**Why:** Auto-resolve stale jobs and reset rider locations

**Options:**
- **Simple:** Cron jobs calling Python functions
- **Advanced:** Celery with Redis

**Files to create:**
- `app/tasks.py` - Background task functions
- `app/scheduler.py` - Task scheduling logic

**Functions needed:**
```python
def auto_resolve_stale_jobs():
    """Find jobs older than 3 hours and auto-resolve them."""
    pass

def reset_rider_locations():
    """Reset all riders to home_stage_code at 3 AM."""
    pass

def expire_old_hazards():
    """Mark hazards older than 12 hours as expired."""
    pass
```

### 2. Health Check Endpoint
**Why:** Monitor system status

**Add to `app/api.py`:**
```python
@app.route('/health')
def health_check():
    return {'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}
```

### 3. Rate Limiting
**Why:** Prevent USSD/SMS abuse

**Install:**
```bash
pip install Flask-Limiter
```

**Add to app:**
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: request.values.get('phoneNumber'))

@limiter.limit("10 per minute")
@app.route('/ussd', methods=['POST'])
def ussd_callback():
    ...
```

### 4. Structured Logging
**Why:** Debug production issues

**Add to `app/__init__.py`:**
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=3)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
```

### 5. CORS Configuration
**Why:** Allow frontend dashboard to access API

**Install:**
```bash
pip install Flask-CORS
```

**Add to app:**
```python
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

### 6. Error Monitoring (Sentry)
**Why:** Track production errors

**Install:**
```bash
pip install sentry-sdk[flask]
```

**Add to `app/__init__.py`:**
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration()]
    )
```

### 7. Database Backup Strategy
**Why:** Prevent data loss

**For SQLite (development):**
```bash
# Daily backup cron
0 2 * * * cp /path/to/instance/okoaroute.db /path/to/backups/okoaroute_$(date +\%Y\%m\%d).db
```

**For PostgreSQL (production):**
```bash
# Daily backup cron
0 2 * * * pg_dump okoaroute > /path/to/backups/okoaroute_$(date +\%Y\%m\%d).sql
```

## 📋 Pre-Launch Checklist

### Security
- [ ] Change all default secrets in `.env`
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS (required by Africa's Talking)
- [ ] Implement rate limiting
- [ ] Review API endpoint authentication
- [ ] Set strong database password (production)

### Infrastructure
- [ ] Set up production database (PostgreSQL)
- [ ] Configure Gunicorn or uWSGI
- [ ] Set up Nginx reverse proxy
- [ ] Configure SSL certificate
- [ ] Set up background task scheduler
- [ ] Configure log rotation

### Africa's Talking
- [ ] Test USSD flow in sandbox
- [ ] Test SMS sending in sandbox
- [ ] Configure production webhooks
- [ ] Load production account with airtime
- [ ] Set up delivery report callbacks

### Monitoring
- [ ] Add health check endpoint
- [ ] Set up error monitoring (Sentry)
- [ ] Configure log aggregation
- [ ] Set up uptime monitoring
- [ ] Create alerting rules

### Testing
- [ ] Run full test suite (`pytest`)
- [ ] Run smoke tests
- [ ] Test all USSD menu paths
- [ ] Test SMS broadcast and claim flow
- [ ] Test edge cases (ghost rider, timeout, etc.)
- [ ] Load test with multiple concurrent requests

### Documentation
- [ ] Update README with setup instructions
- [ ] Document API endpoints
- [ ] Create runbook for common issues
- [ ] Document deployment process
- [ ] Create pitch deck for judges

## 🎯 Hackathon Demo Checklist

### Day Before (March 12)
- [ ] Test complete flow end-to-end
- [ ] Record backup demo video (20 seconds)
- [ ] Prepare slide deck
- [ ] Test on actual feature phone (if possible)
- [ ] Ensure Ngrok is stable
- [ ] Seed database with demo data

### Demo Day (March 13)
- [ ] Start Flask server early
- [ ] Start Ngrok and note URL
- [ ] Update Africa's Talking webhooks
- [ ] Test USSD code before presentation
- [ ] Have backup video ready
- [ ] Prepare to add judges as riders live
- [ ] Practice 5-minute pitch

## 📊 What Makes This Production-Ready

### Current State: MVP ✅
- Core USSD flow working
- Database schema complete
- SMS integration ready
- Basic error handling

### Missing for Production: 🚧
1. Background task scheduler
2. Rate limiting
3. Structured logging
4. Error monitoring
5. Database backups
6. Health checks
7. CORS for frontend
8. Load testing

### Timeline to Production-Ready
- **Hackathon (March 13):** MVP demo-ready ✅
- **Week 1 Post-Hackathon:** Add background tasks, logging, monitoring
- **Week 2 Post-Hackathon:** Security hardening, load testing
- **Week 3 Post-Hackathon:** Production deployment with real users

## 🆘 Emergency Contacts

- Africa's Talking Support: support@africastalking.com
- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy Docs: https://docs.sqlalchemy.org/

## 📝 Notes

- Keep `.env` file secure and never commit to git
- Test in sandbox before production
- Monitor SMS costs in production
- Have rollback plan ready
- Document all configuration changes
