PYTHON=.venv-1/bin/python
PIP=.venv-1/bin/pip
FLASK=.venv-1/bin/flask

install-deps:
	$(PIP) install -r requirements.txt

init-db: export FLASK_APP=app:create_app
init-db:
	$(FLASK) init-db

db-migrate: export FLASK_APP=app:create_app
db-migrate:
	$(FLASK) db migrate -m "migration"

db-upgrade: export FLASK_APP=app:create_app
db-upgrade:
	$(FLASK) db upgrade

db-stamp: export FLASK_APP=app:create_app
db-stamp:
	$(FLASK) db stamp head

run: export FLASK_APP=app:create_app
run:
	$(PYTHON) app.py

.PHONY: install-deps init-db db-migrate db-upgrade db-stamp run
VENV=.venv
PY=${VENV}/bin/python
PIP=${VENV}/bin/pip

.PHONY: venv install run test

venv:
	python3 -m venv ${VENV}

install: venv
	. ${VENV}/bin/activate && ${PIP} install -r requirements.txt

run: venv
	. ${VENV}/bin/activate && ${PY} app.py

test: venv
	. ${VENV}/bin/activate && ${PY} -m pytest -q
