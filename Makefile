.PHONY: install install-dev dev worker format lint test docker-build docker-up docker-down

VENV?=.venv
PYTHON?=python3

install:
$(PYTHON) -m venv $(VENV)
$(VENV)/bin/pip install --upgrade pip
$(VENV)/bin/pip install -r requirements.txt

install-dev:
$(PYTHON) -m venv $(VENV)
$(VENV)/bin/pip install --upgrade pip
$(VENV)/bin/pip install -r requirements-dev.txt

dev:
$(VENV)/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
$(VENV)/bin/python -m app.worker

format:
$(VENV)/bin/black app tests

lint:
$(VENV)/bin/ruff check app tests

test:
$(VENV)/bin/pytest -q

docker-build:
docker build -t image-to-video-api .

docker-up:
docker compose up --build

docker-down:
docker compose down

