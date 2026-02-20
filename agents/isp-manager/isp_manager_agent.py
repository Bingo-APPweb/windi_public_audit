#!/usr/bin/env python3
"""
WINDI ISP Manager Agent v1.0.0
================================
Manages the lifecycle of ISP Profiles and Template Registry.

Principle: AI processes. Human decides. WINDI guarantees.
Execution Mode: human-mediated (NEVER autonomous)
Invariant I9: No auto_apply. Human confirmation gate required.

Three Dragons Council — 07-08 Feb 2026
"""

import json
import os
import sys
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

AGENT_ID = "windi://agent/core/isp-manager"
AGENT_VERSION = "1.0.0"

# Strato paths (production)
ISP_LIBRARY_PATH = "/opt/windi/isp"
TEMPLATE_REGISTRY_DB = "/opt/windi/data/template_registry.db"
GOVERNANCE_LEVELS_PATH = "/opt/windi/engine/governance_levels.json"
ISP_SCANNER_PATH = "/opt/windi/isp_scanner_v1.1.py"
REPORTS_PATH = "/opt/windi/reports"

# Agent workspace (write-only zone)
AGENT_BASE = "/opt/windi/agents/isp-manager"
DRAFTS_PATH = os.path.join(AGENT_BASE, "drafts")
ALERTS_PATH = os.path.join(AGENT_BASE, "alerts")
RECEIPTS_PATH = os.path.join(AGENT_BASE, "receipts")
AGENT_REPORTS_PATH = os.path.join(AGENT_BASE, "reports")

# Governance level definitions
GOVERNANCE_LEVELS = {"HIGH", "MEDIUM", "LOW"}

# Minimum template counts by governance level
MIN_TEMPLATES = {"HIGH": 12, "MEDIUM": 10, "LOW": 8}

# Required fields in profile.json
REQUIRED_FIELDS = ["profile_id", "profile_name", "version", "governance_level",
                   "institution", "templates", "sge_keywords"]
RECOMMENDED_FIELDS = ["cross_references", "identity_license", "compliance_frameworks"]


# ═══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def generate_receipt_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%d%b%y-%H%M%S").upper()
    h = hashlib.sha256(str(datetime.now(timezone.utc).timestamp()).encode()).hexdigest()[:8]
    return f"WINDI-AGENT-ISP-{ts}-{h}"

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def ensure_dirs():
    for d in [DRAFTS_PATH, ALERTS_PATH, RECEIPTS_PATH, AGENT_REPORTS_PATH]:
        os.makedirs(d, exist_ok=True)

def save_json(path: str, data: dict):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(path: str) -> Optional[dict]:
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return None


# ═══════════════════════════════════════════════════════════════
# ISP PROFILE SCANNER
# ═══════════════════════════════════════════════════════════════

