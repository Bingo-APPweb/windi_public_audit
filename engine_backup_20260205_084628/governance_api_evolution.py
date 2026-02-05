"""
WINDI Governance API Evolution Routes v1.0
New endpoints for platform maturity features.

Add these routes to windi_governance_api.py or run standalone on port 8081.

New Endpoints:
  GET  /api/governance/status          - Health check (quick)
  GET  /api/governance/health          - Full health check
  POST /api/governance/detect          - Identity detection in text
  POST /api/governance/recommend       - Governance recommendation (Advisor Mode)
  POST /api/governance/medium/register - Register MEDIUM document
  GET  /api/governance/medium/list     - List MEDIUM registry entries
  GET  /api/governance/medium/verify   - Verify MEDIUM content hash
  POST /api/governance/medium/proof    - Generate Governance Statement
  GET  /api/governance/events          - Query event log
  GET  /api/governance/events/stats    - Event log statistics
  GET  /api/governance/identity/list   - List known institutions
  GET  /api/governance/identity/lookup - Lookup specific institution
  POST /api/governance/identity/add    - Add new institution
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(__file__))

from identity_detector import IdentityDetector
from governance_event_log import GovernanceEventLog
from medium_registry import MediumRegistry
from governance_health import GovernanceHealthCheck


BASE_DIR = os.environ.get("WINDI_BASE", "/opt/windi")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
ENGINE_DIR = os.path.join(BASE_DIR, "engine")
FORENSIC_DIR = os.path.join(BASE_DIR, "forensic")

detector = IdentityDetector(
    directory_path=os.path.join(CONFIG_DIR, "identity_directory.json")
)
event_log = GovernanceEventLog(
    db_path=os.path.join(FORENSIC_DIR, "governance_events.db")
)
medium_registry = MediumRegistry(
    db_path=os.path.join(FORENSIC_DIR, "medium_registry.db")
)
health_check = GovernanceHealthCheck(
    governance_config_path=os.path.join(ENGINE_DIR, "governance_levels.json"),
    isp_directory=ENGINE_DIR,
    identity_dir_path=os.path.join(CONFIG_DIR, "identity_directory.json"),
    event_log=event_log,
    medium_registry=medium_registry,
    identity_detector=detector
)


class EvolutionAPIHandler(BaseHTTPRequestHandler):
    """HTTP handler for WINDI Evolution API endpoints."""

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            body = self.rfile.read(length)
            return json.loads(body.decode("utf-8"))
        return {}

    def do_OPTIONS(self):
        self._send_json({})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        routes = {
            "/api/governance/status": self._handle_quick_status,
            "/api/governance/health": self._handle_full_health,
            "/api/governance/events": self._handle_events_query,
            "/api/governance/events/stats": self._handle_events_stats,
            "/api/governance/medium/list": self._handle_medium_list,
            "/api/governance/identity/list": self._handle_identity_list,
            "/api/governance/identity/lookup": self._handle_identity_lookup,
        }

        handler = routes.get(path)
        if handler:
            handler(params)
        else:
            self._send_json({"error": "Not found", "path": path}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        routes = {
            "/api/governance/detect": self._handle_detect,
            "/api/governance/recommend": self._handle_recommend,
            "/api/governance/medium/register": self._handle_medium_register,
            "/api/governance/medium/verify": self._handle_medium_verify,
            "/api/governance/medium/proof": self._handle_medium_proof,
            "/api/governance/identity/add": self._handle_identity_add,
        }

        handler = routes.get(path)
        if handler:
            body = self._read_body()
            handler(body)
        else:
            self._send_json({"error": "Not found", "path": path}, 404)

    # === Health Check ===

    def _handle_quick_status(self, params):
        result = health_check.quick_status()
        self._send_json(result)

    def _handle_full_health(self, params):
        result = health_check.full_check()
        self._send_json(result)

    # === Identity Detection ===

    def _handle_detect(self, body):
        text = body.get("text", "")
        if not text:
            self._send_json({"error": "Missing 'text' field"}, 400)
            return

        detections = detector.scan_text(text)

        for det in detections:
            event_log.log_event(
                event_type="identity_detected",
                action_taken="detected",
                institution_id=det.get("institution_id"),
                institution_name=det.get("institution_name"),
                governance_level=det.get("recommended_level"),
                reason=f"Confidence: {det.get('confidence', 0)*100:.0f}%",
                policy_version=detector.directory.get("meta", {}).get("policy_version")
            )

        self._send_json({
            "detections": detections,
            "count": len(detections)
        })

    def _handle_recommend(self, body):
        text = body.get("text", "")
        current_level = body.get("current_level", "LOW")

        if not text:
            self._send_json({"error": "Missing 'text' field"}, 400)
            return

        recommendation = detector.get_governance_recommendation(text, current_level)

        if recommendation.get("action") == "upgrade":
            event_log.log_event(
                event_type="advisor_triggered",
                action_taken="upgrade_recommended",
                governance_level=recommendation.get("recommended_level"),
                reason=recommendation.get("reason"),
                policy_version=detector.directory.get("meta", {}).get("policy_version")
            )

        self._send_json(recommendation)

    # === Medium Registry ===

    def _handle_medium_register(self, body):
        content = body.get("content", "")
        if not content:
            self._send_json({"error": "Missing 'content' field"}, 400)
            return

        result = medium_registry.register(
            content=content,
            isp_name=body.get("isp_name"),
            isp_version=body.get("isp_version"),
            institution_id=body.get("institution_id"),
            institution_name=body.get("institution_name"),
            institution_type=body.get("institution_type"),
            institution_country=body.get("institution_country"),
            identity_license_status=body.get("identity_license_status"),
            disclaimer_included=body.get("disclaimer_included", True),
            logo_used=body.get("logo_used", False),
            document_type=body.get("document_type"),
            policy_version=body.get("policy_version"),
            metadata=body.get("metadata"),
            notes=body.get("notes")
        )

        if result.get("success"):
            event_log.log_event(
                event_type="registry_entry_created",
                action_taken="medium_registered",
                document_id=result.get("entry_id"),
                governance_level="MEDIUM",
                isp_name=body.get("isp_name"),
                institution_id=body.get("institution_id"),
                institution_name=body.get("institution_name"),
                identity_license_status=body.get("identity_license_status"),
                policy_version=body.get("policy_version")
            )

        self._send_json(result)

    def _handle_medium_list(self, params):
        result = medium_registry.list_entries(
            isp_name=params.get("isp", [None])[0],
            institution_id=params.get("institution_id", [None])[0],
            since=params.get("since", [None])[0],
            limit=int(params.get("limit", [50])[0])
        )
        self._send_json({"entries": result, "count": len(result)})

    def _handle_medium_verify(self, body):
        entry_id = body.get("entry_id", "")
        content = body.get("content", "")
        if not entry_id or not content:
            self._send_json({"error": "Missing 'entry_id' or 'content'"}, 400)
            return

        result = medium_registry.verify_content(entry_id, content)
        self._send_json(result)

    def _handle_medium_proof(self, body):
        entry_id = body.get("entry_id", "")
        if not entry_id:
            self._send_json({"error": "Missing 'entry_id'"}, 400)
            return

        statement = medium_registry.generate_governance_statement(entry_id)
        if statement:
            self._send_json(statement)
        else:
            self._send_json({"error": "Entry not found"}, 404)

    # === Event Log ===

    def _handle_events_query(self, params):
        events = event_log.query_events(
            event_type=params.get("type", [None])[0],
            document_id=params.get("document_id", [None])[0],
            institution_id=params.get("institution_id", [None])[0],
            governance_level=params.get("level", [None])[0],
            since=params.get("since", [None])[0],
            until=params.get("until", [None])[0],
            limit=int(params.get("limit", [100])[0])
        )
        self._send_json({"events": events, "count": len(events)})

    def _handle_events_stats(self, params):
        stats = event_log.get_event_stats()
        integrity = event_log.verify_chain_integrity()
        stats["chain_integrity"] = integrity
        self._send_json(stats)

    # === Identity Directory ===

    def _handle_identity_list(self, params):
        country = params.get("country", [None])[0]
        inst_type = params.get("type", [None])[0]
        institutions = detector.list_institutions(country=country, inst_type=inst_type)

        summary = []
        for inst in institutions:
            summary.append({
                "id": inst["id"],
                "name": inst["name_official"],
                "country": inst["country"],
                "type": inst["type"],
                "isp_exists": inst.get("isp_exists", False),
                "license_status": inst.get("identity_license", {}).get("status", "unknown"),
                "default_level": inst.get("default_governance_level", "LOW")
            })

        self._send_json({"institutions": summary, "count": len(summary)})

    def _handle_identity_lookup(self, params):
        inst_id = params.get("id", [None])[0]
        if not inst_id:
            self._send_json({"error": "Missing 'id' parameter"}, 400)
            return

        inst = detector.lookup_institution(inst_id)
        if inst:
            self._send_json(inst)
        else:
            self._send_json({"error": "Institution not found"}, 404)

    def _handle_identity_add(self, body):
        result = detector.add_institution(body)
        if result.get("success"):
            event_log.log_event(
                event_type="isp_created",
                action_taken="institution_added",
                institution_id=body.get("id"),
                institution_name=body.get("name_official"),
                reason="Added via API"
            )
        self._send_json(result)

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[WINDI-EVO] {self.address_string()} - {format % args}")


def run_server(port=8081):
    """Run the evolution API server."""
    server = HTTPServer(("0.0.0.0", port), EvolutionAPIHandler)
    print(f"[WINDI] Evolution API v1.0 running on port {port}")
    print(f"[WINDI] Policy version: {detector.directory.get('meta', {}).get('policy_version', 'unknown')}")
    print(f"[WINDI] Institutions loaded: {len(detector.institutions)}")
    print(f"[WINDI] Endpoints:")
    print(f"  GET  /api/governance/status")
    print(f"  GET  /api/governance/health")
    print(f"  POST /api/governance/detect")
    print(f"  POST /api/governance/recommend")
    print(f"  POST /api/governance/medium/register")
    print(f"  GET  /api/governance/medium/list")
    print(f"  POST /api/governance/medium/verify")
    print(f"  POST /api/governance/medium/proof")
    print(f"  GET  /api/governance/events")
    print(f"  GET  /api/governance/events/stats")
    print(f"  GET  /api/governance/identity/list")
    print(f"  GET  /api/governance/identity/lookup")
    print(f"  POST /api/governance/identity/add")
    server.serve_forever()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WINDI Evolution API")
    parser.add_argument("--port", type=int, default=8081, help="Port number")
    args = parser.parse_args()
    run_server(port=args.port)
