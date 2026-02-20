#!/bin/bash
# ============================================================
# WINDI Certification Backoffice — Deployment Script
# ============================================================
# DOC-ID: CERT-DEPLOY-2026-001
# Date: 10 February 2026
# Author: Three Dragons Protocol (Guardian)
#
# USAGE:
#   chmod +x deploy_backoffice.sh
#   ./deploy_backoffice.sh
#
# PREREQUISITES:
#   - SSH access to Strato (windi@87.106.29.233)
#   - Existing Flask app serving admin.windia4desk.tech
#   - Python3, Flask, sqlite3
# ============================================================

set -e

echo "🐉 WINDI Certification Backoffice — Deployment"
echo "================================================"
echo ""

# ===== CONFIGURATION =====
# CHANGE THESE BEFORE DEPLOY:
ADMIN_TOKEN="YOUR_SECURE_TOKEN_HERE"       # Generate: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
NOTIFY_EMAIL="your@email.com"              # Email for notifications (optional)

REMOTE_HOST="windi@87.106.29.233"
CERT_DIR="/opt/windi/agents/certification"
BACKUP_DIR="/opt/windi/backups/pre_backoffice_$(date +%Y%m%d_%H%M%S)"

echo "📋 Pre-deployment checklist:"
echo "   [ ] ADMIN_TOKEN set? (current: ${ADMIN_TOKEN:0:10}...)"
echo "   [ ] NOTIFY_EMAIL set? (current: ${NOTIFY_EMAIL})"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 1; fi

# ===== STEP 1: BACKUP =====
echo ""
echo "1️⃣  Creating backup..."
ssh $REMOTE_HOST "mkdir -p $BACKUP_DIR && \
  cp -r $CERT_DIR $BACKUP_DIR/ 2>/dev/null || echo 'No existing cert dir to backup' && \
  echo '✅ Backup at $BACKUP_DIR'"

# ===== STEP 2: CREATE DIRECTORY STRUCTURE =====
echo ""
echo "2️⃣  Creating directory structure..."
ssh $REMOTE_HOST "mkdir -p $CERT_DIR"

# ===== STEP 3: UPLOAD FILES =====
echo ""
echo "3️⃣  Uploading backoffice files..."
scp backoffice.py $REMOTE_HOST:$CERT_DIR/backoffice.py
scp admin_dashboard.html $REMOTE_HOST:$CERT_DIR/admin_dashboard.html
echo "   ✅ Files uploaded"

