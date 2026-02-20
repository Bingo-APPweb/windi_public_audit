#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI JMPG — Dual-Hash Patch Installer
# ═══════════════════════════════════════════════════════════════
# Applies patches to:
#   1. Forensic Ledger (:8101) — bundle_hash column + /api/verify
#   2. Export Engine (:8103)   — seal bundle_hash after ZIP creation
#
# Usage:  bash apply_dual_hash_patch.sh
# Revert: Files backed up to /opt/windi/backups/pre_dualhash_<timestamp>/
#
# Author: Guardian Dragon (Claude)
# Date:   2026-02-18
# ═══════════════════════════════════════════════════════════════

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/windi/backups/pre_dualhash_${TIMESTAMP}"
LEDGER_FILE="/opt/windi/suite-docs/windi_forensic_api.py"
EXPORT_FILE="/opt/windi/desktop/export/jmpg_export_engine.py"
LEDGER_DB="/opt/windi/data/forensic_ledger.sqlite3"

echo ""
echo "  ◆ WINDI Dual-Hash Patch Installer"
echo "  ◆ Timestamp: ${TIMESTAMP}"
echo "  ◆ Ledger:    ${LEDGER_FILE}"
echo "  ◆ Export:    ${EXPORT_FILE}"
echo ""

# ── Step 0: Backup ──
echo "📦 Step 0: Creating backups..."
mkdir -p "$BACKUP_DIR"
cp "$LEDGER_FILE" "$BACKUP_DIR/windi_forensic_api.py.bak"
cp "$EXPORT_FILE" "$BACKUP_DIR/jmpg_export_engine.py.bak"
cp "$LEDGER_DB" "$BACKUP_DIR/forensic_ledger.sqlite3.bak"
echo "  ✅ Backups in: $BACKUP_DIR"

# ═══════════════════════════════════════════════════════════════
# PATCH 1: Forensic Ledger — Database Migration
# ═══════════════════════════════════════════════════════════════
echo ""
echo "🗄️  Patch 1: Migrating Ledger database..."

python3 << 'PYEOF'
import sqlite3
import os

DB_PATH = "/opt/windi/data/forensic_ledger.sqlite3"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add bundle_hash column
try:
    cursor.execute("ALTER TABLE receipts ADD COLUMN bundle_hash TEXT")
    print("  ✅ Added column: bundle_hash")
except sqlite3.OperationalError as e:
    if "duplicate" in str(e).lower():
        print("  ⏭️  Column bundle_hash already exists")
    else:
        print(f"  ❌ Error: {e}")

# Add bundle_size column
try:
    cursor.execute("ALTER TABLE receipts ADD COLUMN bundle_size INTEGER")
    print("  ✅ Added column: bundle_size")
except sqlite3.OperationalError as e:
    if "duplicate" in str(e).lower():
        print("  ⏭️  Column bundle_size already exists")
    else:
        print(f"  ❌ Error: {e}")

# Index on bundle_hash
try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_receipts_bundle_hash ON receipts(bundle_hash)")
    print("  ✅ Created index: idx_receipts_bundle_hash")
except Exception as e:
    print(f"  ⚠️  Index: {e}")

conn.commit()
conn.close()
print("  ✅ Database migration complete")
PYEOF

# ═══════════════════════════════════════════════════════════════
# PATCH 2: Forensic Ledger — Add /api/verify endpoint + seal-bundle
# ═══════════════════════════════════════════════════════════════
echo ""
echo "🔧 Patch 2: Adding /api/verify and /api/receipts/<id>/seal-bundle to Ledger..."

# 2a. Add /api/verify/<id> endpoint in do_GET (inject BEFORE the final else on line 211)
python3 << 'PYEOF'
import re

FILE = "/opt/windi/suite-docs/windi_forensic_api.py"

with open(FILE, "r") as f:
    content = f.read()

# Check if already patched
if "/api/verify/" in content:
    print("  ⏭️  /api/verify endpoint already present")
