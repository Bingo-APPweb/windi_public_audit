#!/usr/bin/env python3
"""
WINDI Maestro — ResolutionAssembler Module v1.0.0
==================================================
"O Preparador da Decisão"

Assembles all relevant governance data from ISP Manager findings,
Sentinela alerts, and Forensic Ledger proofs into a single
DecisionPackage for the human decision-maker.

Principle: The human sees EVERYTHING needed to decide. Nothing hidden. Nothing assumed.

DecisionPackage Structure:
    ┌────────────────────────────────────────────────┐
    │              DECISION PACKAGE                   │
    │                                                 │
    │  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
    │  │ Finding   │  │   ISP    │  │  Governance  │ │
    │  │ Context   │  │ Context  │  │   Context    │ │
    │  │           │  │          │  │              │ │
    │  │ What      │  │ Which    │  │ How serious  │ │
    │  │ happened  │  │ profile  │  │ & who owns   │ │
    │  └──────────┘  └──────────┘  └──────────────┘ │
    │                                                 │
    │  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
    │  │   SLA    │  │ Forensic │  │   Related    │ │
    │  │  Status  │  │  Proof   │  │  Findings    │ │
    │  │          │  │          │  │              │ │
    │  │ Deadline │  │ Integrity│  │  Patterns    │ │
    │  │ & health │  │  chain   │  │  & clusters  │ │
    │  └──────────┘  └──────────┘  └──────────────┘ │
    │                                                 │
    │  integrity_hash: SHA-256 of entire package      │
    │  auto_apply: false (ALWAYS)                     │
    └────────────────────────────────────────────────┘

Version: 1.0.0
Created: 2026-02-08
Author: WINDI Publishing House / Three Dragons Protocol
"""

import json
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================================
# PATHS
# ============================================================================

ISP_LIBRARY = Path("/opt/windi/isp")
AGENTS_ROOT = Path("/opt/windi/agents")
ENGINE_PATH = Path("/opt/windi/engine")
GOVERNANCE_LEVELS = ENGINE_PATH / "governance_levels.json"


# ============================================================================
# RESOLUTION ASSEMBLER
# ============================================================================

