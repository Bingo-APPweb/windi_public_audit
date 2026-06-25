"""
VPSE · Provenance Module
========================
Regra Canónica 1 e 2 (I9 confirmado, sessão 2026-06-25):
  Nenhuma afirmação sai do VPSE sem carimbo de proveniência.
  Riscos e compliance questions NUNCA saem como verdade nua.

Aplicação de MÉTODO-MEMORIA-001:
  "A memória propõe, a fonte dispõe, o Humano decide."

Os três carimbos canónicos:
  [lido]          → derivado de fonte verificável presente no input/base
  [estimado]      → inferência do motor, plausível mas não confirmada
  [nao_verificado]→ asserção que requer verificação humana/externa antes de uso
"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


class Provenance(str, Enum):
    LIDO = "[lido]"
    ESTIMADO = "[estimado]"
    NAO_VERIFICADO = "[nao_verificado]"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class Claim:
    """
    Unidade atómica de afirmação do VPSE.
    NENHUM risco, compliance question ou achado pode existir fora desta forma.
    """
    content: str
    provenance: Provenance
    confidence: Confidence = Confidence.LOW
    source_hint: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        # Postura epistémica: um Claim sem proveniência é proibido por construção.
        if not isinstance(self.provenance, Provenance):
            raise ValueError(
                "VPSE_PROVENANCE_VIOLATION: todo Claim exige carimbo de proveniência. "
                "Verdade nua é proibida (Regra Canónica 2)."
            )
        # Asserções estimadas ou não-verificadas nunca podem alegar confiança HIGH.
        if self.provenance in (Provenance.ESTIMADO, Provenance.NAO_VERIFICADO):
            if self.confidence == Confidence.HIGH:
                self.confidence = Confidence.MEDIUM

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["provenance"] = self.provenance.value
        d["confidence"] = self.confidence.value
        # remove campos None para JSON limpo
        return {k: v for k, v in d.items() if v is not None}


def lido(content: str, confidence: Confidence = Confidence.HIGH,
         source_hint: Optional[str] = None, notes: Optional[str] = None) -> Claim:
    return Claim(content, Provenance.LIDO, confidence, source_hint, notes)


def estimado(content: str, confidence: Confidence = Confidence.MEDIUM,
             source_hint: Optional[str] = None, notes: Optional[str] = None) -> Claim:
    return Claim(content, Provenance.ESTIMADO, confidence, source_hint, notes)


def nao_verificado(content: str, confidence: Confidence = Confidence.LOW,
                   source_hint: Optional[str] = None, notes: Optional[str] = None) -> Claim:
    return Claim(content, Provenance.NAO_VERIFICADO, confidence, source_hint, notes)
