"""
W-WORKBENCH-001 — Workbench Efémero Governado
WINDI Publishing House · 2026

Ambiente de construção pré-identidade onde o utilizador cria antes de reclamar.
"""

import uuid
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ArtifactType(Enum):
    """Tipos de artefacto permitidos. v0: apenas DOCUMENT."""
    DOCUMENT = "document"
    # Futuro: PAGE, MEMORY, AGENT, UPLOAD


class SignalAction(Enum):
    """Acções registadas no log de sinais."""
    CREATE = "create"
    EDIT = "edit"
    DELETE = "delete"
    EXPORT = "export"
    IDLE = "idle"
    RETURN = "return"


class PatternType(Enum):
    """Padrões de construção inferidos. NUNCA identidade."""
    LEGAL = "legal"
    FINANCIAL = "financial"
    CREATIVE = "creative"
    RESEARCH = "research"
    ORGANIZATION = "organization"
    GENERAL = "general"  # confidence < 0.7


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Artifact:
    """Artefacto criado no workbench."""
    artifact_id: str
    type: ArtifactType
    title: str
    content: str = ""
    content_hash: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    word_count: int = 0

    def __post_init__(self):
        if not self.artifact_id:
            self.artifact_id = f"art_{uuid.uuid4().hex[:16]}"
        self._update_hash()

    def _update_hash(self):
        """Actualiza hash do conteúdo."""
        self.content_hash = f"sha256:{hashlib.sha256(self.content.encode()).hexdigest()}"
        self.word_count = len(self.content.split()) if self.content else 0

    def update_content(self, content: str):
        """Actualiza conteúdo e recalcula hash."""
        self.content = content
        self.updated_at = datetime.utcnow()
        self._update_hash()


@dataclass
class Signal:
    """Sinal de actividade para observação de padrões."""
    timestamp: datetime
    action: SignalAction
    artifact_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class Pattern:
    """Padrão de construção inferido."""
    pattern_id: str
    type: PatternType
    confidence: float
    detected_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.pattern_id:
            self.pattern_id = f"pat_{uuid.uuid4().hex[:8]}"
        # Regra: confidence < 0.7 → GENERAL
        if self.confidence < 0.7:
            self.type = PatternType.GENERAL


@dataclass
class Capability:
    """Capacidade oferecida ao utilizador (opt-in)."""
    capability_id: str
    name: str  # Human-friendly: "organizar cronologicamente"
    offered_at: datetime = field(default_factory=datetime.utcnow)
    accepted: bool = False
    accepted_at: Optional[datetime] = None

    def accept(self):
        """Utilizador aceita a capacidade."""
        self.accepted = True
        self.accepted_at = datetime.utcnow()


@dataclass
class ClaimState:
    """Estado de claim do workbench."""
    eligible: bool = False
    prompted: bool = False
    prompted_at: Optional[datetime] = None
    claimed: bool = False
    claimed_at: Optional[datetime] = None
    did: Optional[str] = None  # did:windi:... após claim


# ============================================================================
# WORKBENCH
# ============================================================================

