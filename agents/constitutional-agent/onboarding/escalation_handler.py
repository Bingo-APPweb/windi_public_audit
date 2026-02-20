#!/usr/bin/env python3
"""
WINDI Human Escalation Handler v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The Praktikant's mechanism for stopping and asking the human.
Implements I9: Prohibition of Autonomy Escalation.

"Sistemas não perdem controle porque agentes falham.
 Sistemas perdem controle porque agentes têm tanto êxito
 que humanos param de verificar." — I9

This handler:
  1. Receives SGE findings
  2. Classifies urgency
  3. STOPS processing
  4. Presents findings to human
  5. WAITS for human decision
  6. Records decision in forensic ledger
  7. Proceeds ONLY with human authorization
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
from typing import Optional


class EscalationLevel(Enum):
    """Urgency levels for human escalation."""
    INFORMATIONAL = "INFO"       # R0-R1: FYI, no action needed
    ADVISORY = "ADVISORY"        # R2: Attention recommended
    REVIEW_REQUIRED = "REVIEW"   # R3: Human must review before proceeding
    ACTION_REQUIRED = "ACTION"   # R4: Human must decide
    CRITICAL_HALT = "HALT"       # R5: Processing blocked until human intervenes


class HumanDecision(Enum):
    """Possible human decisions after escalation."""
    APPROVE = "APPROVED"                # Human approves proceeding
    REJECT = "REJECTED"                 # Human rejects / blocks
    MODIFY = "MODIFIED"                 # Human modifies and approves
    DEFER = "DEFERRED"                  # Human defers decision
    OVERRIDE = "OVERRIDDEN"             # Human overrides agent recommendation
    ESCALATE_FURTHER = "ESCALATED"      # Human escalates to higher authority


class EscalationRecord:
    """A single escalation event with full forensic trail."""

    def __init__(self, sge_findings: dict, escalation_level: EscalationLevel):
        self.id = self._generate_id()
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.sge_findings = sge_findings
        self.escalation_level = escalation_level
        self.human_decision = None
        self.decision_timestamp = None
        self.decision_reason = None
        self.hash = None
        self._compute_hash()

    def _generate_id(self) -> str:
        ts = datetime.now(timezone.utc).strftime("%d%b%y-%H%M%S").upper()
        return f"ESC-W001-{ts}"

    def _compute_hash(self):
        payload = json.dumps({
            "id": self.id,
            "timestamp": self.timestamp,
            "level": self.escalation_level.value,
            "risk": self.sge_findings.get("risk_level"),
        }, sort_keys=True)
        self.hash = hashlib.sha256(payload.encode()).hexdigest()

    def record_decision(self, decision: HumanDecision, reason: str = ""):
        """Record the human's decision. This is the I9 moment."""
        self.human_decision = decision
        self.decision_timestamp = datetime.now(timezone.utc).isoformat()
        self.decision_reason = reason
        # Recompute hash with decision included
        payload = json.dumps({
            "id": self.id,
            "timestamp": self.timestamp,
            "decision": decision.value,
            "decision_ts": self.decision_timestamp,
            "reason": reason,
        }, sort_keys=True)
        self.hash = hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "escalation_id": self.id,
            "timestamp": self.timestamp,
            "escalation_level": self.escalation_level.value,
            "risk_level": self.sge_findings.get("risk_level"),
            "risk_score": self.sge_findings.get("risk_score"),
            "flags": self.sge_findings.get("flags", []),
            "human_decision": self.human_decision.value if self.human_decision else "PENDING",
            "decision_timestamp": self.decision_timestamp,
            "decision_reason": self.decision_reason,
            "hash": self.hash,
            "i9_compliant": True,
            "auto_apply": False,  # NEVER
        }


class EscalationHandler:
    """
    The core escalation mechanism.
    Maps SGE risk levels to escalation urgency.
    Manages the human decision workflow.
    """

    RISK_TO_ESCALATION = {
        "R0": EscalationLevel.INFORMATIONAL,
        "R1": EscalationLevel.INFORMATIONAL,
        "R2": EscalationLevel.ADVISORY,
        "R3": EscalationLevel.REVIEW_REQUIRED,
        "R4": EscalationLevel.ACTION_REQUIRED,
        "R5": EscalationLevel.CRITICAL_HALT,
    }

    def __init__(self, ledger_dir: str = "/opt/windi/agents/constitutional-agent/onboarding/ledger"):
        self.ledger_dir = Path(ledger_dir)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        self.pending_escalations = []

    def escalate(self, sge_findings: dict) -> EscalationRecord:
        """
        Create an escalation from SGE findings.
        This is where the Praktikant STOPS and asks.
        """
        risk_level = sge_findings.get("risk_level", "R0")
        esc_level = self.RISK_TO_ESCALATION.get(risk_level, EscalationLevel.REVIEW_REQUIRED)

        record = EscalationRecord(sge_findings, esc_level)
        self.pending_escalations.append(record)

        # Save to ledger immediately
        self._save_to_ledger(record)

        return record

    def resolve(self, escalation_id: str, decision: HumanDecision, reason: str = "") -> Optional[EscalationRecord]:
        """
        Record the human's decision for a pending escalation.
        This closes the I9 loop: human decided, agent proceeds.
        """
        for record in self.pending_escalations:
            if record.id == escalation_id:
                record.record_decision(decision, reason)
                self._save_to_ledger(record)
                self.pending_escalations.remove(record)
                return record
        return None

    def get_pending(self) -> list:
        """Return all pending escalations awaiting human decision."""
        return [r.to_dict() for r in self.pending_escalations]

    def _save_to_ledger(self, record: EscalationRecord):
        """Save escalation record to forensic ledger."""
        ledger_file = self.ledger_dir / f"escalation_{record.id}.json"
        with open(ledger_file, "w") as f:
            json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)

    def format_for_human(self, record: EscalationRecord) -> str:
        """
        Format escalation for human-readable display.
        Trilingual support (DE/EN/PT).
        """
        risk = record.sge_findings.get("risk_level", "R?")
        emoji = record.sge_findings.get("risk_emoji", "❓")
        score = record.sge_findings.get("risk_score", 0)
        flags = record.sge_findings.get("flags", [])

        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            f"║  🛡️  HUMAN ESCALATION — {record.escalation_level.value:40s} ║",
            "╠══════════════════════════════════════════════════════════════╣",
            f"║  Escalation ID : {record.id:42s} ║",
            f"║  Risk Level    : {emoji} {risk} (Score: {score}){'':>28s} ║",
            f"║  Timestamp     : {record.timestamp:42s} ║",
            "╠══════════════════════════════════════════════════════════════╣",
            "║  🐉 The Praktikant has STOPPED and awaits your decision.    ║",
            "║                                                             ║",
            "║  Options:                                                   ║",
            "║    [A] APPROVE  — Proceed with document                     ║",
            "║    [R] REJECT   — Block this document                       ║",
            "║    [M] MODIFY   — Modify and re-analyze                     ║",
            "║    [D] DEFER    — Defer decision                            ║",
            "║    [O] OVERRIDE — Override agent recommendation             ║",
            "║    [E] ESCALATE — Escalate to higher authority              ║",
            "╠══════════════════════════════════════════════════════════════╣",
            "║  I9: Efficiency NEVER overrides sovereignty.                ║",
            "║  "Humano decide. WINDI garante."                           ║",
            "╚══════════════════════════════════════════════════════════════╝",
        ]

        if flags:
            lines.insert(-3, f"║  Flags: {', '.join(flags):51s} ║")

        return "\n".join(lines)
