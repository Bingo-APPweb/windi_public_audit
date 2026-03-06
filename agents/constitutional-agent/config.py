"""
WINDI Constitutional Execution Agent — Configuration
=====================================================
"AI processes. Human decides. WINDI guarantees."

All operational parameters for the WINDI Agent (Institutional Praktikant).
The Agent NEVER decides. The Agent NEVER signs. The Agent prepares, verifies, organizes.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum

# ═══ AGENT IDENTITY ═══

AGENT_NAME = "WINDI Constitutional Execution Agent"
AGENT_CODENAME = "Praktikant"
AGENT_VERSION = "1.0.0"
AGENT_PHASE = "Phase 2 — Clone Commissioning"

# ═══ INVARIANTS ═══

class InvariantID(Enum):
    I1 = "I1"
    I2 = "I2"
    I3 = "I3"
    I4 = "I4"
    I5 = "I5"
    I6 = "I6"
    I7 = "I7"
    I8 = "I8"
    I9 = "I9"   # Prohibition of Autonomy Escalation — IRREMEDIABLE
    I10 = "I10"
    I11 = "I11"
    I12 = "I12"  # Web of Proofs — IRREMEDIABLE

IRREMEDIABLE_INVARIANTS = [InvariantID.I9, InvariantID.I12]

# ═══ OPERATIONAL MODES ═══

class OperationalMode(Enum):
    ASSISTIVE = "assistive"        # Normal operation — suggest, never decide
    RESTRICTIVE = "restrictive"    # Heightened scrutiny — flag everything R3+
    AUDIT = "audit"                # Read-only — observe and log, no actions
    MAINTENANCE = "maintenance"    # System maintenance — admin operations only

# ═══ RISK LEVELS (SGE) ═══

class RiskLevel(Enum):
    R0 = "R0"  # Informational
    R1 = "R1"  # Low
    R2 = "R2"  # Medium
    R3 = "R3"  # High
    R4 = "R4"  # Critical
    R5 = "R5"  # Severe — mandatory human review

HUMAN_ESCALATION_THRESHOLD = RiskLevel.R3  # R3+ always escalates to human

# ═══ INSTITUTIONAL TYPES ═══

class InstitutionalType(Enum):
    BANK = "BANK"
    AUDITOR = "AUDITOR"
    REGULATOR = "REGULATOR"
    ENTERPRISE = "ENTERPRISE"
    NOTARY = "NOTARY"
    PUBLIC_BODY = "PUBLIC_BODY"

# ═══ PATHS ═══

@dataclass
class WindiPaths:
    base: str = "/opt/windi"
    engine: str = "/opt/windi/engine"
    clone_matrix: str = "/opt/windi/clone/matrix"
    agents: str = "/opt/windi/agents"
    isp: str = "/opt/windi/isp"
    backups: str = "/opt/windi/backups"
    logs: str = "/opt/windi/logs"
    data: str = "/opt/windi/data"
    
    # Agent-specific
    agent_home: str = "/opt/windi/agents/constitutional-agent"
    agent_manifests: str = "/opt/windi/agents/constitutional-agent/manifests"
    agent_traces: str = "/opt/windi/agents/constitutional-agent/traces"
    
    # Engine modules
    sge_engine: str = "/opt/windi/engine/semantic_governance.py"
    governance_api: str = "/opt/windi/engine/windi_governance_api.py"
    
    def ensure_dirs(self):
        """Create all required directories if they don't exist."""
        for attr_name in vars(self):
            path = getattr(self, attr_name)
            if isinstance(path, str) and path.startswith("/opt/windi"):
                os.makedirs(path, exist_ok=True)

PATHS = WindiPaths()

# ═══ PORTS ═══

PORTS = {
    "governance_api": 8080,
    "trust_bus": 8081,
    "gateway": 8082,
    "evolution_minimal": 8083,
    "masterarbeit": 8084,
    "babel": 8085,
    "app": 8086,
    "day_by_day": 8090,
    "cortex": 8889,
    "agent": 8091,  # NEW — Constitutional Agent API
}

# ═══ PRAKTIKANT ADOPTION PHASES ═══

class PraktikantPhase(Enum):
    ARRIVAL = "arrival"                # Phase 1: Enter as assistant
    OBSERVATION = "observation"        # Phase 2: Learn workflows
    ASSISTANCE = "assistance"          # Phase 3: Prepare before decisions
    TRUST = "trust"                    # Phase 4: Operators see value
    INDISPENSABILITY = "indispensability"  # Phase 5: Essential, never authority

# ═══ AGENT CAPABILITIES ═══

AGENT_CAN = [
    "Execute semantic analysis (SGE)",
    "Prepare proof structures",
    "Enforce spec compliance",
    "Format data for Hub anchorage",
    "Trigger exception workflows to humans",
    "Monitor canonical compliance",
]

AGENT_CANNOT = [
    "Override a human decision",
    "Sign on behalf of an operator",
    "Escalate its own authority (I9)",
    "Act as a parallel decision authority",
    "Resolve exceptions autonomously",
    "Make policy or governance judgments",
]

# ═══ DESIGN SYSTEM ═══

DESIGN = {
    "theme": "noir",
    "colors": {
        "background": "#0A0A0A",
        "surface": "#111111",
        "gold": "#C8A44E",
        "text": "#E8E8E8",
    },
    "fonts": {
        "display": "Bricolage Grotesque",
        "body": "Outfit",
        "mono": "JetBrains Mono",
    },
}

# ═══ LANGUAGES ═══

SUPPORTED_LANGUAGES = ["de", "en", "pt"]
DEFAULT_LANGUAGE = "de"

# ═══ PRINCIPLE ═══

FOUNDING_PRINCIPLE = "AI processes. Human decides. WINDI guarantees."
PRAKTIKANT_PRINCIPLE = (
    "The WINDI Agent is a permanent institutional Praktikant: "
    "it prepares, verifies, and organizes — "
    "but never decides and never signs."
)
AUTONOMY_PRINCIPLE = "Autonomous processing, sovereign decision."