# ===== STEP 4: INITIALIZE DATABASE =====
echo ""
echo "4️⃣  Initializing database..."
ssh $REMOTE_HOST "cd $CERT_DIR && python3 -c '
import sqlite3, os
os.makedirs(os.path.dirname(\"applications.db\"), exist_ok=True)
conn = sqlite3.connect(\"applications.db\")
conn.executescript(\"\"\"
CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    agent_model TEXT,
    operator_name TEXT NOT NULL,
    operator_email TEXT NOT NULL,
    motivation TEXT,
    accepted_terms INTEGER DEFAULT 0,
    status TEXT DEFAULT \\\"pending\\\",
    review_notes TEXT,
    reviewed_by TEXT,
    reviewed_at TEXT,
    certification_level TEXT,
    created_at TEXT DEFAULT (datetime(\\\"now\\\")),
    updated_at TEXT DEFAULT (datetime(\\\"now\\\")),
    integrity_hash TEXT
);
CREATE TABLE IF NOT EXISTS certification_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT,
    actor TEXT DEFAULT \\\"system\\\",
    created_at TEXT DEFAULT (datetime(\\\"now\\\")),
    integrity_hash TEXT,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);
CREATE INDEX IF NOT EXISTS idx_app_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_app_created ON applications(created_at);
\"\"\")
conn.commit()
print(\"✅ Database initialized\")
'"

# ===== STEP 5: MIGRATE EXISTING APPLICATIONS =====
echo ""
echo "5️⃣  Checking for existing applications to migrate..."
ssh $REMOTE_HOST "
  # Look for existing application files
  for f in $CERT_DIR/applications.json $CERT_DIR/../applications.json /opt/windi/data/applications.json; do
    if [ -f \"\$f\" ]; then
      echo \"   Found: \$f — will migrate after integration\"
    fi
  done
  echo '   ✅ Migration check complete'
"

# ===== STEP 6: INTEGRATION INSTRUCTIONS =====
echo ""
echo "6️⃣  Integration instructions:"
echo ""
echo "   The backoffice needs to be integrated with the existing Flask app."
echo "   Find the main Flask app file (likely serving admin.windia4desk.tech)"
echo "   and add these lines:"
echo ""
echo "   ──────────────────────────────────────────────────"
echo "   # At the top of the file:"
echo "   import os"
echo "   os.environ['WINDI_ADMIN_TOKEN'] = '$ADMIN_TOKEN'"
echo "   os.environ['WINDI_NOTIFY_EMAIL'] = '$NOTIFY_EMAIL'"
echo ""
echo "   # Import backoffice"
echo "   import sys"
echo "   sys.path.insert(0, '$CERT_DIR')"
echo "   from backoffice import backoffice_bp, init_backoffice"
echo ""
echo "   # After app = Flask(__name__):"
echo "   init_backoffice(app)"
echo "   app.register_blueprint(backoffice_bp)"
echo ""
echo "   # Add admin dashboard route:"
echo "   @app.route('/admin')"
echo "   def admin_dashboard():"
echo "       token = request.args.get('token', '')"
echo "       if token != os.environ.get('WINDI_ADMIN_TOKEN'):"
echo "           return 'Unauthorized', 401"
echo "       with open('$CERT_DIR/admin_dashboard.html') as f:"
echo "           return f.read()"
echo "   ──────────────────────────────────────────────────"
echo ""
echo "   Then restart the Flask app."
echo ""

# ===== STEP 7: GENERATE SECURE TOKEN =====
echo "7️⃣  Generate a secure admin token:"
echo ""
echo "   Run on Strato:"
echo "   python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
echo ""
echo "   Then set it in the Flask app environment."
echo ""

# ===== STEP 8: VERIFY =====
echo "8️⃣  After integration, verify:"
echo ""
echo "   # Check admin dashboard"
echo "   curl -s -o /dev/null -w '%{http_code}' https://admin.windia4desk.tech/admin?token=YOUR_TOKEN"
echo "   # Should return 200"
echo ""
echo "   # Check applications API"
echo "   curl -s https://admin.windia4desk.tech/api/applications -H 'Authorization: Bearer YOUR_TOKEN'"
echo "   # Should return JSON with applications list"
echo ""
echo "   # Check ledger"
echo "   curl -s https://admin.windia4desk.tech/api/certification-ledger -H 'Authorization: Bearer YOUR_TOKEN'"
echo "   # Should return JSON with ledger entries"
echo ""

echo "================================================"
echo "🐉 Deployment preparation complete!"
echo ""
echo "ACCESS: https://admin.windia4desk.tech/admin?token=YOUR_TOKEN"
echo ""
echo "ENDPOINTS:"
echo "  GET  /admin                    — Dashboard UI"
echo "  POST /api/apply                — New applications (public)"
echo "  GET  /api/applications         — List all (admin)"
echo "  GET  /api/applications/<id>    — Detail + events (admin)"
echo "  POST /api/applications/<id>/review — Approve/Reject (admin)"
echo "  GET  /api/applications/stats   — Dashboard stats (admin)"
echo "  GET  /api/certification-ledger — Forensic ledger (admin)"
echo "  POST /api/migrate-existing     — Import old data (admin)"
echo ""
echo "\"AI processes. Human decides. WINDI guarantees.\" 🐉🛡️"
