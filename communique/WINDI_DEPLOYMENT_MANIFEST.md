# WINDI DEPLOYMENT MANIFEST — PACT v1.0 Components
# Date: 2026-02-19
# For: Claude Code deployment on Strato (87.106.29.233)
# SSH: windi@87.106.29.233

## OVERVIEW

This manifest defines EXACTLY where to deploy each component built during
the PACT Protocol v1.0 development session. Claude Code should read this
file BEFORE executing any deployment commands.

Reference skills:
- /mnt/skills/user/windi-location-matrix/SKILL.md (port/path GPS)
- /mnt/skills/user/windi-infra/SKILL.md (nginx/systemd procedures)

---

## COMPONENT 1: WINDI PACT Protocol v1.0

**Type:** Governance document (markdown)
**Source:** WINDI_PACT_PROTOCOL_v1.0.md
**Destination:** `/opt/windi/isp/schema/WINDI_PACT_v1.0.md`
**Action:** Copy file, then seal hash in Ledger

```bash
# Deploy
cp WINDI_PACT_PROTOCOL_v1.0.md /opt/windi/isp/schema/WINDI_PACT_v1.0.md
chown windi:windi /opt/windi/isp/schema/WINDI_PACT_v1.0.md

# Seal in Ledger
HASH=$(sha256sum /opt/windi/isp/schema/WINDI_PACT_v1.0.md | cut -d' ' -f1)
curl -X POST http://127.0.0.1:8101/api/receipts \
  -H "Content-Type: application/json" \
  -d "{
    \"doc_type\": \"governance\",
    \"doc_name\": \"[PACT] WINDI PACT Protocol v1.0 — Three Dragons Sealed\",
    \"content_hash\": \"$HASH\",
    \"status\": \"sealed\"
  }"
```

**Verification:**
```bash
ls -la /opt/windi/isp/schema/WINDI_PACT_v1.0.md
curl -s http://127.0.0.1:8101/api/receipts | python3 -c "
import sys,json
data=json.load(sys.stdin)
receipts=data.get('receipts',data) if isinstance(data,dict) else data
for r in receipts[-3:]:
    print(r.get('doc_name','')[:60], r.get('id',''))
"
```

---

## COMPONENT 2: JMPG Packager v1.0

**Type:** Python module (packaging engine)
**Source:** jmpg_packager.py
**Destination:** `/opt/windi/export-engine/jmpg_packager.py`
**Integrates with:** Export Engine (:8103)
**Dependencies:** Python 3.11+ stdlib only (hashlib, zipfile, json, io)

```bash
# Deploy
cp jmpg_packager.py /opt/windi/export-engine/jmpg_packager.py
chown windi:windi /opt/windi/export-engine/jmpg_packager.py

# Test
cd /opt/windi/export-engine
python3 jmpg_packager.py pack
python3 jmpg_packager.py verify /tmp/windi_jmpg_test/*.jmpg
```

**Integration notes:**
- The Export Engine (:8103) currently generates PDFs with reportlab+qrcode
- jmpg_packager.py adds .jmpg bundle creation capability
- Import in existing export code: `from jmpg_packager import package_communique, CommuniqueContent, EvidenceFile`
- Output staging dir: `/opt/windi/vault/staging/` (packager creates it if missing)
- After packaging, the .jmpg should be moved to Vault: `/opt/windi/vault/public/multimedia/`
- Restart Export Engine after integration: `sudo systemctl restart windi-export`

---

## COMPONENT 3: Sovereign Reader v2.1

**Type:** Static HTML file (standalone, zero dependencies)
**Source:** WINDI_Sovereign_Reader_v2.1.html
**Destination:** `/var/www/windi-reader/index.html`
**Public URL:** `https://admin.windia4desk.tech/reader/`
**Also accessible at:** JMPG Viewer (:8104) can serve it

### Deploy as static file (recommended for universal access):

```bash
# Create directory
sudo mkdir -p /var/www/windi-reader
sudo cp WINDI_Sovereign_Reader_v2.1.html /var/www/windi-reader/index.html
sudo chown -R www-data:www-data /var/www/windi-reader

# Add nginx location (in admin.windia4desk.tech config)
# INJECT BEFORE 'listen 443 ssl;' line
#
#     # ── Sovereign Reader (universal, static) ─────────
#     location /reader/ {
#         alias /var/www/windi-reader/;
#         index index.html;
#         add_header Cache-Control "no-cache";
#         add_header X-WINDI-Component "Sovereign-Reader-v2.1";
#     }
#     # ── END Sovereign Reader ────────────────────────

sudo nginx -t && sudo systemctl reload nginx
```

