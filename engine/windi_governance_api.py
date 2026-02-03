"""
WINDI Governance API v1.0
HTTP endpoints connecting the React dashboard to the real engine.

Endpoints:
  POST /api/generate         — Generate governed document
  GET  /api/submissions      — List submissions (with filters)
  GET  /api/submissions/<id> — Lookup specific submission
  GET  /api/dashboard        — Audit dashboard overview
  GET  /api/integrity        — Chain integrity check
  GET  /api/status           — System status
  GET  /api/compliance       — Compliance matrix data

Runs on port 8080 alongside A4 Desk BABEL on 8085.
AI processes. Human decides. WINDI guarantees.
"""

import json
import os
import sys
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

# Engine imports
ENGINE_DIR = "/opt/windi/engine"
ISP_DIR = "/opt/windi/isp"
sys.path.insert(0, ENGINE_DIR)

from isp_loader import ISPLoader
from submission_registry import SubmissionRegistry
from audit_dashboard import AuditDashboard
from governance_validator import GovernanceValidator
from governance_validator import validate_metadata_by_block, validate_institutional_metadata

# --- Initialize engine ---
CONFIG_PATH = os.path.join(ENGINE_DIR, "governance_levels.json")
SUBMISSIONS_DIR = os.path.join(ENGINE_DIR, "submissions")

loader = ISPLoader(CONFIG_PATH, ISP_DIR, SUBMISSIONS_DIR)
loader.load_all()

dashboard = AuditDashboard(SUBMISSIONS_DIR)
validator = GovernanceValidator(CONFIG_PATH)

print(f"[WINDI-API] Engine loaded. Profiles: {loader.discover()}")
print(f"[WINDI-API] Config hash: {validator.config_hash()[:16]}...")


# --- ISP Profile Auto-Detection ---
# Maps governance levels to default ISP profiles
LEVEL_TO_PROFILE = {
    "HIGH": "bis-style",
    "MEDIUM": "bundesregierung",
    "LOW": "deutsche-bahn",
}


def detect_profile(level, profile_name=None):
    """Auto-detect ISP profile from governance level if not specified."""
    if profile_name and profile_name in loader.profiles:
        return profile_name
    if profile_name and profile_name not in loader.profiles:
        try:
            loader.load(profile_name)
            return profile_name
        except Exception:
            pass
    return LEVEL_TO_PROFILE.get(level, "deutsche-bahn")