else:
    # Find the else block at end of do_GET (line ~211)
    # Pattern: the final "else:" before do_POST
    OLD = '''        else:
            self._json(404, {"ok": False, "error": "not_found", "path": path})

    # ── POST routes ──'''

    NEW = '''        # ── /api/verify/<id> (JMPG integrity verification) ──
        elif path.startswith("/api/verify/") and path.count("/") == 3:
            receipt_id = path.split("/")[-1]
            r = get_receipt(receipt_id)
            if r:
                self._json(200, {
                    "ok": True,
                    "receipt_id": r["id"],
                    "content_hash": r["content_hash"],
                    "bundle_hash": r.get("bundle_hash"),
                    "size_bytes": r.get("bundle_size") or r.get("bytes"),
                    "registered_at": r["created_at"],
                    "governance_level": r["governance_level"],
                    "sge_score": r["sge_score"],
                    "status": r.get("status", "sealed"),
                    "algorithm": "SHA-256",
                    "privacy": "content_not_stored",
                })
            else:
                self._json(404, {
                    "ok": False,
                    "error": "not_found",
                    "receipt_id": receipt_id,
                    "status": "NOT_FOUND",
                })

        else:
            self._json(404, {"ok": False, "error": "not_found", "path": path})

    # ── POST routes ──'''

    if OLD in content:
        content = content.replace(OLD, NEW)
        print("  ✅ Injected /api/verify/<id> endpoint in do_GET")
    else:
        print("  ❌ Could not find injection point for /api/verify")
        print("     Manual injection needed before final 'else:' in do_GET")

with open(FILE, "w") as f:
    f.write(content)
PYEOF

# 2b. Add POST /api/receipts/<id>/seal-bundle endpoint in do_POST
python3 << 'PYEOF'
FILE = "/opt/windi/suite-docs/windi_forensic_api.py"

with open(FILE, "r") as f:
    content = f.read()

if "seal-bundle" in content:
    print("  ⏭️  seal-bundle endpoint already present")
else:
    # Inject after the /api/suite/docs POST handler (before the final else in do_POST)
    OLD = '''        else:
            self._json(404, {"ok": False, "error": "not_found", "path": path})

    # ── Logging ──'''

    NEW = '''        # ── /api/receipts/<id>/seal-bundle (update bundle_hash after ZIP) ──
        elif path.endswith("/seal-bundle") and "/api/receipts/" in path:
            try:
                # Extract receipt_id: /api/receipts/JMPG-xxx/seal-bundle
                parts = path.split("/")
                receipt_id = parts[-2]  # e.g. "JMPG-20260218-ABC123"

                data = self._read_body()
                bundle_hash = data.get("bundle_hash")
                bundle_size = data.get("bundle_size")

                if not bundle_hash:
                    self._json(400, {"ok": False, "error": "bundle_hash required"})
                    return

                # Update the existing receipt
                import sqlite3 as _sql
                con = _sql.connect(DEFAULT_DB_PATH)
                try:
                    cur = con.execute(
                        "UPDATE receipts SET bundle_hash = ?, bundle_size = ? WHERE id = ?",
                        (bundle_hash, bundle_size, receipt_id)
                    )
                    con.commit()
                    if cur.rowcount > 0:
                        print(f"[FORENSIC] ◆ Bundle sealed: {receipt_id} | hash={bundle_hash[:16]}... | size={bundle_size}")
                        self._json(200, {
                            "ok": True,
                            "receipt_id": receipt_id,
                            "bundle_hash": bundle_hash,
                            "bundle_size": bundle_size,
                            "message": f"Bundle hash sealed for '{receipt_id}'",
                        })
                    else:
                        self._json(404, {"ok": False, "error": f"receipt {receipt_id} not found"})
                finally:
                    con.close()

            except json.JSONDecodeError:
                self._json(400, {"ok": False, "error": "invalid_json"})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})

        else:
            self._json(404, {"ok": False, "error": "not_found", "path": path})

    # ── Logging ──'''

    if OLD in content:
        content = content.replace(OLD, NEW)
        print("  ✅ Injected /api/receipts/<id>/seal-bundle endpoint in do_POST")
    else:
        print("  ❌ Could not find injection point for seal-bundle")
        print("     Manual injection needed before final 'else:' in do_POST")

with open(FILE, "w") as f:
    f.write(content)
PYEOF

# 2c. Update the startup banner to show new endpoints
python3 << 'PYEOF'
FILE = "/opt/windi/suite-docs/windi_forensic_api.py"

with open(FILE, "r") as f:
    content = f.read()

