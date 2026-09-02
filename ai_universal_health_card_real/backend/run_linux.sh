#!/usr/bin/env bash
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
echo "Edit .env, create MySQL database, then run:"
echo "uvicorn app.main:app --reload --port 8000"