class GovernanceAPIHandler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, data):
        body = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code, msg):
        self._json(code, {"error": msg})

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        try:
            if path == "/api/status":
                self._json(200, self._status())

            elif path == "/api/dashboard":
                self._json(200, dashboard.overview())

            elif path == "/api/integrity":
                self._json(200, dashboard.integrity_check())

            elif path == "/api/submissions":
                self._json(200, self._list_submissions(params))

            elif path.startswith("/api/submissions/"):
                sid = path.split("/api/submissions/")[1]
                self._json(200, dashboard.lookup(sid))

            elif path == "/api/compliance":
                self._json(200, self._compliance_data())

            elif path == "/api/entity" and "name" in params:
                self._json(200, dashboard.entity_report(params["name"][0]))

            elif path == "/api/health":
                self._json(200, {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

            else:
                self._error(404, f"Unknown endpoint: {path}")

        except Exception as e:
            traceback.print_exc()
            self._error(500, str(e))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            if path == "/api/generate":
                body = self._read_body()
                self._json(200, self._generate(body))

            elif path == "/api/export":
                export_path = os.path.join(SUBMISSIONS_DIR, f"export-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json")
                data = dashboard.export(export_path)
                self._json(200, {"exported_to": export_path, "total": data.get("total", 0)})

            else:
                self._error(404, f"Unknown endpoint: {path}")

        except ValueError as e:
            # Governance validation errors (BLOCKED)
            self._json(422, {
                "status": "BLOCKED",
                "error": str(e),
                "governance_level": self._read_body().get("governance_level", "UNKNOWN") if False else "UNKNOWN",
            })
        except Exception as e:
            traceback.print_exc()
            self._error(500, str(e))

    # --- Endpoint implementations ---

    def _generate(self, body):
        """POST /api/generate — Core document generation."""
        level = body.get("governance_level", "LOW").upper()
        metadata = body.get("metadata", None)
        profile_name = body.get("isp_profile", None)
        document_type = body.get("document_type", None)
        document_id = body.get("document_id", None)
        policy_version = body.get("policy_version", None)

        # Auto-detect profile
        profile = detect_profile(level, profile_name)

        # Generate through the real engine pipeline
        try:
            package = loader.generate_document(
                profile_name=profile,
                metadata=metadata,
                document_type=document_type,
                governance_level=level,
                document_id=document_id,
                policy_version=policy_version,
            )
        except ValueError as e:
            # Validation blocked — return structured error
            return {
                "status": "BLOCKED",
                "governance_level": level,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Enrich with Identity Governance (MEDIUM+)
        if level in ("MEDIUM", "HIGH"):
            try:
                from governance_validator import validate_identity_license
                profile_data = loader.profiles.get(profile).data if loader.profiles.get(profile) else {}
                config = loader.validator.config
                identity_gov = validate_identity_license(profile_data, config)
                package["identity_governance"] = {
                    "institution": profile_data.get("organization_name", profile_data.get("isp_profile", profile or "Unknown")),
                    "license_status": identity_gov.get("license_status", "model_only"),
                    "logo_allowed": identity_gov.get("logo_allowed", False),
                    "disclaimer_required": identity_gov.get("disclaimer_required", True),
                    "disclaimer_text": identity_gov.get("disclaimer_text", {}).get("en", "") if identity_gov.get("disclaimer_required") else None,
                    "audit_category": identity_gov.get("audit_category", "model_simulation"),
                    "authorization_ref": identity_gov.get("authorization_ref"),
                    "restrictions": identity_gov.get("restrictions", [])
                }
            except Exception as e:
                package["identity_governance"] = {"error": str(e)}
        # Flatten for the UI
        audit = package.get("audit_record", {})
        result = {
            "status": package["status"],
            "governance_level": package["governance_level"],
            "governance_name": package["governance_name"],
            "isp_profile": package["isp_profile"],
            "organization": package["organization"],
            "policy_version": package["policy_version"],
            "timestamp": audit.get("timestamp", ""),
            "config_hash": audit.get("config_hash", ""),
            "submission_id": package.get("submission_id"),
            "submission_header": package.get("submission_header"),
            "integrity_hash": audit.get("integrity_hash"),
            "sealed_at": audit.get("sealed_at"),
            "metadata": audit.get("metadata"),
            "identity_governance": package.get("identity_governance"),
        }
        return result

    def _list_submissions(self, params):
        """GET /api/submissions — Query submissions with filters."""
        level = params.get("level", [None])[0]
        entity = params.get("entity", [None])[0]
        after = params.get("after", [None])[0]
        before = params.get("before", [None])[0]
        limit = int(params.get("limit", [50])[0])

        registry = SubmissionRegistry(SUBMISSIONS_DIR)
        results = registry.query(level=level, entity=entity, after=after, before=before, limit=limit)
        stats = registry.get_stats()

        return {
            "count": len(results),
            "total": stats.get("total", 0),
            "stats": stats,
            "results": results,
        }

    def _status(self):
        """GET /api/status — System status."""
        return {
            "api": "WINDI Governance API v1.0",
            "engine": loader.status(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "principle": "AI processes. Human decides. WINDI guarantees.",
        }

    def _compliance_data(self):
        """GET /api/compliance — Governance feature matrix."""
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        return {
            "version": config.get("_version", ""),
            "principle": config.get("_principle", ""),
            "levels": config.get("levels", {}),
            "metadata_schemas": config.get("metadata_schemas", {}),
            "invariants_enforced": 8,
            "invariants_total": 8,
        }

    def log_message(self, format, *args):
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[WINDI-API {ts}] {args[0]}")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(("0.0.0.0", port), GovernanceAPIHandler)
    print()
    print("=" * 60)
    print(f"  WINDI Governance API v1.0")
    print(f"  Port: {port}")
    print(f"  Engine: {ENGINE_DIR}")
    print(f"  ISP: {ISP_DIR}")
    print(f"  Profiles: {loader.discover()}")
    print(f"  Config hash: {validator.config_hash()[:16]}...")
    print()
    print(f"  Endpoints:")
    print(f"    POST /api/generate")
    print(f"    GET  /api/submissions")
    print(f"    GET  /api/submissions/<id>")
    print(f"    GET  /api/dashboard")
    print(f"    GET  /api/integrity")
    print(f"    GET  /api/compliance")
    print(f"    GET  /api/status")
    print(f"    GET  /api/health")
    print()
    print(f"  AI processes. Human decides. WINDI guarantees.")
    print("=" * 60)
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[WINDI-API] Shutdown.")
        server.server_close()


if __name__ == "__main__":
    main()


# === MEDIUM Generate Handler (added by MEDIUM deploy) ===
def handle_medium_generate(metadata, config, profile_data, policy_version):
    """Handle MEDIUM-level document generation.
    
    MEDIUM produces:
    - Validated institutional metadata
    - Policy version reference
    - Standard audit trail entry
    - Discreet watermark flag
    
    MEDIUM does NOT produce:
    - submission_id
    - integrity_hash  
    - config_hash seal
    - forensic registry entry
    """
    from governance_validator import validate_metadata_by_block
    
    # Validate institutional metadata
    validate_metadata_by_block("MEDIUM", metadata, config)
    
    # Identity Governance Layer
    from governance_validator import validate_identity_license
    identity_gov = validate_identity_license(profile_data, config)
    
    result = {
        "status": "APPROVED",
        "governance_level": "MEDIUM",
        "governance_name": "Institutional Standard",
        "isp_profile": profile_data.get("isp_profile", "bundesregierung"),
        "organization": profile_data.get("organization_name", "Unknown"),
        "policy_version": policy_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_hash": "",
        "submission_id": None,
        "submission_header": None,
        "integrity_hash": None,
        "identity_governance": {
            "institution": profile_data.get("organization_name", profile_data.get("isp_profile", "Unknown")),
            "license_status": identity_gov.get("license_status", "model_only"),
            "logo_allowed": identity_gov.get("logo_allowed", False),
            "disclaimer_required": identity_gov.get("disclaimer_required", True),
            "disclaimer_text": identity_gov.get("disclaimer_text", {}).get("en", "") if identity_gov.get("disclaimer_required") else None,
            "audit_category": identity_gov.get("audit_category", "model_simulation"),
            "authorization_ref": identity_gov.get("authorization_ref"),
            "restrictions": identity_gov.get("restrictions", [])
        },
        "sealed_at": None,
        "audit_trail": "standard",
        "watermark": "institutional-discreet",
        "metadata": metadata
    }
    
    return result

# === END MEDIUM Generate Handler ===
