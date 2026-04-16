#!/bin/bash
# Start WINDI Briefing Aggregator

cd /opt/windi/engine
nohup python3 briefing_aggregator.py > /opt/windi/logs/briefing.log 2>&1 &
echo $! > /tmp/briefing.pid
sleep 2

if curl -s http://127.0.0.1:8123/health | grep -q "healthy"; then
    echo "✅ Briefing Aggregator started on :8123"
    echo "   PID: $(cat /tmp/briefing.pid)"
else
    echo "❌ Failed to start"
    cat /opt/windi/logs/briefing.log | tail -20
fi
