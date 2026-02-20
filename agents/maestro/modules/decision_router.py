#!/usr/bin/env python3
"""
WINDI Maestro — DecisionRouter Module v1.0.0
=============================================
"O Maestro de Tráfego"

Routes governance findings to the correct human decision-maker
based on severity, ISP governance level, institutional hierarchy,
and finding category.

Principle: The Router NEVER decides resolution — it decides WHO decides.

Routing Logic:
    ┌─────────────┐
    │   Finding    │
    │  (from Sent.)│
    └──────┬──────┘
           │
    ┌──────▼──────┐     ┌──────────────┐
    │  Classify   │────▶│ Simple Config │──▶ INSTITUTIONAL_CHANNEL
    │  Severity   │     │   (R0-R3)    │     (standard SLA)
    └──────┬──────┘     └──────────────┘
           │
           │ R4-R5      ┌──────────────┐
           └───────────▶│ Alert Mode   │──▶ ALERT_CHANNEL
                        │ (Priority)   │     (urgent SLA)
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │  Stakeholder │──▶ Specific human(s)
                        │   Mapping    │     by ISP + role
                        └──────────────┘

Version: 1.0.0
Created: 2026-02-08
Author: WINDI Publishing House / Three Dragons Protocol
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================================
# STAKEHOLDER REGISTRY
# ============================================================================

# Default stakeholder mapping by governance level
# In production, this would be loaded from a config file per client
DEFAULT_STAKEHOLDER_MAP = {
    "HIGH": {
        "primary": "Chief Governance Officer",
        "escalation": "Board / Vorstand",
        "notify": ["Compliance Officer", "Legal Counsel"],
        "institutions": ["bafin", "ecb", "bundesbank", "bka"],
    },
    "MEDIUM": {
        "primary": "Governance Controller",
        "escalation": "Chief Governance Officer",
        "notify": ["Department Head"],
        "institutions": ["bundesregierung", "bmas", "bmwk"],
    },
    "LOW": {
        "primary": "Document Owner",
        "escalation": "Governance Controller",
        "notify": [],
        "institutions": ["deutsche-bahn", "ihk-schwaben", "siemens", "stadtwerke-kempten", "tuev-sued"],
    },
}

# Finding category → resolution domain mapping
CATEGORY_DOMAIN_MAP = {
    # ISP structural issues
    "MISSING_IDENTITY_LICENSE": "isp_integrity",
    "INVALID_GOVERNANCE_LEVEL": "isp_integrity",
    "ORPHAN_TEMPLATE": "isp_integrity",
    "SCHEMA_VIOLATION": "isp_integrity",
    "GOVERNANCE_DRIFT": "isp_integrity",
    
    # Compliance issues
    "REGULATORY_GAP": "compliance",
    "EU_AI_ACT_VIOLATION": "compliance",
    "DSGVO_CONCERN": "compliance",
    "BSI_C5_DEVIATION": "compliance",
    
    # Document governance issues
    "UNSIGNED_DOCUMENT": "document_governance",
    "MISSING_APPROVAL": "document_governance",
    "EXPIRED_CERTIFICATION": "document_governance",
    "VALUE_RANGE_ANOMALY": "document_governance",
    
    # Autonomy concerns (I9)
    "AUTONOMY_ESCALATION_ATTEMPT": "critical_security",
    "AUTO_APPLY_DETECTED": "critical_security",
    "HUMAN_BYPASS_DETECTED": "critical_security",
    
    # SGE findings
    "SGE_SCORE_INCONSISTENCY": "sge_review",
    "SEMANTIC_RISK_ELEVATED": "sge_review",
    "CROSS_REFERENCE_BROKEN": "sge_review",
}


# ============================================================================
# DECISION ROUTER
# ============================================================================

class DecisionRouter:
    """
    Routes governance findings to the appropriate human stakeholder
    and communication channel.
    
    The Router determines:
    1. CHANNEL: Institutional (R0-R3) vs Alert (R4-R5)
    2. STAKEHOLDER: Who receives the finding for decision
    3. PRIORITY: Routing priority based on combined signals
    4. DOMAIN: Which resolution domain handles this category
    
    The Router NEVER determines:
    - What the resolution should be
    - Whether the finding is valid
    - How to fix the issue
    """

    def __init__(self, stakeholder_config: Dict = None, isp_library_path: Path = None):
        self.stakeholder_map = stakeholder_config or DEFAULT_STAKEHOLDER_MAP
        self.isp_library = isp_library_path or Path("/opt/windi/isp")

    def route(self, finding: Dict) -> Dict:
        """
        Route a finding to the appropriate channel, stakeholder, and domain.
        
        Args:
            finding: Dict with keys: finding_id, severity, category, 
                     summary, source_agent, isp_id (optional)
        
        Returns:
            RoutingDecision with channel, stakeholder, priority, domain, rationale
        """
        severity = finding.get("severity", "R2")
        category = finding.get("category", "UNKNOWN")
        isp_id = finding.get("isp_id", None)
        
        # 1. Determine channel (dual-mode communication)
        channel = self._determine_channel(severity, category)
        
        # 2. Determine governance level from ISP
        gov_level = self._resolve_governance_level(isp_id)
        
        # 3. Map to stakeholder
        stakeholder = self._map_stakeholder(gov_level, severity, category)
        
        # 4. Calculate routing priority
        priority = self._calculate_priority(severity, category, gov_level)
        
        # 5. Determine resolution domain
        domain = self._resolve_domain(category)
        
        # 6. Build rationale (transparency — I2)
        rationale = self._build_rationale(
            severity, category, channel, gov_level, stakeholder, priority
        )

        routing_decision = {
            "finding_id": finding.get("finding_id", "UNKNOWN"),
            "channel": channel,
            "stakeholder": stakeholder,
            "priority": priority,
            "domain": domain,
            "governance_level": gov_level,
            "rationale": rationale,
            "routing_timestamp": datetime.now(timezone.utc).isoformat(),
            "auto_apply": False,  # I9
        }
        
        return routing_decision

    def route_batch(self, findings: List[Dict]) -> List[Dict]:
        """Route multiple findings, detecting patterns across them."""
        decisions = [self.route(f) for f in findings]
        
        # Detect pattern: multiple findings for same ISP → potential systemic issue
        isp_counts = {}
        for f, d in zip(findings, decisions):
            isp_id = f.get("isp_id", "unknown")
            isp_counts[isp_id] = isp_counts.get(isp_id, 0) + 1
        
        # Flag systemic patterns
        for d in decisions:
            finding = next(
                (f for f in findings if f.get("finding_id") == d["finding_id"]), {}
            )
            isp_id = finding.get("isp_id", "unknown")
            if isp_counts.get(isp_id, 0) >= 3:
                d["pattern_flag"] = {
                    "type": "SYSTEMIC",
                    "message": f"Multiple findings ({isp_counts[isp_id]}) for ISP '{isp_id}' — potential systemic issue",
                    "recommendation": "HUMAN_REVIEW_CLUSTER",
                }
                # Upgrade priority if pattern detected
                if d["priority"]["score"] < 80:
                    d["priority"]["score"] = min(d["priority"]["score"] + 15, 100)
                    d["priority"]["level"] = self._priority_level(d["priority"]["score"])
                    d["priority"]["boost_reason"] = "systemic_pattern_detected"
        
        return decisions

    # ── Channel determination ──────────────────────────────────────────

    def _determine_channel(self, severity: str, category: str) -> Dict:
        """
        Dual-mode communication:
        - INSTITUTIONAL_CHANNEL (R0-R3): Standard governance flow
        - ALERT_CHANNEL (R4-R5): Priority/urgent governance flow
        
        Special case: I9 violations always go to ALERT regardless of severity
        """
        is_i9_violation = category in (
            "AUTONOMY_ESCALATION_ATTEMPT", 
            "AUTO_APPLY_DETECTED", 
            "HUMAN_BYPASS_DETECTED",
        )
        
        if severity in ("R4", "R5") or is_i9_violation:
            return {
                "type": "ALERT_CHANNEL",
                "mode": "URGENT",
                "notification": "IMMEDIATE",
                "dashboard_highlight": True,
                "reason": "I9 security violation" if is_i9_violation else f"Severity {severity}",
            }
        else:
            return {
                "type": "INSTITUTIONAL_CHANNEL",
                "mode": "STANDARD",
                "notification": "QUEUED",
                "dashboard_highlight": severity == "R3",
                "reason": f"Standard governance flow for {severity}",
            }

    # ── Governance level resolution ────────────────────────────────────

    def _resolve_governance_level(self, isp_id: Optional[str]) -> str:
        """Look up the governance level from the ISP profile."""
        if not isp_id:
            return "MEDIUM"  # Default when ISP unknown
        
        profile_path = self.isp_library / isp_id / "profile.json"
        if profile_path.exists():
            try:
                with open(profile_path) as f:
                    profile = json.load(f)
                return profile.get("governance", {}).get("level", "MEDIUM").upper()
            except (json.JSONDecodeError, IOError):
                pass
        
        # Fallback: check known institutions
        for level, config in self.stakeholder_map.items():
            if isp_id in config.get("institutions", []):
                return level
        
        return "MEDIUM"

    # ── Stakeholder mapping ────────────────────────────────────────────

    def _map_stakeholder(self, gov_level: str, severity: str, category: str) -> Dict:
        """Map to specific stakeholder based on governance level and severity."""
        level_config = self.stakeholder_map.get(gov_level, self.stakeholder_map["MEDIUM"])
        
        # I9 violations always go to highest authority
        if category in ("AUTONOMY_ESCALATION_ATTEMPT", "AUTO_APPLY_DETECTED", "HUMAN_BYPASS_DETECTED"):
            return {
                "primary": "Chief Governance Officer",
                "escalation": "Board / Vorstand",
                "notify": ["All Governance Controllers", "Legal Counsel"],
                "override_reason": "I9 — Prohibition of Autonomy Escalation",
            }
        
        # R5 critical → escalation level directly
        if severity == "R5":
            return {
                "primary": level_config["escalation"],
                "escalation": "Board / Vorstand" if gov_level == "HIGH" else level_config["escalation"],
                "notify": level_config.get("notify", []) + [level_config["primary"]],
                "override_reason": f"R5 Critical — direct escalation for {gov_level} governance",
            }
        
        # Standard routing
        return {
            "primary": level_config["primary"],
            "escalation": level_config["escalation"],
            "notify": level_config.get("notify", []),
        }

    # ── Priority calculation ───────────────────────────────────────────

    def _calculate_priority(self, severity: str, category: str, gov_level: str) -> Dict:
        """
        Calculate routing priority score (0-100).
        
        Factors:
        - Severity weight (40%)
        - Governance level weight (30%)
        - Category criticality (30%)
        """
        # Severity score
        severity_scores = {"R0": 0, "R1": 10, "R2": 30, "R3": 50, "R4": 80, "R5": 100}
        severity_score = severity_scores.get(severity, 30)
        
        # Governance level score
        gov_scores = {"LOW": 20, "MEDIUM": 50, "HIGH": 90}
        gov_score = gov_scores.get(gov_level, 50)
        
        # Category criticality
        domain = CATEGORY_DOMAIN_MAP.get(category, "general")
        domain_scores = {
            "critical_security": 100,
            "compliance": 80,
            "document_governance": 60,
            "sge_review": 50,
            "isp_integrity": 40,
            "general": 30,
        }
        cat_score = domain_scores.get(domain, 30)
        
        # Weighted total
        total = int(severity_score * 0.4 + gov_score * 0.3 + cat_score * 0.3)
        
        return {
            "score": total,
            "level": self._priority_level(total),
            "breakdown": {
                "severity_contribution": round(severity_score * 0.4, 1),
                "governance_contribution": round(gov_score * 0.3, 1),
                "category_contribution": round(cat_score * 0.3, 1),
            },
        }

    @staticmethod
    def _priority_level(score: int) -> str:
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        return "INFO"

    # ── Domain resolution ──────────────────────────────────────────────

    def _resolve_domain(self, category: str) -> Dict:
        """Determine which resolution domain handles this finding category."""
        domain = CATEGORY_DOMAIN_MAP.get(category, "general")
        
        domain_info = {
            "critical_security": {
                "name": "Critical Security",
                "description": "I9 violations and autonomy concerns — highest priority",
                "typical_actions": ["Immediate system review", "Audit trail analysis", "Invariant enforcement"],
            },
            "compliance": {
                "name": "Regulatory Compliance",
                "description": "EU AI Act, DSGVO, BSI C5, sector-specific regulations",
                "typical_actions": ["Regulatory gap analysis", "Framework alignment", "Documentation update"],
            },
            "document_governance": {
                "name": "Document Governance",
                "description": "Document lifecycle, approvals, certifications",
                "typical_actions": ["Approval chain review", "Re-certification", "Value range audit"],
            },
            "sge_review": {
                "name": "SGE Review",
                "description": "Semantic Governance Engine findings and score analysis",
                "typical_actions": ["SGE recalibration", "Cross-reference repair", "Score validation"],
            },
            "isp_integrity": {
                "name": "ISP Integrity",
                "description": "Institutional Style Profile structural issues",
                "typical_actions": ["Profile field correction", "Template alignment", "Governance level review"],
            },
            "general": {
                "name": "General Governance",
                "description": "Uncategorized governance findings",
                "typical_actions": ["Manual classification", "Human assessment"],
            },
        }
        
        return {
            "domain_id": domain,
            **domain_info.get(domain, domain_info["general"]),
        }

    # ── Rationale builder ──────────────────────────────────────────────

    def _build_rationale(self, severity, category, channel, gov_level, stakeholder, priority) -> str:
        """Build human-readable rationale for routing decision (I2 — non-opacity)."""
        parts = [
            f"Finding classified as {severity} severity",
            f"in {gov_level} governance context.",
            f"Category '{category}' maps to {CATEGORY_DOMAIN_MAP.get(category, 'general')} domain.",
            f"Routed via {channel['type']} ({channel['mode']} mode)",
            f"to {stakeholder['primary']} as primary decision-maker.",
            f"Priority score: {priority['score']}/100 ({priority['level']}).",
        ]
        if stakeholder.get("override_reason"):
            parts.append(f"Override: {stakeholder['override_reason']}.")
        
        return " ".join(parts)
