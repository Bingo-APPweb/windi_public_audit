#!/bin/bash
# ═══════════════════════════════════════════════════════════
# WINDI Integrity Watchdog — Cron Job
# Runs every 6 hours + dead-man check every hour
# Three Dragons Protocol — Guardian Approved
# ═══════════════════════════════════════════════════════════

set -e

WATCHDOG_DIR="/opt/windi/agents/integrity_watchdog"
LOG_DIR="$WATCHDOG_DIR/logs"
LOG="$LOG_DIR/cron_$(date +%Y%m%d).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Watchdog cron triggered" >> "$LOG"

cd "$WATCHDOG_DIR"

# Run full verification check
python3 watchdog_engine.py --full-check --json >> "$LOG" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WATCHDOG FAILURE exit=$EXIT_CODE" >> "$LOG"
    # Trigger dead-man alert
    python3 watchdog_scheduler.py --dead-man-check >> "$LOG" 2>&1
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Watchdog cron completed (exit=$EXIT_CODE)" >> "$LOG"

# Cleanup old logs (keep last 30 days)
find "$LOG_DIR" -name "cron_*.log" -mtime +30 -delete 2>/dev/null || true
find "$LOG_DIR" -name "watchdog_*.log" -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE
