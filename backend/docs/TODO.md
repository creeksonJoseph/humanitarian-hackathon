# TODO: Critical Items for Production

## 🚨 HIGH PRIORITY (Implement Before Production)

### 1. Background Task Scheduler ⏰
**Why:** Auto-resolve stale jobs and reset rider locations

**Create:** `app/tasks.py`
```python
from datetime import datetime, timedelta
from app import db
from app.models import EmergencyJob, Rider

def auto_resolve_stale_jobs():
    """Auto-resolve jobs older than 3 hours."""
    cutoff = datetime.utcnow() - timedelta(hours=3)
    stale_jobs = EmergencyJob.query.filter(
        EmergencyJob.status == 'CLAIMED',
        EmergencyJob.created_at < cutoff
    ).all()
    
    for job in stale_jobs:
        job.status = 'AUTO_RESOLVED'
        job.resolved_at = datetime.utcnow()
        job.cancellation_reason = 'SYSTEM_TIMEOUT'
        
        # Free up the rider
        if job.assigned_rider:
            rider = db.session.get(Rider, job.assigned_rider)
            if rider:
                rider.status = 'AVAILABLE'
    
    db.session.commit()
    return len(stale_jobs)

def reset_rider_locations():
    """Reset all riders to home_stage_code at 3 AM."""
    riders = Rider.query.all()
    for rider in riders:
        rider.last_known_location_code = rider.home_stage_code
    db.session.commit()
    return len(riders)

def expire_old_hazards():
    """Mark hazards older than 12 hours as expired."""
    from app.models import HazardReport
    now = datetime.utcnow()
    expired = HazardReport.query.filter(
        HazardReport.expires_at < now,
        HazardReport.status.in_(['ACTIVE', 'UNVERIFIED'])
    ).all()
    
    for hazard in expired:
        hazard.status = 'EXPIRED'
    
    db.session.commit()
    return len(expired)
```

**Setup Cron Jobs:**
```bash
# Edit crontab
crontab -e

# Add these lines:
*/15 * * * * cd /path/to/backend && .venv/bin/python -c "from app.tasks import auto_resolve_stale_jobs; auto_resolve_stale_jobs()"
0 3 * * * cd /path/to/backend && .venv/bin/python -c "from app.tasks import reset_rider_locations; reset_rider_locations()"
*/30 * * * * cd /path/to/backend && .venv/bin/python -c "from app.tasks import expire_old_hazards; expire_old_hazards()"
```

---

### 2. Health Check Endpoint 🏥
**Why:** Monitor system status

**Add to:** `app/api.py`
```python
from datetime import datetime
from flask import jsonify

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'ok'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'ok' if db_status == 'ok' else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'version': '1.0.0'
    })
```

---

### 3. Rate Limiting 🛡️
**Why:** Prevent USSD/SMS abuse

**Install:**
```bash
pip install Flask-Limiter
```

**Add to:** `app/__init__.py`
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=lambda: request.values.get('phoneNumber', get_remote_address()),
    default_limits=["200 per day", "50 per hour"]
)

# Then in app.py, apply to USSD endpoint:
@limiter.limit("10 per minute")
@app.route('/ussd', methods=['POST'])
def ussd_callback():
    ...
```

---

### 4. Structured Logging 📝
**Why:** Debug production issues

**Add to:** `app/__init__.py`
```python
import logging
from logging.handlers import RotatingFileHandler
import os

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler(
        'logs/okoaroute.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('OkoaRoute startup')
```

---

### 5. CORS Configuration 🌐
**Why:** Allow frontend dashboard to access API

**Install:**
```bash
pip install Flask-CORS
```

**Add to:** `app/__init__.py`
```python
from flask_cors import CORS

# Allow all origins in development, restrict in production
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('CORS_ORIGINS', '*').split(',')
    }
})
```

**Add to:** `.env`
```bash
# Development
CORS_ORIGINS=*

# Production
# CORS_ORIGINS=https://yourdomain.com,https://dashboard.yourdomain.com
```

---

### 6. Error Monitoring (Sentry) 🔍
**Why:** Track production errors

**Install:**
```bash
pip install sentry-sdk[flask]
```

**Add to:** `app/__init__.py`
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0,
        environment=os.getenv('FLASK_ENV', 'development')
    )
```

**Add to:** `.env`
```bash
# Get from sentry.io after creating project
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

---

### 7. Database Backup Strategy 💾
**Why:** Prevent data loss

**For SQLite (Development):**
```bash
# Add to crontab
0 2 * * * cp /path/to/instance/okoaroute.db /path/to/backups/okoaroute_$(date +\%Y\%m\%d).db

# Keep only last 7 days
0 3 * * * find /path/to/backups -name "okoaroute_*.db" -mtime +7 -delete
```

**For PostgreSQL (Production):**
```bash
# Add to crontab
0 2 * * * pg_dump okoaroute | gzip > /path/to/backups/okoaroute_$(date +\%Y\%m\%d).sql.gz

# Keep only last 30 days
0 3 * * * find /path/to/backups -name "okoaroute_*.sql.gz" -mtime +30 -delete
```

---

## 📋 MEDIUM PRIORITY (Nice to Have)

### 8. API Documentation
**Tool:** Flask-RESTX or Swagger

### 9. Metrics Dashboard
**Tool:** Prometheus + Grafana

### 10. SMS Delivery Tracking
**Enhancement:** Track delivery status from Africa's Talking

### 11. Multi-language Support
**Enhancement:** Support multiple languages in USSD menus

### 12. Load Testing
**Tool:** Locust or Apache Bench

---

## ✅ Implementation Checklist

Copy this to track your progress:

```
Background Tasks:
[ ] Create app/tasks.py
[ ] Implement auto_resolve_stale_jobs()
[ ] Implement reset_rider_locations()
[ ] Implement expire_old_hazards()
[ ] Set up cron jobs

Monitoring:
[ ] Add /health endpoint
[ ] Set up structured logging
[ ] Configure Sentry (optional)

Security:
[ ] Install Flask-Limiter
[ ] Add rate limiting to USSD endpoint
[ ] Add rate limiting to SMS endpoint

Frontend Integration:
[ ] Install Flask-CORS
[ ] Configure CORS origins
[ ] Test from frontend

Operations:
[ ] Set up database backups
[ ] Test backup restoration
[ ] Document backup procedure

Testing:
[ ] Test background tasks manually
[ ] Test rate limiting
[ ] Test health endpoint
[ ] Load test with 100+ concurrent requests
```

---

## 🚀 Quick Implementation Order

**For Hackathon (March 13):**
1. Health check endpoint (5 minutes)
2. Basic logging (10 minutes)
3. Test everything works

**Post-Hackathon (Week 1):**
1. Background tasks (2 hours)
2. Rate limiting (30 minutes)
3. CORS (15 minutes)
4. Database backups (30 minutes)

**Post-Hackathon (Week 2):**
1. Sentry integration (30 minutes)
2. Load testing (2 hours)
3. Security audit (2 hours)

---

## 📞 Need Help?

- **Background Tasks:** See `DEPLOYMENT.md` section on cron jobs
- **Rate Limiting:** Flask-Limiter docs: https://flask-limiter.readthedocs.io/
- **Logging:** Flask docs: https://flask.palletsprojects.com/en/latest/logging/
- **Sentry:** Sentry Flask docs: https://docs.sentry.io/platforms/python/guides/flask/

---

**Remember:** Your app works without these! They're for production hardening.
Focus on the hackathon demo first, implement these after. 🚀
