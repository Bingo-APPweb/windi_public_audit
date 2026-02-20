"""
WINDI Maestro Agent — Internal Modules
=======================================

Four modules that form the Maestro's nervous system:

1. DecisionRouter   — "O Maestro de Tráfego"
   Routes findings to the correct human decision-maker

2. SLAGuardian      — "O Relógio da Governança"  
   Monitors SLA compliance and triggers escalations

3. ResolutionAssembler — "O Preparador da Decisão"
   Assembles complete DecisionPackages for human review

4. ConflictProtocol — "O Coração Prático"
   Manages divergence between institutional pillars

"AI processes. Human decides. WINDI guarantees."
"""

from .decision_router import DecisionRouter
from .sla_guardian import SLAGuardian
from .resolution_assembler import ResolutionAssembler
from .conflict_protocol import InstitutionalConflictProtocol

__all__ = ["DecisionRouter", "SLAGuardian", "ResolutionAssembler", "InstitutionalConflictProtocol"]
