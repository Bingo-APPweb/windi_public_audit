#!/usr/bin/env python3
# WINDI Cortex - Metacognição Governada
# Porta: 8889

import os
import sqlite3
import hashlib
import requests
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, List, Dict
from flask import Flask, request, jsonify
from functools import wraps

CORTEX_PORT = 8889
TRUST_BUS_URL = "http://127.0.0.1:8081"
LEDGER_PATH = "/opt/windi/data/virtue_history.db"


class Phase(Enum):
    IDLE = "IDLE"
    CONTEXT_MODE = "CONTEXT_MODE"
    DESK_MODE = "DESK_MODE"
    HANDSHAKE_ACTIVE = "HANDSHAKE_ACTIVE"
    AWAITING_HUMAN = "AWAITING_HUMAN"
    REFLECTION = "REFLECTION"


VALID_TRANSITIONS = {
    Phase.IDLE: [Phase.CONTEXT_MODE],
    Phase.CONTEXT_MODE: [Phase.DESK_MODE, Phase.REFLECTION, Phase.HANDSHAKE_ACTIVE, Phase.IDLE],
    Phase.DESK_MODE: [Phase.AWAITING_HUMAN, Phase.CONTEXT_MODE, Phase.IDLE],
    Phase.HANDSHAKE_ACTIVE: [Phase.AWAITING_HUMAN, Phase.CONTEXT_MODE],
    Phase.REFLECTION: [Phase.AWAITING_HUMAN, Phase.CONTEXT_MODE],
    Phase.AWAITING_HUMAN: [Phase.CONTEXT_MODE, Phase.DESK_MODE]
}

class LedgerReader:
    def __init__(self, db_path):
        self._db_path = db_path
    
    def _execute(self, query, params=()):
        if not query.strip().upper().startswith("SELECT"):
            raise PermissionError("Only SELECT allowed")
        conn = sqlite3.connect(f"file:{self._db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        results = [dict(row) for row in cur.fetchall()]
        conn.close()
        return results
    
    def get_events(self, action=None, limit=50):
        if action:
            return self._execute(
                "SELECT * FROM ledger WHERE action = ? ORDER BY id DESC LIMIT ?",
                (action, limit))
        return self._execute("SELECT * FROM ledger ORDER BY id DESC LIMIT ?", (limit,))
    
    def get_pending_proposals(self):
        try:
            return self._execute("SELECT * FROM cortex_proposals WHERE status = 'AWAITING_HUMAN'")
        except:
            return []
    
    def health(self):
        try:
            self._execute("SELECT 1")
            return {"healthy": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}


class TrustBusClient:
    def __init__(self, base_url):
        self._url = base_url.rstrip("/")
    
    def emit(self, event_type, data):
        event = {
            "event_id": f"CORTEX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "actor": "windi-cortex",
            "action": event_type,
            "payload": str(data)
        }
        try:
            r = requests.post(f"{self._url}/event", json=event, timeout=5)
            return {"success": True, "response": r.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def health(self):
        try:
            r = requests.get(f"{self._url}/health", timeout=3)
            return {"reachable": True}
        except:
            return {"reachable": False}


@dataclass
class PhaseGuard:
    current: Phase = Phase.IDLE
    entered_at: datetime = field(default_factory=datetime.now)
    transition_count: int = 0
    _bus: TrustBusClient = None
    
    def set_bus(self, bus):
        self._bus = bus
    
    def can_go(self, target):
        return target in VALID_TRANSITIONS.get(self.current, [])
    
    def valid_targets(self):
        return [p.value for p in VALID_TRANSITIONS.get(self.current, [])]
    
    def is_blocked(self):
        return self.current == Phase.AWAITING_HUMAN
    
    def transition(self, target, reason="", session_id=""):
        if not self.can_go(target):
            return {"success": False, "error": f"Invalid: {self.current.value} -> {target.value}"}
        old = self.current
        self.current = target
        self.entered_at = datetime.now()
        self.transition_count += 1
        data = {"from": old.value, "to": target.value, "reason": reason, "session_id": session_id}
        if self._bus:
            result = self._bus.emit("CORTEX_PHASE_TRANSITION", data)
            if not result["success"]:
                self.current = old
                self.transition_count -= 1
                return {"success": False, "error": "CI1: Failed to record"}
        return {"success": True, **data}


class VolatileMemory:
    def __init__(self, phase):
        self._store = {}
        self._phase = phase
        self._session_id = hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16]
    
    @property
    def session_id(self):
        return self._session_id
    
    def store(self, key, value, source="unknown"):
        if self._phase.current in [Phase.IDLE, Phase.AWAITING_HUMAN]:
            return False
        self._store[key] = {"value": value, "source": source}
        return True
    
    def clear(self):
        n = len(self._store)
        self._store.clear()
        return n
    
    def reset(self):
        self._session_id = hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16]
        self._store.clear()
        return self._session_id

