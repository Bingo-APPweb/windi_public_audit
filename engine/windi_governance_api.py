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
  GET  /api/agents/health    — Agent health check
  GET  /api/agents/registry  — Agent registry
  GET  /api/agents/isp-manager/status  — ISP Manager status
  POST /api/agents/isp-manager/audit   — Run ISP audit
  GET  /api/agents/isp-manager/alerts  — ISP alerts
  GET  /api/agents/isp-manager/report  — ISP health report
  POST /api/agents/isp-manager/validate — Validate specific ISP
  GET  /api/agents/isp-manager/receipts — Forensic receipts

Runs on port 8080 alongside A4 Desk BABEL on 8085.
AI processes. Human decides. WINDI guarantees.
"""

import json
import os
import sys
import traceback
import subprocess
import glob as glob_module
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

# Engine imports
ENGINE_DIR = "/opt/windi/engine"
ISP_DIR = "/opt/windi/isp"
sys.path.insert(0, ENGINE_DIR)

from isp_governance_loader import ISPLoader
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


# ─── Agent API Bridge Configuration ─────────────────────────────
AGENT_PATH = "/opt/windi/agents/isp-manager"
AGENT_SCRIPT = os.path.join(AGENT_PATH, "isp_manager_agent.py")
AGENT_RECEIPTS_DIR = os.path.join(AGENT_PATH, "receipts")
AGENT_ALERTS_DIR = os.path.join(AGENT_PATH, "alerts")
AGENT_REPORTS_DIR = os.path.join(AGENT_PATH, "reports")
AGENT_MANIFEST_PATH = os.path.join(AGENT_PATH, "manifest.json")
AGENT_CAPSULE_PATH = os.path.join(AGENT_PATH, "capsule.json")
AGENT_REGISTRY_PATH = "/opt/windi/agents/registry.json"


def _run_agent(action, extra_args=None, timeout=60):
    """Execute agent command and capture output."""
    cmd = ["python3", AGENT_SCRIPT, action]
    if extra_args:
        cmd.extend(extra_args)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=AGENT_PATH
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": f"Agent timed out after {timeout}s", "return_code": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "return_code": -1}


def _load_json_file(path):
    """Safely load a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return {"error": str(e)}


def _list_json_files(directory, limit=20):
    """List JSON files in a directory, newest first."""
    if not os.path.isdir(directory):
        return []
    files = glob_module.glob(os.path.join(directory, "*.json"))
    files.sort(key=os.path.getmtime, reverse=True)
    results = []
    for f in files[:limit]:
        try:
            stat = os.stat(f)
            data = _load_json_file(f)
            results.append({
                "filename": os.path.basename(f),
                "path": f,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "data": data
            })
        except Exception:
            results.append({"filename": os.path.basename(f), "error": "Could not read file"})
    return results


