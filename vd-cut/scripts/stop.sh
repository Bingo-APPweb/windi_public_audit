#!/bin/bash
# W-VD-CUT-001 — Stop Script
# Liga IA+H · Kempten, Bavaria · 2026

PORT=8128

echo "Stopping W-VD-CUT-001..."

# Find and kill process
pid=$(ss -tlnp 2>/dev/null | grep ":$PORT" | grep -oP 'pid=\K\d+' | head -1)

if [ -n "$pid" ]; then
    kill "$pid"
    echo "Stopped process $pid"
else
    echo "W-VD-CUT-001 not running"
fi
