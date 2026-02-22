# /opt/windi/engine/wisdom/schema.py
# ═══════════════════════════════════════════════════════════════════
# WINDI Wisdom Protocol v0.1 — Schema Imutável
# "Se não cabe em 280, ainda não é essência."
#
# Convergência: Guardian × Architect × Witness × Human Dragon
# Data de Selagem: 2026-02-21
# Genesis Block: WB-INSP-00000000
# ═══════════════════════════════════════════════════════════════════
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Literal


# === TIPOS GOVERNADOS ===
Chamber = Literal["echo", "pattern", "archetype"]
Status = Literal["candidate", "deferred", "rejected", "sealed"]
I1Action = Literal["approve", "defer", "reject"]
RejectionClass = Literal["noise", "premature", "duplicate-pattern"]
Maturity = Literal["seed", "validated", "canonical", "legacy"]
Visibility = Literal["public", "internal", "restricted", "guardian-only"]
Situation = Literal["crisis", "audit", "design", "conflict", "milestone",
                     "operational", "strategic", "discovery"]

# === GOVERNANÇA SELADA (decisões do Human Dragon 2026-02-21) ===
ESSENCE_MAX_DEFAULT = 280    # compressão forçada = clareza
ESSENCE_MAX_EXCEPTION = 500  # só com justificativa humana explícita

TTL_DEFAULT_MINUTES_BY_CHAMBER: Dict[Chamber, int] = {
    "echo":      90,    # 1h30 — reacção imediata
    "pattern":   360,   # 6h   — ciclo de trabalho
    "archetype": 1440,  # 24h  — sedimentação profunda
}

# Shelf N1 domains (diretórios de blocos selados)
SHELF_N1_DOMAINS = [
    "governance",
    "infrastructure",
    "legal-compliance",
    "security-risk",
    "operations",
    "human-factors",
    "philosophy-ethics",
    "culture-language",
    "manifest-ledger",
]


def iso_now() -> str:
    """UTC timestamp sem microsegundos."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class EmergenceContext:
    """Contexto forense: onde e com quem nasceu este insight."""
    situation: str = "design"
    actors_involved: List[str] = field(default_factory=list)
    intensity: float = 0.5  # 0.0-1.0 — gravidade do momento


@dataclass
class OsmoticWeight:
    """Peso osmótico com memória de recorrência.
    
    new_weight = base + recurrence_bonus - staleness_decay
    
    recurrence_bonus: sobe se padrão reaparece em contextos distintos
    staleness_decay:  sobe se padrão reaparece no mesmo contexto trivial
    """
    base: float = 0.6
    recurrence_count: int = 0
    recurrence_bonus: float = 0.0
    staleness_decay: float = 0.0
    effective: float = 0.0

    def recompute(self) -> None:
        self.effective = max(0.0, min(1.0,
            self.base + self.recurrence_bonus - self.staleness_decay
        ))

    def apply_recurrence(self, distinct_context: bool = True) -> None:
        """Chamado quando candidato reemergir por mérito."""
        self.recurrence_count += 1
        if distinct_context:
            # contexto diferente = sinal forte
            self.recurrence_bonus = min(0.3, self.recurrence_bonus + 0.08)
        else:
            # mesmo contexto = pode ser ruído repetido
            self.recurrence_bonus = min(0.3, self.recurrence_bonus + 0.02)
        self.recompute()

    def apply_staleness(self, cycle_penalty: float = 0.05) -> None:
        """Chamado quando TTL expira sem decisão."""
        self.staleness_decay = min(0.4, self.staleness_decay + cycle_penalty)
        self.recompute()


@dataclass
class I1Decision:
    """Decisão soberana do Human Dragon.
    
    Três modos:
    - approve → sela como Wisdom Block
    - defer   → volta ao ciclo com flag de recorrência  
    - reject  → classifica (noise|premature|duplicate-pattern)
    
    reject não significa apagar — significa classificar.
    """
    action: Optional[I1Action] = None
    rejection_class: Optional[RejectionClass] = None
    decided_at: Optional[str] = None
    decided_by: str = "human_dragon"  # SEMPRE humano, NUNCA AI (I9)

    def seal_action(self, action: I1Action,
                    rejection_class: Optional[RejectionClass] = None) -> None:
        self.action = action
        self.rejection_class = rejection_class
        self.decided_at = iso_now()


@dataclass
class ShelfCoordinates:
    """N1-N5: o endereço do bloco na Prateleira de Sabedoria.
    
    N1 = Domain     (governance, infrastructure, ...)
    N2 = SubDomain  (guiding-principles, architecture, ...)
    N3 = Context    (crisis, design, milestone, ...)
    N4 = Maturity   (seed → validated → canonical → legacy)
    N5 = Visibility (public, internal, restricted, guardian-only)
    
    Sistema sugere. Human Dragon valida.
    """
    n1_domain: str = "philosophy-ethics"
    n2_subdomain: str = "guiding-principles"
    n3_context: str = "design"
    n4_maturity: Maturity = "seed"
    n5_visibility: Visibility = "internal"

    def to_dict(self) -> Dict[str, str]:
        return {
            "N1": self.n1_domain,
            "N2": self.n2_subdomain,
            "N3": self.n3_context,
            "N4": self.n4_maturity,
            "N5": self.n5_visibility,
        }


@dataclass
class WisdomBlockCandidate:
    """O átomo de sabedoria do WINDI Wisdom Protocol.
    
    Ciclo de vida:
    candidate → [deferred ↔ candidate]* → sealed | rejected
    
    "O átomo precisa estar estável antes do organismo crescer."
    """
    # === IDENTIDADE ===
    candidate_id: str
    origin_session: str
    origin_chamber: Chamber

    # === CONTEÚDO DESTILADO ===
    essence: str  # 280 chars padrão; 500 excepcional
    context_tags: List[str] = field(default_factory=list)
    source_fragments: int = 0

    # === CONTEXTO DE EMERGÊNCIA (forense) ===
    emergence_context: EmergenceContext = field(
        default_factory=lambda: EmergenceContext(situation="design"))

    # === PESO OSMÓTICO ===
    weight: OsmoticWeight = field(
        default_factory=lambda: OsmoticWeight(base=0.6))

    # === CICLO DE VIDA ===
    status: Status = "candidate"
    ttl_remaining: int = 0
    created_at: str = field(default_factory=iso_now)
    last_evaluated: str = field(default_factory=iso_now)
    cycle_count: int = 0

    # === DECISÃO I1 (soberania humana) ===
    i1_decision: I1Decision = field(default_factory=I1Decision)

    # === SELAGEM (só após approve) ===
    sealed_as: Optional[str] = None
    sha256: Optional[str] = None
    shelf: Optional[Dict[str, str]] = None

    def __post_init__(self) -> None:
        if self.ttl_remaining == 0:
            self.ttl_remaining = TTL_DEFAULT_MINUTES_BY_CHAMBER.get(
                self.origin_chamber, 360)
        self.weight.recompute()

    def validate_essence(self) -> None:
        n = len(self.essence)
        if n == 0:
            raise ValueError("essence cannot be empty")
        if n > ESSENCE_MAX_EXCEPTION:
            raise ValueError(
                f"essence too long: {n} chars (max {ESSENCE_MAX_EXCEPTION}). "
                f"Se não cabe em 280, ainda não é essência.")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
