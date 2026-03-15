#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# W-KEYS-001 — PLAYBOOK COMPLETO
# Bloco 2 (nginx /api-docs/) → Smoke Tests → Bloco 3 (Market Schemas)
# ═══════════════════════════════════════════════════════════════════════════════
# Sealed: 15 Mar 2026
# Author: Human Dragon (Jober Mögele Correa) · CGO · WINDI Publishing House
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "  W-KEYS-001 — PLAYBOOK COMPLETO"
echo "  Bloco 2 → Smoke Tests → Bloco 3"
echo "═══════════════════════════════════════════════════════════════"

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP_DIR="/opt/windi/backups"
SPECS_DIR="/opt/windi/specs"
DOCS_DIR="/opt/windi/api-docs"
TIMESTAMP=$(date +%Y%m%d_%H%M)

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCO 2: nginx /api-docs/ route
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  BLOCO 2: nginx /api-docs/ route"
echo "═══════════════════════════════════════════════════════════════"

# 2.1 Create api-docs directory
echo "[2.1] Creating /api-docs/ directory..."
mkdir -p "$DOCS_DIR"

# 2.2 Create Swagger UI index.html
echo "[2.2] Creating Swagger UI..."
cat > "$DOCS_DIR/index.html" << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WINDI API Documentation</title>
<link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
<style>
  body { margin: 0; background: #0F0F0F; }
  .swagger-ui .topbar { background: #1A1A1A; padding: 10px 0; }
  .swagger-ui .topbar .download-url-wrapper { display: none; }
  .swagger-ui .info .title { color: #C9A84C; }
  .swagger-ui .info .description { color: #E8E0CC; }
  .swagger-ui .opblock.opblock-get { border-color: #2D6A2D; background: rgba(45,106,45,0.1); }
  .swagger-ui .opblock.opblock-post { border-color: #C9A84C; background: rgba(201,168,76,0.1); }
  .swagger-ui .scheme-container { background: #1A1A1A; }
  .swagger-ui select { background: #2A2A2A; color: #E8E0CC; }
  .windi-header {
    background: linear-gradient(135deg, #1A1A1A 0%, #0F0F0F 100%);
    padding: 20px;
    text-align: center;
    border-bottom: 2px solid #C9A84C;
  }
  .windi-logo { font-size: 24px; font-weight: 700; color: #C9A84C; letter-spacing: 0.15em; }
  .windi-subtitle { font-size: 12px; color: #888; margin-top: 5px; }
</style>
</head>
<body>
<div class="windi-header">
  <div class="windi-logo">WINDI</div>
  <div class="windi-subtitle">API Documentation · W-KEYS-001</div>
</div>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
  window.onload = function() {
    SwaggerUIBundle({
      url: "/specs/w-keys-001-openapi.yaml",
      dom_id: '#swagger-ui',
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
      layout: "BaseLayout",
      deepLinking: true,
      defaultModelsExpandDepth: 1,
      displayRequestDuration: true
    });
  }
</script>
</body>
</html>
HTMLEOF
echo "      ✅ Swagger UI created"

# 2.3 Create nginx patch script (requires sudo)
echo "[2.3] Creating nginx patch script..."
cat > "/tmp/patch_nginx_api_docs.py" << 'PYEOF'
import re
import sys

conf_path = "/etc/nginx/sites-enabled/windi-domain.com"

with open(conf_path, 'r') as f:
    content = f.read()

# Check if /api-docs/ already exists
if 'location /api-docs/' in content:
    print("      ⚠️  /api-docs/ already exists in nginx config")
    sys.exit(0)

# Find the W-KEYS-001 block end marker and insert before it
marker = "    # ══════════════════════════════════════════════════════════════\n    # END W-KEYS-001 Bloco 2"

api_docs_block = '''    # ── /api-docs/ — API Documentation (Swagger UI) ──────────────
    location /api-docs/ {
        alias /opt/windi/api-docs/;
        index index.html;
        try_files $uri $uri/ =404;
        add_header Cache-Control "public, max-age=3600";
        add_header X-WINDI-Service "api-docs" always;
    }

    # ── /specs/ — OpenAPI Specs (public) ───────────────────────────
    location /specs/ {
        alias /opt/windi/specs/;
        add_header Content-Type "text/yaml; charset=utf-8";
        add_header Access-Control-Allow-Origin "*";
        add_header X-WINDI-Service "specs" always;
    }

'''

if marker in content:
    content = content.replace(marker, api_docs_block + marker)
    with open(conf_path, 'w') as f:
        f.write(content)
    print("      ✅ nginx config patched")
else:
    print("      ❌ W-KEYS-001 marker not found")
    sys.exit(1)
PYEOF

echo "[2.4] Executing nginx patch (requires sudo)..."
echo "      → Run: sudo python3 /tmp/patch_nginx_api_docs.py"
echo ""
echo "      After patching, run:"
echo "      → sudo nginx -t"
echo "      → sudo systemctl reload nginx"

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCO 3: Market Schemas
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  BLOCO 3: Market Schemas"
echo "═══════════════════════════════════════════════════════════════"

# 3.1 Tourism Schema
echo "[3.1] Creating Tourism market schema..."
cat > "$SPECS_DIR/market-schema-tourism.json" << 'JSONEOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://windi-domain.com/specs/market-schema-tourism.json",
  "title": "WINDI Tourism Market Schema",
  "description": "Schema for tourism sector document attestation",
  "type": "object",
  "properties": {
    "sector": {
      "const": "TOURISM",
      "description": "Market sector identifier"
    },
    "document_type": {
      "type": "string",
      "enum": ["promotional_photo", "hotel_certificate", "tour_guide_license", "travel_agency_permit", "hospitality_rating"],
      "description": "Type of tourism document"
    },
    "jurisdiction": {
      "type": "string",
      "description": "Geographic jurisdiction (e.g., Florianópolis, Bavaria)"
    },
    "attestation": {
      "type": "object",
      "properties": {
        "issuer_did": { "type": "string", "pattern": "^did:windi:" },
        "seal_date": { "type": "string", "format": "date-time" },
        "content_hash": { "type": "string", "pattern": "^sha256:" },
        "tier": { "type": "string", "enum": ["SEED", "NODAL", "SOVEREIGN", "ORACLE"] }
      },
      "required": ["issuer_did", "seal_date", "content_hash", "tier"]
    },
    "metadata": {
      "type": "object",
      "properties": {
        "establishment_name": { "type": "string" },
        "location": { "type": "string" },
        "rating_stars": { "type": "integer", "minimum": 1, "maximum": 5 },
        "valid_until": { "type": "string", "format": "date" }
      }
    }
  },
  "required": ["sector", "document_type", "attestation"]
}
JSONEOF
echo "      ✅ Tourism schema created"

# 3.2 Journalism Schema
echo "[3.2] Creating Journalism market schema..."
cat > "$SPECS_DIR/market-schema-journalism.json" << 'JSONEOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://windi-domain.com/specs/market-schema-journalism.json",
  "title": "WINDI Journalism Market Schema",
  "description": "Schema for journalism and editorial content attestation",
  "type": "object",
  "properties": {
    "sector": {
      "const": "JOURNALISM",
      "description": "Market sector identifier"
    },
    "document_type": {
      "type": "string",
      "enum": ["article", "editorial", "investigative_report", "press_release", "interview_transcript", "photo_essay"],
      "description": "Type of journalistic content"
    },
    "publication": {
      "type": "object",
      "properties": {
        "outlet_name": { "type": "string" },
        "outlet_did": { "type": "string", "pattern": "^did:windi:" },
        "editorial_tier": { "type": "string", "enum": ["LOCAL", "REGIONAL", "NATIONAL", "INTERNATIONAL"] }
      },
      "required": ["outlet_name"]
    },
    "attestation": {
      "type": "object",
      "properties": {
        "author_did": { "type": "string", "pattern": "^did:windi:" },
        "editor_approved": { "type": "boolean" },
        "seal_date": { "type": "string", "format": "date-time" },
        "content_hash": { "type": "string", "pattern": "^sha256:" },
        "word_count": { "type": "integer", "minimum": 1 }
      },
      "required": ["seal_date", "content_hash", "editor_approved"]
    },
    "governance": {
      "type": "object",
      "properties": {
        "i9_human_approved": { "type": "boolean", "const": true },
        "grove_consensus": { "type": "string", "enum": ["ALL_AGREE", "TWO_VS_ONE", "ALL_DIFFER"] },
        "stage": { "type": "string", "pattern": "^J[1-6]$" }
      },
      "required": ["i9_human_approved"]
    }
  },
  "required": ["sector", "document_type", "attestation", "governance"]
}
JSONEOF
echo "      ✅ Journalism schema created"

# 3.3 Skill Certification Schema
echo "[3.3] Creating Skill Certification market schema..."
cat > "$SPECS_DIR/market-schema-skill-certification.json" << 'JSONEOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://windi-domain.com/specs/market-schema-skill-certification.json",
  "title": "WINDI Skill Certification Market Schema",
  "description": "Schema for professional skill and competency certification",
  "type": "object",
  "properties": {
    "sector": {
      "const": "SKILL_CERTIFICATION",
      "description": "Market sector identifier"
    },
    "certification_type": {
      "type": "string",
      "enum": ["professional_license", "competency_certificate", "training_completion", "skill_assessment", "language_proficiency", "safety_certification"],
      "description": "Type of skill certification"
    },
    "subject": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "did": { "type": "string", "pattern": "^did:windi:" },
        "wallet_id": { "type": "string", "pattern": "^wal_" }
      },
      "required": ["name"]
    },
    "certification": {
      "type": "object",
      "properties": {
        "skill_name": { "type": "string" },
        "skill_level": { "type": "string", "enum": ["BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT", "MASTER"] },
        "issuing_authority": { "type": "string" },
        "issuer_did": { "type": "string", "pattern": "^did:windi:" },
        "issue_date": { "type": "string", "format": "date" },
        "expiry_date": { "type": "string", "format": "date" },
        "credential_id": { "type": "string" }
      },
      "required": ["skill_name", "skill_level", "issuing_authority", "issue_date"]
    },
    "attestation": {
      "type": "object",
      "properties": {
        "seal_date": { "type": "string", "format": "date-time" },
        "content_hash": { "type": "string", "pattern": "^sha256:" },
        "tier": { "type": "string", "enum": ["SEED", "NODAL", "SOVEREIGN", "ORACLE"] },
        "verification_url": { "type": "string", "format": "uri" }
      },
      "required": ["seal_date", "content_hash", "tier"]
    },
    "compliance": {
      "type": "object",
      "properties": {
        "gdpr_compliant": { "type": "boolean" },
        "eidas_level": { "type": "string", "enum": ["LOW", "SUBSTANTIAL", "HIGH"] },
        "portable": { "type": "boolean", "description": "Can be used across EU jurisdictions" }
      }
    }
  },
  "required": ["sector", "certification_type", "subject", "certification", "attestation"]
}
JSONEOF
echo "      ✅ Skill Certification schema created"

# 3.4 Update master schemas index
echo "[3.4] Creating market schemas index..."
cat > "$SPECS_DIR/market-schemas-index.json" << 'JSONEOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://windi-domain.com/specs/market-schemas-index.json",
  "title": "WINDI Market Schemas Index",
  "description": "Index of all available market-specific schemas for WINDI API Keys",
  "version": "1.0.0",
  "sealed": "2026-03-15",
  "schemas": {
    "tourism": {
      "name": "Tourism",
      "description": "Hotels, travel agencies, tour guides, hospitality",
      "file": "market-schema-tourism.json",
      "url": "https://windi-domain.com/specs/market-schema-tourism.json",
      "recommended_tier": "NODAL"
    },
    "journalism": {
      "name": "Journalism",
      "description": "News outlets, editorial content, press releases",
      "file": "market-schema-journalism.json",
      "url": "https://windi-domain.com/specs/market-schema-journalism.json",
      "recommended_tier": "SOVEREIGN"
    },
    "skill_certification": {
      "name": "Skill Certification",
      "description": "Professional licenses, competency certificates, training",
      "file": "market-schema-skill-certification.json",
      "url": "https://windi-domain.com/specs/market-schema-skill-certification.json",
      "recommended_tier": "NODAL"
    }
  },
  "note": "Additional market schemas will be added as Pioneer partnerships expand."
}
JSONEOF
echo "      ✅ Market schemas index created"

# ═══════════════════════════════════════════════════════════════════════════════
# SMOKE TESTS
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  SMOKE TESTS"
echo "═══════════════════════════════════════════════════════════════"

echo "[TEST] api-keys/health..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8091/api-keys/health 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "      ✅ api-keys/health → $HTTP_CODE"
else
    echo "      ❌ api-keys/health → $HTTP_CODE"
fi

echo "[TEST] api-keys/tiers..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8091/api-keys/tiers 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "      ✅ api-keys/tiers → $HTTP_CODE"
else
    echo "      ❌ api-keys/tiers → $HTTP_CODE"
fi

echo "[TEST] External api-keys/health..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://windi-domain.com/api-keys/health 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "      ✅ External api-keys/health → $HTTP_CODE"
else
    echo "      ❌ External api-keys/health → $HTTP_CODE"
fi

echo "[TEST] Pioneer /florianopolis/..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://windi-domain.com/pioneer/florianopolis/ 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "      ✅ Pioneer florianopolis → $HTTP_CODE"
else
    echo "      ❌ Pioneer florianopolis → $HTTP_CODE"
fi

echo "[TEST] Market schemas exist..."
if [ -f "$SPECS_DIR/market-schema-tourism.json" ] && \
   [ -f "$SPECS_DIR/market-schema-journalism.json" ] && \
   [ -f "$SPECS_DIR/market-schema-skill-certification.json" ]; then
    echo "      ✅ All 3 market schemas exist"
else
    echo "      ❌ Missing market schemas"
fi

echo "[TEST] api-docs directory..."
if [ -f "$DOCS_DIR/index.html" ]; then
    echo "      ✅ api-docs/index.html exists"
else
    echo "      ❌ api-docs/index.html missing"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  W-KEYS-001 — DEPLOY SUMMARY"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  ✅ BLOCO 3: Market Schemas DEPLOYED"
echo "     - market-schema-tourism.json"
echo "     - market-schema-journalism.json"
echo "     - market-schema-skill-certification.json"
echo "     - market-schemas-index.json"
echo ""
echo "  ✅ Swagger UI created at /opt/windi/api-docs/"
echo ""
echo "  ⏳ BLOCO 2: nginx /api-docs/ route PENDING"
echo "     Manual steps required:"
echo ""
echo "     1. sudo python3 /tmp/patch_nginx_api_docs.py"
echo "     2. sudo nginx -t"
echo "     3. sudo systemctl reload nginx"
echo ""
echo "  After nginx reload, verify:"
echo "     curl -I https://windi-domain.com/api-docs/"
echo "     curl https://windi-domain.com/specs/market-schema-tourism.json"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  🐉 W-KEYS-001 PLAYBOOK COMPLETO"
echo "  \"AI processes. Human decides. WINDI guarantees.\""
echo "═══════════════════════════════════════════════════════════════"
