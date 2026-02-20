"""
WINDI Constitutional Gate
===========================
Every Agent operation passes through this gate BEFORE execution.
The gate checks invariants, validates constitutional compliance,
and generates a Decision Trace Commitment for the audit trail.

"The template NEVER decides the level. The API decides. The template only manifests."
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable
from functools import wraps

from core.invariants import InvariantEnforcer, InvariantViolation, I9Violation


@dataclass
class DecisionTraceCommitment:
    """
    Cryptographic commitment to the process used for an AI-assisted step.
    
    What becomes immutable is the RECORD OF THE PROCESS,
    not the authority of the decision.
    """
    operation: str
    context_hash: str          # Hash of input context
    rules_applied: list        # Which rules/policies were applied
    model_version: str         # AI model version used
    agent_version: str         # Agent version
    parameters_hash: str       # Hash of operation parameters
    timestamp: float
    invariants_checked: bool
    result_hash: Optional[str] = None  # Hash of output (set after execution)
    human_override: bool = False
    human_override_reason: Optional[str] = None
    
    def to_hash(self) -> str:
        """Generate the commitment hash."""
        payload = json.dumps({
            "operation": self.operation,
            "context_hash": self.context_hash,
            "rules_applied": self.rules_applied,
            "model_version": self.model_version,
            "agent_version": self.agent_version,
            "parameters_hash": self.parameters_hash,
            "timestamp": self.timestamp,
            "invariants_checked": self.invariants_checked,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "commitment_hash": self.to_hash(),
            "operation": self.operation,
            "context_hash": self.context_hash,
            "rules_applied": self.rules_applied,
            "model_version": self.model_version,
            "agent_version": self.agent_version,
            "parameters_hash": self.parameters_hash,
            "timestamp": self.timestamp,
            "invariants_checked": self.invariants_checked,
            "result_hash": self.result_hash,
            "human_override": self.human_override,
            "human_override_reason": self.human_override_reason,
        }


class ConstitutionalGate:
    """
    The Constitutional Gate validates every Agent operation against:
    1. The 9 Invariants (I1-I9)
    2. Operational mode constraints
    3. Role boundaries (Agent CAN vs CANNOT)
    
    Every passage through the gate generates a DecisionTraceCommitment
    that is appended to the forensic trail.
    
    Principle: The Agent is a Praktikant — it prepares but never decides.
    """
    
    def __init__(self, agent_version: str = "1.0.0", model_version: str = "unknown"):
        self.enforcer = InvariantEnforcer()
        self.agent_version = agent_version
        self.model_version = model_version
        self.trace_log: list = []
        self.gate_count = 0
        self.blocked_count = 0
    
    def validate(
        self,
        operation: str,
        context: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        rules_applied: list = None,
    ) -> DecisionTraceCommitment:
        """
        Validate an operation through the Constitutional Gate.
        
        Args:
            operation: Name of the operation to validate
            context: Input context for the operation
            params: Operation parameters
            rules_applied: List of policy/rule names being applied
            
        Returns:
            DecisionTraceCommitment — the cryptographic commitment
            
        Raises:
            I9Violation: Autonomy escalation detected (IRREMEDIABLE)
            InvariantViolation: Other invariant would be violated
        """
        self.gate_count += 1
        context = context or {}
        params = params or {}
        rules_applied = rules_applied or []
        
        # Generate context and parameter hashes (zero-knowledge: we hash, not store)
        context_hash = hashlib.sha256(
            json.dumps(context, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        params_hash = hashlib.sha256(
            json.dumps(params, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        # ═══ INVARIANT CHECK ═══
        try:
            self.enforcer.check_operation(operation, params)
            invariants_ok = True
        except (I9Violation, InvariantViolation):
            self.blocked_count += 1
            raise
        
        # ═══ GENERATE COMMITMENT ═══
        commitment = DecisionTraceCommitment(
            operation=operation,
            context_hash=context_hash,
            rules_applied=rules_applied,
            model_version=self.model_version,
            agent_version=self.agent_version,
            parameters_hash=params_hash,
            timestamp=time.time(),
            invariants_checked=invariants_ok,
        )
        
        self.trace_log.append(commitment.to_dict())
        return commitment
    
    def record_result(self, commitment: DecisionTraceCommitment, result: Any):
        """Record the result hash after operation execution."""
        result_str = json.dumps(result, sort_keys=True, default=str)
        commitment.result_hash = hashlib.sha256(result_str.encode()).hexdigest()
    
    def record_human_override(
        self, 
        commitment: DecisionTraceCommitment, 
        reason: str = None
    ):
        """
        Record that a human overrode the Agent's suggestion.
        This is a VIRTUE — it proves human sovereignty is active.
        """
        commitment.human_override = True
        commitment.human_override_reason = reason
    
    def get_gate_stats(self) -> Dict[str, Any]:
        """Return gate statistics."""
        return {
            "total_passages": self.gate_count,
            "blocked": self.blocked_count,
            "passed": self.gate_count - self.blocked_count,
            "block_rate": (
                self.blocked_count / self.gate_count 
                if self.gate_count > 0 else 0
            ),
            "trace_entries": len(self.trace_log),
            "invariant_report": self.enforcer.get_integrity_report(),
        }


def constitutional_guard(operation_name: str = None, rules: list = None):
    """
    Decorator that wraps any Agent method with Constitutional Gate validation.
    
    Usage:
        @constitutional_guard("analyze_document", rules=["SGE_v1", "ISP_check"])
        def analyze(self, document):
            ...
    
    The decorated method will:
    1. Pass through the Constitutional Gate before execution
    2. Generate a DecisionTraceCommitment
    3. Block if any invariant would be violated
    4. Record the result hash after execution
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Determine operation name
            op_name = operation_name or func.__name__
            
            # Extract params from kwargs for invariant checking
            params = {k: v for k, v in kwargs.items() if k != "self"}
            
            # Pass through the Constitutional Gate
            commitment = self.gate.validate(
                operation=op_name,
                context={"args_count": len(args)},
                params=params,
                rules_applied=rules or [],
            )
            
            # Execute the actual operation
            result = func(self, *args, **kwargs)
            
            # Record the result
            self.gate.record_result(commitment, result)
            
            return result
        return wrapper
    return decorator