class ResolutionAssembler:
    """
    Assembles governance data into a single DecisionPackage for human review.
    
    The Assembler:
    - Gathers finding details from Sentinela
    - Enriches with ISP profile context
    - Adds SLA status information
    - Builds integrity proof chain
    - Detects related findings (pattern clustering)
    - Produces a self-contained package for the Command Center dashboard
    
    The Assembler NEVER:
    - Suggests what the resolution should be
    - Filters or hides information
    - Modifies any source data
    """

    def __init__(self, state_db_path: Path = None):
        self.db_path = state_db_path or Path("/opt/windi/agents/maestro/state/maestro_state.db")

    def assemble(self, finding_id: str, routing_decision: Dict = None) -> Dict:
        """
        Assemble a complete DecisionPackage for a finding.
        
        Args:
            finding_id: The governance cycle finding ID
            routing_decision: Optional pre-computed routing from DecisionRouter
        
        Returns:
            DecisionPackage: Complete, self-contained governance decision context
        """
        now = datetime.now(timezone.utc)
        
        # 1. Get core finding data
        finding_data = self._get_finding_data(finding_id)
        if not finding_data:
            return {"error": f"Finding {finding_id} not found", "auto_apply": False}
        
        # 2. Enrich with ISP context
        isp_context = self._get_isp_context(finding_data)
        
        # 3. Get governance context
        governance_context = self._get_governance_context(finding_data)
        
        # 4. Get SLA status
        sla_status = self._get_sla_status(finding_data)
        
        # 5. Build forensic proof chain
        proof_chain = self._build_proof_chain(finding_id, finding_data)
        
        # 6. Find related findings (pattern detection)
        related = self._find_related(finding_data)
        
        # 7. Get event timeline
        timeline = self._get_timeline(finding_id)
        
        # Assemble the package
        package = {
            "package_type": "DECISION_PACKAGE",
            "package_version": "1.0.0",
            "finding_id": finding_id,
            "assembled_at": now.isoformat(),
            
            # Core sections
            "finding_context": {
                "severity": finding_data.get("severity", "R2"),
                "category": finding_data.get("category", "UNKNOWN"),
                "summary": finding_data.get("summary", ""),
                "source_agent": finding_data.get("source_agent", "unknown"),
                "current_status": finding_data.get("status", "OPEN"),
                "created_at": finding_data.get("created_at", ""),
            },
            
            "isp_context": isp_context,
            "governance_context": governance_context,
            "sla_status": sla_status,
            "proof_chain": proof_chain,
            "related_findings": related,
            "timeline": timeline,
            
            # Routing (if provided)
            "routing": routing_decision if routing_decision else {
                "note": "No pre-computed routing available"
            },
            
            # Constitutional guarantees
            "constitutional": {
                "I1_sovereignty": "This package is for HUMAN DECISION only",
                "I2_non_opacity": "All data sources and reasoning are fully visible",
                "I3_transparency": "Integrity hash ensures no tampering",
                "I9_no_autonomy": "auto_apply is always false",
            },
            
            "auto_apply": False,
        }
        
        # 8. Generate integrity hash of entire package
        package["integrity_hash"] = self._hash_package(package)
        
        return package

    def assemble_batch(self, finding_ids: List[str]) -> Dict:
        """Assemble packages for multiple findings with cross-reference analysis."""
        packages = []
        for fid in finding_ids:
            pkg = self.assemble(fid)
            if "error" not in pkg:
                packages.append(pkg)
        
        # Cross-finding analysis
        severity_distribution = {}
        isp_involved = set()
        for pkg in packages:
            sev = pkg["finding_context"]["severity"]
            severity_distribution[sev] = severity_distribution.get(sev, 0) + 1
            isp_id = pkg["isp_context"].get("isp_id")
            if isp_id:
                isp_involved.add(isp_id)
        
        return {
            "batch_type": "DECISION_BATCH",
            "total_packages": len(packages),
            "severity_distribution": severity_distribution,
            "isp_involved": list(isp_involved),
            "packages": packages,
            "assembled_at": datetime.now(timezone.utc).isoformat(),
            "auto_apply": False,
        }

    # ── Data gathering methods ─────────────────────────────────────────

    def _get_finding_data(self, finding_id: str) -> Optional[Dict]:
        """Get finding from Maestro state DB."""
        if not self.db_path.exists():
            return None
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM governance_cycles WHERE finding_id = ?", (finding_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def _get_isp_context(self, finding_data: Dict) -> Dict:
        """Enrich with ISP profile context if available."""
        # Try to extract ISP ID from finding
        isp_id = finding_data.get("isp_id")
        category = finding_data.get("category", "")
        summary = finding_data.get("summary", "")
        
        # Try to infer ISP from summary
        if not isp_id:
            isp_id = self._infer_isp_from_text(summary)
        
        if not isp_id:
            return {"isp_id": None, "note": "No ISP context available"}
        
        # Look up ISP profile
        profile_path = ISP_LIBRARY / isp_id / "profile.json"
        if not profile_path.exists():
            return {"isp_id": isp_id, "note": "ISP profile not found on disk"}
        
        try:
            with open(profile_path) as f:
                profile = json.load(f)
            
            return {
                "isp_id": isp_id,
                "institution_name": profile.get("institution", {}).get("name", isp_id),
                "governance_level": profile.get("governance", {}).get("level", "UNKNOWN"),
                "identity_license": profile.get("identity_license", {}).get("status", "unknown"),
                "template_count": len(profile.get("templates", [])),
                "compliance_frameworks": profile.get("compliance", {}).get("frameworks", []),
                "last_audit": profile.get("metadata", {}).get("last_audit", "unknown"),
            }
        except (json.JSONDecodeError, IOError):
            return {"isp_id": isp_id, "note": "Error reading ISP profile"}

    def _get_governance_context(self, finding_data: Dict) -> Dict:
        """Get governance level configuration context."""
        severity = finding_data.get("severity", "R2")
        
        # Risk level descriptions
        risk_descriptions = {
            "R0": {"label": "No Risk", "color": "🟢", "action": "Proceed"},
            "R1": {"label": "Minimal", "color": "🟢", "action": "Informative only"},
            "R2": {"label": "Low", "color": "🟡", "action": "Attention recommended"},
            "R3": {"label": "Medium", "color": "🟠", "action": "Review required"},
            "R4": {"label": "High", "color": "🔴", "action": "Action required"},
            "R5": {"label": "Critical", "color": "⚫", "action": "Block recommended"},
        }
        
        risk_info = risk_descriptions.get(severity, risk_descriptions["R2"])
        
        # Load governance levels config if available
        gov_config = {}
        if GOVERNANCE_LEVELS.exists():
            try:
                with open(GOVERNANCE_LEVELS) as f:
                    gov_config = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            "risk_level": severity,
            "risk_label": risk_info["label"],
            "risk_color": risk_info["color"],
            "recommended_action": risk_info["action"],
            "governance_config_available": bool(gov_config),
        }

    def _get_sla_status(self, finding_data: Dict) -> Dict:
        """Calculate current SLA status for the finding."""
        now = datetime.now(timezone.utc)
        status = finding_data.get("status", "OPEN")
        
        result = {
            "current_status": status,
            "acknowledge_deadline": finding_data.get("sla_acknowledge_deadline"),
            "resolve_deadline": finding_data.get("sla_resolve_deadline"),
            "acknowledged_at": finding_data.get("acknowledged_at"),
            "resolved_at": finding_data.get("resolved_at"),
        }
        
        # Calculate time remaining / overdue
        if status == "OPEN" and result["acknowledge_deadline"]:
            ack_dl = datetime.fromisoformat(result["acknowledge_deadline"])
            if now > ack_dl:
                overdue = (now - ack_dl).total_seconds() / 3600
                result["acknowledge_status"] = "BREACHED"
                result["acknowledge_overdue_hours"] = round(overdue, 2)
            else:
                remaining = (ack_dl - now).total_seconds() / 3600
                result["acknowledge_status"] = "PENDING"
                result["acknowledge_remaining_hours"] = round(remaining, 2)
        
        if status in ("ACKNOWLEDGED", "IN_PROGRESS", "ESCALATED") and result["resolve_deadline"]:
            res_dl = datetime.fromisoformat(result["resolve_deadline"])
            if now > res_dl:
                overdue = (now - res_dl).total_seconds() / 3600
                result["resolve_status"] = "BREACHED"
                result["resolve_overdue_hours"] = round(overdue, 2)
            else:
                remaining = (res_dl - now).total_seconds() / 3600
                result["resolve_status"] = "ON_TRACK"
                result["resolve_remaining_hours"] = round(remaining, 2)
        
        return result

    def _build_proof_chain(self, finding_id: str, finding_data: Dict) -> Dict:
        """Build forensic proof chain for integrity verification."""
        receipt_chain = []
        raw_chain = finding_data.get("receipt_chain", "[]")
        if isinstance(raw_chain, str):
            try:
                receipt_chain = json.loads(raw_chain)
            except json.JSONDecodeError:
                receipt_chain = []
        else:
            receipt_chain = raw_chain
        
        # Verify receipt files exist
        receipts_dir = Path("/opt/windi/agents/maestro/receipts")
        verified_receipts = []
        for rid in receipt_chain:
            receipt_file = receipts_dir / f"{rid}.json"
            if receipt_file.exists():
                try:
                    with open(receipt_file) as f:
                        receipt = json.load(f)
                    verified_receipts.append({
                        "receipt_id": rid,
                        "action": receipt.get("action", "unknown"),
                        "timestamp": receipt.get("timestamp", "unknown"),
                        "integrity_hash": receipt.get("integrity_hash", "missing"),
                        "verified": True,
                    })
                except (json.JSONDecodeError, IOError):
                    verified_receipts.append({"receipt_id": rid, "verified": False, "error": "parse_error"})
            else:
                verified_receipts.append({"receipt_id": rid, "verified": False, "error": "file_not_found"})
        
        # Chain integrity: each receipt should be linkable
        chain_intact = all(r.get("verified", False) for r in verified_receipts)
        
        return {
            "total_receipts": len(receipt_chain),
            "verified_receipts": len([r for r in verified_receipts if r.get("verified")]),
            "chain_intact": chain_intact,
            "receipts": verified_receipts,
            "chain_hash": hashlib.sha256(
                json.dumps(receipt_chain, sort_keys=True).encode()
            ).hexdigest()[:16] if receipt_chain else None,
        }

    def _find_related(self, finding_data: Dict) -> Dict:
        """Find related findings by ISP, category, or severity pattern."""
        if not self.db_path.exists():
            return {"related": [], "patterns": []}
        
        finding_id = finding_data.get("finding_id", "")
        category = finding_data.get("category", "")
        severity = finding_data.get("severity", "")
        summary = finding_data.get("summary", "")
        
        related = []
        patterns = []
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            
            # Same category findings
            cursor = conn.execute("""
                SELECT finding_id, severity, category, summary, status, created_at
                FROM governance_cycles 
                WHERE category = ? AND finding_id != ?
                ORDER BY created_at DESC LIMIT 10
            """, (category, finding_id))
            
            same_category = [dict(row) for row in cursor.fetchall()]
            if same_category:
                related.extend([{
                    "finding_id": r["finding_id"],
                    "relation": "SAME_CATEGORY",
                    "severity": r["severity"],
                    "status": r["status"],
                } for r in same_category])
                
                if len(same_category) >= 3:
                    patterns.append({
                        "type": "RECURRING_CATEGORY",
                        "category": category,
                        "occurrences": len(same_category) + 1,
                        "insight": f"Category '{category}' has {len(same_category) + 1} total findings — potential systemic issue",
                    })
            
            # Same severity findings (open only)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM governance_cycles 
                WHERE severity = ? AND status NOT IN ('RESOLVED', 'CLOSED') AND finding_id != ?
            """, (severity, finding_id))
            same_severity_count = cursor.fetchone()[0]
            
            if same_severity_count >= 5:
                patterns.append({
                    "type": "SEVERITY_CLUSTER",
                    "severity": severity,
                    "open_count": same_severity_count + 1,
                    "insight": f"{same_severity_count + 1} open {severity} findings — workload concentration risk",
                })
        
        return {
            "related": related[:10],
            "patterns": patterns,
            "total_related": len(related),
        }

    def _get_timeline(self, finding_id: str) -> List[Dict]:
        """Get chronological event timeline for the finding."""
        if not self.db_path.exists():
            return []
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("""
                SELECT event_type, event_data, timestamp, receipt_id
                FROM cycle_events 
                WHERE finding_id = ?
                ORDER BY timestamp ASC
            """, (finding_id,))
            
            return [{
                "event": row[0],
                "data": json.loads(row[1]) if row[1] else {},
                "timestamp": row[2],
                "receipt_id": row[3],
            } for row in cursor.fetchall()]

    def _infer_isp_from_text(self, text: str) -> Optional[str]:
        """Try to infer ISP ID from finding text. Simple keyword matching."""
        text_lower = text.lower()
        known_isps = {
            "bafin": "bafin",
            "ecb": "ecb", "european central bank": "ecb",
            "bundesregierung": "bundesregierung",
            "deutsche bahn": "deutsche-bahn", "db ": "deutsche-bahn",
            "ihk": "ihk-schwaben",
            "siemens": "siemens",
            "kempten": "stadtwerke-kempten", "stadtwerke": "stadtwerke-kempten",
            "tüv": "tuev-sued", "tuev": "tuev-sued", "tÜv": "tuev-sued",
            "bundesbank": "bundesbank",
            "bka": "bka",
            "bmas": "bmas",
        }
        for keyword, isp_id in known_isps.items():
            if keyword in text_lower:
                return isp_id
        return None

    def _hash_package(self, package: Dict) -> str:
        """Generate SHA-256 integrity hash of the entire package."""
        # Remove hash field before hashing (it doesn't exist yet)
        hashable = {k: v for k, v in package.items() if k != "integrity_hash"}
        return hashlib.sha256(
            json.dumps(hashable, sort_keys=True, default=str).encode()
        ).hexdigest()
