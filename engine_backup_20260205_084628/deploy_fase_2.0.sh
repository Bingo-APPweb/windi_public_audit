#!/bin/bash
# ============================================================
# WINDI Phase 2.0 — Templates Governed by API
# "O template NUNCA decide o nivel. A API decide.
#  O template apenas manifesta."
#
# Date: 02 Feb 2026
# Principle: Zero-Violence Deployment
# ============================================================
#
# What this does:
#   1. Backs up current BABEL file
#   2. Copies governance-editor.js to BABEL static/
#   3. Adds evolution API proxy route to BABEL Python
#   4. Injects <script> tag into BABEL HTML
#   5. Restarts BABEL
#   6. Runs verification tests
#
# Prerequisites:
#   - Phase 1.2 deployed (evolution API on port 8083)
#   - BABEL running on port 8085
#
# Rollback: bash rollback_to_pre2.0.sh
# ============================================================

set -e

BABEL_PY="/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
STATIC_DIR="/opt/windi/a4desk-editor/static"
BACKUP_DIR="/opt/windi/backups/fase_2.0_backup"
JS_SOURCE="/opt/windi/engine/governance-editor.js"

echo "============================================"
echo "  WINDI Phase 2.0 — Templates Governed by API"
echo "  $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================"
echo ""

# --- Step 0: Pre-flight ---
echo "[0/6] Pre-flight checks..."

if ! ss -tulnp | grep -q ":8083"; then
    echo "  ERROR: Evolution API not running on port 8083!"
    echo "  Deploy Phase 1.2 first."
    exit 1
fi
echo "  Evolution API (8083): OK"

if ! ss -tulnp | grep -q ":8085"; then
    echo "  WARNING: BABEL not running on port 8085"
fi
echo "  BABEL (8085): $(ss -tulnp | grep -q ':8085' && echo 'OK' || echo 'NOT RUNNING')"

if [ ! -f "$BABEL_PY" ]; then
    echo "  ERROR: $BABEL_PY not found!"
    exit 1
fi
echo "  BABEL Python: OK"

