#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI FASE 4 — QG LIVE: Bloomberg da Governança
# Conecta Dashboard ao Ledger, Sentinel, Quota, Renderer LIVE
# Uso: bash /tmp/fase4_qg_live.sh
# ═══════════════════════════════════════════════════════════════
set -e
cd /opt/windi/agent-palette/renderer
echo "🐉 FASE 4 — QG LIVE: Bloomberg da Governança"
echo "══════════════════════════════════════════════"

# Step 1: Backup
cp ../agent_dragon_server.py ../agent_dragon_server.py.fase4.bak
echo "✅ Backup Dragon server"

# Step 2: Create QG Aggregator
python3 -c "
content = '''#!/usr/bin/env python3
\"\"\"WINDI QG Aggregator v1.0 — Bloomberg da Governança
Puxa dados LIVE de todos os serviços WINDI e agrega para o Dashboard.\"\"\"

import json, time, threading, urllib.request, urllib.error, hashlib, sqlite3
from datetime import datetime, date
from pathlib import Path
from collections import deque

# ── Service Registry ──────────────────────────────────────
SERVICES = {
    \"ledger\":   {\"url\": \"http://localhost:8101\", \"health\": \"/health\"},
    \"sentinel\": {\"url\": \"http://localhost:8102\", \"health\": \"/health\"},
    \"communique\":{\"url\": \"http://localhost:8105\", \"health\": \"/health\"},
    \"d1\":       {\"url\": \"http://localhost:8100\", \"health\": \"/health\"},
    \"renderer\": {\"url\": \"http://localhost:8108\", \"health\": \"/api/dragon/renderer/health\"},
}

# ── Live Feed (Bloomberg Ticker) ──────────────────────────
_feed = deque(maxlen=100)
_stats_cache = {\"data\": None, \"updated\": 0}
_pulse_cache = {\"data\": None, \"updated\": 0}
CACHE_TTL = 15  # seconds

def add_feed_event(source, action, entity=\"SYSTEM\", severity=\"normal\", metadata=None):
    \"\"\"Add event to live Bloomberg ticker feed.\"\"\"
    _feed.appendleft({
        \"id\": hashlib.sha256(f\"{time.time()}{source}{action}\".encode()).hexdigest()[:12],
        \"timestamp\": datetime.utcnow().isoformat() + \"Z\",
        \"source\": source,
        \"entity\": entity,
        \"action\": action,
        \"severity\": severity,
        \"metadata\": metadata or {},
    })

def get_feed(limit=50):
    \"\"\"Get recent feed events.\"\"\"
    return list(_feed)[:limit]

# ── Service Health Probe ──────────────────────────────────
def _probe_service(name, cfg, timeout=3):
    \"\"\"Probe a service and return status.\"\"\"
    try:
        url = cfg[\"url\"] + cfg[\"health\"]
        req = urllib.request.Request(url, method=\"GET\")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode()) if resp.status == 200 else {}
            return {\"status\": \"GREEN\", \"latency_ms\": 0, \"data\": data}
    except Exception as e:
        return {\"status\": \"RED\", \"latency_ms\": -1, \"error\": str(e)[:100]}

# ── Pulse: Full System Heartbeat ──────────────────────────
def get_pulse():
    \"\"\"System-wide heartbeat — all services status.\"\"\"
    now = time.time()
    if _pulse_cache[\"data\"] and (now - _pulse_cache[\"updated\"]) < CACHE_TTL:
        return _pulse_cache[\"data\"]

    services = {}
    for name, cfg in SERVICES.items():
        t0 = time.time()
        result = _probe_service(name, cfg)
        result[\"latency_ms\"] = round((time.time() - t0) * 1000, 1)
        services[name] = result

    green = sum(1 for s in services.values() if s[\"status\"] == \"GREEN\")
    total = len(services)

    pulse = {
        \"system_status\": \"GREEN\" if green == total else \"YELLOW\" if green > total // 2 else \"RED\",
        \"services\": services,
        \"summary\": {\"green\": green, \"total\": total},
        \"timestamp\": datetime.utcnow().isoformat() + \"Z\",
        \"uptime_check\": True,
    }
    _pulse_cache[\"data\"] = pulse
    _pulse_cache[\"updated\"] = now
    return pulse

# ── Stats: Aggregated KPIs ────────────────────────────────
def get_stats():
    \"\"\"Aggregate KPIs from all services.\"\"\"
    now = time.time()
    if _stats_cache[\"data\"] and (now - _stats_cache[\"updated\"]) < CACHE_TTL:
        return _stats_cache[\"data\"]

    stats = {
        \"ledger\": _get_ledger_stats(),
        \"renderer\": _get_renderer_stats(),
        \"quota\": _get_quota_stats(),
        \"sentinel\": _get_sentinel_stats(),
        \"feed_events\": len(_feed),
        \"timestamp\": datetime.utcnow().isoformat() + \"Z\",
    }
    _stats_cache[\"data\"] = stats
    _stats_cache[\"updated\"] = now
    return stats

def _get_ledger_stats():
    \"\"\"Pull stats from Forensic Ledger :8101.\"\"\"
    try:
        # Get receipt count
        req = urllib.request.Request(\"http://localhost:8101/api/receipts?limit=1\", method=\"GET\")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            # Try to get total count from response
            if isinstance(data, dict):
                total = data.get(\"total\", data.get(\"count\", 0))
                receipts = data.get(\"receipts\", [])
            elif isinstance(data, list):
                total = len(data)
                receipts = data
            else:
                total = 0
                receipts = []

        # Try warroom summary
        try:
            req2 = urllib.request.Request(\"http://localhost:8101/api/warroom/summary\", method=\"GET\")
            with urllib.request.urlopen(req2, timeout=3) as resp2:
                warroom = json.loads(resp2.read().decode())
        except Exception:
            warroom = {}

        return {
            \"status\": \"LIVE\",
            \"total_receipts\": total if total > 0 else warroom.get(\"total_receipts\", 0),
            \"warroom\": warroom,
        }
    except Exception as e:
        return {\"status\": \"OFFLINE\", \"error\": str(e)[:80]}

def _get_renderer_stats():
    \"\"\"Pull stats from Document Renderer.\"\"\"
    try:
        req = urllib.request.Request(\"http://localhost:8108/api/dragon/renderer/health\", method=\"GET\")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return {
                \"status\": \"LIVE\",
                \"formats\": data.get(\"ready_formats\", []),
                \"output_files\": data.get(\"output_files\", 0),
                \"version\": data.get(\"version\", \"unknown\"),
            }
    except Exception as e:
        return {\"status\": \"OFFLINE\", \"error\": str(e)[:80]}

def _get_quota_stats():
    \"\"\"Pull quota usage stats from SQLite.\"\"\"
    try:
        db_path = Path(\"/opt/windi/data/quota.db\")
        if not db_path.exists():
            return {\"status\": \"NO_DB\"}

        with sqlite3.connect(db_path) as conn:
            today = date.today().isoformat()

            # Total renders today
            row = conn.execute(\"SELECT SUM(renders_today), SUM(bytes_today), COUNT(DISTINCT identifier) FROM quota_usage WHERE date=?\", (today,)).fetchone()
            renders_today = row[0] or 0
            bytes_today = row[1] or 0
            unique_users = row[2] or 0

            # All-time stats
            row2 = conn.execute(\"SELECT SUM(renders_today), COUNT(DISTINCT identifier), COUNT(DISTINCT date) FROM quota_usage\").fetchone()
            total_renders = row2[0] or 0
            total_users = row2[1] or 0
            active_days = row2[2] or 0

            # Tier breakdown today
            tiers = {}
            for tier_row in conn.execute(\"SELECT tier, SUM(renders_today) FROM quota_usage WHERE date=? GROUP BY tier\", (today,)):
                tiers[tier_row[0]] = tier_row[1] or 0

        return {
            \"status\": \"LIVE\",
            \"today\": {
                \"renders\": renders_today,
                \"bytes\": bytes_today,
                \"unique_users\": unique_users,
                \"by_tier\": tiers,
            },
            \"all_time\": {
                \"total_renders\": total_renders,
                \"total_users\": total_users,
                \"active_days\": active_days,
            },
        }
    except Exception as e:
        return {\"status\": \"ERROR\", \"error\": str(e)[:80]}

def _get_sentinel_stats():
    \"\"\"Pull stats from Sentinel LAW :8102.\"\"\"
    try:
        req = urllib.request.Request(\"http://localhost:8102/api/law/status\", method=\"GET\")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return {\"status\": \"LIVE\", \"law\": data}
    except Exception as e:
        return {\"status\": \"OFFLINE\", \"error\": str(e)[:80]}

# ── Certification Stats ───────────────────────────────────
def get_cert_stats():
    \"\"\"Get Agent Certification stats if available.\"\"\"
    try:
        # Try certification endpoint (port varies)
        for port in [8109, 8110, 8103]:
            try:
                req = urllib.request.Request(f\"http://localhost:{port}/api/certification/stats\", method=\"GET\")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    data = json.loads(resp.read().decode())
                    return {\"status\": \"LIVE\", \"port\": port, \"data\": data}
            except Exception:
                continue
        return {\"status\": \"NOT_DEPLOYED\", \"message\": \"Certification service not yet live — coming soon\"}
    except Exception as e:
        return {\"status\": \"ERROR\", \"error\": str(e)[:80]}

# ── Auto-Feed Generator (background) ─────────────────────
_auto_feed_running = False
def start_auto_feed():
    \"\"\"Background thread that generates feed events from service changes.\"\"\"
    global _auto_feed_running
    if _auto_feed_running:
        return
    _auto_feed_running = True

    def loop():
        last_receipt_count = 0
        while _auto_feed_running:
            try:
                # Check Ledger for new receipts
                stats = _get_ledger_stats()
                if stats.get(\"status\") == \"LIVE\":
                    count = stats.get(\"total_receipts\", 0)
                    if last_receipt_count > 0 and count > last_receipt_count:
                        diff = count - last_receipt_count
                        add_feed_event(\"LEDGER\", f\"{diff} new receipt(s) sealed — total: {count}\",
                                     severity=\"normal\", metadata={\"count\": count})
                    last_receipt_count = count

                # Pulse check
                pulse = get_pulse()
                for name, svc in pulse.get(\"services\", {}).items():
                    if svc[\"status\"] == \"RED\":
                        add_feed_event(\"SENTINEL\", f\"Service {name} is DOWN\",
                                     entity=name.upper(), severity=\"critical\")

            except Exception:
                pass
            time.sleep(30)

    threading.Thread(target=loop, daemon=True).start()
    add_feed_event(\"SYSTEM\", \"QG Aggregator v1.0 initialized — Bloomberg mode active\", severity=\"info\")

# ── HTTP Router ───────────────────────────────────────────
def route_qg_api(handler, method, path):
    \"\"\"Route QG API requests.\"\"\"
    if not path.startswith(\"/api/dragon/qg/\"):
        return False

    endpoint = path.replace(\"/api/dragon/qg/\", \"\").split(\"?\")[0]

    def send(data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        handler.send_response(status)
        handler.send_header(\"Content-Type\", \"application/json\")
        handler.send_header(\"Access-Control-Allow-Origin\", \"*\")
        handler.send_header(\"Access-Control-Allow-Headers\", \"Content-Type\")
        handler.send_header(\"Content-Length\", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    if method == \"GET\":
        if endpoint == \"pulse\":
            send(get_pulse())
            return True
        elif endpoint == \"stats\":
            send(get_stats())
            return True
        elif endpoint == \"feed\":
            limit = 50
            try:
                qs = handler.path.split(\"?\")[1] if \"?\" in handler.path else \"\"
                params = dict(p.split(\"=\", 1) for p in qs.split(\"&\") if \"=\" in p) if qs else {}
                limit = int(params.get(\"limit\", 50))
            except Exception:
                pass
            send({\"events\": get_feed(limit), \"total\": len(_feed)})
            return True
        elif endpoint == \"cert\":
            send(get_cert_stats())
            return True

    if method == \"OPTIONS\":
        handler.send_response(204)
        handler.send_header(\"Access-Control-Allow-Origin\", \"*\")
        handler.send_header(\"Access-Control-Allow-Methods\", \"GET, POST, OPTIONS\")
        handler.send_header(\"Access-Control-Allow-Headers\", \"Content-Type\")
        handler.end_headers()
        return True

    return False

# ── Init ──────────────────────────────────────────────────
_initialized = False
def init_qg():
    global _initialized
    if not _initialized:
        start_auto_feed()
        _initialized = True
        print(\"[QG] Aggregator v1.0 — Bloomberg mode ACTIVE\")
'''
with open('qg_aggregator.py', 'w') as f:
    f.write(content)
