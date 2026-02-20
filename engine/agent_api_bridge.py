#!/usr/bin/env python3
"""
WINDI Agent API Bridge — Flask Blueprint
=========================================
Connects ISP Manager Agent to Governance API (:8080)

Endpoints:
  GET  /api/agents/isp-manager/status    → Agent status
  POST /api/agents/isp-manager/audit     → Run full audit
  GET  /api/agents/isp-manager/alerts    → Latest alerts
  GET  /api/agents/isp-manager/report    → Latest health report
  POST /api/agents/isp-manager/validate  → Validate specific ISP
  GET  /api/agents/isp-manager/receipts  → Forensic receipts list

Principle: AI processes. Human decides. WINDI guarantees.
Invariante I9: ZERO auto_apply. Human confirmation gate for ALL.

Version: 1.0.0 | 08 Feb 2026
"""

import json
import os
import subprocess
import glob
from datetime import datetime
from flask import Blueprint, jsonify, request

# ─── Configuration ───────────────────────────────────────────────
AGENT_PATH = "/opt/windi/agents/isp-manager"
AGENT_SCRIPT = os.path.join(AGENT_PATH, "isp_manager_agent.py")
RECEIPTS_DIR = os.path.join(AGENT_PATH, "receipts")
ALERTS_DIR = os.path.join(AGENT_PATH, "alerts")
REPORTS_DIR = os.path.join(AGENT_PATH, "reports")
DRAFTS_DIR = os.path.join(AGENT_PATH, "drafts")
MANIFEST_PATH = os.path.join(AGENT_PATH, "manifest.json")
CAPSULE_PATH = os.path.join(AGENT_PATH, "capsule.json")
REGISTRY_PATH = "/opt/windi/agents/registry.json"

# ─── Blueprint ───────────────────────────────────────────────────
agent_bp = Blueprint('agent_api', __name__, url_prefix='/api/agents')


def _run_agent(action, extra_args=None, timeout=60):
    """Execute agent command and capture output."""
    cmd = ["python3", AGENT_SCRIPT, action]
    if extra_args:
        cmd.extend(extra_args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=AGENT_PATH
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Agent timed out after {timeout}s",
            "return_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1
        }


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
    files = glob.glob(os.path.join(directory, "*.json"))
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
            results.append({
                "filename": os.path.basename(f),
                "error": "Could not read file"
            })
    return results


def _parse_audit_output(stdout):
    """Parse agent audit stdout into structured data."""
    result = {
        "grade": None,
        "score": None,
        "total_profiles": 0,
        "violations": 0,
        "warnings": 0,
        "profiles": {"HIGH": [], "MEDIUM": [], "LOW": []},
        "alerts": [],
        "receipt_id": None,
        "raw_output": stdout
    }

    lines = stdout.strip().split('\n')
    for line in lines:
        line_stripped = line.strip()

        # Parse grade line: "Grade: C (84)"
        if line_stripped.startswith("Grade:") or "Grade:" in line_stripped:
            parts = line_stripped.split("Grade:")[-1].strip()
            if "(" in parts:
                grade_part = parts.split("(")
                result["grade"] = grade_part[0].strip()
                score_str = grade_part[1].replace(")", "").strip()
                try:
                    result["score"] = int(score_str)
                except ValueError:
                    pass

        # Parse totals: "17 perfis" or "profiles"
        if "perfis" in line_stripped.lower() or "profiles" in line_stripped.lower():
            for word in line_stripped.split():
                if word.isdigit():
                    result["total_profiles"] = int(word)
                    break

        # Parse violations/warnings counts
        if "violation" in line_stripped.lower():
            for word in line_stripped.split():
                if word.isdigit():
                    result["violations"] = int(word)
                    break
        if "warning" in line_stripped.lower():
            for word in line_stripped.split():
                if word.isdigit():
                    result["warnings"] = int(word)
                    break

        # Parse receipt ID
        if "WINDI-AGENT-ISP" in line_stripped:
            for part in line_stripped.split():
                if part.startswith("WINDI-AGENT-ISP"):
                    result["receipt_id"] = part.strip()

        # Parse alert codes (ISP-W003, ISP-V001, etc.)
        if any(code in line_stripped for code in ["ISP-V", "ISP-W", "TR-V", "TR-W", "GM-V", "GM-W"]):
            result["alerts"].append(line_stripped)

        # Parse profile lists by level
        for level in ["HIGH", "MEDIUM", "LOW"]:
            if f"({level})" in line_stripped or f"[{level}]" in line_stripped:
                # Extract profile name before the level marker
                name = line_stripped.split("(")[0].split("[")[0].strip()
                if name and name not in result["profiles"][level]:
                    result["profiles"][level].append(name)

    return result


