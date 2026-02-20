"""
WINDI Proof Orchestration Layer
==================================
The Agent prepares "digital deeds" — the Hub acts as Notary.

The Agent is the Praktikant who prepares the escritura (deed).
The Hub is the Notar who attests and seals.
The Human is the authority who decides and signs.
"""

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class ProofType(Enum):
    GOVERNANCE_EVENT = "governance_event"
    DOCUMENT_ANALYSIS = "document_analysis"
    HUMAN_OVERRIDE = "human_override"
    COMPLIANCE_CHECK = "compliance_check"
    EXCEPTION_ESCALATION = "exception_escalation"


@dataclass
class VirtueReceipt:
    """
    WINDI Virtue Receipt — the governance proof unit.
    
    Contains: hash + categories + governance + decision + flags
    The receipt proves that a governance process occurred with integrity.
    It does NOT contain document content (zero-knowledge).
    """
    
    # Identity
    receipt_id: str = field(default_factory=lambda: f"VR-{uuid.uuid4().hex[:12].upper()}")
    proof_type: str = ProofType.GOVERNANCE_EVENT.value
    
    # Document fingerprint (NOT content)
    document_hash: str = ""
    
    # Categories (what, not content)
    categories: Dict[str, str] = field(default_factory=lambda: {
        "doc_type": "",       # CONTRACT, INVOICE, APPROVAL, etc.
        "impact_level": "",   # LOW, MED, HIGH, CRIT
        "value_range": "",    # R1-R5 (ranges, not values!)
        "domain": "",         # Finance, Legal, Operations, etc.
    })
    
    # Governance metadata
    governance: Dict[str, Any] = field(default_factory=lambda: {
        "sge_score": 0.0,
        "risk_level": "R0",
        "validation_passed": False,
        "rules_applied": [],
        "agent_version": "",
    })
    
    # Decision (the human part)
    decision: Dict[str, Any] = field(default_factory=lambda: {
        "action": "",           # approved, rejected, escalated, modified
        "role": "",             # Who decided (role, not person — privacy)
        "timestamp": 0.0,
        "ai_recommendation": "",  # What the Agent suggested
        "human_override": False,  # Did human override AI?
        "override_reason": None,
    })
    
    # Flags
    flags: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: float = field(default_factory=time.time)
    
    def compute_hash(self) -> str:
        """Compute the receipt's integrity hash."""
        payload = json.dumps({
            "receipt_id": self.receipt_id,
            "proof_type": self.proof_type,
            "document_hash": self.document_hash,
            "categories": self.categories,
            "governance": self.governance,
            "decision": self.decision,
            "flags": sorted(self.flags),
            "created_at": self.created_at,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        d = {
            "receipt_id": self.receipt_id,
            "receipt_hash": self.compute_hash(),
            "proof_type": self.proof_type,
            "document_hash": self.document_hash,
            "categories": self.categories,
            "governance": self.governance,
            "decision": self.decision,
            "flags": self.flags,
            "created_at": self.created_at,
        }
        return d
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class HumanEscalation:
    """
    Represents a decision point that MUST be escalated to a human.
    
    The Agent NEVER resolves exceptions autonomously.
    It prepares the context and waits.
    """
    
    def __init__(
        self,
        reason: str,
        context: Dict[str, Any],
        sge_score: float = 0.0,
        risk_level: str = "R3",
        suggested_actions: List[str] = None,
    ):
        self.escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        self.reason = reason
        self.context = context
        self.sge_score = sge_score
        self.risk_level = risk_level
        self.suggested_actions = suggested_actions or []
        self.created_at = time.time()
        self.resolved = False
        self.resolved_by = None
        self.resolution = None
    
    def resolve(self, resolved_by: str, resolution: str):
        """Mark escalation as resolved by a human."""
        self.resolved = True
        self.resolved_by = resolved_by
        self.resolution = resolution
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "escalation_id": self.escalation_id,
            "reason": self.reason,
            "context_hash": hashlib.sha256(
                json.dumps(self.context, default=str).encode()
            ).hexdigest(),
            "sge_score": self.sge_score,
            "risk_level": self.risk_level,
            "suggested_actions": self.suggested_actions,
            "created_at": self.created_at,
            "resolved": self.resolved,
            "resolved_by": self.resolved_by,
            "resolution": self.resolution,
        }


class ProofOrchestrator:
    """
    Orchestrates the preparation of governance proofs.
    
    The Praktikant prepares all the paperwork.
    The Notar (Hub) will attest.
    The Human decides what gets signed.
    """
    
    def __init__(self, node_id: str, agent_version: str = "1.0.0"):
        self.node_id = node_id
        self.agent_version = agent_version
        self.receipts: List[VirtueReceipt] = []
        self.escalations: List[HumanEscalation] = []
        self.pending_escalations: List[HumanEscalation] = []
    
    def prepare_receipt(
        self,
        document_hash: str,
        doc_type: str,
        impact_level: str,
        risk_level: str,
        sge_score: float,
        rules_applied: List[str] = None,
        domain: str = "",
        value_range: str = "",
        flags: List[str] = None,
    ) -> VirtueReceipt:
        """
        Prepare a Virtue Receipt for a governance event.
        
        The receipt is PREPARED, not finalized. It needs human decision
        before it becomes a complete governance proof.
        
        Returns:
            VirtueReceipt ready for human decision
        """
        receipt = VirtueReceipt(
            proof_type=ProofType.GOVERNANCE_EVENT.value,
            document_hash=document_hash,
            categories={
                "doc_type": doc_type,
                "impact_level": impact_level,
                "value_range": value_range,
                "domain": domain,
            },
            governance={
                "sge_score": sge_score,
                "risk_level": risk_level,
                "validation_passed": sge_score >= 0.7,
                "rules_applied": rules_applied or [],
                "agent_version": self.agent_version,
                "node_id": self.node_id,
            },
            decision={
                "action": "pending_human_decision",
                "role": "",
                "timestamp": 0.0,
                "ai_recommendation": self._generate_recommendation(risk_level, sge_score),
                "human_override": False,
                "override_reason": None,
            },
            flags=flags or [],
        )
        
        self.receipts.append(receipt)
        return receipt
    
    def escalate_to_human(
        self,
        reason: str,
        context: Dict[str, Any],
        sge_score: float = 0.0,
        risk_level: str = "R3",
    ) -> HumanEscalation:
        """
        Create a human escalation.
        
        The Agent CANNOT resolve this. It prepares context, suggests actions,
        and WAITS for human resolution.
        """
        escalation = HumanEscalation(
            reason=reason,
            context=context,
            sge_score=sge_score,
            risk_level=risk_level,
            suggested_actions=self._suggest_actions(risk_level),
        )
        
        self.escalations.append(escalation)
        self.pending_escalations.append(escalation)
        return escalation
    
    def finalize_receipt(
        self,
        receipt: VirtueReceipt,
        action: str,
        role: str,
        human_override: bool = False,
        override_reason: str = None,
    ) -> VirtueReceipt:
        """
        Finalize a receipt with human decision.
        
        This is called AFTER the human has decided.
        The Agent records the decision — it does not make it.
        """
        receipt.decision = {
            "action": action,
            "role": role,
            "timestamp": time.time(),
            "ai_recommendation": receipt.decision.get("ai_recommendation", ""),
            "human_override": human_override,
            "override_reason": override_reason,
        }
        
        return receipt
    
    def _generate_recommendation(self, risk_level: str, sge_score: float) -> str:
        """
        Generate an AI recommendation (suggestion only, never binding).
        
        This is what the Praktikant suggests — the Notar decides.
        """
        if risk_level in ("R4", "R5"):
            return "RECOMMEND: Detailed review required. High-risk indicators detected."
        elif risk_level == "R3":
            return "RECOMMEND: Review flagged items before proceeding."
        elif sge_score < 0.5:
            return "RECOMMEND: Low conformity score. Consider revision."
        else:
            return "RECOMMEND: Appears compliant. Standard review suggested."
    
    def _suggest_actions(self, risk_level: str) -> List[str]:
        """Suggest possible actions for human escalation."""
        base = ["Review document", "Request additional context"]
        
        if risk_level in ("R4", "R5"):
            base.extend([
                "Escalate to compliance officer",
                "Request legal review",
                "Flag for audit committee",
            ])
        elif risk_level == "R3":
            base.extend([
                "Review with senior officer",
                "Request clarification from author",
            ])
        
        return base
    
    def get_orchestration_stats(self) -> Dict[str, Any]:
        """Return orchestration statistics."""
        return {
            "total_receipts": len(self.receipts),
            "pending_decisions": sum(
                1 for r in self.receipts 
                if r.decision.get("action") == "pending_human_decision"
            ),
            "finalized": sum(
                1 for r in self.receipts 
                if r.decision.get("action") != "pending_human_decision"
            ),
            "total_escalations": len(self.escalations),
            "pending_escalations": len(self.pending_escalations),
            "resolved_escalations": sum(
                1 for e in self.escalations if e.resolved
            ),
            "human_overrides": sum(
                1 for r in self.receipts 
                if r.decision.get("human_override", False)
            ),
        }
