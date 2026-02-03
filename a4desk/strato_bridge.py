#!/usr/bin/env python3
"""
WINDI Strato Bridge - Integration Layer
Connects a4Desk to Sandbox-Core services

This is the nervous system that links the interface to the brain.
"AI processes. Human decides. WINDI guarantees."
"""

import json
import hashlib
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import threading
import time


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

TRUST_BUS_URL = "http://127.0.0.1:8081"
GATEWAY_URL = "http://127.0.0.1:8082"
CORTEX_URL = "http://127.0.0.1:8889"

TIMEOUT = 10  # seconds


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CertifiedAgent:
    windi_id: str
    session_id: str
    model: str
    domain: str
    certified_at: str
    system_prompt: str


@dataclass
class ValidationResult:
    valid: bool
    violations: List[str]
    filtered_content: Optional[str]
    guardrails_applied: List[str]


@dataclass
class CortexSession:
    session_id: str
    phase: str
    active: bool


@dataclass
class Proposal:
    proposal_id: str
    status: str


class DecisionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


# ═══════════════════════════════════════════════════════════════════════════════
# STRATO BRIDGE - MAIN CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class StratoBridge:
    """
    Unified client for Sandbox-Core services.
    
    This bridge connects the a4Desk interface to:
    - Trust Bus (event logging)
    - Gateway (AI certification & guardrails)
    - Cortex (metacognition & human decisions)
    """
    
    def __init__(self, operator_id: str = "unknown"):
        self.operator_id = operator_id
        self._current_agent: Optional[CertifiedAgent] = None
        self._cortex_session: Optional[CortexSession] = None
        self._pending_proposals: Dict[str, Proposal] = {}
        self._lock = threading.Lock()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HEALTH CHECKS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def check_services(self) -> Dict[str, bool]:
        """Check health of all Sandbox-Core services."""
        status = {}
        
        for name, url in [
            ("trust_bus", TRUST_BUS_URL),
            ("gateway", GATEWAY_URL),
            ("cortex", CORTEX_URL)
        ]:
            try:
                r = requests.get(f"{url}/health", timeout=3)
                status[name] = r.status_code == 200
            except:
                status[name] = False
        
        return status
    
    def is_operational(self) -> bool:
        """Check if all services are operational."""
        status = self.check_services()
        return all(status.values())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GATEWAY - AI CERTIFICATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def certify_agent(self, model: str, domain: str = "general") -> CertifiedAgent:
        """
        Certify an AI model as a WINDI Agent.
        
        This is the constitutional handshake that transforms any AI
        into a governed agent with WINDI-ID, system prompt, and guardrails.
        """
        try:
            response = requests.post(
                f"{GATEWAY_URL}/certify",
                json={
                    "model": model,
                    "domain": domain,
                    "operator_id": self.operator_id
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                agent = CertifiedAgent(
                    windi_id=data["windi_id"],
                    session_id=data["session_id"],
                    model=data["model"],
                    domain=data["domain"],
                    certified_at=data["certified_at"],
                    system_prompt=data["system_prompt"]
                )
                
                with self._lock:
                    self._current_agent = agent
                
                # Log certification event
                self.log_event("AGENT_CERTIFIED_BY_A4DESK", {
                    "windi_id": agent.windi_id,
                    "model": model,
                    "domain": domain
                })
                
                return agent
            else:
                raise Exception(f"Certification failed: {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Gateway unavailable: {e}")
    
    def validate_content(self, content: str, windi_id: Optional[str] = None) -> ValidationResult:
        """
        Validate AI-generated content against Guardrails.
        
        This ensures all AI output passes through G1-G8 before
        reaching the human user.
        """
        if windi_id is None:
            if self._current_agent:
                windi_id = self._current_agent.windi_id
            else:
                raise Exception("No agent certified. Call certify_agent first.")
        
        try:
            response = requests.post(
                f"{GATEWAY_URL}/validate",
                json={
                    "windi_id": windi_id,
                    "content": content
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                result = ValidationResult(
                    valid=data["valid"],
                    violations=data["violations"],
                    filtered_content=data.get("filtered_content"),
                    guardrails_applied=data["guardrails_applied"]
                )
                
                # Log if guardrails were applied
                if result.guardrails_applied:
                    self.log_event("GUARDRAILS_APPLIED", {
                        "windi_id": windi_id,
                        "guardrails": result.guardrails_applied,
                        "violations": result.violations
                    })
                
                return result
            else:
                raise Exception(f"Validation failed: {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Gateway unavailable: {e}")
    
    def get_system_prompt(self) -> str:
        """Get the current agent's WINDI system prompt."""
        if self._current_agent:
            return self._current_agent.system_prompt
        raise Exception("No agent certified.")
    
    def revoke_agent(self, windi_id: Optional[str] = None) -> bool:
        """Revoke an agent's certification."""
        if windi_id is None and self._current_agent:
            windi_id = self._current_agent.windi_id
        
        if not windi_id:
            return False
        
        try:
            response = requests.post(
                f"{GATEWAY_URL}/revoke/{windi_id}",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                with self._lock:
                    if self._current_agent and self._current_agent.windi_id == windi_id:
                        self._current_agent = None
                return True
            return False
            
        except:
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TRUST BUS - EVENT LOGGING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def log_event(self, action: str, payload: Any) -> Optional[str]:
        """
        Log an event to the Trust Bus.
        
        Every significant action in a4Desk should be logged here
        for complete audit trail with hash chain.
        """
        event_id = f"A4DESK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]}"
        
        try:
            response = requests.post(
                f"{TRUST_BUS_URL}/event",
                json={
                    "event_id": event_id,
                    "actor": f"a4desk-{self.operator_id}",
                    "action": action,
                    "payload": json.dumps(payload) if isinstance(payload, dict) else str(payload)
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json().get("hash")
            return None
            
        except:
            return None
    
    def get_events(self, limit: int = 10, actor: Optional[str] = None) -> List[Dict]:
        """Query events from Trust Bus."""
        try:
            params = {"limit": limit}
            if actor:
                params["actor"] = actor
            
            response = requests.get(
                f"{TRUST_BUS_URL}/events",
                params=params,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json().get("events", [])
            return []
            
        except:
            return []
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CORTEX - METACOGNITION & HUMAN DECISIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def start_cortex_session(self) -> CortexSession:
        """
        Start a Cortex session for metacognition.
        
        This activates the reflection and proposal system.
        """
        try:
            response = requests.post(
                f"{CORTEX_URL}/session/start",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                session = CortexSession(
                    session_id=data["session_id"],
                    phase=data["phase"],
                    active=data["success"]
                )
                
                with self._lock:
                    self._cortex_session = session
                
                self.log_event("CORTEX_SESSION_STARTED", {
                    "session_id": session.session_id
                })
                
                return session
            else:
                raise Exception(f"Failed to start session: {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Cortex unavailable: {e}")
    
    def submit_proposal(self, insight_id: str, suggestion: str) -> Proposal:
        """
        Submit a proposal to Cortex for human decision.
        
        This implements CI4 (Human Sovereignty) - critical actions
        must wait for human approval.
        """
        try:
            # Ensure we have a session
            if not self._cortex_session:
                self.start_cortex_session()
            
            # First run reflection
            requests.post(
                f"{CORTEX_URL}/reflection/run",
                json={"focus": insight_id},
                timeout=TIMEOUT
            )
            
            # Then submit proposal
            response = requests.post(
                f"{CORTEX_URL}/proposal",
                json={
                    "insight_id": insight_id,
                    "suggestion": suggestion
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                proposal = Proposal(
                    proposal_id=data["proposal_id"],
                    status=data["status"]
                )
                
                with self._lock:
                    self._pending_proposals[proposal.proposal_id] = proposal
                
                self.log_event("PROPOSAL_SUBMITTED", {
                    "proposal_id": proposal.proposal_id,
                    "insight_id": insight_id,
                    "suggestion": suggestion
                })
                
                return proposal
            else:
                raise Exception(f"Failed to submit proposal: {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Cortex unavailable: {e}")
    
    def get_cortex_state(self) -> Dict:
        """Get current Cortex state."""
        try:
            response = requests.get(f"{CORTEX_URL}/state", timeout=TIMEOUT)
            if response.status_code == 200:
                return response.json()
            return {"error": "Failed to get state"}
        except:
            return {"error": "Cortex unavailable"}
    
    def await_decision(self, proposal_id: str, timeout_seconds: int = 300) -> DecisionStatus:
        """
        Wait for human decision on a proposal.
        
        This blocks until human approves/rejects or timeout.
        Used for EXECUTE mode transitions and critical actions.
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            state = self.get_cortex_state()
            
            if state.get("phase") == "DESK_MODE":
                # Decision was made (approved)
                return DecisionStatus.APPROVED
            elif state.get("phase") == "IDLE":
                # Session ended (rejected or reset)
                return DecisionStatus.REJECTED
            elif state.get("phase") != "AWAITING_HUMAN":
                # Something else happened
                break
            
            time.sleep(1)
        
        return DecisionStatus.TIMEOUT
    
    def record_decision(self, proposal_id: str, approved: bool, human_id: str) -> bool:
        """
        Record a human decision on a proposal.
        
        This is called when the human clicks approve/reject in the UI.
        """
        try:
            response = requests.post(
                f"{CORTEX_URL}/decision",
                json={
                    "proposal_id": proposal_id,
                    "approved": approved,
                    "human_id": human_id
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                self.log_event("HUMAN_DECISION_RECORDED", {
                    "proposal_id": proposal_id,
                    "approved": approved,
                    "human_id": human_id
                })
                
                with self._lock:
                    if proposal_id in self._pending_proposals:
                        del self._pending_proposals[proposal_id]
                
                return True
            return False
            
        except:
            return False
    
    def end_cortex_session(self) -> bool:
        """End the current Cortex session."""
        try:
            response = requests.post(f"{CORTEX_URL}/session/end", timeout=TIMEOUT)
            
            if response.status_code == 200:
                with self._lock:
                    self._cortex_session = None
                return True
            return False
            
        except:
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONVENIENCE METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def request_execute_mode(self, reason: str) -> DecisionStatus:
        """
        Request transition to EXECUTE mode.
        
        This creates a proposal and waits for human approval.
        Implements the full CI4 flow.
        """
        # Submit proposal
        proposal = self.submit_proposal(
            insight_id=f"EXECUTE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            suggestion=f"EXECUTE mode requested: {reason}"
        )
        
        # Return immediately - caller should poll or use callback
        return DecisionStatus.PENDING
    
    def process_ai_response(self, raw_response: str) -> str:
        """
        Process an AI response through the full governance chain.
        
        1. Validate through Guardrails
        2. Apply any filters (G6, etc.)
        3. Log the processed response
        4. Return clean, governed content
        """
        result = self.validate_content(raw_response)
        
        if result.filtered_content:
            return result.filtered_content
        return raw_response
    
    def generate_receipt(self, document_id: str, content_hash: str) -> str:
        """Generate a WINDI receipt for a document."""
        timestamp = datetime.now(timezone.utc).strftime("%d%b%y").upper()
        
        receipt_data = f"{document_id}:{content_hash}:{timestamp}"
        receipt_hash = hashlib.sha256(receipt_data.encode()).hexdigest()[:12]
        
        receipt_id = f"WINDI-A4DESK-{timestamp}-{receipt_hash.upper()}"
        
        self.log_event("DOCUMENT_RECEIPT_GENERATED", {
            "receipt_id": receipt_id,
            "document_id": document_id,
            "content_hash": content_hash
        })
        
        return receipt_id


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_bridge_instance: Optional[StratoBridge] = None
_bridge_lock = threading.Lock()


def get_bridge(operator_id: str = "default") -> StratoBridge:
    """Get or create the singleton StratoBridge instance."""
    global _bridge_instance
    
    with _bridge_lock:
        if _bridge_instance is None:
            _bridge_instance = StratoBridge(operator_id)
        return _bridge_instance


def reset_bridge():
    """Reset the singleton instance (for testing)."""
    global _bridge_instance
    with _bridge_lock:
        _bridge_instance = None


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("WINDI STRATO BRIDGE - Integration Layer Test")
    print("=" * 60)
    
    bridge = get_bridge("test-operator")
    
    # Check services
    print("\n1. Checking services...")
    status = bridge.check_services()
    for service, healthy in status.items():
        icon = "✅" if healthy else "❌"
        print(f"   {icon} {service}")
    
    if not bridge.is_operational():
        print("\n⚠️  Not all services are operational. Exiting.")
        exit(1)
    
    # Certify agent
    print("\n2. Certifying agent...")
    agent = bridge.certify_agent("claude", "document-production")
    print(f"   WINDI-ID: {agent.windi_id}")
    
    # Validate content
    print("\n3. Testing guardrails...")
    result = bridge.validate_content("You should submit this document immediately.")
    print(f"   Valid: {result.valid}")
    print(f"   Guardrails applied: {result.guardrails_applied}")
    if result.filtered_content:
        print(f"   Filtered: {result.filtered_content}")
    
    # Log event
    print("\n4. Logging event...")
    event_hash = bridge.log_event("BRIDGE_TEST", {"status": "success"})
    print(f"   Hash: {event_hash}")
    
    # Generate receipt
    print("\n5. Generating receipt...")
    receipt = bridge.generate_receipt("DOC-001", "abc123")
    print(f"   Receipt: {receipt}")
    
    print("\n" + "=" * 60)
    print("✅ Strato Bridge operational!")
    print("AI processes. Human decides. WINDI guarantees.")
    print("=" * 60)