# ─── Endpoints ───────────────────────────────────────────────────

@agent_bp.route('/isp-manager/status', methods=['GET'])
def agent_status():
    """GET /api/agents/isp-manager/status — Agent identity and status."""
    manifest = _load_json_file(MANIFEST_PATH)
    capsule = _load_json_file(CAPSULE_PATH)

    # Count existing artifacts
    receipt_count = len(glob.glob(os.path.join(RECEIPTS_DIR, "*.json"))) if os.path.isdir(RECEIPTS_DIR) else 0
    alert_count = len(glob.glob(os.path.join(ALERTS_DIR, "*.json"))) if os.path.isdir(ALERTS_DIR) else 0
    report_count = len(glob.glob(os.path.join(REPORTS_DIR, "*.json"))) if os.path.isdir(REPORTS_DIR) else 0

    # Run status command for live check
    live_status = _run_agent("status", timeout=15)

    return jsonify({
        "agent_id": "isp-manager",
        "version": manifest.get("version", "unknown"),
        "status": "operational" if live_status["success"] else "error",
        "manifest": manifest,
        "capsule_summary": {
            "can_do": capsule.get("can_do", []),
            "cannot_do": capsule.get("cannot_do", [])
        },
        "artifact_counts": {
            "receipts": receipt_count,
            "alerts": alert_count,
            "reports": report_count
        },
        "invariante_i9": True,
        "auto_apply": False,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@agent_bp.route('/isp-manager/audit', methods=['POST'])
def agent_audit():
    """POST /api/agents/isp-manager/audit — Run full ISP audit.

    I9 Compliance: Audit is READ-ONLY. Never modifies profiles.
    """
    result = _run_agent("audit", timeout=120)

    if not result["success"]:
        return jsonify({
            "success": False,
            "error": result["stderr"],
            "invariante_i9": "Audit is read-only — no modifications made",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500

    parsed = _parse_audit_output(result["stdout"])

    # Also grab the latest receipt if generated
    latest_receipt = None
    if os.path.isdir(RECEIPTS_DIR):
        receipts = sorted(
            glob.glob(os.path.join(RECEIPTS_DIR, "*.json")),
            key=os.path.getmtime,
            reverse=True
        )
        if receipts:
            latest_receipt = _load_json_file(receipts[0])

    return jsonify({
        "success": True,
        "audit": parsed,
        "receipt": latest_receipt,
        "invariante_i9": "Audit is read-only — no modifications made",
        "auto_apply": False,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@agent_bp.route('/isp-manager/alerts', methods=['GET'])
def agent_alerts():
    """GET /api/agents/isp-manager/alerts — Latest structured alerts."""
    limit = request.args.get('limit', 20, type=int)
    severity = request.args.get('severity', None)  # CRITICAL, HIGH, MEDIUM, LOW

    alerts = _list_json_files(ALERTS_DIR, limit=limit)

    # Filter by severity if requested
    if severity:
        severity = severity.upper()
        filtered = []
        for a in alerts:
            data = a.get("data", {})
            if isinstance(data, dict):
                alert_severity = data.get("severity", "")
                if alert_severity.upper() == severity:
                    filtered.append(a)
                # Also check nested alerts array
                elif "alerts" in data:
                    has_match = any(
                        al.get("severity", "").upper() == severity
                        for al in data.get("alerts", [])
                        if isinstance(al, dict)
                    )
                    if has_match:
                        filtered.append(a)
            else:
                filtered.append(a)
        alerts = filtered

    return jsonify({
        "agent_id": "isp-manager",
        "total": len(alerts),
        "filter_severity": severity,
        "alerts": alerts,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@agent_bp.route('/isp-manager/report', methods=['GET'])
def agent_report():
    """GET /api/agents/isp-manager/report — Latest health report."""
    reports = _list_json_files(REPORTS_DIR, limit=1)

    if not reports:
        # Run a fresh health report
        result = _run_agent("health_report", timeout=60)
        if result["success"]:
            reports = _list_json_files(REPORTS_DIR, limit=1)

    return jsonify({
        "agent_id": "isp-manager",
        "report": reports[0] if reports else None,
        "available_reports": len(glob.glob(os.path.join(REPORTS_DIR, "*.json"))) if os.path.isdir(REPORTS_DIR) else 0,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@agent_bp.route('/isp-manager/validate', methods=['POST'])
def agent_validate():
    """POST /api/agents/isp-manager/validate — Validate specific ISP profile.

    Body: {"isp_id": "bafin"}
    I9 Compliance: Validation is READ-ONLY.
    """
    body = request.get_json(silent=True) or {}
    isp_id = body.get("isp_id", "").strip()

    if not isp_id:
        return jsonify({
            "success": False,
            "error": "Missing required field: isp_id",
            "example": {"isp_id": "bafin"}
        }), 400

    # Sanitize isp_id (prevent injection)
    if not all(c.isalnum() or c in "-_" for c in isp_id):
        return jsonify({
            "success": False,
            "error": "Invalid isp_id format. Use alphanumeric, hyphens, or underscores."
        }), 400

    result = _run_agent("validate", extra_args=["--isp-id", isp_id], timeout=30)

    return jsonify({
        "success": result["success"],
        "isp_id": isp_id,
        "output": result["stdout"],
        "errors": result["stderr"] if result["stderr"] else None,
        "invariante_i9": "Validation is read-only — no modifications made",
        "auto_apply": False,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@agent_bp.route('/isp-manager/receipts', methods=['GET'])
def agent_receipts():
    """GET /api/agents/isp-manager/receipts — Forensic receipts list."""
    limit = request.args.get('limit', 20, type=int)
    receipts = _list_json_files(RECEIPTS_DIR, limit=limit)

    return jsonify({
        "agent_id": "isp-manager",
        "total": len(receipts),
        "receipts": receipts,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


# ─── Health / Meta ───────────────────────────────────────────────

@agent_bp.route('/registry', methods=['GET'])
def agent_registry():
    """GET /api/agents/registry — Master agent registry."""
    registry = _load_json_file(REGISTRY_PATH)
    return jsonify({
        "registry": registry,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@agent_bp.route('/health', methods=['GET'])
def agents_health():
    """GET /api/agents/health — Quick health check for all agents."""
    agents = []

    # ISP Manager
    isp_manifest = _load_json_file(MANIFEST_PATH)
    isp_status = _run_agent("status", timeout=10)
    agents.append({
        "agent_id": "isp-manager",
        "version": isp_manifest.get("version", "unknown"),
        "operational": isp_status["success"],
        "invariante_i9": True,
        "auto_apply": False
    })

    return jsonify({
        "total_agents": len(agents),
        "agents": agents,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


# ─── Integration Instructions ────────────────────────────────────
"""
INTEGRATION INTO GOVERNANCE API (:8080):
=========================================

In /opt/windi/engine/windi_governance_api.py, add:

    from agent_api_bridge import agent_bp
    app.register_blueprint(agent_bp)

Then the following endpoints become available:
    GET  /api/agents/registry
    GET  /api/agents/health
    GET  /api/agents/isp-manager/status
    POST /api/agents/isp-manager/audit
    GET  /api/agents/isp-manager/alerts
    GET  /api/agents/isp-manager/report
    POST /api/agents/isp-manager/validate
    GET  /api/agents/isp-manager/receipts

PROXY IN a4DESK (:8085):
=========================

In a4desk_tiptap_babel.py, add proxy routes:

    import requests
    GOV_API = "http://localhost:8080"

    @app.route('/api/gov/agents/<path:subpath>', methods=['GET', 'POST'])
    def proxy_agents(subpath):
        url = f"{GOV_API}/api/agents/{subpath}"
        if request.method == 'POST':
            resp = requests.post(url, json=request.get_json(silent=True), timeout=120)
        else:
            resp = requests.get(url, params=request.args, timeout=30)
        return (resp.content, resp.status_code, {'Content-Type': 'application/json'})
"""