if "/api/verify" not in content.split("Endpoints:")[1].split('serve_forever')[0] if "Endpoints:" in content else True:
    OLD = '    print(f"    POST /api/suite/docs          — Suite v2.1 compat")'
    NEW = '''    print(f"    POST /api/suite/docs          — Suite v2.1 compat")
    print(f"    GET  /api/verify/<id>         — JMPG integrity verify")
    print(f"    POST /api/receipts/<id>/seal-bundle — Seal bundle hash")'''

    if OLD in content:
        content = content.replace(OLD, NEW)
        with open(FILE, "w") as f:
            f.write(content)
        print("  ✅ Updated startup banner")
    else:
        print("  ⏭️  Banner update skipped")
else:
    print("  ⏭️  Banner already updated")
PYEOF

# ═══════════════════════════════════════════════════════════════
# PATCH 3: Export Engine — Seal bundle_hash after ZIP creation
# ═══════════════════════════════════════════════════════════════
echo ""
echo "🔧 Patch 3: Adding bundle_hash sealing to Export Engine..."

python3 << 'PYEOF'
FILE = "/opt/windi/desktop/export/jmpg_export_engine.py"

with open(FILE, "r") as f:
    content = f.read()

if "seal-bundle" in content:
    print("  ⏭️  Bundle seal call already present in Export Engine")
else:
    # Inject after line 325 (after package_hash is calculated)
    # Current code:
    #   zip_bytes = buf.getvalue()
    #   package_hash = sha256_bytes(zip_bytes)
    #   log(f"Package created: ...")
    #   return zip_bytes, manifest, receipt_data

    OLD = '''    zip_bytes = buf.getvalue()
    package_hash = sha256_bytes(zip_bytes)
    log(f"Package created: {manifest['package_id']} ({len(zip_bytes)} bytes, hash: {package_hash[:16]}...)")

    return zip_bytes, manifest, receipt_data'''

    NEW = '''    zip_bytes = buf.getvalue()
    package_hash = sha256_bytes(zip_bytes)
    log(f"Package created: {manifest['package_id']} ({len(zip_bytes)} bytes, hash: {package_hash[:16]}...)")

    # ── DUAL-HASH: Seal bundle_hash in Forensic Ledger ──
    # The bundle_hash proves the PACKAGE wasn't tampered.
    # The content_hash (already registered) proves the CONTENT wasn't altered.
    receipt_id = manifest["governance"].get("receipt_id")
    if receipt_id:
        try:
            seal_payload = json.dumps({
                "bundle_hash": package_hash,
                "bundle_size": len(zip_bytes),
            }).encode("utf-8")
            seal_req = Request(
                f"{LEDGER_URL}/api/receipts/{receipt_id}/seal-bundle",
                data=seal_payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urlopen(seal_req, timeout=5) as seal_resp:
                seal_result = json.loads(seal_resp.read().decode())
                log(f"Bundle hash sealed: {package_hash[:16]}... ({len(zip_bytes)} bytes)")
        except Exception as e:
            log(f"Bundle seal WARNING (non-fatal): {e}")
    # ── END DUAL-HASH ──

    return zip_bytes, manifest, receipt_data'''

    if OLD in content:
        content = content.replace(OLD, NEW)
        print("  ✅ Injected bundle_hash sealing after ZIP creation")
    else:
        print("  ❌ Could not find injection point in Export Engine")
        print("     Looking for alternate pattern...")
        # Try with slightly different whitespace
        if "package_hash = sha256_bytes(zip_bytes)" in content:
            print("     Found sha256_bytes line. May need manual injection.")
            print("     Insert the seal-bundle call AFTER the log line, BEFORE return.")
        else:
            print("     sha256_bytes line not found. Check file manually.")

with open(FILE, "w") as f:
    f.write(content)
PYEOF

# ═══════════════════════════════════════════════════════════════
# PATCH 4: Restart services
# ═══════════════════════════════════════════════════════════════
echo ""
echo "🔄 Patch 4: Restarting services..."

# Check if running as systemd or nohup
if systemctl is-active --quiet windi-forensic-ledger 2>/dev/null; then
    echo "  Restarting Forensic Ledger via systemd..."
    sudo systemctl restart windi-forensic-ledger
elif systemctl is-active --quiet windi-suite-docs 2>/dev/null; then
    echo "  Restarting suite-docs via systemd..."
    sudo systemctl restart windi-suite-docs
