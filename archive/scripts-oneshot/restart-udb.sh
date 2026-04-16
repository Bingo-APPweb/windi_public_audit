#!/bin/bash
# W-UDB-001 Restart Script
# Restarts the Unified Dashboard service

set -e

echo "=== W-UDB-001 Restart ==="

cd /opt/windi/udb

# Kill any existing process on 8140
echo "Stopping any existing UDB process..."
fuser -k 8140/tcp 2>/dev/null || true
sleep 1

# Start UDB with nohup
echo "Starting UDB on port 8140..."
nohup python3 app.py > /tmp/udb.log 2>&1 &
echo $! > /opt/windi/udb/udb.pid

# Wait and test
sleep 3

echo "Testing health endpoint..."
if curl -s http://localhost:8140/health | grep -q "ok"; then
    echo "✅ W-UDB-001 is running!"
    echo "PID: $(cat /opt/windi/udb/udb.pid)"
else
    echo "❌ UDB failed to start. Check /tmp/udb.log"
    cat /tmp/udb.log | tail -20
fi