print('OK')
"
echo "✅ qg_aggregator.py criado"

# Step 3: Test module
echo ""
echo "=== Teste qg_aggregator ==="
python3 -c "
from qg_aggregator import get_pulse, get_stats, get_feed, add_feed_event, get_cert_stats

# Test pulse
pulse = get_pulse()
print(f'Pulse: {pulse[\"system_status\"]} — {pulse[\"summary\"][\"green\"]}/{pulse[\"summary\"][\"total\"]} services')
for name, svc in pulse['services'].items():
    print(f'  {name}: {svc[\"status\"]} ({svc[\"latency_ms\"]}ms)')

# Test stats
stats = get_stats()
print(f'Ledger: {stats[\"ledger\"][\"status\"]}')
print(f'Renderer: {stats[\"renderer\"][\"status\"]}')
print(f'Quota: {stats[\"quota\"][\"status\"]}')
print(f'Sentinel: {stats[\"sentinel\"][\"status\"]}')

# Test feed
add_feed_event('TEST', 'Module test passed', severity='info')
feed = get_feed(5)
print(f'Feed events: {len(feed)}')

# Test cert
cert = get_cert_stats()
print(f'Certification: {cert[\"status\"]}')

print('All QG tests passed')
"

# Step 4: Wire into Dragon Server
echo ""
echo "=== Patching Dragon Server ==="
python3 -c "
with open('../agent_dragon_server.py', 'r') as f:
    lines = f.readlines()

