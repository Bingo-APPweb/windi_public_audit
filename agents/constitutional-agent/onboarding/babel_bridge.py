#!/usr/bin/env python3
"""
WINDI BABEL Bridge v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━

Connects a4Desk BABEL (L1 edge) to the Constitutional Agent.
Every document event in BABEL flows through this bridge:

  a4Desk BABEL → BABEL Bridge → SGE Bridge → Escalation Handler → Human
                                    ↓
                              Virtue Receipt → Forensic Ledger

The bridge is EVENT-DRIVEN, not polling.
Document lifecycle events trigger agent analysis.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable
from enum import Enum


class DocumentEvent(Enum):
    """Events that trigger agent analysis."""
    CREATED = "doc.created"
    MODIFIED = "doc.modified"
    SEALED = "doc.sealed"
    SUBMITTED = "doc.submitted"
    EVIDENCE_ADDED = "doc.evidence_added"
    CLASSIFICATION_CHANGED = "doc.classification_changed"
    EXPORTED = "doc.exported"


class BABELBridge:
    """
    Bridge between a4Desk BABEL and the Constitutional Agent.

    Architecture:
        L1 (a4Desk) → BABELBridge → SGEBridge → EscalationHandler
                                          ↓
                                    VirtueReceipt → L3 (Forensic Ledger)
    """

    def __init__(self, agent_api_url: str = "http://127.0.0.1:8091",
                 sge_bridge=None, escalation_handler=None):
        self.agent_api_url = agent_api_url
        self.sge_bridge = sge_bridge
        self.escalation_handler = escalation_handler
        self.event_log = []
        self.listeners = {}

    def on_event(self, event_type: DocumentEvent, callback: Callable):
        """Register a listener for document events."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def emit(self, event_type: DocumentEvent, document_data: dict) -> dict:
        """
        Process a document event from a4Desk BABEL.
        This is the main entry point for L1 → Agent communication.
        """
        ts = datetime.now(timezone.utc).isoformat()
        doc_hash = hashlib.sha256(
            json.dumps(document_data, sort_keys=True).encode()
        ).hexdigest()

        event = {
            "event_id": f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{doc_hash[:8]}",
            "event_type": event_type.value,
            "timestamp": ts,
            "document_hash": doc_hash,
            "document_type": document_data.get("type", "UNKNOWN"),
            "isp_profile": document_data.get("isp_profile"),
            "processed": False,
            "sge_result": None,
            "escalation": None,
            "virtue_receipt": None,
        }

        # Step 1: SGE Analysis
        if self.sge_bridge:
            content = document_data.get("content", "")
            sge_result = self.sge_bridge.analyze(
                content,
                document_type=document_data.get("type", "UNKNOWN"),
                isp_profile=document_data.get("isp_profile"),
            )
            event["sge_result"] = sge_result

            # Step 2: Escalation if needed
            risk_level = sge_result.get("risk_level", "R0")
            risk_num = int(risk_level[1]) if risk_level.startswith("R") else 0

            if risk_num >= 3 and self.escalation_handler:
                esc_record = self.escalation_handler.escalate(sge_result)
                event["escalation"] = {
                    "id": esc_record.id,
                    "level": esc_record.escalation_level.value,
                    "status": "PENDING_HUMAN_DECISION",
                }
                event["processing_halted"] = True  # I9 enforcement
            else:
                event["processing_halted"] = False

        event["processed"] = True
        self.event_log.append(event)

        # Notify listeners
        for callback in self.listeners.get(event_type, []):
            try:
                callback(event)
            except Exception:
                pass

        return event

    def get_status(self) -> dict:
        """Return bridge operational status."""
        return {
            "bridge": "operational",
            "agent_api": self.agent_api_url,
            "sge_connected": self.sge_bridge is not None,
            "escalation_connected": self.escalation_handler is not None,
            "events_processed": len(self.event_log),
            "listeners": {k.value: len(v) for k, v in self.listeners.items()},
            "i9_enforced": True,
            "auto_apply": False,  # NEVER
        }

    def get_event_summary(self) -> dict:
        """Return summary of processed events."""
        if not self.event_log:
            return {"total": 0}

        escalated = sum(1 for e in self.event_log if e.get("escalation"))
        halted = sum(1 for e in self.event_log if e.get("processing_halted"))

        return {
            "total_events": len(self.event_log),
            "escalated": escalated,
            "halted_for_human": halted,
            "by_type": {},
            "latest_event": self.event_log[-1]["event_id"] if self.event_log else None,
        }
