#!/bin/sh
set -e
cd "$(dirname "$0")/backend"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.txt
exec .venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8000
