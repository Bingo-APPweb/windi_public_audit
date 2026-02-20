# WINDI Maestro — Capsule Module
"""
Core modules for Governance Orchestration:

- resolution_case_manager: Case lifecycle management
- routing_engine: Deterministic routing based on severity/invariants
- sla_tracker: SLA computation and breach detection
- human_ack_protocol: Human acknowledgment and decision recording

Principles:
- COORDINATION ONLY: Routes, never decides
- HUMAN-MEDIATED: All state transitions require human ACK
- DETERMINISTIC: Routing is rule-based, auditable
- ZERO-KNOWLEDGE: Only metadata, never document content
"""

__version__ = "1.0.0"

# Case Management
from .resolution_case_manager import (
    Case,
    new_case,
    compute_case_hash,
    case_hash,
    transition_case,
    load_case,
    save_case
)

# Routing
from .routing_engine import (
    load_routing_matrix,
    pick_route,
    explain_route,
    get_escalation_target,
    get_channel_config
)

# SLA Tracking
from .sla_tracker import (
    load_sla,
    load_sla_config,
    compute_deadlines,
    is_breached,
    get_sla_status,
    check_notification_threshold,
    get_breach_cases
)

# Human ACK Protocol
from .human_ack_protocol import (
    generate_nonce,
    make_ack_token,
    verify_ack_token,
    ack_record,
    validate_ack,
    check_dual_ack,
    create_decision_ack,
    create_escalation_ack
)

__all__ = [
    # Case Management
    "Case",
    "new_case",
    "compute_case_hash",
    "case_hash",
    "transition_case",
    "load_case",
    "save_case",
    # Routing
    "load_routing_matrix",
    "pick_route",
    "explain_route",
    "get_escalation_target",
    "get_channel_config",
    # SLA
    "load_sla",
    "load_sla_config",
    "compute_deadlines",
    "is_breached",
    "get_sla_status",
    "check_notification_threshold",
    "get_breach_cases",
    # ACK Protocol
    "generate_nonce",
    "make_ack_token",
    "verify_ack_token",
    "ack_record",
    "validate_ack",
    "check_dual_ack",
    "create_decision_ack",
    "create_escalation_ack"
]