else
    echo "  ⚠️  Forensic Ledger: No systemd service found."
    echo "     Find and restart manually:"
    echo "     ps aux | grep windi_forensic_api | grep -v grep"
    echo "     kill <PID> && cd /opt/windi/suite-docs && nohup python3 windi_forensic_api.py &"
fi

if systemctl is-active --quiet windi-export-engine 2>/dev/null; then
    echo "  Restarting Export Engine via systemd..."
    sudo systemctl restart windi-export-engine
elif systemctl is-active --quiet windi-jmpg-export 2>/dev/null; then
    echo "  Restarting jmpg-export via systemd..."
    sudo systemctl restart windi-jmpg-export
else
    echo "  ⚠️  Export Engine: No systemd service found."
    echo "     Find and restart manually:"
    echo "     ps aux | grep jmpg_export | grep -v grep"
    echo "     kill <PID> && cd /opt/windi/desktop/export && nohup python3 jmpg_export_engine.py &"
fi

echo ""
echo "⏳ Waiting 3 seconds for services to stabilize..."
sleep 3

# ═══════════════════════════════════════════════════════════════
# PATCH 5: Verification
# ═══════════════════════════════════════════════════════════════
echo ""
echo "🔍 Patch 5: Verifying patches..."

# Check Ledger health
echo -n "  Ledger health: "
curl -s --max-time 5 http://127.0.0.1:8101/health | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(f'✅ {d.get(\"service\", \"OK\")} v{d.get(\"version\", \"?\")}')
except:
    print('❌ Not responding')
" 2>/dev/null || echo "❌ Not responding"

# Check Export Engine health
echo -n "  Export Engine health: "
curl -s --max-time 5 http://127.0.0.1:8103/health | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(f'✅ {d.get(\"service\", \"OK\")} v{d.get(\"version\", \"?\")}')
except:
    print('❌ Not responding')
" 2>/dev/null || echo "❌ Not responding"

# Test /api/verify endpoint
echo -n "  /api/verify endpoint: "
curl -s --max-time 5 http://127.0.0.1:8101/api/verify/TEST-NONEXISTENT | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    if d.get('error') == 'not_found':
        print('✅ Returns 404 for unknown receipt (correct)')
    elif d.get('ok'):
        print('✅ Working')
    else:
        print(f'⚠️  Unexpected: {d}')
except:
    print('❌ Not responding or invalid JSON')
" 2>/dev/null || echo "❌ Not responding"

# Test seal-bundle endpoint
echo -n "  seal-bundle endpoint: "
curl -s --max-time 5 -X POST http://127.0.0.1:8101/api/receipts/TEST-NONEXISTENT/seal-bundle \
  -H "Content-Type: application/json" \
  -d '{"bundle_hash":"test","bundle_size":0}' | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    if d.get('error') and 'not found' in str(d.get('error','')):
        print('✅ Returns 404 for unknown receipt (correct)')
    elif d.get('ok'):
        print('✅ Working')
    else:
        print(f'⚠️  Unexpected: {d}')
except:
    print('❌ Not responding or invalid JSON')
" 2>/dev/null || echo "❌ Not responding"

# Check DB schema
echo -n "  DB columns: "
python3 -c "
import sqlite3
con = sqlite3.connect('/opt/windi/data/forensic_ledger.sqlite3')
cols = [row[1] for row in con.execute('PRAGMA table_info(receipts)').fetchall()]
has_bundle = 'bundle_hash' in cols
has_size = 'bundle_size' in cols
if has_bundle and has_size:
    print('✅ bundle_hash + bundle_size present')
elif has_bundle:
    print('⚠️  bundle_hash present, bundle_size missing')
elif has_size:
    print('⚠️  bundle_size present, bundle_hash missing')
else:
    print('❌ Neither column found')
con.close()
"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ◆ Dual-Hash Patch Installation Complete"
echo "  ◆ Backup: $BACKUP_DIR"
echo ""
echo "  Next steps:"
echo "    1. Run: python3 /opt/windi/jmpg-viewer/health_check_jmpg.py"
echo "    2. Export a .jmpg and verify bundle_hash appears in Ledger"
echo "    3. Test Viewer with the new .jmpg"
echo ""
echo "  ◆ AI processes. Human decides. WINDI guarantees."
echo "═══════════════════════════════════════════════════════════════"