### Also deploy to JMPG Viewer service:

```bash
# The Viewer (:8104) can serve the Reader as its main page
cp WINDI_Sovereign_Reader_v2.1.html /opt/windi/jmpg-viewer/reader.html
chown windi:windi /opt/windi/jmpg-viewer/reader.html
sudo systemctl restart windi-viewer
```

**Verification:**
```bash
curl -s -o /dev/null -w "%{http_code}" https://admin.windia4desk.tech/reader/
# Expected: 200
```

**URL patterns the Reader accepts:**
- `https://admin.windia4desk.tech/reader/` — drop zone (offline mode)
- `https://admin.windia4desk.tech/reader/?id=VR-COM-xxxxx` — auto-fetch from Vault
- `https://admin.windia4desk.tech/reader/?bundle=https://...` — fetch from any URL

---

## COMPONENT 4: Evidence Uploader (React)

**Type:** React component (.jsx)
**Source:** EvidenceUploader.jsx
**Destination:** `/opt/windi/desktop/src/components/EvidenceUploader.jsx`
**Integrates with:** Desktop (:8100) — React+Tiptap+Zustand app

```bash
# Deploy
cp EvidenceUploader.jsx /opt/windi/desktop/src/components/EvidenceUploader.jsx
chown windi:windi /opt/windi/desktop/src/components/EvidenceUploader.jsx

# Integration in Desktop app:
# 1. Import in the Composer/Editor view
# 2. Add as panel/modal triggered by "Add Evidence" button
# 3. Connect "Seal Evidence" button to Export Engine API
# 4. Rebuild React app: cd /opt/windi/desktop && npm run build
# 5. Restart: sudo systemctl restart windi-desktop
```

**Integration notes:**
- Component uses React hooks (useState, useRef, useCallback)
- Uses Web Crypto API for client-side SHA-256 (no npm dependencies)
- Designed for Zustand store integration (evidence state)
- WINDI design system: Bricolage Grotesque + Outfit + JetBrains Mono
- Noir/Klar theme toggle built-in (matches Desktop theme)
- Output: manifest-ready evidence metadata for jmpg_packager

---

## DEPENDENCY CHAIN (after deployment)

```
Human drops files → Evidence Uploader (Desktop :8100)
                         │ (client-side SHA-256)
                         ▼
                    Export Engine (:8103)
                         │ (jmpg_packager.py creates .jmpg)
                         ▼
                    Forensic Vault (:8106)
                         │ (stores immutable bundle)
                         ▼
                    Forensic Ledger (:8101)
                         │ (seals hash + receipt)
                         ▼
                    Communiqué Engine (:8105)
                         │ (publishes to feed)
                         ▼
                    Sovereign Reader (/reader/ or :8104)
                         │ (client-side verification)
                         ▼
                    Human verifies truth ✓
```

---

## PRE-DEPLOYMENT CHECKLIST

```
□ 1. SSH into Strato: ssh windi@87.106.29.233
□ 2. Backup: mkdir -p /opt/windi/backups/pre_$(date +%Y%m%d_%H%M%S)
□ 3. Upload all 4 files to /tmp/ on server
□ 4. Deploy PACT (Component 1) → verify in /opt/windi/isp/schema/
□ 5. Deploy Packager (Component 2) → test: python3 jmpg_packager.py pack
□ 6. Deploy Reader (Component 3) → verify: curl https://admin.windia4desk.tech/reader/
□ 7. Deploy Uploader (Component 4) → rebuild Desktop, verify at :8100
□ 8. Run E2E test: create communiqué → package → vault → reader verify
□ 9. Seal PACT hash in Ledger (:8101)
□ 10. Update location-matrix skill with new routes
```

---

## LOCATION MATRIX UPDATES (after deployment)

Add these entries to the location matrix:

```
Reader:8104:A/reader/:windi-reader/:α (static alias)
Packager:—:—:export-engine/jmpg_packager.py:module (no port, library)
PACT:—:—:isp/schema/WINDI_PACT_v1.0.md:document (governance)
```

---

## PORTS: NO NEW PORTS NEEDED

All components integrate with EXISTING services:
- Packager → Export Engine (:8103)
- Reader → static nginx alias OR Viewer (:8104)
- Uploader → Desktop (:8100)
- PACT → ISP schema directory (no service)

Zero port conflicts. Zero new systemd services needed.
