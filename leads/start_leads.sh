#!/bin/bash
set -a
source /opt/windi/leads/.env
set +a
cd /opt/windi/leads
exec python3 -m uvicorn app:app --host 0.0.0.0 --port 8096