@dataclass
class Insight:
    insight_id: str
    observation: str
    source_records: List[str]
    session_id: str
    suggestion: str = None
    
    def validate_ci2(self):
        return not (self.suggestion and not self.source_records)
    
    def to_proposal(self):
        if not self.validate_ci2():
            raise ValueError("CI2: Needs source_records")
        return {
            "proposal_id": f"PROP-{self.insight_id}",
            "observation": self.observation,
            "suggestion": self.suggestion,
            "source_records": self.source_records,
            "session_id": self.session_id,
            "status": "AWAITING_HUMAN"
        }


class ReflectionEngine:
    def __init__(self, phase, memory, ledger):
        self._phase = phase
        self._memory = memory
        self._ledger = ledger
        self._insights = []
    
    def reflect_on_events(self, focus, action=None):
        if self._phase.current != Phase.REFLECTION:
            return None
        events = self._ledger.get_events(action=action, limit=30)
        self._memory.store(f"reflection_{focus}", events, "ledger")
        source_ids = [str(e.get("id", "")) for e in events]
        insight_id = hashlib.sha256(f"{focus}{datetime.now()}".encode()).hexdigest()[:12]
        insight = Insight(insight_id, f"Analisados {len(events)} eventos", source_ids, self._memory.session_id)
        self._insights.append(insight)
        return insight
    
    def get_insight(self, insight_id):
        for i in self._insights:
            if i.insight_id == insight_id:
                return i
        return None
    
    def list_insights(self):
        return [{"id": i.insight_id, "observation": i.observation} for i in self._insights]
    
    def clear(self):
        n = len(self._insights)
        self._insights.clear()
        return n


