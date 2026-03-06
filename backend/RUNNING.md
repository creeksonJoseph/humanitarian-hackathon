Quickstart (development)

1. Create a virtualenv and install deps:

`````bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
````markdown
Quickstart (development)

1. Create a virtualenv and install deps

```bash
python -m venv .venv-1
source .venv-1/bin/activate
pip install -r requirements.txt
`````

2. Initialize the DB (development helper)

```bash
export FLASK_APP=app:create_app
flask init-db   # creates tables via SQLAlchemy (dev convenience)
```

3. Alembic (recommended for migrations)

```bash
export FLASK_APP=app:create_app
flask db init            # one-time (already created in repo)
flask db migrate -m "describe change"
flask db upgrade
```

If you have an existing DB that already matches your models, stamp the head to baseline migrations:

```bash
flask db stamp head
```

4. Run the app

```bash
# with Makefile
make run

# or directly
python app.py
```

5. Run tests

```bash
pytest -q
```

Notes

- The project uses a stub SMS adapter at `app/sms/stub.py` for development. To switch to Africa's Talking, replace the implementation and configure credentials via environment variables.
- API key protected endpoints expect header `X-API-Key` matching `API_KEY` in app config. For local testing set `API_KEY` via `create_app` test_config or environment.

```

```