class ISPProfileScanner:
    """Scans ISP profiles for structural consistency."""

    def __init__(self, isp_path: str = ISP_LIBRARY_PATH):
        self.isp_path = isp_path

    def scan_all(self) -> Dict[str, Any]:
        results = {
            "scan_type": "isp.audit",
            "timestamp": now_iso(),
            "profiles_found": 0,
            "profiles_healthy": 0,
            "profiles_with_issues": 0,
            "total_violations": 0,
            "total_warnings": 0,
            "details": [],
            "summary_by_level": {"HIGH": [], "MEDIUM": [], "LOW": [], "UNKNOWN": []}
        }

        if not os.path.isdir(self.isp_path):
            results["error"] = f"ISP library not found: {self.isp_path}"
            return results

        for entry in sorted(os.listdir(self.isp_path)):
            profile_dir = os.path.join(self.isp_path, entry)
            if not os.path.isdir(profile_dir):
                continue
            if entry.startswith(".") or entry.startswith("_"):
                continue

            profile_result = self.scan_profile(entry, profile_dir)
            results["details"].append(profile_result)
            results["profiles_found"] += 1

            level = profile_result.get("governance_level", "UNKNOWN")
            results["summary_by_level"].get(level, results["summary_by_level"]["UNKNOWN"]).append(entry)

            if profile_result["violations"]:
                results["profiles_with_issues"] += 1
                results["total_violations"] += len(profile_result["violations"])
            else:
                results["profiles_healthy"] += 1

            results["total_warnings"] += len(profile_result.get("warnings", []))

        results["grade"] = self._calculate_grade(results)
        return results

    def scan_profile(self, isp_id: str, profile_dir: str) -> Dict:
        result = {
            "isp_id": isp_id,
            "path": profile_dir,
            "violations": [],
            "warnings": [],
            "governance_level": "UNKNOWN",
            "template_count": 0,
            "keyword_count": 0,
            "institution_name": ""
        }

        # Check profile.json exists
        profile_path = os.path.join(profile_dir, "profile.json")
        if not os.path.isfile(profile_path):
            result["violations"].append({
                "code": "ISP-V001",
                "severity": "CRITICAL",
                "message": f"Missing profile.json in {isp_id}"
            })
            return result

        # Parse JSON
        raw = load_json(profile_path)
        if raw is None:
            result["violations"].append({
                "code": "ISP-V002",
                "severity": "CRITICAL",
                "message": f"Invalid JSON in {isp_id}/profile.json"
            })
            return result

        # ── Handle nested isp_profile structure ──
        # Real ISPs use: { "isp_profile": { "metadata": {...}, "templates": [...], ... } }
        # Also support flat structure for forward compatibility
        if "isp_profile" in raw:
            isp = raw["isp_profile"]
            metadata = isp.get("metadata", {})
            organization = isp.get("organization", {})
            governance = isp.get("governance", {})
            templates = isp.get("templates", [])
            sge_keywords = isp.get("sge_keywords", {})
            cross_refs = isp.get("cross_references", [])
        else:
            # Flat structure fallback
            isp = raw
            metadata = raw
            organization = raw
            governance = raw
            templates = raw.get("templates", [])
            sge_keywords = raw.get("sge_keywords", {})
            cross_refs = raw.get("cross_references", [])

        # ── Check required sections (nested) ──
        if "isp_profile" in raw:
            required_sections = {
                "metadata": metadata,
                "organization": organization,
                "templates": templates,
                "sge_keywords": sge_keywords
            }
            for section_name, section_data in required_sections.items():
                if not section_data:
                    result["violations"].append({
                        "code": "ISP-V003",
                        "severity": "HIGH",
                        "message": f"Missing or empty section: isp_profile.{section_name}"
                    })

            # Required metadata fields
            for field in ["profile_id", "version", "governance_level"]:
                if field not in metadata:
                    result["violations"].append({
                        "code": "ISP-V003",
                        "severity": "HIGH",
                        "message": f"Missing required field: metadata.{field}"
                    })

            # Required organization fields
            if not organization.get("name_full") and not organization.get("name_short"):
                result["warnings"].append({
                    "code": "ISP-W001",
                    "severity": "MEDIUM",
                    "message": "Missing organization name (name_full or name_short)"
                })
        else:
            # Flat structure: check old-style required fields
            for field in REQUIRED_FIELDS:
                if field not in raw:
                    result["violations"].append({
                        "code": "ISP-V003",
                        "severity": "HIGH",
                        "message": f"Missing required field: {field}"
                    })

        # ── Governance level ──
        level = metadata.get("governance_level", "UNKNOWN")
        if level not in GOVERNANCE_LEVELS and level != "UNKNOWN":
            result["violations"].append({
                "code": "ISP-V004",
                "severity": "HIGH",
                "message": f"Invalid governance level: {level} (expected HIGH/MEDIUM/LOW)"
            })
        result["governance_level"] = level if level in GOVERNANCE_LEVELS else "UNKNOWN"

        # ── Institution name ──
        result["institution_name"] = (
            organization.get("name_short") or
            organization.get("name_full") or
            isp_id
        )

        # ── Template count ──
        if isinstance(templates, list):
            result["template_count"] = len(templates)
        elif isinstance(templates, dict):
            # Some profiles may use dict with template IDs as keys
            result["template_count"] = len(templates)
        else:
            result["template_count"] = 0

        min_required = MIN_TEMPLATES.get(level, 8)
        if result["template_count"] < min_required:
            result["warnings"].append({
                "code": "ISP-W002",
                "severity": "LOW",
                "message": f"Below minimum templates: {result['template_count']}/{min_required} for {level}"
            })

        # ── Keyword count ──
        if isinstance(sge_keywords, dict):
            total_kw = sum(
                len(v) if isinstance(v, list) else 1
                for v in sge_keywords.values()
            )
        elif isinstance(sge_keywords, list):
            total_kw = len(sge_keywords)
        else:
            total_kw = 0
        result["keyword_count"] = total_kw

        # ── Cross references ──
        if not cross_refs:
            result["warnings"].append({
                "code": "ISP-W001",
                "severity": "MEDIUM",
                "message": "Missing or empty cross_references"
            })

        # ── Identity license for HIGH/MEDIUM ──
        identity_license = governance.get("identity_license") if isinstance(governance, dict) else None
        if level in ("HIGH", "MEDIUM") and not identity_license:
            result["warnings"].append({
                "code": "ISP-W003",
                "severity": "MEDIUM",
                "message": f"Missing identity_license in governance section for {level} profile"
            })

        # ── Compliance frameworks ──
        compliance = governance.get("compliance_frameworks") if isinstance(governance, dict) else None
        if not compliance:
            result["warnings"].append({
                "code": "ISP-W005",
                "severity": "LOW",
                "message": "Missing compliance_frameworks in governance section"
            })

        # ── Version check ──
        version = metadata.get("version", "")
        if version and (not isinstance(version, str) or not any(c.isdigit() for c in version)):
            result["warnings"].append({
                "code": "ISP-W004",
                "severity": "LOW",
                "message": f"Version format unclear: {version}"
            })

        # ── Audit hash ──
        if not metadata.get("audit_hash"):
            result["warnings"].append({
                "code": "ISP-W006",
                "severity": "LOW",
                "message": "Missing audit_hash in metadata"
            })

        result["profile_hash"] = hash_content(json.dumps(raw, sort_keys=True))
        result["version"] = metadata.get("version", "?")
        return result

    def _calculate_grade(self, results: Dict) -> str:
        total = results["profiles_found"]
        if total == 0:
            return "N/A"
        violations = results["total_violations"]
        warnings = results["total_warnings"]

        # Critical violations = -15 points each, High = -10, warnings = -2
        critical_count = sum(
            1 for d in results["details"]
            for v in d["violations"]
            if v.get("severity") == "CRITICAL"
        )
        high_count = sum(
            1 for d in results["details"]
            for v in d["violations"]
            if v.get("severity") == "HIGH"
        )

        score = 100 - (critical_count * 15) - (high_count * 10) - (warnings * 2)
        score = max(0, min(100, score))

        if score >= 95:
            return f"A ({score})"
        elif score >= 85:
            return f"B ({score})"
        elif score >= 70:
            return f"C ({score})"
        elif score >= 50:
            return f"D ({score})"
        else:
            return f"F ({score})"


