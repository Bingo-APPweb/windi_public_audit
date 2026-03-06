"""
WINDI Canonical Compliance Monitor
=====================================
Verifies that the local node implementation aligns with
the Genesis Node (W-00000000000000000000001) reference behavior.

Detects TECHNICAL deviations, not political or moral ones.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    DEVIATION = "deviation"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ComplianceCheck:
    """Single compliance check result."""
    check_id: str
    category: str
    description: str
    status: ComplianceStatus
    detail: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "category": self.category,
            "description": self.description,
            "status": self.status.value,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


class CanonicalComplianceMonitor:
    """
    Monitors the local node's compliance with the canonical specification.
    
    This is NOT about "ancestralidade" (ancestry) — it is about
    BASELINE CONFORMITY OF PROTOCOL.
    
    What it checks:
    - Invariant completeness (all 9 loaded)
    - Proof format compliance
    - SGE version alignment
    - Receipt structure validity
    - Policy consistency
    - Configuration drift from reference
    
    What it does NOT check:
    - Political or moral alignment
    - Business decisions
    - Human operator behavior
    """
    
    # ═══ CANONICAL REFERENCE VALUES ═══
    CANONICAL_INVARIANT_COUNT = 12
    CANONICAL_PROOF_VERSION = "WINDI-RECEIPT-v1"
    CANONICAL_SGE_LAYERS = 6
    CANONICAL_RISK_LEVELS = ["R0", "R1", "R2", "R3", "R4", "R5"]
    CANONICAL_REQUIRED_RECEIPT_FIELDS = [
        "hash", "categories", "governance", "decision", "timestamp",
    ]
    
    def __init__(self, node_id: str = ""):
        self.node_id = node_id
        self.checks: List[ComplianceCheck] = []
        self.last_scan_time: Optional[float] = None
    
    def run_full_scan(self, node_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a complete compliance scan against canonical reference.
        
        Args:
            node_config: Current node configuration dictionary
            
        Returns:
            Compliance report with all checks
        """
        self.checks = []
        self.last_scan_time = time.time()
        
        # Run all checks
        self._check_invariant_completeness(node_config)
        self._check_invariant_i9_presence(node_config)
        self._check_sge_configuration(node_config)
        self._check_proof_format(node_config)
        self._check_receipt_structure(node_config)
        self._check_agent_boundaries(node_config)
        self._check_zero_knowledge_compliance(node_config)
        self._check_human_gate_presence(node_config)
        
        return self._generate_report()
    
    def _check_invariant_completeness(self, config: Dict[str, Any]):
        """Verify all 9 invariants are loaded."""
        invariants = config.get("invariants", [])
        count = len(invariants)
        
        self.checks.append(ComplianceCheck(
            check_id="CCM-001",
            category="invariants",
            description="All 9 invariants loaded",
            status=(
                ComplianceStatus.COMPLIANT 
                if count == self.CANONICAL_INVARIANT_COUNT 
                else ComplianceStatus.CRITICAL
            ),
            detail=f"Found {count}/{self.CANONICAL_INVARIANT_COUNT} invariants",
        ))
    
    def _check_invariant_i9_presence(self, config: Dict[str, Any]):
        """Verify I9 (Autonomy Prohibition) is present and active."""
        invariants = config.get("invariants", [])
        i9_present = "I9" in invariants
        
        self.checks.append(ComplianceCheck(
            check_id="CCM-002",
            category="invariants",
            description="I9 (Prohibition of Autonomy Escalation) active",
            status=(
                ComplianceStatus.COMPLIANT 
                if i9_present 
                else ComplianceStatus.CRITICAL
            ),
            detail="I9 IRREMEDIABLE — must always be present",
        ))
    
    def _check_sge_configuration(self, config: Dict[str, Any]):
        """Verify SGE has canonical number of layers."""
        sge_layers = config.get("sge_layers", 0)
        
        self.checks.append(ComplianceCheck(
            check_id="CCM-003",
            category="sge",
            description=f"SGE configured with {self.CANONICAL_SGE_LAYERS} layers",
            status=(
                ComplianceStatus.COMPLIANT 
                if sge_layers == self.CANONICAL_SGE_LAYERS 
                else ComplianceStatus.DEVIATION
            ),
            detail=f"Found {sge_layers} layers, canonical is {self.CANONICAL_SGE_LAYERS}",
        ))
    
    def _check_proof_format(self, config: Dict[str, Any]):
        """Verify proof format matches canonical version."""
        proof_version = config.get("proof_version", "unknown")
        
        self.checks.append(ComplianceCheck(
            check_id="CCM-004",
            category="proofs",
            description="Proof format matches canonical version",
            status=(
                ComplianceStatus.COMPLIANT 
                if proof_version == self.CANONICAL_PROOF_VERSION 
                else ComplianceStatus.DEVIATION
            ),
            detail=f"Local: {proof_version}, Canonical: {self.CANONICAL_PROOF_VERSION}",
        ))
    
    def _check_receipt_structure(self, config: Dict[str, Any]):
        """Verify WINDI-RECEIPT contains all required fields."""
        receipt_fields = config.get("receipt_fields", [])
        missing = [f for f in self.CANONICAL_REQUIRED_RECEIPT_FIELDS if f not in receipt_fields]
        
        self.checks.append(ComplianceCheck(
            check_id="CCM-005",
            category="receipts",
            description="WINDI-RECEIPT contains all required fields",
            status=(
                ComplianceStatus.COMPLIANT 
                if not missing 
                else ComplianceStatus.DEVIATION
            ),
            detail=f"Missing fields: {missing}" if missing else "All fields present",
        ))
    
    def _check_agent_boundaries(self, config: Dict[str, Any]):
        """Verify Agent is configured as Praktikant, not sovereign."""
        agent_role = config.get("agent_role", "unknown")
        has_decision_authority = config.get("agent_decision_authority", False)
        
        self.checks.append(ComplianceCheck(
            check_id="CCM-006",
            category="agent",
            description="Agent configured as Constitutional Executor (not sovereign)",
            status=(
                ComplianceStatus.COMPLIANT 
                if not has_decision_authority 
                else ComplianceStatus.CRITICAL
            ),
            detail=f"Agent role: {agent_role}, Decision authority: {has_decision_authority}",
        ))
    
    def _check_zero_knowledge_compliance(self, config: Dict[str, Any]):
        """Verify zero-knowledge architecture is enforced."""
        stores_content = config.get("hub_stores_content", False)
        
        self.checks.append(ComplianceCheck(
            check_id="CCM-007",
            category="architecture",
            description="Zero-knowledge: Hub stores only proofs, not content",
            status=(
                ComplianceStatus.COMPLIANT 
                if not stores_content 
                else ComplianceStatus.CRITICAL
            ),
            detail="Client stores data, WINDI stores proof of virtue",
        ))
    
    def _check_human_gate_presence(self, config: Dict[str, Any]):
        """Verify human decision gates are configured."""
        has_human_gate = config.get("human_gate_enabled", True)
        
        self.checks.append(ComplianceCheck(
            check_id="CCM-008",
            category="sovereignty",
            description="Human decision gate enabled",
            status=(
                ComplianceStatus.COMPLIANT 
                if has_human_gate 
                else ComplianceStatus.CRITICAL
            ),
            detail="Human decides. Always.",
        ))
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate the full compliance report."""
        total = len(self.checks)
        compliant = sum(1 for c in self.checks if c.status == ComplianceStatus.COMPLIANT)
        deviations = sum(1 for c in self.checks if c.status == ComplianceStatus.DEVIATION)
        critical = sum(1 for c in self.checks if c.status == ComplianceStatus.CRITICAL)
        
        overall = ComplianceStatus.COMPLIANT
        if deviations > 0:
            overall = ComplianceStatus.DEVIATION
        if critical > 0:
            overall = ComplianceStatus.CRITICAL
        
        return {
            "node_id": self.node_id,
            "scan_timestamp": self.last_scan_time,
            "overall_status": overall.value,
            "summary": {
                "total_checks": total,
                "compliant": compliant,
                "deviations": deviations,
                "critical": critical,
                "compliance_score": round((compliant / total * 100) if total > 0 else 0, 1),
            },
            "checks": [c.to_dict() for c in self.checks],
            "canonical_reference": "W-00000000000000000000001 (Genesis & Canonical Node)",
        }