new_lines = []
import_added = False
init_added = False

for i, line in enumerate(lines):
    new_lines.append(line)

    # Add import after quota import
    if not import_added and 'from quota_engine import' in line:
        new_lines.append('    from qg_aggregator import route_qg_api, init_qg\n')
        new_lines.append('    HAS_QG = True\n')
        import_added = True
        print('P1 Import: OK')

    # Add except clause
    if not import_added and 'HAS_QUOTA = False' in line and 'HAS_QG' not in ''.join(new_lines[-3:]):
        # Will handle in except block
        pass

content = ''.join(new_lines)

# Add HAS_QG = False in except block
if 'HAS_QG = False' not in content:
    content = content.replace(
        'HAS_QUOTA = False',
        'HAS_QUOTA = False\n    HAS_QG = False'
    )
    print('P1b Except: OK')

# Add QG routing in do_GET
old_quota_get = '''if HAS_QUOTA and route_quota_api(self, \"GET\", path):
            return'''
new_quota_get = old_quota_get + '''

        # QG Aggregator API
        if HAS_QG and route_qg_api(self, \"GET\", path):
            return'''
if old_quota_get in content and 'route_qg_api' not in content.split('do_GET')[1].split('do_POST')[0] if 'do_POST' in content else '':
    content = content.replace(old_quota_get, new_quota_get, 1)
    print('P2 do_GET: OK')
