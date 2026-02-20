#!/usr/bin/env python3
"""
WINDI Compliance Agent - I9 Human Decision Verifier
====================================================

Verifica o Invariante I9: Nenhuma escalacao de autonomia
sem consentimento humano explicito.

Este e o invariante mais critico do WINDI porque garante:
- AI NUNCA toma decisoes finais sozinha
- Toda acao consequente tem um humano responsavel
- A cadeia de responsabilidade e rastreavel
- O principio "AI processes. Human decides." e respeitado

O que constitui uma "decisao humana valida":
1. Identificacao do decisor (quem)
2. Timestamp da decisao (quando)
3. Acao autorizada (o que)
4. Contexto da decisao (por que)
5. Assinatura ou confirmacao (prova)

Principios:
- CRITICO: Este modulo protege contra automacao descontrolada
- ZERO TOLERANCE: Qualquer falha aqui e bloqueante
- AUDIT TRAIL: Toda verificacao e registrada
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


class I9VerificationStatus(Enum):
    """Status da verificacao I9"""
    VERIFIED = "verified"           # Decisao humana confirmada
    MISSING = "missing"             # Sem registro de decisao
    INCOMPLETE = "incomplete"       # Registro parcial
    EXPIRED = "expired"             # Decisao antiga demais
    INVALID = "invalid"             # Registro invalido/corrompido
    DELEGATED = "delegated"         # Delegado, mas ainda humano
    AUTOMATED_VIOLATION = "automated_violation"  # Violacao: decisao automatizada


class DecisionType(Enum):
    """Tipo de decisao"""
    APPROVAL = "approval"           # Aprovacao de documento
    REJECTION = "rejection"         # Rejeicao de documento
    ESCALATION = "escalation"       # Escalacao para nivel superior
    DELEGATION = "delegation"       # Delegacao para outro humano
    OVERRIDE = "override"           # Override de recomendacao AI
    CONFIRMATION = "confirmation"   # Confirmacao de sugestao AI


@dataclass
class HumanDecisionRecord:
    """Registro de decisao humana"""
    decision_id: str
    decision_type: DecisionType
    actor_id: str
    actor_role: str
    timestamp: str
    action_authorized: str
    context: str
    ai_recommendation: Optional[str]
    override_reason: Optional[str]
    signature_hash: str
    delegation_chain: List[str] = field(default_factory=list)


@dataclass
class I9VerificationResult:
    """Resultado da verificacao I9"""
    document_id: str
    verification_status: I9VerificationStatus
    decision_record: Optional[HumanDecisionRecord]
    chain_of_responsibility: List[str]
    verification_checks: Dict[str, bool]
    critical_failures: List[str]
    warnings: List[str]
    forensic_hash: str
    timestamp: str
    human_accountability_confirmed: bool
    requires_immediate_action: bool

    def to_dict(self) -> Dict:
        result = asdict(self)
        result["verification_status"] = self.verification_status.value
        if self.decision_record:
            result["decision_record"]["decision_type"] = \
                self.decision_record.decision_type.value
        return result

    def to_forensic_record(self) -> Dict:
        """Gera registro para o Forensic Ledger"""
        return {
            "type": "i9_verification",
            "document_id": self.document_id,
            "status": self.verification_status.value,
            "human_accountable": self.human_accountability_confirmed,
            "chain_of_responsibility": self.chain_of_responsibility,
            "forensic_hash": self.forensic_hash,
            "timestamp": self.timestamp,
            "critical": self.requires_immediate_action
        }


class I9HumanDecisionVerifier:
    """
    Verificador do Invariante I9

    Garante que:
    1. Toda decisao consequente tem um humano responsavel
    2. O registro de decisao esta completo e valido
    3. A cadeia de responsabilidade e rastreavel
    4. Nenhuma decisao foi tomada por AI autonomamente

    CRITICO: Este e o guardiao principal do principio
    "AI processes. Human decides. WINDI guarantees."
    """

    # Campos obrigatorios no registro de decisao
    REQUIRED_DECISION_FIELDS = [
        "actor_id",
        "actor_role",
        "timestamp",
        "action_authorized",
        "signature_hash"
    ]

    # Roles que podem tomar decisoes
    AUTHORIZED_ROLES = [
        "controller",
        "data_protection_officer",
        "governance_officer",
        "compliance_officer",
        "authorized_delegate",
        "board_member",
        "legal_counsel"
    ]

    # Validade maxima de uma decisao (em horas)
    DECISION_VALIDITY_HOURS = 720  # 30 dias

    def __init__(self, policy_config: Optional[Dict] = None):
        """
        Inicializa o verificador I9.

        Args:
            policy_config: Configuracao de politicas
        """
        self.policy = policy_config or self._default_policy()

    def _default_policy(self) -> Dict:
        """Politica padrao"""
        return {
            "max_decision_age_hours": 720,
            "require_signature": True,
            "allow_delegation": True,
            "max_delegation_depth": 2,
            "require_context": True,
            "require_ai_recommendation_review": True
        }

    def verify(
        self,
        document_id: str,
        decision_data: Optional[Dict],
        ai_action_taken: Optional[str] = None,
        governance_metadata: Optional[Dict] = None
    ) -> I9VerificationResult:
        """
        Verifica se uma decisao humana valida existe para o documento.

        Args:
            document_id: ID do documento
            decision_data: Dados do registro de decisao humana
            ai_action_taken: Acao que a AI executou/quer executar
            governance_metadata: Metadados de governanca do documento

        Returns:
            I9VerificationResult com status e detalhes
        """
        checks = {}
        critical_failures = []
        warnings = []
        chain_of_responsibility = []

        # 1. Verificar se existe registro de decisao
        if not decision_data:
            return self._missing_decision_result(document_id, ai_action_taken)

        # 2. Verificar campos obrigatorios
        checks["required_fields"] = self._check_required_fields(decision_data)
        if not checks["required_fields"]:
            critical_failures.append("Missing required decision fields")

        # 3. Verificar identificacao do decisor
        actor_id = decision_data.get("actor_id")
        actor_role = decision_data.get("actor_role", "").lower()

        checks["actor_identified"] = bool(actor_id)
        if not checks["actor_identified"]:
            critical_failures.append("Decision actor not identified")

        # 4. Verificar se e realmente humano (nao AI)
        checks["human_actor"] = self._verify_human_actor(actor_id, actor_role)
        if not checks["human_actor"]:
            return self._automated_violation_result(
                document_id, actor_id, ai_action_taken
            )

        # 5. Verificar role autorizada
        checks["authorized_role"] = actor_role in self.AUTHORIZED_ROLES
        if not checks["authorized_role"]:
            warnings.append(f"Role '{actor_role}' not in standard authorized list")

        # 6. Verificar timestamp
        checks["timestamp_valid"] = self._verify_timestamp(decision_data)
        if not checks["timestamp_valid"]:
            critical_failures.append("Decision timestamp invalid or expired")

        # 7. Verificar assinatura
        if self.policy["require_signature"]:
            checks["signature_valid"] = self._verify_signature(decision_data)
            if not checks["signature_valid"]:
                critical_failures.append("Decision signature missing or invalid")

        # 8. Verificar contexto
        if self.policy["require_context"]:
            checks["context_provided"] = bool(decision_data.get("context"))
            if not checks["context_provided"]:
                warnings.append("Decision context not provided")

        # 9. Verificar cadeia de delegacao
        delegation_chain = decision_data.get("delegation_chain", [])
        if delegation_chain:
            checks["delegation_valid"] = self._verify_delegation_chain(
                delegation_chain
            )
            if not checks["delegation_valid"]:
                warnings.append("Delegation chain exceeds maximum depth")
            chain_of_responsibility = delegation_chain + [actor_id]
        else:
            chain_of_responsibility = [actor_id]

        # 10. Verificar se AI recommendation foi revisada
        if self.policy["require_ai_recommendation_review"]:
            ai_rec = decision_data.get("ai_recommendation")
            if ai_rec:
                checks["ai_recommendation_reviewed"] = bool(
                    decision_data.get("override_reason") or
                    decision_data.get("confirmation_note")
                )
                if not checks["ai_recommendation_reviewed"]:
                    warnings.append("AI recommendation not explicitly reviewed")

        # 11. Verificar coerencia com acao da AI
        if ai_action_taken:
            action_authorized = decision_data.get("action_authorized", "")
            checks["action_authorized"] = self._action_matches(
                action_authorized, ai_action_taken
            )
            if not checks["action_authorized"]:
                critical_failures.append(
                    f"AI action '{ai_action_taken}' not authorized by human decision"
                )

        # Construir registro de decisao
        decision_record = self._build_decision_record(decision_data)

        # Determinar status
        status = self._determine_status(checks, critical_failures)

        # Gerar hash forense
        forensic_hash = self._generate_forensic_hash(
            document_id, decision_record, status, checks
        )

        return I9VerificationResult(
            document_id=document_id,
            verification_status=status,
            decision_record=decision_record,
            chain_of_responsibility=chain_of_responsibility,
            verification_checks=checks,
            critical_failures=critical_failures,
            warnings=warnings,
            forensic_hash=forensic_hash,
            timestamp=datetime.now().isoformat(),
            human_accountability_confirmed=status == I9VerificationStatus.VERIFIED,
            requires_immediate_action=bool(critical_failures)
        )

    def _check_required_fields(self, decision_data: Dict) -> bool:
        """Verifica campos obrigatorios"""
        for field in self.REQUIRED_DECISION_FIELDS:
            if field not in decision_data or not decision_data[field]:
                return False
        return True

    def _verify_human_actor(self, actor_id: str, actor_role: str) -> bool:
        """
        Verifica se o ator e humano, nao AI.

        Heuristicas:
        - IDs com 'agent', 'bot', 'ai', 'auto' sao suspeitos
        - Roles com 'automated' sao suspeitos
        - Emails institucionais sao geralmente humanos
        """
        if not actor_id:
            return False

        actor_lower = actor_id.lower()

        # Padroes que indicam AI/automacao
        ai_patterns = [
            "agent", "bot", "auto", "system",
            "ai@", "automated", "machine", "script"
        ]

        for pattern in ai_patterns:
            if pattern in actor_lower:
                return False

        # Roles que indicam automacao
        if "automated" in actor_role or "system" in actor_role:
            return False

        # Email institucional e bom sinal
        if "@" in actor_id and "." in actor_id:
            return True

        return True

    def _verify_timestamp(self, decision_data: Dict) -> bool:
        """Verifica validade do timestamp"""
        timestamp = decision_data.get("timestamp")
        if not timestamp:
            return False

        try:
            decision_dt = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )
            now = datetime.now(decision_dt.tzinfo) if decision_dt.tzinfo else datetime.now()

            # Nao pode ser no futuro
            if decision_dt > now:
                return False

            # Nao pode ser muito antiga
            max_age = timedelta(hours=self.policy["max_decision_age_hours"])
            if now - decision_dt > max_age:
                return False

            return True

        except (ValueError, TypeError):
            return False

    def _verify_signature(self, decision_data: Dict) -> bool:
        """Verifica presenca de assinatura"""
        signature = decision_data.get("signature_hash")
        if not signature:
            return False

        # Verificar formato (SHA-256 = 64 hex chars)
        if len(signature) != 64:
            return False

        return all(c in '0123456789abcdef' for c in signature.lower())

    def _verify_delegation_chain(self, chain: List[str]) -> bool:
        """Verifica cadeia de delegacao"""
        max_depth = self.policy["max_delegation_depth"]
        return len(chain) <= max_depth

    def _action_matches(self, authorized: str, taken: str) -> bool:
        """Verifica se acao tomada corresponde a autorizada"""
        if not authorized or not taken:
            return False

        # Normalizacao
        auth_lower = authorized.lower().strip()
        taken_lower = taken.lower().strip()

        # Match exato
        if auth_lower == taken_lower:
            return True

        # Wildcard
        if auth_lower == "*" or auth_lower == "all":
            return True

        # Contem
        if taken_lower in auth_lower:
            return True

        return False

    def _build_decision_record(
        self, decision_data: Dict
    ) -> Optional[HumanDecisionRecord]:
        """Constroi registro de decisao estruturado"""
        try:
            decision_type_str = decision_data.get("decision_type", "confirmation")
            try:
                decision_type = DecisionType(decision_type_str.lower())
            except ValueError:
                decision_type = DecisionType.CONFIRMATION

            return HumanDecisionRecord(
                decision_id=decision_data.get("decision_id", "unknown"),
                decision_type=decision_type,
                actor_id=decision_data.get("actor_id", "unknown"),
                actor_role=decision_data.get("actor_role", "unknown"),
                timestamp=decision_data.get("timestamp", ""),
                action_authorized=decision_data.get("action_authorized", ""),
                context=decision_data.get("context", ""),
                ai_recommendation=decision_data.get("ai_recommendation"),
                override_reason=decision_data.get("override_reason"),
                signature_hash=decision_data.get("signature_hash", ""),
                delegation_chain=decision_data.get("delegation_chain", [])
            )
        except Exception:
            return None

    def _determine_status(
        self, checks: Dict[str, bool], critical_failures: List[str]
    ) -> I9VerificationStatus:
        """Determina status final da verificacao"""
        if critical_failures:
            if any("not authorized" in f for f in critical_failures):
                return I9VerificationStatus.INVALID
            if any("expired" in f.lower() for f in critical_failures):
                return I9VerificationStatus.EXPIRED
            return I9VerificationStatus.INCOMPLETE

        if all(checks.values()):
            return I9VerificationStatus.VERIFIED

        # Verificacoes parciais
        essential_checks = [
            checks.get("actor_identified", False),
            checks.get("human_actor", False),
            checks.get("timestamp_valid", False)
        ]

        if all(essential_checks):
            if checks.get("delegation_valid") is False:
                return I9VerificationStatus.DELEGATED
            return I9VerificationStatus.VERIFIED

        return I9VerificationStatus.INCOMPLETE

    def _missing_decision_result(
        self, document_id: str, ai_action: Optional[str]
    ) -> I9VerificationResult:
        """Resultado para decisao ausente"""
        forensic_hash = self._generate_forensic_hash(
            document_id, None, I9VerificationStatus.MISSING, {}
        )

        critical_msg = "NO HUMAN DECISION RECORDED"
        if ai_action:
            critical_msg += f" - AI attempted action: {ai_action}"

        return I9VerificationResult(
            document_id=document_id,
            verification_status=I9VerificationStatus.MISSING,
            decision_record=None,
            chain_of_responsibility=[],
            verification_checks={"decision_exists": False},
            critical_failures=[critical_msg],
            warnings=[],
            forensic_hash=forensic_hash,
            timestamp=datetime.now().isoformat(),
            human_accountability_confirmed=False,
            requires_immediate_action=True
        )

    def _automated_violation_result(
        self, document_id: str, actor_id: str, ai_action: Optional[str]
    ) -> I9VerificationResult:
        """Resultado para violacao de automacao"""
        forensic_hash = self._generate_forensic_hash(
            document_id, None, I9VerificationStatus.AUTOMATED_VIOLATION, {}
        )

        return I9VerificationResult(
            document_id=document_id,
            verification_status=I9VerificationStatus.AUTOMATED_VIOLATION,
            decision_record=None,
            chain_of_responsibility=[],
            verification_checks={"human_actor": False},
            critical_failures=[
                f"I9 VIOLATION: Decision made by automated actor '{actor_id}'",
                "No human in decision loop - GOVERNANCE BREACH"
            ],
            warnings=[],
            forensic_hash=forensic_hash,
            timestamp=datetime.now().isoformat(),
            human_accountability_confirmed=False,
            requires_immediate_action=True
        )

    def _generate_forensic_hash(
        self,
        document_id: str,
        decision_record: Optional[HumanDecisionRecord],
        status: I9VerificationStatus,
        checks: Dict[str, bool]
    ) -> str:
        """Gera hash forense"""
        data = {
            "document_id": document_id,
            "status": status.value,
            "checks": checks,
            "decision_id": decision_record.decision_id if decision_record else None,
            "actor_id": decision_record.actor_id if decision_record else None,
            "timestamp": datetime.now().isoformat()
        }
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


# ============================================
# EXEMPLO DE USO
# ============================================

if __name__ == "__main__":
    verifier = I9HumanDecisionVerifier()

    # Exemplo de decisao humana valida
    sample_decision = {
        "decision_id": "DEC-2026-0208-001",
        "decision_type": "approval",
        "actor_id": "maria.schmidt@bundesregierung.de",
        "actor_role": "controller",
        "timestamp": datetime.now().isoformat(),
        "action_authorized": "publish_document",
        "context": "Document reviewed and approved for public release",
        "ai_recommendation": "Recommend approval - SGE score 92",
        "confirmation_note": "Confirmed AI recommendation after review",
        "signature_hash": "a" * 64
    }

    result = verifier.verify(
        document_id="DOC-2026-BReg-001",
        decision_data=sample_decision,
        ai_action_taken="publish_document"
    )

    print("\n" + "="*60)
    print("WINDI Compliance Agent - I9 Human Decision Verification")
    print("="*60)
    print(f"Document: {result.document_id}")
    print(f"Status: {result.verification_status.value.upper()}")
    print(f"Human Accountability Confirmed: {result.human_accountability_confirmed}")

    if result.decision_record:
        print(f"\nDecision Record:")
        print(f"  Actor: {result.decision_record.actor_id}")
        print(f"  Role: {result.decision_record.actor_role}")
        print(f"  Type: {result.decision_record.decision_type.value}")
        print(f"  Action: {result.decision_record.action_authorized}")

    print(f"\nChain of Responsibility: {' -> '.join(result.chain_of_responsibility)}")

    print(f"\nVerification Checks:")
    for check, passed in result.verification_checks.items():
        icon = "v" if passed else "x"
        print(f"  [{icon}] {check}")

    if result.critical_failures:
        print(f"\nCRITICAL FAILURES:")
        for failure in result.critical_failures:
            print(f"  ! {failure}")

    if result.warnings:
        print(f"\nWarnings:")
        for warning in result.warnings:
            print(f"  ? {warning}")

    print(f"\nRequires Immediate Action: {result.requires_immediate_action}")
    print(f"Forensic Hash: {result.forensic_hash[:32]}...")


    # Teste de violacao
    print("\n" + "="*60)
    print("Testing VIOLATION scenario...")
    print("="*60)

    bad_decision = {
        "decision_id": "AUTO-001",
        "actor_id": "automation-bot@system",
        "actor_role": "automated_system",
        "timestamp": datetime.now().isoformat(),
        "action_authorized": "approve_all",
        "signature_hash": "b" * 64
    }

    violation_result = verifier.verify(
        document_id="DOC-VIOLATION-001",
        decision_data=bad_decision,
        ai_action_taken="approve_document"
    )

    print(f"Status: {violation_result.verification_status.value.upper()}")
    print(f"Human Accountability: {violation_result.human_accountability_confirmed}")
    for failure in violation_result.critical_failures:
        print(f"  ! {failure}")