print("[WINDI-API] Agent API Bridge configured")


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

            elif path == "/health":
                self._json(200, {"status": "ok", "service": "windi-governance", "version": "1.0.0", "protocol": "three-dragons", "i9": "active"})
            elif path == "/api/health":
                self._json(200, {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

            # ─── Agent API Endpoints ─────────────────────────────────
            elif path == "/api/agents/health":
                self._json(200, self._agents_health())

            elif path == "/api/agents/registry":
                self._json(200, self._agents_registry())

            elif path == "/api/agents/isp-manager/status":
                self._json(200, self._agent_isp_status())

            elif path == "/api/agents/isp-manager/alerts":
                limit = int(params.get("limit", [20])[0])
                severity = params.get("severity", [None])[0]
                self._json(200, self._agent_isp_alerts(limit, severity))

            elif path == "/api/agents/isp-manager/report":
                self._json(200, self._agent_isp_report())

            elif path == "/api/agents/isp-manager/receipts":
                limit = int(params.get("limit", [20])[0])
                self._json(200, self._agent_isp_receipts(limit))

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

            # ─── Agent API POST Endpoints ────────────────────────────
            elif path == "/api/agents/isp-manager/audit":
                self._json(200, self._agent_isp_audit())

            elif path == "/api/agents/isp-manager/validate":
                body = self._read_body()
                self._json(200, self._agent_isp_validate(body))

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

    # ─── Agent API Implementation ────────────────────────────────
    def _agents_health(self):
        """GET /api/agents/health — Quick health check for all agents."""
        agents = []
        manifest = _load_json_file(AGENT_MANIFEST_PATH)
        status = _run_agent("status", timeout=10)
        agents.append({
            "agent_id": "isp-manager",
            "version": manifest.get("version", "unknown"),
            "operational": status["success"],
            "invariante_i9": True,
            "auto_apply": False
        })
        return {
            "total_agents": len(agents),
            "agents": agents,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }

    def _agents_registry(self):
        """GET /api/agents/registry — Master agent registry."""
        registry = _load_json_file(AGENT_REGISTRY_PATH)
        return {"registry": registry, "timestamp": datetime.now(timezone.utc).isoformat() + "Z"}

    def _agent_isp_status(self):
        """GET /api/agents/isp-manager/status — Agent identity and status."""
        manifest = _load_json_file(AGENT_MANIFEST_PATH)
        capsule = _load_json_file(AGENT_CAPSULE_PATH)
        receipt_count = len(glob_module.glob(os.path.join(AGENT_RECEIPTS_DIR, "*.json"))) if os.path.isdir(AGENT_RECEIPTS_DIR) else 0
        alert_count = len(glob_module.glob(os.path.join(AGENT_ALERTS_DIR, "*.json"))) if os.path.isdir(AGENT_ALERTS_DIR) else 0
        report_count = len(glob_module.glob(os.path.join(AGENT_REPORTS_DIR, "*.json"))) if os.path.isdir(AGENT_REPORTS_DIR) else 0
        live_status = _run_agent("status", timeout=15)
        return {
            "agent_id": "isp-manager",
            "version": manifest.get("version", "unknown"),
            "status": "operational" if live_status["success"] else "error",
            "manifest": manifest,
            "capsule_summary": {"can_do": capsule.get("can_do", []), "cannot_do": capsule.get("cannot_do", [])},
            "artifact_counts": {"receipts": receipt_count, "alerts": alert_count, "reports": report_count},
            "invariante_i9": True,
            "auto_apply": False,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }

    def _agent_isp_alerts(self, limit=20, severity=None):
        """GET /api/agents/isp-manager/alerts — Latest structured alerts."""
        alerts = _list_json_files(AGENT_ALERTS_DIR, limit=limit)
        if severity:
            severity = severity.upper()
            filtered = []
            for a in alerts:
                data = a.get("data", {})
                if isinstance(data, dict):
                    if data.get("severity", "").upper() == severity:
                        filtered.append(a)
                    elif any(al.get("severity", "").upper() == severity for al in data.get("alerts", []) if isinstance(al, dict)):
                        filtered.append(a)
                else:
                    filtered.append(a)
            alerts = filtered
        return {"agent_id": "isp-manager", "total": len(alerts), "filter_severity": severity, "alerts": alerts, "timestamp": datetime.now(timezone.utc).isoformat() + "Z"}

    def _agent_isp_report(self):
        """GET /api/agents/isp-manager/report — Latest health report."""
        reports = _list_json_files(AGENT_REPORTS_DIR, limit=1)
        if not reports:
            result = _run_agent("health_report", timeout=60)
            if result["success"]:
                reports = _list_json_files(AGENT_REPORTS_DIR, limit=1)
        return {
            "agent_id": "isp-manager",
            "report": reports[0] if reports else None,
            "available_reports": len(glob_module.glob(os.path.join(AGENT_REPORTS_DIR, "*.json"))) if os.path.isdir(AGENT_REPORTS_DIR) else 0,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }

    def _agent_isp_receipts(self, limit=20):
        """GET /api/agents/isp-manager/receipts — Forensic receipts list."""
        receipts = _list_json_files(AGENT_RECEIPTS_DIR, limit=limit)
        return {"agent_id": "isp-manager", "total": len(receipts), "receipts": receipts, "timestamp": datetime.now(timezone.utc).isoformat() + "Z"}

    def _agent_isp_audit(self):
        """POST /api/agents/isp-manager/audit — Run full ISP audit (READ-ONLY)."""
        result = _run_agent("audit", timeout=120)
        if not result["success"]:
            return {
                "success": False,
                "error": result["stderr"],
                "invariante_i9": "Audit is read-only — no modifications made",
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
            }
        latest_receipt = None
        if os.path.isdir(AGENT_RECEIPTS_DIR):
            receipts = sorted(glob_module.glob(os.path.join(AGENT_RECEIPTS_DIR, "*.json")), key=os.path.getmtime, reverse=True)
            if receipts:
                latest_receipt = _load_json_file(receipts[0])
        return {
            "success": True,
            "raw_output": result["stdout"],
            "receipt": latest_receipt,
            "invariante_i9": "Audit is read-only — no modifications made",
            "auto_apply": False,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }

    def _agent_isp_validate(self, body):
        """POST /api/agents/isp-manager/validate — Validate specific ISP profile."""
        isp_id = body.get("isp_id", "").strip()
        if not isp_id:
            return {"success": False, "error": "Missing required field: isp_id", "example": {"isp_id": "bafin"}}
        if not all(c.isalnum() or c in "-_" for c in isp_id):
            return {"success": False, "error": "Invalid isp_id format. Use alphanumeric, hyphens, or underscores."}
        result = _run_agent("validate", extra_args=["--isp-id", isp_id], timeout=30)
        return {
            "success": result["success"],
            "isp_id": isp_id,
            "output": result["stdout"],
            "errors": result["stderr"] if result["stderr"] else None,
            "invariante_i9": "Validation is read-only — no modifications made",
            "auto_apply": False,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
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
