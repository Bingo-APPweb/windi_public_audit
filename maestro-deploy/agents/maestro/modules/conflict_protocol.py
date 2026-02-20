#!/usr/bin/env python3
"""
WINDI Maestro — Institutional Conflict Protocol v1.0.0
=======================================================
"O Coração Prático da Arquitetura"

Manages divergence between institutional pillars (Sentinela vs ISP Manager)
through structured conflict resolution that NEVER auto-resolves.

Core Principle:
    Conflict is not a bug — it's governance working.
    When Sentinela says "this ISP is non-compliant" and ISP Manager says
    "this ISP is structurally valid", both are RIGHT in their domain.
    The conflict itself is the signal that requires human decision.

Conflict Types:
    ┌─────────────────────────────────────────────────────────┐
    │              INSTITUTIONAL CONFLICT MATRIX               │
    │                                                          │
    │  Type 1: CONTRADICTION                                   │
    │  Sentinela: "BaFin ISP missing identity_license"        │
    │  ISP Manager: "BaFin ISP passes structural validation"  │
    │  → Both correct in their domain → HUMAN decides          │
    │                                                          │
    │  Type 2: ESCALATION CASCADE                              │
    │  Sentinela finding triggers ISP Manager alert which      │
    │  triggers another Sentinela finding → loop detection      │
    │                                                          │
    │  Type 3: PRIORITY COLLISION                              │
    │  Two findings for same ISP with different severities     │
    │  → Maestro must present BOTH without merging             │
    │                                                          │
    │  Type 4: DOMAIN BOUNDARY                                 │
    │  Finding touches both compliance AND structural integrity │
    │  → Which pillar owns resolution?                         │
    └─────────────────────────────────────────────────────────┘

Resolution Protocol:
    1. Maestro DETECTS conflict (never ignores)
    2. Maestro PRESERVES both positions (never merges)
    3. Maestro PACKAGES conflict for human review
    4. Maestro TRACKS resolution timeline (SLA)
    5. Human DECIDES which position prevails
    6. Maestro RECORDS decision with rationale
    7. Forensic Ledger SEALS the resolution

Version: 1.0.0
Created: 2026-02-08
Author: WINDI Publishing House / Three Dragons Protocol
"""

import json
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum


# ============================================================================
# CONFLICT TYPES
# ============================================================================

class ConflictType(Enum):
    """The four institutional conflict types."""
    CONTRADICTION = "CONTRADICTION"         # Both pillars correct, conclusions differ
    ESCALATION_CASCADE = "ESCALATION_CASCADE"  # Circular trigger between pillars
    PRIORITY_COLLISION = "PRIORITY_COLLISION"   # Same target, different severities
    DOMAIN_BOUNDARY = "DOMAIN_BOUNDARY"     # Finding spans multiple pillar domains


class ConflictSeverity(Enum):
    """Conflict severity — distinct from finding severity."""
    LOW = "LOW"           # Informational divergence, no urgency
    MEDIUM = "MEDIUM"     # Requires human attention within normal SLA
    HIGH = "HIGH"         # Requires priority human attention
    CRITICAL = "CRITICAL" # Potential governance breakdown — immediate attention


class ConflictStatus(Enum):
    """Conflict lifecycle status."""
    DETECTED = "DETECTED"           # Conflict identified by Maestro
    DOCUMENTED = "DOCUMENTED"       # Both positions packaged
    PRESENTED = "PRESENTED"         # Sent to Human Decision Hub
    ADJUDICATED = "ADJUDICATED"     # Human has decided
    IMPLEMENTED = "IMPLEMENTED"     # Winning position applied
    SEALED = "SEALED"               # Forensic Ledger receipt generated


# ============================================================================
# CONFLICT DETECTOR
# ============================================================================

