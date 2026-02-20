#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  WINDI WAR ROOM → systemd Migration                        ║
# ║  B4: Dashboard Resilience                                   ║
# ║  Port: 8090 | Process: Node.js                              ║
# ║  Date: 2026-02-15                                           ║
# ║  "AI processes. Human decides. WINDI guarantees."           ║
# ╚══════════════════════════════════════════════════════════════╝

set -e  # Exit on any error

echo "🐉 WINDI War Room → systemd Migration"
echo "══════════════════════════════════════"
echo ""

# ─── PHASE 1: RECONNAISSANCE ──────────────────────────────────
echo "📡 PHASE 1: Reconnaissance"
echo "──────────────────────────"

echo ""
echo "1.1 Directory contents:"
ls -la /opt/windi/war-room/ 2>/dev/null || { echo "❌ /opt/windi/war-room/ NOT FOUND — ABORT"; exit 1; }

echo ""
echo "1.2 Entry points (JS/PY/SH):"
find /opt/windi/war-room/ -maxdepth 3 \( -name '*.js' -o -name '*.py' -o -name '*.sh' -o -name 'package.json' -o -name '*.json' \) 2>/dev/null

echo ""
echo "1.3 package.json (if exists):"
cat /opt/windi/war-room/package.json 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "(no package.json or not valid JSON)"

echo ""
echo "1.4 Current port 8090 status:"
ss -tlnp | grep :8090 || echo "(port 8090 free)"

echo ""
echo "1.5 Any nohup/orphan process:"
ps aux | grep -E 'war.room|war_room|warroom|8090' | grep -v grep || echo "(no process found)"

echo ""
echo "1.6 Existing systemd unit:"
systemctl status windi-warroom 2>&1 | head -5 || true

echo ""
echo "1.7 Node.js version:"
node --version 2>/dev/null || echo "❌ Node.js NOT INSTALLED"
npm --version 2>/dev/null || echo "❌ npm NOT INSTALLED"

echo ""
echo "1.8 Log directory:"
ls -la /opt/windi/logs/ 2>/dev/null | head -5
mkdir -p /opt/windi/logs

echo ""
echo "1.9 .env file:"
cat /opt/windi/war-room/.env 2>/dev/null || echo "(no .env file)"

echo ""
echo "1.10 nginx war-room block:"
grep -n -A 12 'war-room' /etc/nginx/sites-enabled/admin.windia4desk.tech 2>/dev/null || echo "(no war-room nginx block)"

echo ""
echo "════════════════════════════════════════════"
echo "📋 PHASE 1 COMPLETE — Review output above"
echo "════════════════════════════════════════════"
echo ""
echo "👉 STOP HERE. Review the output."
echo "   Identify:"
echo "   - Entry point file (server.js? app.js? index.js?)"
echo "   - Node or Python process?"
echo "   - Does package.json have a 'start' script?"
echo "   - Is there an .env with PORT=8090?"
echo ""
echo "Then proceed to Phase 2 when ready."
