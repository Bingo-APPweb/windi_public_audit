#!/bin/bash
# DACP Milter Startup Wrapper
# Waits for pymilter to be available before starting milter
# This allows supervisor to autostart while waiting for user-patches.sh to install deps

MAX_WAIT=60
WAITED=0

echo "[DACP-WRAPPER] Waiting for pymilter module..."

while [ $WAITED -lt $MAX_WAIT ]; do
    if python3 -c "import Milter" 2>/dev/null; then
        echo "[DACP-WRAPPER] pymilter available, starting milter..."
        exec python3 /tmp/docker-mailserver/dacp-milter/dacp_milter.py
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

echo "[DACP-WRAPPER] ERROR: pymilter not available after ${MAX_WAIT}s"
exit 1