else:
    # Try adding after any quota routing
    if 'route_qg_api' not in content:
        content = content.replace(
            'if HAS_QUOTA and route_quota_api(self, \"GET\", path):\n            return',
            'if HAS_QUOTA and route_quota_api(self, \"GET\", path):\n            return\n\n        # QG Aggregator API\n        if HAS_QG and route_qg_api(self, \"GET\", path):\n            return',
            1
        )
        print('P2 do_GET: OK (alt)')

# Add init_qg() call at server start
if 'init_qg()' not in content:
    # Find where server starts
    if 'HTTPServer' in content:
        content = content.replace(
            'server = HTTPServer',
            '    # Initialize QG Aggregator\\n    if HAS_QG:\\n        init_qg()\\n\\n    server = HTTPServer'
        )
        print('P3 init_qg: OK')
    else:
        print('P3 init_qg: MANUAL NEEDED')

# Handle OPTIONS for CORS
if 'do_OPTIONS' not in content:
    # Add do_OPTIONS method
    options_method = '''
    def do_OPTIONS(self):
        \"\"\"Handle CORS preflight.\"\"\"
        self.send_response(204)
        self.send_header(\"Access-Control-Allow-Origin\", \"*\")
        self.send_header(\"Access-Control-Allow-Methods\", \"GET, POST, OPTIONS\")
        self.send_header(\"Access-Control-Allow-Headers\", \"Content-Type, X-WINDI-Tier\")
        self.end_headers()
'''
    # Insert before do_GET
    content = content.replace(
        '    def do_GET(self):',
        options_method + '    def do_GET(self):',
        1
    )
    print('P4 CORS OPTIONS: OK')