# ═══════════════════════════════════════════════════════════════
# TEMPLATE REGISTRY SCANNER
# ═══════════════════════════════════════════════════════════════

class TemplateRegistryScanner:
    """Scans the Template Registry DB for inconsistencies."""

    def __init__(self, db_path: str = TEMPLATE_REGISTRY_DB):
        self.db_path = db_path

    def scan(self) -> Dict[str, Any]:
        results = {
            "scan_type": "template_registry",
            "timestamp": now_iso(),
            "violations": [],
            "warnings": [],
            "stats": {}
        }

        if not os.path.isfile(self.db_path):
            results["warnings"].append({
                "code": "TR-W000",
                "severity": "INFO",
                "message": f"Template registry DB not found: {self.db_path} (may not be initialized yet)"
            })
            return results

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row["name"] for row in cursor.fetchall()]
            results["stats"]["tables"] = tables

            if "templates" not in tables:
                results["warnings"].append({
                    "code": "TR-W001",
                    "severity": "MEDIUM",
                    "message": "Could not find 'templates' table — schema may differ"
                })
                conn.close()
                return results

            # Count templates
            cursor.execute("SELECT COUNT(*) as cnt FROM templates")
            results["stats"]["total_templates"] = cursor.fetchone()["cnt"]

            # Check for duplicate template keys
            try:
                cursor.execute("""
                    SELECT template_id, COUNT(*) as cnt
                    FROM templates
                    GROUP BY template_id
                    HAVING cnt > 1
                """)
                dupes = cursor.fetchall()
                for d in dupes:
                    results["violations"].append({
                        "code": "TR-V002",
                        "severity": "HIGH",
                        "message": f"Duplicate template_id: {d['template_id']} (count: {d['cnt']})"
                    })
            except sqlite3.OperationalError:
                pass

            # Check for templates without tenant
            try:
                cursor.execute("""
                    SELECT template_id FROM templates
                    WHERE tenant_id IS NULL OR tenant_id = ''
                """)
                orphans = cursor.fetchall()
                for o in orphans:
                    results["warnings"].append({
                        "code": "TR-W002",
                        "severity": "MEDIUM",
                        "message": f"Template without tenant: {o['template_id']}"
                    })
            except sqlite3.OperationalError:
                pass

            conn.close()

        except Exception as e:
            results["violations"].append({
                "code": "TR-V099",
                "severity": "HIGH",
                "message": f"Database error: {str(e)}"
            })

        return results


