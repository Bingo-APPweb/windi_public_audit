#!/bin/bash
# W-UDB-001 — WINDI Unified Dashboard
# Start script for production

cd /opt/windi/udb

# Activate virtual environment if exists
if [ -d "/opt/windi/venvs/udb" ]; then
    source /opt/windi/venvs/udb/bin/activate
fi

# Export environment
export FLASK_APP=app.py
export FLASK_ENV=production

# Start with gunicorn for production
if command -v gunicorn &> /dev/null; then
    exec gunicorn -w 2 -b 0.0.0.0:8140 --timeout 120 app:app
else
    # Fallback to Flask dev server
    exec python3 app.py
fi