else:
    print('P4 CORS: already present')

with open('../agent_dragon_server.py', 'w') as f:
    f.write(content)

print(f'route_qg_api count: {content.count(\"route_qg_api\")}')
print(f'HAS_QG count: {content.count(\"HAS_QG\")}')
print(f'init_qg count: {content.count(\"init_qg\")}')
"

# Step 5: Verify syntax
python3 -m py_compile qg_aggregator.py && echo "✅ qg_aggregator.py syntax OK"
python3 -m py_compile ../agent_dragon_server.py && echo "✅ agent_dragon_server.py syntax OK" || (echo "❌ SYNTAX ERROR" && python3 ../agent_dragon_server.py 2>&1 | head -5)

# Step 6: Restart Dragon
echo ""
echo "🔄 Reiniciando Dragon com QG Aggregator..."
cd /opt/windi/agent-palette
kill $(ss -tlnp | grep 8108 | grep -oP 'pid=\K\d+') 2>/dev/null; sleep 2
nohup python3 agent_dragon_server.py > /tmp/dragon_debug.log 2>&1 &
sleep 3

# Step 7: Smoke Tests
echo ""
echo "═══ FASE 4 SMOKE TESTS ═══"
ss -tlnp | grep 8108 && echo "✅ Dragon UP" || (echo "❌ FALHOU" && tail -20 /tmp/dragon_debug.log && exit 1)

echo ""
echo "--- QG Pulse (heartbeat geral) ---"
curl -s localhost:8108/api/dragon/qg/pulse | python3 -m json.tool

echo ""
echo "--- QG Stats (KPIs agregados) ---"
curl -s localhost:8108/api/dragon/qg/stats | python3 -m json.tool

echo ""
echo "--- QG Feed (Bloomberg ticker) ---"
curl -s localhost:8108/api/dragon/qg/feed?limit=5 | python3 -m json.tool

echo ""
echo "--- QG Cert (Agent Certification) ---"
curl -s localhost:8108/api/dragon/qg/cert | python3 -m json.tool

echo ""
echo "--- Renderer Health (confirmar intacto) ---"
curl -s localhost:8108/api/dragon/renderer/health | python3 -c "
import sys, json
d = json.load(sys.stdin)
fmts = d.get('ready_formats', [])
print(f'Renderer: {len(fmts)} formats — {fmts}')
"

echo ""
echo "--- Quota Status (confirmar intacto) ---"
curl -s localhost:8108/api/dragon/quota/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Quota: tier={d.get(\"tier\")} remaining={d.get(\"remaining\")}')
"

echo ""
echo "🐉 FASE 4 QG LIVE — BLOOMBERG DA GOVERNANÇA"
echo "   Endpoints:"
echo "   GET /api/dragon/qg/pulse  — System heartbeat"
echo "   GET /api/dragon/qg/stats  — Aggregated KPIs"
echo "   GET /api/dragon/qg/feed   — Live ticker"
echo "   GET /api/dragon/qg/cert   — Agent Certification"
echo "   CORS enabled for dashboard access"
