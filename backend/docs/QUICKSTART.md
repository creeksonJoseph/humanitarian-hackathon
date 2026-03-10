# Quick Start Guide - OkoaRoute

## 🚀 Get Running in 5 Minutes

### Step 1: Environment Setup (2 minutes)
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your credentials
# Minimum required:
# - AFRICAS_TALKING_USERNAME=sandbox
# - AFRICAS_TALKING_API_KEY=your-key-here
# - FLASK_SECRET_KEY=generate-with-command-below

# Generate secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 2: Install Dependencies (1 minute)
```bash
# Activate virtual environment
source .venv-1/bin/activate  # or your venv name

# Install production dependencies
pip install python-dotenv gunicorn psycopg2-binary
```

### Step 3: Test Locally (2 minutes)
```bash
# Run the app
python app.py

# In another terminal, test health
curl http://localhost:8000/health
```

## 🧪 Testing Your Setup

### Run All Tests
```bash
pytest -v
```

### Run Smoke Test
```bash
python tests/smoke_test.py
```

### Test USSD Flow
1. Start server: `python app.py`
2. Start Ngrok: `ngrok http 8000`
3. Copy Ngrok HTTPS URL
4. Go to Africa's Talking Sandbox
5. Set USSD callback: `https://your-ngrok-url.ngrok.io/ussd`
6. Test in simulator

## 📋 Files You Need to Know

| File | Purpose | Action Required |
|------|---------|-----------------|
| `.env` | Your credentials | Create from .env.example |
| `DEPLOYMENT.md` | Full deployment guide | 📖 Read before deploying |

| `config.py` | Configuration management |
| `tests/` | All tests | Run before demo |

## ⚡ Common Commands

```bash
# Development
python app.py                    # Run dev server
pytest -v                        # Run tests
flask db upgrade                 # Run migrations

# Production
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"  # Production server

# Database
flask init-db                    # Initialize database
flask db migrate -m "message"    # Create migration
flask db upgrade                 # Apply migrations

# Testing
pytest -v                        # All tests
pytest tests/test_api.py -v     # Specific test file
python tests/smoke_test.py      # Smoke test
```

## 🔑 Environment Variables Explained

```bash
# Flask
FLASK_ENV=development           # development or production
FLASK_SECRET_KEY=xxx            # Generate with secrets.token_hex(32)

# Database
DATABASE_URL=sqlite:///instance/okoaroute.db  # Dev: SQLite
# DATABASE_URL=postgresql://user:pass@host/db  # Prod: PostgreSQL

# Africa's Talking
AFRICAS_TALKING_USERNAME=sandbox              # "sandbox" for testing
AFRICAS_TALKING_API_KEY=xxx                   # From AT dashboard

# Security
API_KEY=xxx                     # For protected endpoints
```



## 🚨 Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
pip install python-dotenv
```

### USSD not responding
1. Check Flask is running: `curl http://localhost:8000/health`
2. Check Ngrok is running: Visit Ngrok dashboard
3. Verify webhook URL in Africa's Talking
4. Check Flask logs for errors

### Database errors
```bash
# Reset database
rm instance/okoaroute.db
flask db upgrade
```

### SMS not sending
1. Check `.env` has correct API credentials
2. Verify Africa's Talking account is active
3. Check `instance/sms.log` for errors

## 📚 Documentation Quick Links

- **Full Deployment:** See `DEPLOYMENT.md` 
- **Project Overview:** See `README.md`

## 💡 Pro Tips

1. **Always test in sandbox first** - Free and safe
2. **Keep Ngrok running** - Webhook URL changes when restarted
3. **Monitor logs** - `tail -f instance/sms.log`
4. **Use .env for secrets** - Never commit credentials
5. **Test edge cases** - Ghost rider, timeout, invalid input



## 🆘 Need Help?

1. Check `DEPLOYMENT.md` for detailed instructions 
2. Read Flask docs: https://flask.palletsprojects.com/
3. Africa's Talking docs: https://developers.africastalking.com/

---

**You're ready to go! Start with Step 1 above.** 🚀
