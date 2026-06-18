#!/bin/bash
# W-MAIL-DACP-MILTER Watchdog Script
# Spec: §227 Section 10.2 (Survivability Hardening)
# Created: 2026-06-18 by DACP-SURVIVABILITY-HARDENING-001
#
# This script ensures the DACP milter is running inside the container.
# Called by systemd after docker.service is up.

CONTAINER="windi-mailserver"
SUPERVISOR_CONF="/opt/windi/w-mail-001/config/supervisor/dacp-milter.conf"
LOG="/opt/windi/logs/dacp-milter-watchdog.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting DACP milter watchdog"

# Wait for container to be running
RETRIES=30
while [ $RETRIES -gt 0 ]; do
    if docker ps --filter "name=$CONTAINER" --filter "status=running" --format '{{.Names}}' | grep -q "$CONTAINER"; then
        log "Container $CONTAINER is running"
        break
    fi
    log "Waiting for container $CONTAINER... ($RETRIES retries left)"
    sleep 2
    RETRIES=$((RETRIES - 1))
done

if [ $RETRIES -eq 0 ]; then
    log "ERROR: Container $CONTAINER not running after timeout"
    exit 1
fi

# Wait for container to be healthy
sleep 5

# Copy supervisor config into container
log "Copying supervisor config to container..."
docker cp "$SUPERVISOR_CONF" "$CONTAINER:/etc/supervisor/conf.d/dacp-milter.conf"
if [ $? -ne 0 ]; then
    log "ERROR: Failed to copy supervisor config"
    exit 1
fi

# Reload supervisord
log "Reloading supervisord..."
docker exec "$CONTAINER" supervisorctl reread
docker exec "$CONTAINER" supervisorctl update

# Check if milter is already running via supervisor
if docker exec "$CONTAINER" supervisorctl status dacp-milter 2>/dev/null | grep -q "RUNNING"; then
    log "DACP milter already running via supervisor"
    exit 0
fi

# Start the milter via supervisor
log "Starting DACP milter via supervisor..."
docker exec "$CONTAINER" supervisorctl start dacp-milter

# Verify milter is listening
sleep 3
if docker exec "$CONTAINER" ss -tlnp | grep -q ':8890'; then
    log "SUCCESS: DACP milter is running on port 8890"
    exit 0
else
    log "ERROR: DACP milter failed to start on port 8890"
    exit 1
fi
