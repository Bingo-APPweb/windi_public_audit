# ═══════════════════════════════════════════════════════════════
# WINDI Sentinel Bridge — Deployment Guide
# "O Sentinel observa. A Bridge traduz. O Ministro decide."
# ═══════════════════════════════════════════════════════════════
# Date: 15 February 2026
# Port: 8098
# Architecture: sentinel.py → state.json → bridge API → dashboard
# ═══════════════════════════════════════════════════════════════

# ─── STEP 0: Backup ──────────────────────────────────────────
BK="/opt/windi/backups/pre_sentinel_bridge_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BK
# Backup existing sentinel if it exists
cp /opt/windi/sentinel/sentinel.py $BK/ 2>/dev/null
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech $BK/nginx.conf
echo "✓ Backup: $BK"

# ─── STEP 1: Create Bridge Directory ─────────────────────────
mkdir -p /opt/windi/sentinel-bridge
mkdir -p /opt/windi/logs

# ─── STEP 2: Deploy Bridge Files ─────────────────────────────
# Copy sentinel_bridge.py to server
cp sentinel_bridge.py /opt/windi/sentinel-bridge/
cp sentinel_state_writer.py /opt/windi/sentinel-bridge/

# Also copy state writer to sentinel directory for import
cp sentinel_state_writer.py /opt/windi/sentinel/

# ─── STEP 3: Patch Sentinel Daemon ───────────────────────────
# Add to sentinel.py's main loop:
#
# from sentinel_state_writer import write_state, write_history_point, write_incident
#
# At end of each monitoring cycle, call:
#   write_state(services_dict, overall_status, cycle_ms)
#
# On state change, call:
#   write_incident(old_status, new_status, trigger_service)
#
# Every ~60 cycles, call:
#   write_history_point(status, healthy_count, total, avg_latency)

# ─── STEP 4: Check Port Available ────────────────────────────
ss -tlnp | grep :8098
# Should be empty. If not, resolve conflict.

# ─── STEP 5: Test Bridge Locally ─────────────────────────────
cd /opt/windi/sentinel-bridge
python3 sentinel_bridge.py &
sleep 2
curl -s http://localhost:8098/health | python3 -m json.tool
# Should show: {"service": "WINDI Sentinel Bridge", "status": "healthy", ...}
curl -s http://localhost:8098/api/status | python3 -m json.tool
# Should show service states
curl -s http://localhost:8098/api/minister | python3 -m json.tool
# Should show minister-abstracted view
kill %1

# ─── STEP 6: Deploy systemd Service ──────────────────────────
sudo cp windi-sentinel-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable windi-sentinel-bridge.service
sudo systemctl start windi-sentinel-bridge.service
sudo systemctl status windi-sentinel-bridge.service --no-pager

# ─── STEP 7: Configure nginx ─────────────────────────────────
# Find the line number of "listen 443 ssl"
grep -n "listen 443 ssl" /etc/nginx/sites-enabled/admin.windia4desk.tech
# Inject the snippet BEFORE that line (replace LINE_NUM)
# Use the nginx_sentinel_snippet.conf content

sudo nginx -t
sudo systemctl reload nginx

# ─── STEP 8: Test via HTTPS ──────────────────────────────────
curl -s https://admin.windia4desk.tech/sentinel/health | python3 -m json.tool
curl -s https://admin.windia4desk.tech/sentinel/api/status | python3 -m json.tool
curl -s https://admin.windia4desk.tech/sentinel/api/minister | python3 -m json.tool

# ─── STEP 9: Restart Sentinel with State Writer ──────────────
# After patching sentinel.py with state writer calls:
sudo systemctl restart windi-sentinel.service
# Verify state file is being written:
sleep 5
cat /opt/windi/data/sentinel_state.json | python3 -m json.tool

# ─── STEP 10: Smoke Test — Kill a Service ─────────────────────
# Test the full chain: kill a service → sentinel detects → bridge serves → dashboard updates
#
# Terminal 1: Watch the bridge output
# curl -s http://localhost:8098/api/minister | python3 -m json.tool
#
# Terminal 2: Kill a non-critical service temporarily
# sudo systemctl stop windi-clone
# sleep 10
# curl -s http://localhost:8098/api/minister | python3 -m json.tool
# # Should show DEGRADED state
# sudo systemctl start windi-clone
# sleep 10
# curl -s http://localhost:8098/api/minister | python3 -m json.tool
# # Should return to NOMINAL

# ═══════════════════════════════════════════════════════════════
# VERIFICATION CHECKLIST
# ═══════════════════════════════════════════════════════════════
# □ sentinel_bridge.py running on port 8098
# □ systemd service enabled and active
# □ nginx routing /sentinel/ → :8098
# □ /health returns healthy
# □ /api/status returns service data
# □ /api/minister returns abstracted view
# □ sentinel.py writing to sentinel_state.json
# □ State file updates every cycle
# □ Kill-test triggers status change
# □ Recovery restores NOMINAL
# ═══════════════════════════════════════════════════════════════

# PORT MAP UPDATE:
# | 8098 | Sentinel Bridge | python3 | windi-sentinel-bridge | Dashboard nerve system |
