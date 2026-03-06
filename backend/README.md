# OkoaRoute Backend

Offline-first emergency medical dispatch system for rural Kenya using USSD/SMS.

## 🚀 Quick Start

```bash
# 1. Setup environment
cp config/.env.example .env
# Edit .env with your credentials

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

## 📚 Documentation

All documentation is in the [`docs/`](docs/) folder:

- **[docs/START_HERE.md](docs/START_HERE.md)** - Start here for overview
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute setup guide
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment
- **[docs/TODO.md](docs/TODO.md)** - What's missing for production

## 📁 Project Structure

```
backend/
├── app/                    # Application code
├── tests/                  # All tests
├── docs/                   # Documentation
├── config/                 # Configuration files
├── instance/               # Runtime data (gitignored)
├── migrations/             # Database migrations
└── app.py                  # Main entry point
```

## 🔧 Configuration

Configuration files are in [`config/`](config/) folder:

- `config/.env.example` - Environment template
- `config/config.py` - Configuration management
- `config/requirements-prod.txt` - Production dependencies

## 🧪 Testing

```bash
pytest -v                   # Run all tests
python tests/smoke_test.py  # Smoke test
```

## 📖 Full Documentation

See [`docs/README.md`](docs/README.md) for complete documentation index.

## 🎯 Hackathon Demo (March 13)

Ready for demo! See [docs/QUICKSTART.md](docs/QUICKSTART.md) for setup.

## 📊 Production Readiness: 60%

- ✅ Core functionality complete
- ✅ Documentation complete
- 🚧 Background tasks needed (see [docs/TODO.md](docs/TODO.md))

---

**For detailed information, see [docs/START_HERE.md](docs/START_HERE.md)**