class WINDICortex:
    def __init__(self, ledger_path, bus_url):
        self.ledger = LedgerReader(ledger_path)
        self.bus = TrustBusClient(bus_url)
        self.phase = PhaseGuard()
        self.phase.set_bus(self.bus)
        self.memory = VolatileMemory(self.phase)
        self.reflection = ReflectionEngine(self.phase, self.memory, self.ledger)
        self._active = False
        self._proposals = {}
    
    def start_session(self):
        pending = self.ledger.get_pending_proposals()
        if pending:
            return {"success": False, "error": "CI4: Pending decisions", "count": len(pending)}
        session_id = self.memory.reset()
        result = self.phase.transition(Phase.CONTEXT_MODE, "Session start", session_id)
        if not result["success"]:
            return result
        self._active = True
        self.bus.emit("CORTEX_SESSION_STARTED", {"session_id": session_id})
        return {"success": True, "session_id": session_id, "phase": self.phase.current.value}
    
    def end_session(self):
        if self.phase.is_blocked():
            return {"success": False, "error": "Cannot end while AWAITING_HUMAN"}
        session_id = self.memory.session_id
        self.reflection.clear()
        self.memory.clear()
        self.phase.transition(Phase.IDLE, "Session end", session_id)
        self._active = False
        self.bus.emit("CORTEX_SESSION_ENDED", {"session_id": session_id})
        return {"success": True}
    
    def run_reflection(self, focus, action=None):
        if self.phase.current != Phase.REFLECTION:
            trans = self.phase.transition(Phase.REFLECTION, f"Reflect: {focus}", self.memory.session_id)
            if not trans["success"]:
                return trans
        insight = self.reflection.reflect_on_events(focus, action)
        return {"success": True, "insight_id": insight.insight_id, "observation": insight.observation}
    
    def submit_proposal(self, insight_id, suggestion):
        insight = self.reflection.get_insight(insight_id)
        if not insight:
            return {"success": False, "error": "Insight not found"}
        insight.suggestion = suggestion
        if not insight.validate_ci2():
            return {"success": False, "error": "CI2: Needs source_records"}
        proposal = insight.to_proposal()
        self._proposals[proposal["proposal_id"]] = proposal
        self.phase.transition(Phase.AWAITING_HUMAN, f"Proposal: {proposal['proposal_id']}", self.memory.session_id)
        self.bus.emit("CORTEX_PROPOSAL_SUBMITTED", proposal)
        return {"success": True, "proposal_id": proposal["proposal_id"], "status": "AWAITING_HUMAN"}
    
    def receive_decision(self, proposal_id, approved, notes="", human_id="unknown"):
        if not self.phase.is_blocked():
            return {"success": False, "error": "Not awaiting decision"}
        if proposal_id not in self._proposals:
            return {"success": False, "error": f"CI3: Unknown proposal"}
        proposal = self._proposals[proposal_id]
        proposal["status"] = "APPROVED" if approved else "REJECTED"
        target = Phase.DESK_MODE if approved else Phase.CONTEXT_MODE
        self.phase.transition(target, f"Decision: {'approved' if approved else 'rejected'}", self.memory.session_id)
        self.bus.emit("CORTEX_DECISION_RECEIVED", {"proposal_id": proposal_id, "approved": approved})
        return {"success": True, "proposal_id": proposal_id, "approved": approved}
    
    def state(self):
        return {"active": self._active, "session_id": self.memory.session_id, "phase": self.phase.current.value}
    
    def health(self):
        return {"healthy": self.ledger.health()["healthy"] and self.bus.health()["reachable"], "service": "windi-cortex"}


app = Flask(__name__)
cortex = None

def init():
    global cortex
    cortex = WINDICortex(LEDGER_PATH, TRUST_BUS_URL)

def local_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if request.remote_addr not in ['127.0.0.1', '::1']:
            return jsonify({"error": "I4: Local only"}), 403
        return f(*args, **kwargs)
    return wrapped

@app.route('/health')
def health():
    return jsonify(cortex.health())

@app.route('/state')
@local_only
def state():
    return jsonify(cortex.state())

@app.route('/session/start', methods=['POST'])
@local_only
def session_start():
    return jsonify(cortex.start_session())

@app.route('/session/end', methods=['POST'])
@local_only
def session_end():
    return jsonify(cortex.end_session())

@app.route('/reflection/run', methods=['POST'])
@local_only
def reflection_run():
    data = request.get_json() or {}
    return jsonify(cortex.run_reflection(data.get("focus", ""), data.get("action")))

@app.route('/proposal', methods=['POST'])
@local_only
def proposal():
    data = request.get_json() or {}
    return jsonify(cortex.submit_proposal(data.get("insight_id", ""), data.get("suggestion", "")))

@app.route('/decision', methods=['POST'])
@local_only
def decision():
    data = request.get_json() or {}
    return jsonify(cortex.receive_decision(data.get("proposal_id", ""), data.get("approved", False)))

if __name__ == "__main__":
    init()
    print(f"WINDI Cortex running on port {CORTEX_PORT}")
    app.run(host="127.0.0.1", port=CORTEX_PORT, debug=False)
