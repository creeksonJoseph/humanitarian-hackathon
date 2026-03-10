# OkoaRoute Production Deployment Guide

## Prerequisites
- Python 3.8+
- Africa's Talking account (sandbox for testing, production for live)
- PostgreSQL (production) or SQLite (development)
- Ngrok or production server with public URL

## Environment Setup

### 1. Clone and Install Dependencies
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` and set:
- `AFRICAS_TALKING_USERNAME` - Your Africa's Talking username (use "sandbox" for testing)
- `AFRICAS_TALKING_API_KEY` - Get from Africa's Talking dashboard
- `FLASK_SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
- `API_KEY` - For protecting admin endpoints
- `DATABASE_URL` - Database connection string

### 3. Initialize Database
```bash
export FLASK_APP=app:create_app
flask db upgrade  # Run migrations
flask init-db     # Optional: seed initial data
```

## Africa's Talking Configuration

### Sandbox Setup (Development)
1. Sign up at https://account.africastalking.com/
2. Go to Sandbox → USSD
3. Create USSD code (e.g., `*384*99#`)
4. Set callback URL to your Ngrok URL: `https://your-ngrok-url.ngrok.io/ussd`

### SMS Webhook Setup
1. Go to SMS → Callback URLs
2. Set delivery reports URL: `https://your-ngrok-url.ngrok.io/sms/callback`

### Expose Local Server (Development)
```bash
# Terminal 1: Run Flask
python app.py

# Terminal 2: Run Ngrok
ngrok http 8000
```
Copy the HTTPS URL from Ngrok and update Africa's Talking webhooks.

## Production Deployment

### 1. Use Production WSGI Server
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

### 2. Database Migration (PostgreSQL)
```bash
# Update .env
DATABASE_URL=postgresql://user:password@localhost:5432/okoaroute

# Run migrations
flask db upgrade
```

### 3. Setup Background Tasks (CRITICAL)

#### Option A: Cron Jobs (Simple)
Add to crontab (`crontab -e`):
```cron
# Auto-resolve stale jobs every 15 minutes
*/15 * * * * cd /path/to/backend && .venv/bin/python -c "from app.tasks import auto_resolve_stale_jobs; auto_resolve_stale_jobs()"

# Reset rider locations at 3 AM daily
0 3 * * * cd /path/to/backend && .venv/bin/python -c "from app.tasks import reset_rider_locations; reset_rider_locations()"
```

#### Option B: Celery (Advanced)
```bash
pip install celery redis
celery -A app.celery worker --beat
```

### 4. Nginx Reverse Proxy (Production)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. SSL Certificate (Required for Africa's Talking)
```bash
sudo certbot --nginx -d your-domain.com
```

## Security Checklist

- [ ] Change `FLASK_SECRET_KEY` to a strong random value
- [ ] Set `FLASK_ENV=production` in production
- [ ] Use PostgreSQL instead of SQLite in production
- [ ] Enable HTTPS (Africa's Talking requires it)
- [ ] Set strong `API_KEY` for protected endpoints
- [ ] Never commit `.env` file to git
- [ ] Implement rate limiting on USSD/SMS endpoints
- [ ] Set up database backups

## Monitoring & Logging

### Health Check Endpoint
```bash
curl https://your-domain.com/health
```

### View Logs
```bash
tail -f instance/sms.log
tail -f logs/app.log  # If configured
```

### Recommended: Add Sentry for Error Tracking
```bash
pip install sentry-sdk[flask]
```

## Testing

### Run Tests
```bash
pytest -v
```

### Smoke Test
```bash
python tests/smoke_test.py
```

### Manual USSD Test
1. Open Africa's Talking Simulator
2. Dial your USSD code
3. Follow the menu prompts
4. Check database for created records

## Troubleshooting

### USSD Not Working
- Verify Ngrok is running and URL is updated in Africa's Talking
- Check Flask logs for errors
- Ensure callback URL ends with `/ussd`

### SMS Not Sending
- Verify API credentials in `.env`
- Check Africa's Talking account balance (production)
- Review `instance/sms.log` for errors

### Database Errors
- Run migrations: `flask db upgrade`
- Check database connection string
- Verify database file permissions (SQLite)