class Workbench:
    """
    Ambiente efémero governado.

    Regras:
    - TTL: 72h sem actividade
    - Artefactos v0: apenas document
    - Padrões observam construção, nunca identidade
    - Capacidades são oferecidas, nunca impostas
    - Claim só quando existe valor
    """

    TTL_INACTIVITY_HOURS = 72

    def __init__(self, workbench_id: Optional[str] = None):
        self.workbench_id = workbench_id or f"wb_{uuid.uuid4().hex}"
        self.created_at = datetime.utcnow()
        self.last_activity = self.created_at
        self.expires_at = self._calculate_expiry()

        self.artifacts: list[Artifact] = []
        self.signals: list[Signal] = []
        self.patterns: list[Pattern] = []
        self.capabilities_offered: list[Capability] = []
        self.claim_state = ClaimState()
        self.export_count = 0

    def _calculate_expiry(self) -> datetime:
        """Calcula expiração baseada em última actividade."""
        return self.last_activity + timedelta(hours=self.TTL_INACTIVITY_HOURS)

    def _record_activity(self):
        """Regista actividade e actualiza expiração."""
        self.last_activity = datetime.utcnow()
        self.expires_at = self._calculate_expiry()

    def _log_signal(self, action: SignalAction, artifact_id: Optional[str] = None, metadata: dict = None):
        """Regista sinal de actividade."""
        self.signals.append(Signal(
            timestamp=datetime.utcnow(),
            action=action,
            artifact_id=artifact_id,
            metadata=metadata or {}
        ))
        self._record_activity()

    # ---- Artefactos ----

    def create_artifact(self, title: str, content: str = "") -> Artifact:
        """Cria novo artefacto (v0: apenas document)."""
        artifact = Artifact(
            artifact_id="",
            type=ArtifactType.DOCUMENT,
            title=title,
            content=content
        )
        self.artifacts.append(artifact)
        self._log_signal(SignalAction.CREATE, artifact.artifact_id)
        self._check_claim_eligibility()
        return artifact

    def edit_artifact(self, artifact_id: str, content: str) -> Optional[Artifact]:
        """Edita artefacto existente."""
        for artifact in self.artifacts:
            if artifact.artifact_id == artifact_id:
                artifact.update_content(content)
                self._log_signal(SignalAction.EDIT, artifact_id)
                self._check_claim_eligibility()
                return artifact
        return None

    def delete_artifact(self, artifact_id: str) -> bool:
        """Remove artefacto."""
        for i, artifact in enumerate(self.artifacts):
            if artifact.artifact_id == artifact_id:
                del self.artifacts[i]
                self._log_signal(SignalAction.DELETE, artifact_id)
                return True
        return False

    def export_artifact(self, artifact_id: str) -> Optional[dict]:
        """Exporta artefacto (incrementa contador)."""
        for artifact in self.artifacts:
            if artifact.artifact_id == artifact_id:
                self.export_count += 1
                self._log_signal(SignalAction.EXPORT, artifact_id)
                self._check_claim_eligibility()
                return {
                    "artifact_id": artifact.artifact_id,
                    "type": artifact.type.value,
                    "title": artifact.title,
                    "content": artifact.content,
                    "content_hash": artifact.content_hash,
                    "word_count": artifact.word_count,
                    "exported_at": datetime.utcnow().isoformat()
                }
        return None

    # ---- Claim ----

    def _check_claim_eligibility(self):
        """Verifica se claim pode ser oferecido."""
        if self.claim_state.claimed:
            return

        # Regra: 1+ artefacto com conteúdo + 3+ edições ou export
        has_artifact = any(a.content.strip() for a in self.artifacts)
        edit_count = sum(1 for s in self.signals if s.action == SignalAction.EDIT)

        self.claim_state.eligible = has_artifact and (edit_count >= 3 or self.export_count > 0)

    def prompt_claim(self) -> bool:
        """Oferece claim ao utilizador (se elegível)."""
        if not self.claim_state.eligible or self.claim_state.prompted:
            return False

        self.claim_state.prompted = True
        self.claim_state.prompted_at = datetime.utcnow()
        return True

    def complete_claim(self, did: str) -> bool:
        """Completa claim após DID Genesis."""
        if not self.claim_state.eligible:
            return False

        self.claim_state.claimed = True
        self.claim_state.claimed_at = datetime.utcnow()
        self.claim_state.did = did
        return True

    # ---- Capacidades ----

    def offer_capability(self, name: str) -> Capability:
        """Oferece capacidade ao utilizador (opt-in)."""
        cap = Capability(
            capability_id=f"cap_{uuid.uuid4().hex[:8]}",
            name=name
        )
        self.capabilities_offered.append(cap)
        return cap

    def accept_capability(self, capability_id: str) -> bool:
        """Utilizador aceita capacidade oferecida."""
        for cap in self.capabilities_offered:
            if cap.capability_id == capability_id:
                cap.accept()
                return True
        return False

    # ---- Estado ----

    def is_expired(self) -> bool:
        """Verifica se workbench expirou."""
        return datetime.utcnow() > self.expires_at

    def get_edit_count(self) -> int:
        """Conta edições totais."""
        return sum(1 for s in self.signals if s.action == SignalAction.EDIT)

    def should_offer_capabilities(self) -> bool:
        """Verifica se condições para oferecer capacidades estão cumpridas."""
        # Regra R5: 1+ artefacto + 3+ edições
        return len(self.artifacts) > 0 and self.get_edit_count() >= 3

    def to_dict(self) -> dict:
        """Serializa workbench para JSON."""
        return {
            "workbench_id": self.workbench_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ttl_policy": {
                "inactivity_hours": self.TTL_INACTIVITY_HOURS,
                "absolute_hours": None  # Pendente v1
            },
            "artifacts": [
                {
                    "artifact_id": a.artifact_id,
                    "type": a.type.value,
                    "title": a.title,
                    "content_hash": a.content_hash,
                    "created_at": a.created_at.isoformat(),
                    "updated_at": a.updated_at.isoformat(),
                    "word_count": a.word_count
                }
                for a in self.artifacts
            ],
            "signals": [
                {
                    "timestamp": s.timestamp.isoformat(),
                    "action": s.action.value,
                    "artifact_id": s.artifact_id,
                    "metadata": s.metadata
                }
                for s in self.signals
            ],
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "type": p.type.value,
                    "confidence": p.confidence,
                    "detected_at": p.detected_at.isoformat()
                }
                for p in self.patterns
            ],
            "capabilities_offered": [
                {
                    "capability_id": c.capability_id,
                    "name": c.name,
                    "offered_at": c.offered_at.isoformat(),
                    "accepted": c.accepted,
                    "accepted_at": c.accepted_at.isoformat() if c.accepted_at else None
                }
                for c in self.capabilities_offered
            ],
            "claim_state": {
                "eligible": self.claim_state.eligible,
                "prompted": self.claim_state.prompted,
                "prompted_at": self.claim_state.prompted_at.isoformat() if self.claim_state.prompted_at else None,
                "claimed": self.claim_state.claimed,
                "claimed_at": self.claim_state.claimed_at.isoformat() if self.claim_state.claimed_at else None,
                "did": self.claim_state.did
            },
            "export_count": self.export_count
        }


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Criar workbench
    wb = Workbench()
    print(f"Workbench criado: {wb.workbench_id}")
    print(f"Expira em: {wb.expires_at}")

    # Criar artefacto
    doc = wb.create_artifact("Meu primeiro documento", "Conteúdo inicial.")
    print(f"Artefacto criado: {doc.artifact_id}")

    # Editar 3x para atingir threshold
    wb.edit_artifact(doc.artifact_id, "Conteúdo editado v2.")
    wb.edit_artifact(doc.artifact_id, "Conteúdo editado v3.")
    wb.edit_artifact(doc.artifact_id, "Conteúdo final v4.")

    print(f"Edições: {wb.get_edit_count()}")
    print(f"Elegível para claim: {wb.claim_state.eligible}")
    print(f"Pode oferecer capacidades: {wb.should_offer_capabilities()}")

    # Exportar
    export = wb.export_artifact(doc.artifact_id)
    print(f"Exportado: {export['content_hash']}")

    # Serializar
    import json
    print(json.dumps(wb.to_dict(), indent=2))