class ConflictDetector:
    """
    Detects conflicts between pillar outputs.
    
    Scans findings from Sentinela and alerts from ISP Manager to identify
    when their conclusions diverge on the same governance subject.
    
    The Detector NEVER:
    - Decides which pillar is correct
    - Suppresses either position
    - Auto-resolves contradictions
    """

    def __init__(self, state_db_path: Path = None):
        self.db_path = state_db_path or Path("/opt/windi/agents/maestro/state/maestro_state.db")
        self._init_conflict_table()

    def _init_conflict_table(self):
        """Create conflict tracking table if not exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS institutional_conflicts (
                    conflict_id TEXT PRIMARY KEY,
                    conflict_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT DEFAULT 'DETECTED',
                    isp_id TEXT,
                    pillar_a TEXT NOT NULL,
                    pillar_a_finding_id TEXT,
                    pillar_a_position TEXT NOT NULL,
                    pillar_b TEXT NOT NULL,
                    pillar_b_finding_id TEXT,
                    pillar_b_position TEXT NOT NULL,
                    common_subject TEXT,
                    human_decision TEXT,
                    decision_rationale TEXT,
                    decided_by TEXT,
                    created_at TEXT NOT NULL,
                    presented_at TEXT,
                    adjudicated_at TEXT,
                    sealed_at TEXT,
                    receipt_chain TEXT DEFAULT '[]'
                )
            """)
            conn.commit()

    def detect_contradictions(self, sentinela_findings: List[Dict],
                               isp_manager_alerts: List[Dict]) -> List[Dict]:
        """
        Compare Sentinela findings with ISP Manager alerts to detect contradictions.
        
        A contradiction occurs when:
        - Both reference the same ISP
        - One says "non-compliant" while the other says "structurally valid"
        - OR one flags a severity that the other doesn't recognize
        """
        conflicts = []
        
        # Index by ISP ID for cross-reference
        sent_by_isp = self._index_by_isp(sentinela_findings, "sentinela")
        isp_by_isp = self._index_by_isp(isp_manager_alerts, "isp-manager")
        
        # Find ISPs mentioned by both pillars
        common_isps = set(sent_by_isp.keys()) & set(isp_by_isp.keys())
        
        for isp_id in common_isps:
            sent_items = sent_by_isp[isp_id]
            isp_items = isp_by_isp[isp_id]
            
            for s_finding in sent_items:
                for i_alert in isp_items:
                    conflict = self._check_contradiction(s_finding, i_alert, isp_id)
                    if conflict:
                        conflicts.append(conflict)
        
        # Detect priority collisions (same ISP, different severities)
        all_findings = sentinela_findings + isp_manager_alerts
        collisions = self._detect_priority_collisions(all_findings)
        conflicts.extend(collisions)
        
        # Detect escalation cascades
        cascades = self._detect_cascades(sentinela_findings, isp_manager_alerts)
        conflicts.extend(cascades)
        
        return conflicts

    def register_conflict(self, conflict: Dict) -> Dict:
        """Register a detected conflict in the state database."""
        now = datetime.now(timezone.utc)
        conflict_id = conflict.get("conflict_id",
            f"CONF-{now.strftime('%Y%m%d%H%M%S')}-{hashlib.sha256(json.dumps(conflict, sort_keys=True).encode()).hexdigest()[:6]}")
        
        with sqlite3.connect(str(self.db_path)) as conn:
            try:
                conn.execute("""
                    INSERT INTO institutional_conflicts
                    (conflict_id, conflict_type, severity, status, isp_id,
                     pillar_a, pillar_a_finding_id, pillar_a_position,
                     pillar_b, pillar_b_finding_id, pillar_b_position,
                     common_subject, created_at)
                    VALUES (?, ?, ?, 'DETECTED', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conflict_id,
                    conflict.get("type", ConflictType.CONTRADICTION.value),
                    conflict.get("severity", ConflictSeverity.MEDIUM.value),
                    conflict.get("isp_id"),
                    conflict.get("pillar_a", {}).get("name", "unknown"),
                    conflict.get("pillar_a", {}).get("finding_id"),
                    json.dumps(conflict.get("pillar_a", {}).get("position", {})),
                    conflict.get("pillar_b", {}).get("name", "unknown"),
                    conflict.get("pillar_b", {}).get("finding_id"),
                    json.dumps(conflict.get("pillar_b", {}).get("position", {})),
                    conflict.get("common_subject", ""),
                    now.isoformat(),
                ))
                conn.commit()
            except sqlite3.IntegrityError:
                return {"error": f"Conflict {conflict_id} already registered"}
        
        return {
            "conflict_id": conflict_id,
            "status": "DETECTED",
            "type": conflict.get("type"),
            "severity": conflict.get("severity"),
            "isp_id": conflict.get("isp_id"),
            "message": "Conflict registered — awaiting documentation and human review",
            "auto_apply": False,
        }

    def _check_contradiction(self, sentinela_finding: Dict,
                              isp_alert: Dict, isp_id: str) -> Optional[Dict]:
        """Check if a Sentinela finding contradicts an ISP Manager alert."""
        s_category = sentinela_finding.get("category", "")
        i_category = isp_alert.get("category", "")
        s_severity = sentinela_finding.get("severity", "R2")
        i_severity = isp_alert.get("severity", "R2")
        
        # Contradiction patterns
        contradiction_pairs = [
            # Sentinela says non-compliant, ISP Manager says valid
            ({"MISSING_IDENTITY_LICENSE", "SCHEMA_VIOLATION", "REGULATORY_GAP"},
             {"STRUCTURAL_VALID", "SCHEMA_PASS", "AUDIT_PASS"}),
            # Severity mismatch on same subject
            ({"SGE_SCORE_INCONSISTENCY"},
             {"SGE_SCORE_VALID"}),
        ]
        
        for sent_cats, isp_cats in contradiction_pairs:
            if s_category in sent_cats and i_category in isp_cats:
                return {
                    "type": ConflictType.CONTRADICTION.value,
                    "severity": self._assess_conflict_severity(s_severity, i_severity),
                    "isp_id": isp_id,
                    "common_subject": f"{s_category} vs {i_category}",
                    "pillar_a": {
                        "name": "sentinela",
                        "finding_id": sentinela_finding.get("finding_id"),
                        "position": {
                            "conclusion": "NON_COMPLIANT",
                            "category": s_category,
                            "severity": s_severity,
                            "summary": sentinela_finding.get("summary", ""),
                        },
                    },
                    "pillar_b": {
                        "name": "isp-manager",
                        "finding_id": isp_alert.get("finding_id"),
                        "position": {
                            "conclusion": "STRUCTURALLY_VALID",
                            "category": i_category,
                            "severity": i_severity,
                            "summary": isp_alert.get("summary", ""),
                        },
                    },
                }
        
        # Check severity divergence on same category
        if s_category == i_category and s_severity != i_severity:
            severity_order = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5}
            diff = abs(severity_order.get(s_severity, 2) - severity_order.get(i_severity, 2))
            if diff >= 2:  # Significant severity disagreement
                return {
                    "type": ConflictType.CONTRADICTION.value,
                    "severity": ConflictSeverity.HIGH.value if diff >= 3 else ConflictSeverity.MEDIUM.value,
                    "isp_id": isp_id,
                    "common_subject": f"Severity divergence on {s_category}: {s_severity} vs {i_severity}",
                    "pillar_a": {
                        "name": "sentinela",
                        "finding_id": sentinela_finding.get("finding_id"),
                        "position": {"severity": s_severity, "category": s_category,
                                    "summary": sentinela_finding.get("summary", "")},
                    },
                    "pillar_b": {
                        "name": "isp-manager",
                        "finding_id": isp_alert.get("finding_id"),
                        "position": {"severity": i_severity, "category": i_category,
                                    "summary": isp_alert.get("summary", "")},
                    },
                }
        
        return None

    def _detect_priority_collisions(self, all_findings: List[Dict]) -> List[Dict]:
        """Detect when multiple findings target the same ISP with different severities."""
        by_isp = {}
        for f in all_findings:
            isp_id = f.get("isp_id") or self._extract_isp(f.get("summary", ""))
            if isp_id:
                by_isp.setdefault(isp_id, []).append(f)
        
        collisions = []
        for isp_id, findings in by_isp.items():
            if len(findings) < 2:
                continue
            
            severities = set(f.get("severity", "R2") for f in findings)
            if len(severities) >= 2:
                severity_order = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5}
                max_sev = max(severities, key=lambda s: severity_order.get(s, 2))
                min_sev = min(severities, key=lambda s: severity_order.get(s, 2))
                diff = severity_order.get(max_sev, 2) - severity_order.get(min_sev, 2)
                
                if diff >= 2:
                    collisions.append({
                        "type": ConflictType.PRIORITY_COLLISION.value,
                        "severity": ConflictSeverity.MEDIUM.value,
                        "isp_id": isp_id,
                        "common_subject": f"Priority collision: {len(findings)} findings, severities {min_sev}-{max_sev}",
                        "pillar_a": {
                            "name": findings[0].get("source_agent", "unknown"),
                            "finding_id": findings[0].get("finding_id"),
                            "position": {"severity": findings[0].get("severity"),
                                        "summary": findings[0].get("summary", "")},
                        },
                        "pillar_b": {
                            "name": findings[-1].get("source_agent", "unknown"),
                            "finding_id": findings[-1].get("finding_id"),
                            "position": {"severity": findings[-1].get("severity"),
                                        "summary": findings[-1].get("summary", "")},
                        },
                        "all_findings": [f.get("finding_id") for f in findings],
                    })
        
        return collisions

    def _detect_cascades(self, sentinela_findings: List[Dict],
                          isp_alerts: List[Dict]) -> List[Dict]:
        """
        Detect escalation cascades where findings trigger each other in a loop.
        
        Pattern: Sentinela finding → ISP Manager reacts → triggers new Sentinela finding
        This is governance working (each pillar doing its job), but can cause
        infinite loops if not detected.
        """
        cascades = []
        
        # Look for findings that reference each other
        sent_ids = {f.get("finding_id"): f for f in sentinela_findings}
        isp_ids = {f.get("finding_id"): f for f in isp_alerts}
        
        for s_id, s_finding in sent_ids.items():
            triggered_by = s_finding.get("triggered_by")
            if triggered_by and triggered_by in isp_ids:
                # Check if the ISP alert was itself triggered by an earlier Sentinela finding
                isp_alert = isp_ids[triggered_by]
                isp_trigger = isp_alert.get("triggered_by")
                if isp_trigger and isp_trigger in sent_ids:
                    cascades.append({
                        "type": ConflictType.ESCALATION_CASCADE.value,
                        "severity": ConflictSeverity.HIGH.value,
                        "isp_id": s_finding.get("isp_id"),
                        "common_subject": f"Cascade: {isp_trigger} → {triggered_by} → {s_id}",
                        "pillar_a": {
                            "name": "sentinela",
                            "finding_id": s_id,
                            "position": {"chain": [isp_trigger, triggered_by, s_id],
                                        "summary": "Circular trigger detected between pillars"},
                        },
                        "pillar_b": {
                            "name": "isp-manager",
                            "finding_id": triggered_by,
                            "position": {"triggered_by": isp_trigger,
                                        "summary": isp_alert.get("summary", "")},
                        },
                        "cascade_chain": [isp_trigger, triggered_by, s_id],
                    })
        
        return cascades

    def _assess_conflict_severity(self, severity_a: str, severity_b: str) -> str:
        """Assess conflict severity based on the findings involved."""
        severity_order = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5}
        max_level = max(severity_order.get(severity_a, 2), severity_order.get(severity_b, 2))
        
        if max_level >= 4:
            return ConflictSeverity.CRITICAL.value
        elif max_level >= 3:
            return ConflictSeverity.HIGH.value
        elif max_level >= 2:
            return ConflictSeverity.MEDIUM.value
        return ConflictSeverity.LOW.value

    def _index_by_isp(self, findings: List[Dict], source: str) -> Dict[str, List[Dict]]:
        """Index findings by ISP ID."""
        indexed = {}
        for f in findings:
            isp_id = f.get("isp_id") or self._extract_isp(f.get("summary", ""))
            if isp_id:
                f["source_agent"] = source
                indexed.setdefault(isp_id, []).append(f)
        return indexed

    def _extract_isp(self, text: str) -> Optional[str]:
        """Try to extract ISP ID from text."""
        known = {
            "bafin": "bafin", "ecb": "ecb", "bundesregierung": "bundesregierung",
            "deutsche bahn": "deutsche-bahn", "deutsche-bahn": "deutsche-bahn",
            "ihk": "ihk-schwaben", "siemens": "siemens",
            "stadtwerke": "stadtwerke-kempten", "kempten": "stadtwerke-kempten",
            "tüv": "tuev-sued", "tuev": "tuev-sued",
        }
        text_lower = text.lower()
        for keyword, isp_id in known.items():
            if keyword in text_lower:
                return isp_id
        return None


# ============================================================================
# CONFLICT PACKAGER
# ============================================================================

class ConflictPackager:
    """
    Packages conflicts into structured presentations for human decision.
    
    A ConflictPackage is like a DecisionPackage but specifically designed
    for disputes between pillars. It ALWAYS presents BOTH positions
    side-by-side with equal weight — no bias, no recommendation.
    
    ConflictPackage Structure:
        ┌──────────────────────────────────────────────┐
        │            CONFLICT PACKAGE                   │
        │                                               │
        │  ┌─────────────┐    ┌─────────────┐         │
        │  │  Position A  │ vs │  Position B  │         │
        │  │  (Sentinela) │    │ (ISP Manager)│         │
        │  │              │    │              │         │
        │  │  Evidence    │    │  Evidence    │         │
        │  │  Severity    │    │  Severity    │         │
        │  │  Domain      │    │  Domain      │         │
        │  └─────────────┘    └─────────────┘         │
        │                                               │
        │  Common Subject: [what they disagree about]  │
        │  Impact Analysis: [what happens if A or B]   │
        │  Timeline: [SLA for resolution]              │
        │                                               │
        │  ⚠️ HUMAN DECISION REQUIRED                  │
        │  auto_apply: false (ALWAYS)                  │
        └──────────────────────────────────────────────┘
    """

    def package(self, conflict: Dict, context: Dict = None) -> Dict:
        """
        Create a ConflictPackage for human review.
        
        Args:
            conflict: Detected conflict from ConflictDetector
            context: Additional context (ISP profile data, governance levels, etc.)
        """
        now = datetime.now(timezone.utc)
        
        package = {
            "package_type": "CONFLICT_PACKAGE",
            "package_version": "1.0.0",
            "conflict_id": conflict.get("conflict_id", f"CONF-{now.strftime('%Y%m%d%H%M%S')}"),
            "conflict_type": conflict.get("type"),
            "conflict_severity": conflict.get("severity"),
            "assembled_at": now.isoformat(),
            
            # The two positions — presented with EQUAL WEIGHT
            "position_a": self._format_position(conflict.get("pillar_a", {}), "A"),
            "position_b": self._format_position(conflict.get("pillar_b", {}), "B"),
            
            # What they disagree about
            "common_subject": conflict.get("common_subject", ""),
            "isp_context": self._get_isp_context(conflict.get("isp_id"), context),
            
            # Impact analysis — what happens if human chooses A vs B
            "impact_analysis": self._analyze_impact(conflict),
            
            # Resolution options (NOT recommendations — just options)
            "resolution_options": self._generate_options(conflict),
            
            # Constitutional guarantees
            "constitutional": {
                "I1_sovereignty": "HUMAN decides which position prevails",
                "I2_non_opacity": "Both positions presented with full evidence",
                "I3_transparency": "No position is suppressed or weighted",
                "I9_no_autonomy": "Maestro will NEVER auto-resolve this conflict",
                "divergence_principle": "Conflict is governance working, not a system failure",
            },
            
            "auto_apply": False,
        }
        
        # Integrity hash
        package["integrity_hash"] = hashlib.sha256(
            json.dumps({k: v for k, v in package.items() if k != "integrity_hash"},
                       sort_keys=True, default=str).encode()
        ).hexdigest()
        
        return package

    def _format_position(self, pillar_data: Dict, label: str) -> Dict:
        """Format a pillar's position for equal presentation."""
        return {
            "label": f"Position {label}",
            "pillar": pillar_data.get("name", "unknown"),
            "pillar_role": self._get_pillar_role(pillar_data.get("name")),
            "finding_id": pillar_data.get("finding_id"),
            "position": pillar_data.get("position", {}),
            "strength": "This position reflects the pillar's domain expertise",
            "limitation": "This pillar cannot see the full governance picture alone",
        }

    def _get_pillar_role(self, pillar_name: str) -> str:
        roles = {
            "sentinela": "VERIFICATION — Validates compliance and detects violations",
            "isp-manager": "CREATION — Manages ISP profile structural integrity",
            "maestro": "RESOLUTION — Orchestrates but never decides",
        }
        return roles.get(pillar_name, "Unknown pillar")

    def _get_isp_context(self, isp_id: Optional[str], context: Dict = None) -> Dict:
        """Get ISP context for the conflict."""
        if not isp_id:
            return {"isp_id": None, "note": "No ISP context"}
        
        isp_library = Path("/opt/windi/isp")
        profile_path = isp_library / isp_id / "profile.json"
        
        if profile_path.exists():
            try:
                with open(profile_path) as f:
                    profile = json.load(f)
                return {
                    "isp_id": isp_id,
                    "institution": profile.get("institution", {}).get("name", isp_id),
                    "governance_level": profile.get("governance", {}).get("level", "UNKNOWN"),
                    "identity_license": profile.get("identity_license", {}).get("status", "unknown"),
                }
            except (json.JSONDecodeError, IOError):
                pass
        
        return {"isp_id": isp_id, "note": "Profile not accessible"}

    def _analyze_impact(self, conflict: Dict) -> Dict:
        """
        Analyze what happens if human chooses Position A vs Position B.
        This is ANALYSIS, not RECOMMENDATION.
        """
        conflict_type = conflict.get("type", "")
        
        if conflict_type == ConflictType.CONTRADICTION.value:
            return {
                "if_position_a_prevails": {
                    "action": f"{conflict['pillar_a']['name']} conclusion is adopted",
                    "consequence": "ISP may require modification to achieve compliance",
                    "affected_pillar": conflict.get("pillar_b", {}).get("name"),
                },
                "if_position_b_prevails": {
                    "action": f"{conflict['pillar_b']['name']} conclusion is adopted",
                    "consequence": "Compliance finding may be reclassified or dismissed",
                    "affected_pillar": conflict.get("pillar_a", {}).get("name"),
                },
                "if_neither": {
                    "action": "Both positions acknowledged, new governance rule created",
                    "consequence": "Policy update may be required to resolve domain ambiguity",
                },
            }
        elif conflict_type == ConflictType.ESCALATION_CASCADE.value:
            return {
                "cascade_risk": "Circular triggers between pillars can cause infinite loop",
                "recommended_circuit_breaker": "Human must break the cycle by addressing root cause",
                "root_cause_candidates": conflict.get("cascade_chain", []),
            }
        elif conflict_type == ConflictType.PRIORITY_COLLISION.value:
            return {
                "collision_risk": "Multiple severities for same target create ambiguous priority",
                "resolution_needed": "Human must establish which severity governs the response",
            }
        
        return {"note": "Standard conflict — human judgment required"}

    def _generate_options(self, conflict: Dict) -> List[Dict]:
        """
        Generate resolution options (NOT recommendations).
        Each option is equally weighted — the human chooses.
        """
        options = [
            {
                "option": "ADOPT_A",
                "description": f"Accept {conflict.get('pillar_a', {}).get('name', 'Pillar A')} position",
                "effect": "Position A becomes the governing conclusion",
            },
            {
                "option": "ADOPT_B",
                "description": f"Accept {conflict.get('pillar_b', {}).get('name', 'Pillar B')} position",
                "effect": "Position B becomes the governing conclusion",
            },
            {
                "option": "SYNTHESIZE",
                "description": "Create new position incorporating elements of both",
                "effect": "Human writes a new resolution that supersedes both",
            },
            {
                "option": "DEFER",
                "description": "Defer decision pending additional information",
                "effect": "SLA timer continues; escalation if not resolved by deadline",
            },
            {
                "option": "ESCALATE",
                "description": "Escalate to higher authority (Board / Vorstand)",
                "effect": "Conflict moves to escalation channel for senior decision",
            },
        ]
        
        # Add cascade-specific option
        if conflict.get("type") == ConflictType.ESCALATION_CASCADE.value:
            options.append({
                "option": "BREAK_CYCLE",
                "description": "Address root cause to break the escalation cascade",
                "effect": "Human identifies and resolves the originating finding",
            })
        
        return options


# ============================================================================
# CONFLICT RESOLVER (Records human decisions)
# ============================================================================

class ConflictResolver:
    """
    Records human decisions on institutional conflicts.
    
    The Resolver NEVER decides — it only RECORDS the human's choice
    and generates the forensic proof.
    """

    def __init__(self, state_db_path: Path = None):
        self.db_path = state_db_path or Path("/opt/windi/agents/maestro/state/maestro_state.db")

    def adjudicate(self, conflict_id: str, decision: str,
                   rationale: str, decided_by: str) -> Dict:
        """
        Record human adjudication of a conflict.
        
        Args:
            conflict_id: The conflict identifier
            decision: One of ADOPT_A, ADOPT_B, SYNTHESIZE, DEFER, ESCALATE, BREAK_CYCLE
            rationale: Human's reasoning for the decision
            decided_by: Who made the decision
        """
        now = datetime.now(timezone.utc)
        valid_decisions = {"ADOPT_A", "ADOPT_B", "SYNTHESIZE", "DEFER", "ESCALATE", "BREAK_CYCLE"}
        
        if decision not in valid_decisions:
            return {"error": f"Invalid decision '{decision}'. Valid: {valid_decisions}"}
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT status FROM institutional_conflicts WHERE conflict_id = ?",
                (conflict_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {"error": f"Conflict {conflict_id} not found"}
            if row[0] in ("ADJUDICATED", "IMPLEMENTED", "SEALED"):
                return {"error": f"Conflict {conflict_id} already {row[0]}"}
            
            conn.execute("""
                UPDATE institutional_conflicts
                SET status = 'ADJUDICATED', human_decision = ?, 
                    decision_rationale = ?, decided_by = ?, adjudicated_at = ?
                WHERE conflict_id = ?
            """, (decision, rationale, decided_by, now.isoformat(), conflict_id))
            conn.commit()
        
        result = {
            "conflict_id": conflict_id,
            "status": "ADJUDICATED",
            "decision": decision,
            "rationale": rationale,
            "decided_by": decided_by,
            "timestamp": now.isoformat(),
            "next_step": "IMPLEMENT decision and seal with Forensic Ledger",
            "auto_apply": False,
        }
        
        # Generate forensic receipt
        receipt_id = f"CONF-ADJ-{now.strftime('%Y%m%d-%H%M%S')}-{hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()[:8]}"
        result["receipt_id"] = receipt_id
        
        return result

    def seal(self, conflict_id: str, sealed_by: str) -> Dict:
        """Seal a resolved conflict in the Forensic Ledger."""
        now = datetime.now(timezone.utc)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM institutional_conflicts WHERE conflict_id = ?",
                (conflict_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {"error": f"Conflict {conflict_id} not found"}
            
            conflict = dict(row)
            if conflict["status"] not in ("ADJUDICATED", "IMPLEMENTED"):
                return {"error": f"Conflict must be ADJUDICATED before sealing, currently: {conflict['status']}"}
            
            conn.execute("""
                UPDATE institutional_conflicts
                SET status = 'SEALED', sealed_at = ?
                WHERE conflict_id = ?
            """, (now.isoformat(), conflict_id))
            conn.commit()
        
        # Build seal record
        seal = {
            "seal_type": "INSTITUTIONAL_CONFLICT_RESOLUTION",
            "conflict_id": conflict_id,
            "conflict_type": conflict["conflict_type"],
            "pillar_a": conflict["pillar_a"],
            "pillar_b": conflict["pillar_b"],
            "human_decision": conflict["human_decision"],
            "rationale": conflict["decision_rationale"],
            "decided_by": conflict["decided_by"],
            "sealed_by": sealed_by,
            "sealed_at": now.isoformat(),
            "integrity_hash": hashlib.sha256(
                json.dumps(conflict, sort_keys=True, default=str).encode()
            ).hexdigest(),
            "governance_cycle": "CONFLICT_RESOLVED",
            "auto_apply": False,
        }
        
        return seal

    def get_conflicts(self, status: str = None) -> List[Dict]:
        """List conflicts, optionally filtered by status."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                cursor = conn.execute(
                    "SELECT * FROM institutional_conflicts WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM institutional_conflicts ORDER BY created_at DESC"
                )
            return [dict(row) for row in cursor.fetchall()]

    def get_conflict(self, conflict_id: str) -> Optional[Dict]:
        """Get a specific conflict by ID."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM institutional_conflicts WHERE conflict_id = ?",
                (conflict_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None


# ============================================================================
# PUBLIC API — Used by MaestroAgent
# ============================================================================

class InstitutionalConflictProtocol:
    """
    Main entry point for the Institutional Conflict Protocol.
    
    Combines:
    - ConflictDetector: Finds conflicts between pillars
    - ConflictPackager: Presents conflicts for human review
    - ConflictResolver: Records human decisions
    
    Usage:
        protocol = InstitutionalConflictProtocol()
        
        # Detect conflicts
        conflicts = protocol.detect(sentinela_findings, isp_alerts)
        
        # Register and package for human
        for c in conflicts:
            registered = protocol.register(c)
            package = protocol.package(c)
            # → Send to Human Decision Hub
        
        # Record human decision
        protocol.adjudicate(conflict_id, "ADOPT_A", "rationale", "Human Dragon")
        
        # Seal in Forensic Ledger
        protocol.seal(conflict_id, "Human Dragon")
    """

    def __init__(self, state_db_path: Path = None):
        db = state_db_path or Path("/opt/windi/agents/maestro/state/maestro_state.db")
        self.detector = ConflictDetector(db)
        self.packager = ConflictPackager()
        self.resolver = ConflictResolver(db)

    def detect(self, sentinela_findings: List[Dict],
               isp_alerts: List[Dict]) -> List[Dict]:
        return self.detector.detect_contradictions(sentinela_findings, isp_alerts)

    def register(self, conflict: Dict) -> Dict:
        return self.detector.register_conflict(conflict)

    def package(self, conflict: Dict, context: Dict = None) -> Dict:
        return self.packager.package(conflict, context)

    def adjudicate(self, conflict_id: str, decision: str,
                   rationale: str, decided_by: str) -> Dict:
        return self.resolver.adjudicate(conflict_id, decision, rationale, decided_by)

    def seal(self, conflict_id: str, sealed_by: str) -> Dict:
        return self.resolver.seal(conflict_id, sealed_by)

    def list_conflicts(self, status: str = None) -> List[Dict]:
        return self.resolver.get_conflicts(status)

    def get_conflict(self, conflict_id: str) -> Optional[Dict]:
        return self.resolver.get_conflict(conflict_id)