# Check evolution API health
EVOLUTION_STATUS=$(curl -s http://localhost:8083/api/governance/status 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('version','?'))" 2>/dev/null || echo "FAIL")
echo "  Evolution API version: $EVOLUTION_STATUS"
echo ""

# --- Step 1: Backup ---
echo "[1/6] Creating backup..."
mkdir -p "$BACKUP_DIR"
cp "$BABEL_PY" "$BACKUP_DIR/a4desk_tiptap_babel.py.pre2.0.bak"
echo "  Backup: $BACKUP_DIR/a4desk_tiptap_babel.py.pre2.0.bak"
echo ""

# --- Step 2: Copy JS to static ---
echo "[2/6] Installing governance-editor.js..."
mkdir -p "$STATIC_DIR"
if [ -f "$JS_SOURCE" ]; then
    cp "$JS_SOURCE" "$STATIC_DIR/governance-editor.js"
    echo "  Copied: $STATIC_DIR/governance-editor.js"
else
    echo "  ERROR: $JS_SOURCE not found!"
    echo "  Place governance-editor.js in /opt/windi/engine/ first."
    exit 1
fi
echo ""

# --- Step 3: Add evolution proxy route ---
echo "[3/6] Adding evolution API proxy route..."
python3 << 'PYEOF'
import sys

BABEL_PY = "/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"

with open(BABEL_PY, 'r') as f:
    content = f.read()

# Check if proxy already exists
if '/api/evolution/' in content:
    print("  Evolution proxy already exists — skipping.")
    sys.exit(0)

# Find the governance proxy block or the if __name__ block
PROXY_CODE = '''
# === Evolution API Proxy (Phase 2.0) ===
@app.route('/api/evolution/<path:endpoint>', methods=['GET', 'POST', 'OPTIONS'])
def evolution_proxy(endpoint):
    """Proxy requests to Evolution API on localhost:8083"""
    target = f"http://localhost:8083/api/governance/{endpoint}"
    try:
        if request.method == 'GET':
            resp = requests.get(target, timeout=10)
        elif request.method == 'POST':
            resp = requests.post(target, json=request.get_json(silent=True), timeout=10)
        else:
            return '', 204
        return (resp.content, resp.status_code, {
            'Content-Type': 'application/json',
            'X-WINDI-Source': 'evolution-api'
        })
    except Exception as e:
        return jsonify({"error": f"Evolution API unavailable: {str(e)}"}), 502
# === END Evolution API Proxy ===
'''

# Insert before if __name__
main_marker = "if __name__ == '__main__':"
if main_marker in content:
    pos = content.find(main_marker)
    content = content[:pos] + PROXY_CODE + '\n' + content[pos:]
    print("  Proxy route added before __main__.")
else:
    # Fallback: append before last line
    content = content.rstrip() + '\n' + PROXY_CODE + '\n'
    print("  Proxy route appended to end.")

with open(BABEL_PY, 'w') as f:
    f.write(content)

print("  OK: Evolution proxy injected.")
PYEOF
echo ""

# --- Step 4: Inject JS into BABEL HTML ---
echo "[4/6] Injecting governance-editor.js into BABEL HTML..."
python3 << 'PYEOF'
import sys

BABEL_PY = "/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"

with open(BABEL_PY, 'r') as f:
    content = f.read()

JS_TAG = '<script src="/static/governance-editor.js"></script>'

# Check if already injected
if 'governance-editor.js' in content:
    print("  JS already injected — skipping.")
    sys.exit(0)

# Find </body> or </html> in the BABEL_HTML string
# The HTML is inline, so we look for </body> in the Python source
injected = False

# Try </body>
if '</body>' in content:
    content = content.replace('</body>', JS_TAG + '\n</body>', 1)
    injected = True
    print("  Injected before </body>.")

# Fallback: try </html>
if not injected and '</html>' in content:
    content = content.replace('</html>', JS_TAG + '\n</html>', 1)
    injected = True
    print("  Injected before </html>.")

if not injected:
    print("  WARNING: Could not find injection point!")
    print("  Manual injection needed.")
    sys.exit(1)

with open(BABEL_PY, 'w') as f:
    f.write(content)

print("  OK: governance-editor.js injected into HTML.")
PYEOF
echo ""

# --- Step 5: Verify & Restart ---
echo "[5/6] Verifying syntax and restarting BABEL..."
python3 -c "import py_compile; py_compile.compile('$BABEL_PY', doraise=True); print('  SYNTAX OK')"

pkill -f a4desk_tiptap_babel.py 2>/dev/null || echo "  (no previous BABEL process)"
sleep 2

cd /opt/windi/a4desk-editor
source /etc/windi/secrets.env 2>/dev/null || true
nohup python3 a4desk_tiptap_babel.py > /tmp/babel.log 2>&1 &
BABEL_PID=$!
echo "  BABEL PID: $BABEL_PID"
sleep 3

if ps -p $BABEL_PID > /dev/null 2>&1; then
    echo "  BABEL alive: YES"
else
    echo "  ERROR: BABEL died!"
    tail -20 /tmp/babel.log
    echo ""
    echo "  ROLLBACK: cp $BACKUP_DIR/a4desk_tiptap_babel.py.pre2.0.bak $BABEL_PY"
    exit 1
fi

# Check startup log
echo ""
echo "  BABEL startup log:"
tail -8 /tmp/babel.log | sed 's/^/    /'
echo ""

# --- Step 6: Tests ---
echo "[6/6] Running verification tests..."
echo ""

echo "  TEST 1: BABEL homepage"
echo "  -------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8085/)
echo "  HTTP $HTTP_CODE (expect 200)"
echo ""

echo "  TEST 2: Governance JS served"
echo "  -------"
JS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8085/static/governance-editor.js)
JS_SIZE=$(curl -s http://localhost:8085/static/governance-editor.js 2>/dev/null | wc -c)
echo "  HTTP $JS_CODE, Size: $JS_SIZE bytes (expect 200, >5000)"
echo ""

echo "  TEST 3: Evolution proxy — heartbeat"
echo "  -------"
curl -s http://localhost:8085/api/evolution/status | python3 -m json.tool 2>/dev/null || echo "  PROXY FAILED"
echo ""

echo "  TEST 4: Evolution proxy — detect"
echo "  -------"
curl -s -X POST http://localhost:8085/api/evolution/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "Deutsche Bahn quarterly report summary"}' \
  | python3 -m json.tool 2>/dev/null || echo "  PROXY FAILED"
echo ""

echo "  TEST 5: Evolution proxy — recommend"
echo "  -------"
curl -s -X POST http://localhost:8085/api/evolution/recommend \
  -H "Content-Type: application/json" \
  -d '{"text": "Sehr geehrte Damen und Herren der Deutschen Bahn", "current_level": "LOW"}' \
  | python3 -m json.tool 2>/dev/null || echo "  PROXY FAILED"
echo ""

echo "  TEST 6: Existing governance proxy still works"
echo "  -------"
GOV_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8085/api/gov/status)
echo "  HTTP $GOV_CODE (expect 200)"
echo ""

echo "  TEST 7: JS injection verified in HTML"
echo "  -------"
if curl -s http://localhost:8085/ | grep -q "governance-editor.js"; then
    echo "  governance-editor.js found in HTML: YES"
else
    echo "  governance-editor.js found in HTML: NO (manual check needed)"
fi
echo ""

# --- Summary ---
echo "============================================"
echo "  PHASE 2.0 DEPLOYMENT SUMMARY"
echo "============================================"
echo "  BABEL PID: $BABEL_PID"
echo "  Backup: $BACKUP_DIR/"
echo ""
echo "  What was added:"
echo "    1. Evolution proxy: /api/evolution/* -> localhost:8083"
echo "    2. governance-editor.js in BABEL static/"
echo "    3. <script> tag injected in BABEL HTML"
echo ""
echo "  How it works:"
echo "    - Governance badge appears in BABEL editor"
echo "    - Click badge -> opens governance panel"
echo "    - Click 'Check Document' -> scans editor content"
echo "    - API detects institutions, recommends level"
echo "    - Editor border changes color (green/amber/red)"
echo "    - Advisor message shown in user's language"
echo ""
echo "  Principle enforced:"
echo "    'O template NUNCA decide o nivel."
echo "     A API decide. O template apenas manifesta.'"
echo ""
echo "  Test in browser:"
echo "    http://87.106.29.233:8085"
echo "    -> Write text with 'Deutsche Bahn' or 'ECB'"
echo "    -> Click shield badge -> Check Document"
echo "    -> See governance level change"
echo "============================================"