# ═══════════════════════════════════════════════════════════════
# GOVERNANCE MATRIX SCANNER
# ═══════════════════════════════════════════════════════════════

class GovernanceMatrixScanner:
    """Validates governance level consistency across the ecosystem."""

    def __init__(self, isp_path: str = ISP_LIBRARY_PATH,
                 governance_path: str = GOVERNANCE_LEVELS_PATH):
        self.isp_path = isp_path
        self.governance_path = governance_path

    def scan(self) -> Dict[str, Any]:
        results = {
            "scan_type": "governance_matrix",
            "timestamp": now_iso(),
            "violations": [],
            "warnings": [],
            "matrix": {}
        }

        # Load governance levels config
        gov_config = load_json(self.governance_path)
        if gov_config is None:
            results["warnings"].append({
                "code": "GM-W001",
                "severity": "MEDIUM",
                "message": f"Governance config not found: {self.governance_path}"
            })

        # Scan profiles and build matrix
        if os.path.isdir(self.isp_path):
            for entry in sorted(os.listdir(self.isp_path)):
                profile_dir = os.path.join(self.isp_path, entry)
                if not os.path.isdir(profile_dir):
                    continue
                if entry.startswith(".") or entry.startswith("_"):
                    continue

                profile_path = os.path.join(profile_dir, "profile.json")
                data = load_json(profile_path)
                if data is None:
                    continue

                # Handle nested isp_profile structure
                if "isp_profile" in data:
                    isp = data["isp_profile"]
                    metadata = isp.get("metadata", {})
                    governance = isp.get("governance", {})
                    templates = isp.get("templates", [])
                else:
                    metadata = data
                    governance = data
                    templates = data.get("templates", [])

                level = metadata.get("governance_level", "UNKNOWN")
                results["matrix"][entry] = {
                    "declared_level": level,
                    "template_count": len(templates) if isinstance(templates, (list, dict)) else 0,
                    "has_identity_license": bool(governance.get("identity_license")) if isinstance(governance, dict) else False,
                    "has_cross_references": bool(data.get("isp_profile", data).get("cross_references"))
                }

                # Cross-check with governance config
                if gov_config and entry in gov_config:
                    config_level = gov_config[entry].get("level", "UNKNOWN")
                    if config_level != level:
                        results["violations"].append({
                            "code": "GM-V002",
                            "severity": "HIGH",
                            "message": f"Governance drift: {entry} declares '{level}' but config says '{config_level}'"
                        })

        # Distribution summary
        dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
        for entry, info in results["matrix"].items():
            lvl = info["declared_level"]
            dist[lvl] = dist.get(lvl, 0) + 1
        results["distribution"] = dist

        return results


