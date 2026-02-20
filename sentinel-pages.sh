#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI SENTINEL — Page & Service Guardian
# "Antes de operar código, opera ambiente."
# Runs every 5 min via cron. Auto-restores broken pages.
# ═══════════════════════════════════════════════════════════════

LOG="/opt/windi/logs/sentinel-pages.log"
BACKUP_DIR="/opt/windi/sentinel-snapshots"
mkdir -p "$BACKUP_DIR" "$(dirname $LOG)"

ts() { date "+%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(ts)] $1" >> "$LOG"; }

ALERT=0

# ═══ PROTECTED PAGES ═══
declare -A PAGES
PAGES[suite]="/opt/windi/desktop/suite.html"
PAGES[composer]="/opt/windi/desktop/communique-composer.html"

for name in "${!PAGES[@]}"; do
    file="${PAGES[$name]}"
    snap="$BACKUP_DIR/${name}.html.good"
    
    if [ ! -f "$file" ] || [ ! -s "$file" ]; then
        # FILE MISSING OR EMPTY
        log "ALERT: $name is MISSING or EMPTY ($file)"
        if [ -f "$snap" ] && [ -s "$snap" ]; then
            cp "$snap" "$file"
            chmod 644 "$file"
            log "RESTORED $name from sentinel snapshot ($(wc -c < "$snap") bytes)"
        else
            log "CRITICAL: No snapshot available for $name!"
        fi
        ALERT=1
    elif ! head -1 "$file" | grep -qi "<!DOCTYPE\|<html"; then
        # FILE CORRUPTED (not valid HTML)
        log "ALERT: $name corrupted — no HTML header ($file)"
        if [ -f "$snap" ] && [ -s "$snap" ]; then
            cp "$snap" "$file"
            chmod 644 "$file"
            log "RESTORED $name from sentinel snapshot"
        fi
        ALERT=1
    else
        # FILE HEALTHY — update snapshot
        size=$(wc -c < "$file")
        if [ "$size" -gt 1000 ]; then
            cp "$file" "$snap"
            log "OK: $name healthy (${size}B) — snapshot updated"
        fi
    fi
done

# ═══ CRITICAL PORTS ═══
PORTS="8100:Desktop 8101:Ledger 8103:Export 8104:Viewer 8105:Communique"
for entry in $PORTS; do
    port="${entry%%:*}"
    name="${entry##*:}"
    if ss -tlnp | grep -q ":${port} "; then
        log "OK: $name :$port listening"
    else
        log "ALERT: $name :$port DOWN"
        ALERT=1
    fi
done

# ═══ NGINX CHECK ═══
if nginx -t 2>&1 | grep -q "successful"; then
    log "OK: nginx config valid"
else
    log "ALERT: nginx config INVALID"
    ALERT=1
fi

# ═══ HTTP CHECKS ═══
for url in "https://admin.windia4desk.tech/desktop/suite.html" "https://admin.windia4desk.tech/desktop/communique-composer.html"; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
    page=$(basename "$url")
    if [ "$code" = "200" ]; then
        log "OK: $page HTTP $code"
    else
        log "ALERT: $page HTTP $code"
        ALERT=1
    fi
done

if [ "$ALERT" -eq 0 ]; then
    log "--- SENTINEL PASS ---"
else
    log "!!! SENTINEL ALERT — issues detected !!!"
fi
