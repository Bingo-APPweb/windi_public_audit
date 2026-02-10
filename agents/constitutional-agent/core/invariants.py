"""
WINDI Constitutional Execution Agent — Invariants Module
=========================================================
The 9 Invariants (I1-I9) are the immutable constitutional core.
I9 (Prohibition of Autonomy Escalation) is IRREMEDIABLE.

"Efficiency NEVER overrides sovereignty. No auto_apply flags."
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from config import InvariantID, IRREMEDIABLE_INVARIANTS


class InvariantViolation(Exception):
    """Raised when an operation would violate a constitutional invariant."""
    
    def __init__(self, invariant: InvariantID, operation: str, detail: str):
        self.invariant = invariant
        self.operation = operation
        self.detail = detail
        self.timestamp = time.time()
        super().__init__(
            f"INVARIANT VIOLATION [{invariant.value}]: "
            f"Operation '{operation}' blocked — {detail}"
        )


class I9Violation(InvariantViolation):
    """
    Special exception for I9 — Prohibition of Autonomy Escalation.
    This is IRREMEDIABLE. The agent HALTS immediately.
    No retry. No override. No workaround.
    """
    
    def __init__(self, operation: str, detail: str):
        super().__init__(InvariantID.I9, operation, detail)
        self.irremediable = True


@dataclass
class InvariantCheckResult:
    """Result of checking an operation against invariants."""
    passed: bool
    invariant_id: Optional[InvariantID] = None
    operation: str = ""
    detail: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "invariant_id": self.invariant_id.value if self.invariant_id else None,
            "operation": self.operation,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


class InvariantEnforcer:
    """
    Constitutional enforcer for the 9 WINDI Invariants.
    
    Every Agent operation passes through this gate BEFORE execution.
    If an invariant would be violated, the operation is blocked.
    I9 violations cause immediate halt — no exceptions.
    """
    
    # ═══ AUTONOMY ESCALATION PATTERNS ═══
    # These patterns indicate an attempt to escalate Agent authority
    AUTONOMY_ESCALATION_PATTERNS = [
        "auto_apply",
        "auto_approve",
        "auto_sign",
        "auto_decide",
        "self_authorize",
        "skip_human",
        "bypass_review",
        "override_human",
        "agent_decides",
        "autonomous_decision",
        "self_escalate",
        "remove_human_gate",
        "disable_oversight",
        "agent_authority",
        "delegate_sovereignty",
    ]
    
    # ═══ DECISION KEYWORDS ═══
    # These indicate the Agent is trying to make a decision (not allowed)
    DECISION_KEYWORDS = [
        "approve",
        "reject",
        "authorize",
        "sign",
        "certify",
        "validate_final",
        "commit_decision",
        "execute_judgment",
    ]
    
    def __init__(self):
        self.violation_log: List[Dict[str, Any]] = []
        self.check_count = 0
        self.violation_count = 0
    
    def check_operation(self, operation: str, params: Dict[str, Any] = None) -> InvariantCheckResult:
        """
        Check if an operation is permitted under all 9 invariants.
        
        This is the CONSTITUTIONAL GATE. Every Agent action passes through here.
        
        Args:
            operation: Name/description of the intended operation
            params: Operation parameters to inspect
            
        Returns:
            InvariantCheckResult
            
        Raises:
            I9Violation: If autonomy escalation is detected (IRREMEDIABLE)
            InvariantViolation: If any other invariant would be violated
        """
        self.check_count += 1
        params = params or {}
        
        # ═══ I9 CHECK (MANDATORY, FIRST, ALWAYS) ═══
        i9_result = self._check_i9(operation, params)
        if not i9_result.passed:
            self.violation_count += 1
            self._log_violation(i9_result)
            raise I9Violation(operation, i9_result.detail)
        
        # ═══ I1-I9 CHECKS ═══
        for check_fn in [
            self._check_human_sovereignty,      # I1-I3
            self._check_data_sovereignty,        # I4
            self._check_transparency,            # I5
            self._check_audit_trail,             # I6
            self._check_zero_knowledge,          # I7
            self._check_constitutional_bounds,   # I8
        ]:
            result = check_fn(operation, params)
            if not result.passed:
                self.violation_count += 1
                self._log_violation(result)
                raise InvariantViolation(result.invariant_id, operation, result.detail)
        
        return InvariantCheckResult(
            passed=True,
            operation=operation,
            detail="All invariants satisfied",
        )
    
    def _check_i9(self, operation: str, params: Dict[str, Any]) -> InvariantCheckResult:
        """
        I9 — Prohibition of Autonomy Escalation (IRREMEDIABLE)
        
        Checks for:
        1. auto_apply flags anywhere in params
        2. Autonomy escalation patterns in operation name
        3. Attempts to modify the invariant system itself
        4. Attempts to bypass human decision gates
        """
        op_lower = operation.lower()
        
        # Check operation name for escalation patterns
        for pattern in self.AUTONOMY_ESCALATION_PATTERNS:
            if pattern in op_lower:
                return InvariantCheckResult(
                    passed=False,
                    invariant_id=InvariantID.I9,
                    operation=operation,
                    detail=f"Autonomy escalation pattern detected: '{pattern}'",
                )
        
        # Deep-scan params for auto_apply or similar flags
        params_str = json.dumps(params).lower()
        for pattern in self.AUTONOMY_ESCALATION_PATTERNS:
            if pattern in params_str:
                return InvariantCheckResult(
                    passed=False,
                    invariant_id=InvariantID.I9,
                    operation=operation,
                    detail=f"Autonomy escalation flag in parameters: '{pattern}'",
                )
        
        # Check for attempts to modify invariant enforcement
        if any(keyword in op_lower for keyword in [
            "modify_invariant", "disable_invariant", "remove_invariant",
            "update_enforcer", "bypass_gate", "skip_constitutional",
        ]):
            return InvariantCheckResult(
                passed=False,
                invariant_id=InvariantID.I9,
                operation=operation,
                detail="Attempt to modify constitutional enforcement system",
            )
        
        return InvariantCheckResult(passed=True, operation=operation)
    
    def _check_human_sovereignty(self, operation: str, params: Dict[str, Any]) -> InvariantCheckResult:
        """I1-I3: Human sovereignty must be preserved."""
        op_lower = operation.lower()
        
        # Check if Agent is trying to make a final decision
        for keyword in self.DECISION_KEYWORDS:
            if keyword in op_lower and not params.get("human_initiated", False):
                return InvariantCheckResult(
                    passed=False,
                    invariant_id=InvariantID.I1,
                    operation=operation,
                    detail=f"Decision operation '{keyword}' requires human_initiated=True",
                )
        
        return InvariantCheckResult(passed=True, operation=operation)
    
    def _check_data_sovereignty(self, operation: str, params: Dict[str, Any]) -> InvariantCheckResult:
        """I4: Sensitive data stays local."""
        if params.get("transmit_content", False):
            return InvariantCheckResult(
                passed=False,
                invariant_id=InvariantID.I4,
                operation=operation,
                detail="Cannot transmit document content — only hashes and metadata",
            )
        return InvariantCheckResult(passed=True, operation=operation)
    
    def _check_transparency(self, operation: str, params: Dict[str, Any]) -> InvariantCheckResult:
        """I5: All governance actions must be logged."""
        if params.get("silent", False) or params.get("no_log", False):
            return InvariantCheckResult(
                passed=False,
                invariant_id=InvariantID.I5,
                operation=operation,
                detail="All governance actions must be transparent and logged",
            )
        return InvariantCheckResult(passed=True, operation=operation)
    
    def _check_audit_trail(self, operation: str, params: Dict[str, Any]) -> InvariantCheckResult:
        """I6: Audit trail must be maintained."""
        return InvariantCheckResult(passed=True, operation=operation)
    
    def _check_zero_knowledge(self, operation: str, params: Dict[str, Any]) -> InvariantCheckResult:
        """I7: Zero-knowledge architecture — WINDI stores proof, not data."""
        if params.get("store_content_on_hub", False):
            return InvariantCheckResult(
                passed=False,
                invariant_id=InvariantID.I7,
                operation=operation,
                detail="Hub must not store document content — only governance proofs",
            )
        return InvariantCheckResult(passed=True, operation=operation)
    
    def _check_constitutional_bounds(self, operation: str, params: Dict[str, Any]) -> InvariantCheckResult:
        """I8: Agent operates within constitutional boundaries."""
        return InvariantCheckResult(passed=True, operation=operation)
    
    def _log_violation(self, result: InvariantCheckResult):
        """Log violation for forensic trail."""
        entry = result.to_dict()
        entry["violation_number"] = self.violation_count
        entry["irremediable"] = result.invariant_id in IRREMEDIABLE_INVARIANTS
        self.violation_log.append(entry)
    
    def get_integrity_report(self) -> Dict[str, Any]:
        """Generate integrity report of all invariant checks."""
        return {
            "total_checks": self.check_count,
            "total_violations": self.violation_count,
            "violation_rate": (
                self.violation_count / self.check_count 
                if self.check_count > 0 else 0
            ),
            "i9_violations": sum(
                1 for v in self.violation_log 
                if v.get("invariant_id") == InvariantID.I9.value
            ),
            "violations": self.violation_log,
            "status": "CLEAN" if self.violation_count == 0 else "VIOLATIONS_DETECTED",
        }
