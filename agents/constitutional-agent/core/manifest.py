"""
WINDI Agent Initialization Manifest
======================================
A professional, auditable record of Agent activation.
Defines version, invariants loaded, policies active, mode, and ledger anchor.

This replaces any symbolic "initialization ritual" with something
that is auditable, professional, regulatory, and real.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional

from config import (
    AGENT_NAME, AGENT_VERSION, AGENT_PHASE,
    OperationalMode, FOUNDING_PRINCIPLE, PRAKTIKANT_PRINCIPLE,
    AGENT_CAN, AGENT_CANNOT, SUPPORTED_LANGUAGES,
)


@dataclass
class AgentManifest:
    """
    The Agent Initialization Manifest — generated at every Agent startup.
    
    This is the "birth certificate" of each Agent session:
    - What version is running
    - Which invariants are loaded
    - Which policies are active
    - What mode it's operating in
    - Cryptographic proof of configuration
    """
    
    # Identity
    agent_name: str = AGENT_NAME
    agent_version: str = AGENT_VERSION
    agent_phase: str = AGENT_PHASE
    node_id: str = ""
    
    # Configuration
    operational_mode: str = OperationalMode.ASSISTIVE.value
    invariants_loaded: List[str] = field(default_factory=lambda: [
        "I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9"
    ])
    policies_active: List[str] = field(default_factory=list)
    isp_profile: Optional[str] = None
    languages: List[str] = field(default_factory=lambda: SUPPORTED_LANGUAGES.copy())
    
    # Capabilities (declared, not assumed)
    capabilities: List[str] = field(default_factory=lambda: AGENT_CAN.copy())
    restrictions: List[str] = field(default_factory=lambda: AGENT_CANNOT.copy())
    
    # Activation record
    activated_at: float = field(default_factory=time.time)
    activated_by: str = "system"  # or human operator name
    
    # Principles (embedded in every manifest)
    founding_principle: str = FOUNDING_PRINCIPLE
    praktikant_principle: str = PRAKTIKANT_PRINCIPLE
    
    def config_hash(self) -> str:
        """
        Generate a deterministic hash of the Agent's configuration.
        This is the cryptographic proof that THIS specific configuration
        was active at THIS specific time.
        """
        config_payload = json.dumps({
            "agent_version": self.agent_version,
            "invariants_loaded": sorted(self.invariants_loaded),
            "policies_active": sorted(self.policies_active),
            "operational_mode": self.operational_mode,
            "isp_profile": self.isp_profile,
            "node_id": self.node_id,
        }, sort_keys=True)
        return hashlib.sha256(config_payload.encode()).hexdigest()
    
    def integrity_hash(self) -> str:
        """
        Full integrity hash including activation timestamp.
        Unique per session.
        """
        payload = json.dumps({
            "config_hash": self.config_hash(),
            "activated_at": self.activated_at,
            "activated_by": self.activated_by,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Export manifest as dictionary."""
        d = asdict(self)
        d["config_hash"] = self.config_hash()
        d["integrity_hash"] = self.integrity_hash()
        return d
    
    def to_json(self, indent: int = 2) -> str:
        """Export manifest as formatted JSON."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def save(self, path: str):
        """Save manifest to file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.to_json())
    
    def verify_invariants_complete(self) -> bool:
        """Verify all 9 invariants are loaded. I9 is MANDATORY."""
        required = {"I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9"}
        loaded = set(self.invariants_loaded)
        return required.issubset(loaded)
    
    def print_activation_log(self):
        """Print a human-readable activation log."""
        lines = [
            "═" * 60,
            f"  {self.agent_name}",
            f"  Version: {self.agent_version} | Phase: {self.agent_phase}",
            f"  Node: {self.node_id or 'NOT ASSIGNED'}",
            "─" * 60,
            f"  Mode: {self.operational_mode.upper()}",
            f"  Invariants: {', '.join(self.invariants_loaded)}",
            f"  I9 (Autonomy Prohibition): {'✅ LOADED' if 'I9' in self.invariants_loaded else '❌ MISSING'}",
            f"  Policies: {', '.join(self.policies_active) or 'none'}",
            f"  ISP Profile: {self.isp_profile or 'none'}",
            f"  Languages: {', '.join(self.languages)}",
            "─" * 60,
            f"  Config Hash:    {self.config_hash()[:16]}...",
            f"  Integrity Hash: {self.integrity_hash()[:16]}...",
            f"  Activated by:   {self.activated_by}",
            f"  Activated at:   {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.activated_at))}",
            "─" * 60,
            f'  "{self.founding_principle}"',
            "═" * 60,
        ]
        return "\n".join(lines)
