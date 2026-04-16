#!/bin/bash
# Restart W-COST-001 with .env loaded

set -e

# Kill existing
PID=$(lsof -ti:8152 2>/dev/null || true)
if [ -n "$PID" ]; then
    kill -9 $PID
    sleep 1
    echo "Killed PID $PID"
fi

# Start with nohup
cd /opt/windi/w-cost-001
nohup python3 app.py > /opt/windi/logs/w-cost-001.log 2>&1 &
sleep 2

# Verify
NEW_PID=$(lsof -ti:8152 2>/dev/null || true)
if [ -n "$NEW_PID" ]; then
    echo "✓ W-COST-001 running on :8152 (PID $NEW_PID)"

    # Test health endpoint
    curl -s http://127.0.0.1:8152/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✓ Status: {d[\"status\"]}'); print(f'✓ Events: {d[\"events_recorded\"]}')"
else
    echo "✗ Failed to start"
    exit 1
fi
