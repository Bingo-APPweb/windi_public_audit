#!/bin/bash
# WINDI Forensic API Startup Script

cd /opt/windi/forensic

# Kill previous instance if running
pkill -f forensic_validate_handwritten.py || true

# Wait a moment
sleep 2

# Start API
nohup python3 forensic_validate_handwritten.py > /tmp/forensic_api.log 2>&1 &

# Get PID
PID=$!

echo "🐉 WINDI Forensic API started"
echo "   PID: $PID"
echo "   Log: /tmp/forensic_api.log"
echo ""
echo "   Test with:"
echo "   curl http://localhost:8091/health"
echo ""

# Show log tail
sleep 2
echo "📋 Log tail:"
tail -20 /tmp/forensic_api.log