# ═══════════════════════════════════════════════════════════════
# FORENSIC RECEIPT GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_receipt(action: str, results: Dict, output_path: str = RECEIPTS_PATH) -> Dict:
    """Generate a forensic receipt for any agent execution."""
    receipt_id = generate_receipt_id()
    receipt = {
        "receipt_id": receipt_id,
        "agent_id": AGENT_ID,
        "agent_version": AGENT_VERSION,
        "action": action,
        "timestamp": now_iso(),
        "human_confirmed": False,
        "results_hash": hash_content(json.dumps(results, sort_keys=True, default=str)),
        "summary": {
            "profiles_scanned": results.get("profiles_found", 0),
            "violations": results.get("total_violations", len(results.get("violations", []))),
            "warnings": results.get("total_warnings", len(results.get("warnings", []))),
            "grade": results.get("grade", "N/A")
        },
        "invariant_compliance": {
            "I1_sovereignty": "Agent proposed only — no modifications made",
            "I9_no_escalation": "No auto_apply executed"
        }
    }

    os.makedirs(output_path, exist_ok=True)
    receipt_file = os.path.join(output_path, f"{receipt_id}.json")
    save_json(receipt_file, receipt)
    return receipt


# ═══════════════════════════════════════════════════════════════
# ALERT GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_alerts(results: Dict, output_path: str = ALERTS_PATH) -> List[Dict]:
    """Extract and save alerts from scan results."""
    alerts = []

    # Collect from all result types
    for detail in results.get("details", [results]):
        for v in detail.get("violations", []):
            alerts.append({
                "alert_type": "VIOLATION",
                "severity": v.get("severity", "HIGH"),
                "code": v.get("code", "UNKNOWN"),
                "message": v.get("message", ""),
                "source": detail.get("isp_id", detail.get("scan_type", "unknown")),
                "timestamp": now_iso()
            })
        for w in detail.get("warnings", []):
            alerts.append({
                "alert_type": "WARNING",
                "severity": w.get("severity", "LOW"),
                "code": w.get("code", "UNKNOWN"),
                "message": w.get("message", ""),
                "source": detail.get("isp_id", detail.get("scan_type", "unknown")),
                "timestamp": now_iso()
            })

    if alerts:
        os.makedirs(output_path, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        alert_file = os.path.join(output_path, f"alerts_{ts}.json")
        save_json(alert_file, {"alerts": alerts, "count": len(alerts), "timestamp": now_iso()})

    return alerts


# ═══════════════════════════════════════════════════════════════
# DRAFT PATCH GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_draft_patches(audit_results: Dict, output_path: str = DRAFTS_PATH) -> List[Dict]:
    """Generate correction proposals (NEVER applied directly)."""
    patches = []

    for detail in audit_results.get("details", []):
        isp_id = detail.get("isp_id", "unknown")
        for v in detail.get("violations", []):
            patch = {
                "target": isp_id,
                "violation_code": v.get("code"),
                "severity": v.get("severity"),
                "description": v.get("message"),
                "proposed_action": _suggest_fix(v.get("code", "")),
                "status": "DRAFT — awaiting human review",
                "auto_apply": False,  # I9: NEVER
                "timestamp": now_iso()
            }
            patches.append(patch)

    if patches:
        os.makedirs(output_path, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        draft_file = os.path.join(output_path, f"draft_patches_{ts}.json")
        save_json(draft_file, {
            "patches": patches,
            "count": len(patches),
            "timestamp": now_iso(),
            "notice": "These are PROPOSALS only. Human review required. I9 applies."
        })

    return patches

def _suggest_fix(code: str) -> str:
    """Suggest a fix based on violation code."""
    fixes = {
        "ISP-V001": "Create profile.json with required fields from ISP schema",
        "ISP-V002": "Fix JSON syntax errors in profile.json",
        "ISP-V003": "Add missing required field to profile.json",
        "ISP-V004": "Set governance_level to HIGH, MEDIUM, or LOW",
        "TR-V002": "Remove duplicate template_id entries from registry",
        "GM-V002": "Align governance level between profile.json and governance_levels.json",
    }
    return fixes.get(code, "Review and correct manually")


# ═══════════════════════════════════════════════════════════════
# HEALTH REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_health_report(output_path: str = AGENT_REPORTS_PATH) -> Dict:
    """Generate comprehensive ecosystem health report."""
    ensure_dirs()
    report = {
        "report_type": "isp_ecosystem_health",
        "agent_id": AGENT_ID,
        "agent_version": AGENT_VERSION,
        "timestamp": now_iso(),
        "sections": {}
    }

    # Section 1: ISP Profiles
    profile_scanner = ISPProfileScanner()
    profile_results = profile_scanner.scan_all()
    report["sections"]["isp_profiles"] = profile_results

    # Section 2: Template Registry
    tr_scanner = TemplateRegistryScanner()
    tr_results = tr_scanner.scan()
    report["sections"]["template_registry"] = tr_results

    # Section 3: Governance Matrix
    gm_scanner = GovernanceMatrixScanner()
    gm_results = gm_scanner.scan()
    report["sections"]["governance_matrix"] = gm_results

    # Overall health
    total_violations = (
        profile_results.get("total_violations", 0) +
        len(tr_results.get("violations", [])) +
        len(gm_results.get("violations", []))
    )
    total_warnings = (
        profile_results.get("total_warnings", 0) +
        len(tr_results.get("warnings", [])) +
        len(gm_results.get("warnings", []))
    )

    report["overall"] = {
        "total_violations": total_violations,
        "total_warnings": total_warnings,
        "grade": profile_results.get("grade", "N/A"),
        "profiles_found": profile_results.get("profiles_found", 0),
        "healthy": total_violations == 0
    }

    # Save
    os.makedirs(output_path, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_path, f"health_report_{ts}.json")
    save_json(report_file, report)

    # Generate receipt
    generate_receipt("health_report", report)

    report["_saved_to"] = report_file
    return report


# ═══════════════════════════════════════════════════════════════
# CLI: ACTIONS
# ═══════════════════════════════════════════════════════════════

def action_status(as_json: bool = False) -> Dict:
    """Show agent status."""
    status = {
        "agent_id": AGENT_ID,
        "version": AGENT_VERSION,
        "status": "ACTIVE",
        "execution_mode": "human-mediated",
        "invariants": ["I1-I9"],
        "timestamp": now_iso(),
        "paths": {
            "isp_library": ISP_LIBRARY_PATH,
            "isp_library_exists": os.path.isdir(ISP_LIBRARY_PATH),
            "template_registry_db": TEMPLATE_REGISTRY_DB,
            "template_db_exists": os.path.isfile(TEMPLATE_REGISTRY_DB),
            "governance_levels": GOVERNANCE_LEVELS_PATH,
            "governance_exists": os.path.isfile(GOVERNANCE_LEVELS_PATH),
            "agent_base": AGENT_BASE
        }
    }
    if as_json:
        print(json.dumps(status, indent=2))
    else:
        print()
        print("╔═══════════════════════════════════════════════════════╗")
        print("║   🏛️  WINDI ISP Manager Agent — Status                ║")
        print("╚═══════════════════════════════════════════════════════╝")
        print()
        print(f"  Agent:     {AGENT_ID}")
        print(f"  Version:   {AGENT_VERSION}")
        print(f"  Status:    ACTIVE")
        print(f"  Mode:      human-mediated (I9)")
        print(f"  Time:      {status['timestamp']}")
        print()
        print("  📂 Paths:")
        for k, v in status["paths"].items():
            icon = "✅" if v is True else ("❌" if v is False else "📁")
            print(f"    {icon} {k}: {v}")
        print()
    return status


def action_audit(as_json: bool = False) -> Dict:
    """Run full ISP audit."""
    ensure_dirs()
    print() if not as_json else None
    print("🔍 Running ISP Audit...") if not as_json else None

    scanner = ISPProfileScanner()
    results = scanner.scan_all()

    # Generate alerts and receipt
    alerts = generate_alerts(results)
    receipt = generate_receipt("audit", results)

    if as_json:
        print(json.dumps(results, indent=2))
    else:
        print()
        print("╔═══════════════════════════════════════════════════════╗")
        print("║   🏛️  WINDI ISP Audit Results                         ║")
        print("╚═══════════════════════════════════════════════════════╝")
        print()
        print(f"  📊 Grade:      {results.get('grade', 'N/A')}")
        print(f"  📁 Profiles:   {results['profiles_found']}")
        print(f"  ✅ Healthy:    {results['profiles_healthy']}")
        print(f"  ⚠️  Issues:    {results['profiles_with_issues']}")
        print(f"  ❌ Violations: {results['total_violations']}")
        print(f"  ⚠️  Warnings:  {results['total_warnings']}")
        print()
        print("  📋 By Governance Level:")
        for level, profiles in results["summary_by_level"].items():
            if profiles:
                print(f"    {level}: {', '.join(profiles)}")
        print()

        if results["details"]:
            print("  📝 Profile Details:")
            for d in results["details"]:
                icon = "✅" if not d["violations"] else "❌"
                name = d.get("institution_name", d["isp_id"])
                ver = d.get("version", "?")
                print(f"    {icon} {d['isp_id']} ({name}) [{d['governance_level']}] v{ver}"
                      f" — {d['template_count']} templates, {d['keyword_count']} keywords")
                for v in d["violations"]:
                    print(f"      ❌ [{v['code']}] {v['message']}")
                for w in d["warnings"]:
                    print(f"      ⚠️  [{w['code']}] {w['message']}")
            print()

        print(f"  📋 Receipt: {receipt['receipt_id']}")
        if alerts:
            print(f"  🚨 Alerts:  {len(alerts)} generated")
        print()
        print("  AI processes. Human decides. WINDI guarantees.")
        print()

    return results


def action_validate(isp_id: str, as_json: bool = False) -> Dict:
    """Validate a specific ISP profile."""
    ensure_dirs()
    scanner = ISPProfileScanner()
    profile_dir = os.path.join(ISP_LIBRARY_PATH, isp_id)

    if not os.path.isdir(profile_dir):
        error = {"error": f"ISP not found: {isp_id}", "path": profile_dir}
        if as_json:
            print(json.dumps(error, indent=2))
        else:
            print(f"\n  ❌ ISP not found: {isp_id}\n  Path: {profile_dir}\n")
        return error

    result = scanner.scan_profile(isp_id, profile_dir)
    receipt = generate_receipt(f"validate:{isp_id}", result)

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        icon = "✅" if not result["violations"] else "❌"
        print(f"\n  {icon} {isp_id} [{result['governance_level']}]")
        print(f"  Templates: {result['template_count']}, Keywords: {result['keyword_count']}")
        for v in result["violations"]:
            print(f"  ❌ [{v['code']}] {v['message']}")
        for w in result["warnings"]:
            print(f"  ⚠️  [{w['code']}] {w['message']}")
        print(f"\n  Receipt: {receipt['receipt_id']}\n")

    return result


def action_drift_check(as_json: bool = False) -> Dict:
    """Check governance matrix for drift."""
    ensure_dirs()
    scanner = GovernanceMatrixScanner()
    results = scanner.scan()
    receipt = generate_receipt("drift_check", results)

    if as_json:
        print(json.dumps(results, indent=2))
    else:
        print()
        print("╔═══════════════════════════════════════════════════════╗")
        print("║   🏛️  Governance Matrix — Drift Check                  ║")
        print("╚═══════════════════════════════════════════════════════╝")
        print()
        print("  📊 Distribution:")
        for level, count in results.get("distribution", {}).items():
            if count > 0:
                print(f"    {level}: {count}")
        print()
        if results["violations"]:
            print("  🚨 Drift Detected:")
            for v in results["violations"]:
                print(f"    ❌ [{v['code']}] {v['message']}")
        else:
            print("  ✅ No governance drift detected")
        if results["warnings"]:
            for w in results["warnings"]:
                print(f"    ⚠️  [{w['code']}] {w['message']}")
        print(f"\n  Receipt: {receipt['receipt_id']}\n")

    return results


def action_health_report(as_json: bool = False) -> Dict:
    """Generate comprehensive health report."""
    report = generate_health_report()

    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print()
        print("╔═══════════════════════════════════════════════════════╗")
        print("║   🏛️  ISP Ecosystem Health Report                      ║")
        print("╚═══════════════════════════════════════════════════════╝")
        print()
        overall = report.get("overall", {})
        print(f"  📊 Grade:      {overall.get('grade', 'N/A')}")
        print(f"  📁 Profiles:   {overall.get('profiles_found', 0)}")
        print(f"  ❌ Violations: {overall.get('total_violations', 0)}")
        print(f"  ⚠️  Warnings:  {overall.get('total_warnings', 0)}")
        print(f"  💚 Healthy:    {'YES' if overall.get('healthy') else 'NO'}")
        print(f"\n  📄 Report saved: {report.get('_saved_to', '?')}")
        print()
        print("  AI processes. Human decides. WINDI guarantees.")
        print()

    return report


def action_draft_patch(as_json: bool = False) -> List:
    """Generate draft patches from latest audit."""
    ensure_dirs()
    scanner = ISPProfileScanner()
    audit = scanner.scan_all()
    patches = generate_draft_patches(audit)
    receipt = generate_receipt("draft_patch", {"patches": len(patches)})

    if as_json:
        print(json.dumps(patches, indent=2))
    else:
        print()
        print(f"  📝 Generated {len(patches)} draft patches")
        for p in patches:
            print(f"    [{p['severity']}] {p['target']}: {p['description']}")
            print(f"      → {p['proposed_action']}")
        print(f"\n  ⚠️  All patches are DRAFTS. Human review required (I9).")
        print(f"  Receipt: {receipt['receipt_id']}\n")

    return patches


# ═══════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def print_usage():
    print()
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   🏛️  WINDI ISP Manager Agent v1.0.0                   ║")
    print("║   AI processes. Human decides. WINDI guarantees.      ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()
    print("  Commands:")
    print()
    print("    status         Show agent status")
    print("    audit          Full scan of all ISP profiles")
    print("    validate       Validate specific ISP (--isp-id <id>)")
    print("    drift_check    Check governance matrix consistency")
    print("    health_report  Comprehensive ecosystem health report")
    print("    draft_patch    Generate correction proposals")
    print()
    print("  Flags:")
    print("    --json         Output in JSON format")
    print("    --isp-id <id>  Specify ISP profile ID (for validate)")
    print()
    print("  🐉 OM SHANTI")
    print()


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    command = sys.argv[1].lower()
    as_json = "--json" in sys.argv

    # Parse --isp-id
    isp_id = None
    if "--isp-id" in sys.argv:
        idx = sys.argv.index("--isp-id")
        if idx + 1 < len(sys.argv):
            isp_id = sys.argv[idx + 1]

    if command == "status":
        action_status(as_json)
    elif command == "audit":
        action_audit(as_json)
    elif command == "validate":
        if not isp_id:
            print("\n  ❌ --isp-id required for validate\n")
            sys.exit(1)
        action_validate(isp_id, as_json)
    elif command == "drift_check":
        action_drift_check(as_json)
    elif command == "health_report":
        action_health_report(as_json)
    elif command == "draft_patch":
        action_draft_patch(as_json)
    else:
        print(f"\n  ❌ Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
