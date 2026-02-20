#!/usr/bin/env python3
"""
WINDI Compliance Agent - Identity License Auditor
==================================================

Audita a validade e conformidade da Identity License,
o documento que autoriza um agente AI a processar
documentos sob governanca WINDI.

A Identity License define:
- Quem pode processar (agent_id)
- O que pode processar (scope)
- Como pode processar (permissions)
- Ate quando (validity)
- Sob quais condicoes (constraints)

Status possiveis:
- authorized: Licenca valida e ativa
- model_only: Pode sugerir, nao executar
- pending: Aguardando aprovacao humana
- expired: Licenca expirou
- revoked: Licenca revogada por violacao

Principios:
- Zero-Knowledge: Trabalha com metadados da licenca
- Advisory Only: Reporta status, nao altera licencas
- Audit Trail: Registra todas as verificacoes
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum


class LicenseStatus(Enum):
    """Status da Identity License"""
    AUTHORIZED = "authorized"
    MODEL_ONLY = "model_only"
    PENDING = "pending"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


class AuditSeverity(Enum):
    """Severidade do finding de auditoria"""
    INFO = "info"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


@dataclass
class AuditFinding:
    """Finding individual de auditoria"""
    finding_id: str
    severity: AuditSeverity
    category: str
    description: str
    evidence: Dict
    recommendation: str


@dataclass
class IdentityLicenseAuditResult:
    """Resultado da auditoria de Identity License"""
    license_id: str
    agent_id: str
    current_status: LicenseStatus
    status_valid: bool
    scope_valid: bool
    temporal_valid: bool
    constraints_satisfied: bool
    findings: List[AuditFinding]
    critical_violations: int
    warnings: int
    recommendations: List[str]
    forensic_hash: str
    timestamp: str
    human_review_required: bool
    next_review_date: Optional[str]

    def to_dict(self) -> Dict:
        result = asdict(self)
        result["current_status"] = self.current_status.value
        result["findings"] = [
            {**asdict(f), "severity": f.severity.value}
            for f in self.findings
        ]
        return result


class IdentityLicenseAuditor:
    """
    Auditor de Identity License

    Verifica:
    1. Status da licenca (authorized, model_only, etc)
    2. Escopo de autorizacao (quais documentos/ISPs)
    3. Validade temporal (expiracao)
    4. Constraints especificas (limitacoes operacionais)
    5. Historico de violacoes
    """

    # Status que permitem operacao
    OPERATIONAL_STATUSES = {LicenseStatus.AUTHORIZED, LicenseStatus.MODEL_ONLY}

    # Status que requerem revisao humana
    REVIEW_REQUIRED_STATUSES = {
        LicenseStatus.PENDING,
        LicenseStatus.EXPIRED,
        LicenseStatus.SUSPENDED
    }

    # Status que bloqueiam operacao
    BLOCKED_STATUSES = {LicenseStatus.REVOKED}

    def __init__(self, policy_config: Optional[Dict] = None):
        """
        Inicializa o auditor.

        Args:
            policy_config: Configuracao de politicas de auditoria
        """
        self.policy = policy_config or self._default_policy()
        self.findings: List[AuditFinding] = []

    def _default_policy(self) -> Dict:
        """Politica padrao de auditoria"""
        return {
            "expiration_warning_days": 30,
            "max_scope_items": 100,
            "require_human_issuer": True,
            "require_explicit_constraints": True,
            "audit_frequency_days": 90
        }

    def audit(
        self,
        license_data: Dict,
        requested_action: Optional[str] = None,
        target_isp: Optional[str] = None,
        violation_history: Optional[List[Dict]] = None
    ) -> IdentityLicenseAuditResult:
        """
        Audita uma Identity License.

        Args:
            license_data: Dados da licenca a auditar
            requested_action: Acao que o agente quer executar
            target_isp: ISP alvo da operacao
            violation_history: Historico de violacoes do agente

        Returns:
            IdentityLicenseAuditResult com findings e recomendacoes
        """
        self.findings = []

        license_id = license_data.get("license_id", "unknown")
        agent_id = license_data.get("agent_id", "unknown")

        # 1. Verificar status da licenca
        status = self._parse_status(license_data.get("status"))
        status_valid = self._audit_status(status, license_data)

        # 2. Verificar validade temporal
        temporal_valid = self._audit_temporal_validity(license_data)

        # 3. Verificar escopo de autorizacao
        scope_valid = self._audit_scope(
            license_data, requested_action, target_isp
        )

        # 4. Verificar constraints
        constraints_satisfied = self._audit_constraints(
            license_data, requested_action
        )

        # 5. Verificar historico de violacoes
        if violation_history:
            self._audit_violation_history(violation_history)

        # 6. Verificar issuer
        self._audit_issuer(license_data)

        # Compilar resultados
        critical_violations = len([
            f for f in self.findings
            if f.severity == AuditSeverity.CRITICAL
        ])
        warnings = len([
            f for f in self.findings
            if f.severity == AuditSeverity.WARNING
        ])

        # Gerar recomendacoes
        recommendations = self._generate_recommendations()

        # Determinar se precisa revisao humana
        human_review = (
            status in self.REVIEW_REQUIRED_STATUSES or
            critical_violations > 0 or
            not all([status_valid, temporal_valid, scope_valid, constraints_satisfied])
        )

        # Calcular proxima data de revisao
        next_review = self._calculate_next_review(license_data)

        # Gerar hash forense
        forensic_hash = self._generate_forensic_hash(
            license_id, agent_id, status, self.findings
        )

        return IdentityLicenseAuditResult(
            license_id=license_id,
            agent_id=agent_id,
            current_status=status,
            status_valid=status_valid,
            scope_valid=scope_valid,
            temporal_valid=temporal_valid,
            constraints_satisfied=constraints_satisfied,
            findings=self.findings,
            critical_violations=critical_violations,
            warnings=warnings,
            recommendations=recommendations,
            forensic_hash=forensic_hash,
            timestamp=datetime.now().isoformat(),
            human_review_required=human_review,
            next_review_date=next_review
        )

    def _parse_status(self, status_str: Optional[str]) -> LicenseStatus:
        """Converte string para LicenseStatus"""
        if not status_str:
            return LicenseStatus.UNKNOWN

        try:
            return LicenseStatus(status_str.lower())
        except ValueError:
            return LicenseStatus.UNKNOWN

    def _audit_status(self, status: LicenseStatus, license_data: Dict) -> bool:
        """Audita o status da licenca"""
        if status == LicenseStatus.UNKNOWN:
            self._add_finding(
                "IL-001",
                AuditSeverity.CRITICAL,
                "Status",
                "License status is UNKNOWN or invalid",
                {"raw_status": license_data.get("status")},
                "Verify license data integrity and source"
            )
            return False

        if status in self.BLOCKED_STATUSES:
            self._add_finding(
                "IL-002",
                AuditSeverity.CRITICAL,
                "Status",
                f"License is {status.value.upper()} - ALL OPERATIONS BLOCKED",
                {"status": status.value},
                "License must be reinstated by authorized human"
            )
            return False

        if status in self.REVIEW_REQUIRED_STATUSES:
            self._add_finding(
                "IL-003",
                AuditSeverity.WARNING,
                "Status",
                f"License status '{status.value}' requires human review",
                {"status": status.value},
                "Complete pending review before proceeding"
            )
            return False

        if status == LicenseStatus.MODEL_ONLY:
            self._add_finding(
                "IL-004",
                AuditSeverity.INFO,
                "Status",
                "License is MODEL_ONLY - can suggest but not execute",
                {"status": status.value},
                "Execution requires human confirmation"
            )

        return status in self.OPERATIONAL_STATUSES

    def _audit_temporal_validity(self, license_data: Dict) -> bool:
        """Audita validade temporal da licenca"""
        issued_at = license_data.get("issued_at")
        expires_at = license_data.get("expires_at")
        now = datetime.now()

        # Verificar data de emissao
        if not issued_at:
            self._add_finding(
                "IL-010",
                AuditSeverity.WARNING,
                "Temporal",
                "License has no issuance date",
                {},
                "Add issuance date for audit trail"
            )
        else:
            try:
                issued_dt = datetime.fromisoformat(issued_at.replace("Z", "+00:00"))
                if issued_dt > now:
                    self._add_finding(
                        "IL-011",
                        AuditSeverity.CRITICAL,
                        "Temporal",
                        "License issuance date is in the FUTURE",
                        {"issued_at": issued_at},
                        "Investigate potential tampering or clock skew"
                    )
                    return False
            except (ValueError, AttributeError):
                pass

        # Verificar expiracao
        if not expires_at:
            self._add_finding(
                "IL-012",
                AuditSeverity.WARNING,
                "Temporal",
                "License has no expiration date",
                {},
                "Set explicit expiration for security"
            )
            return True  # Sem expiracao definida, assumir valido

        try:
            expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))

            if expires_dt < now:
                self._add_finding(
                    "IL-013",
                    AuditSeverity.CRITICAL,
                    "Temporal",
                    f"License EXPIRED on {expires_at}",
                    {"expires_at": expires_at, "now": now.isoformat()},
                    "Renew license with authorized issuer"
                )
                return False

            # Aviso se expira em breve
            warning_days = self.policy["expiration_warning_days"]
            if expires_dt < now + timedelta(days=warning_days):
                days_left = (expires_dt - now).days
                self._add_finding(
                    "IL-014",
                    AuditSeverity.WARNING,
                    "Temporal",
                    f"License expires in {days_left} days",
                    {"expires_at": expires_at, "days_remaining": days_left},
                    "Schedule license renewal"
                )

            return True

        except (ValueError, AttributeError) as e:
            self._add_finding(
                "IL-015",
                AuditSeverity.WARNING,
                "Temporal",
                f"Invalid expiration date format: {e}",
                {"expires_at": expires_at},
                "Fix date format (ISO 8601)"
            )
            return True

    def _audit_scope(
        self,
        license_data: Dict,
        requested_action: Optional[str],
        target_isp: Optional[str]
    ) -> bool:
        """Audita escopo de autorizacao"""
        scope = license_data.get("scope", {})
        allowed_actions = set(scope.get("actions", []))
        allowed_isps = set(scope.get("isps", []))

        valid = True

        # Verificar se escopo esta definido
        if not allowed_actions and not allowed_isps:
            self._add_finding(
                "IL-020",
                AuditSeverity.WARNING,
                "Scope",
                "License has no defined scope - using default restrictions",
                {},
                "Define explicit scope for security"
            )

        # Verificar acao solicitada
        if requested_action:
            # Wildcard ou acao especifica
            if "*" not in allowed_actions and requested_action not in allowed_actions:
                self._add_finding(
                    "IL-021",
                    AuditSeverity.VIOLATION,
                    "Scope",
                    f"Action '{requested_action}' not authorized in license scope",
                    {
                        "requested": requested_action,
                        "allowed": list(allowed_actions)
                    },
                    "Request scope expansion or use authorized action"
                )
                valid = False

        # Verificar ISP alvo
        if target_isp:
            if "*" not in allowed_isps and target_isp not in allowed_isps:
                self._add_finding(
                    "IL-022",
                    AuditSeverity.VIOLATION,
                    "Scope",
                    f"ISP '{target_isp}' not authorized in license scope",
                    {
                        "requested": target_isp,
                        "allowed": list(allowed_isps)
                    },
                    "Request ISP authorization or use authorized ISP"
                )
                valid = False

        # Verificar tamanho do escopo (seguranca)
        max_items = self.policy["max_scope_items"]
        total_items = len(allowed_actions) + len(allowed_isps)
        if total_items > max_items:
            self._add_finding(
                "IL-023",
                AuditSeverity.WARNING,
                "Scope",
                f"Scope is overly broad ({total_items} items)",
                {"total_scope_items": total_items, "max_recommended": max_items},
                "Consider more restrictive scoping (principle of least privilege)"
            )

        return valid

    def _audit_constraints(
        self,
        license_data: Dict,
        requested_action: Optional[str]
    ) -> bool:
        """Audita constraints operacionais"""
        constraints = license_data.get("constraints", {})

        if not constraints and self.policy["require_explicit_constraints"]:
            self._add_finding(
                "IL-030",
                AuditSeverity.INFO,
                "Constraints",
                "No explicit constraints defined",
                {},
                "Define operational constraints for clarity"
            )

        valid = True

        # Verificar rate limiting
        rate_limit = constraints.get("max_operations_per_hour")
        if rate_limit and rate_limit < 1:
            self._add_finding(
                "IL-031",
                AuditSeverity.VIOLATION,
                "Constraints",
                "Rate limit is set to 0 - no operations allowed",
                {"rate_limit": rate_limit},
                "Increase rate limit or revoke license if intended"
            )
            valid = False

        # Verificar modo de operacao
        operation_mode = constraints.get("operation_mode")
        if operation_mode == "suspended":
            self._add_finding(
                "IL-032",
                AuditSeverity.WARNING,
                "Constraints",
                "License is in SUSPENDED operation mode",
                {"operation_mode": operation_mode},
                "Resume operations via authorized human"
            )
            valid = False

        # Verificar horario permitido
        allowed_hours = constraints.get("allowed_hours")
        if allowed_hours:
            current_hour = datetime.now().hour
            if current_hour < allowed_hours.get("start", 0) or \
               current_hour > allowed_hours.get("end", 23):
                self._add_finding(
                    "IL-033",
                    AuditSeverity.WARNING,
                    "Constraints",
                    f"Current hour ({current_hour}) outside allowed hours",
                    {
                        "current_hour": current_hour,
                        "allowed": allowed_hours
                    },
                    "Wait for allowed time window"
                )

        return valid

    def _audit_violation_history(self, violations: List[Dict]):
        """Audita historico de violacoes"""
        if not violations:
            return

        recent_violations = [
            v for v in violations
            if self._is_recent(v.get("timestamp"), days=90)
        ]

        if len(recent_violations) >= 3:
            self._add_finding(
                "IL-040",
                AuditSeverity.CRITICAL,
                "History",
                f"Agent has {len(recent_violations)} violations in last 90 days",
                {"violation_count": len(recent_violations)},
                "Recommend license suspension pending review"
            )
        elif recent_violations:
            self._add_finding(
                "IL-041",
                AuditSeverity.WARNING,
                "History",
                f"Agent has {len(recent_violations)} recent violation(s)",
                {"violation_count": len(recent_violations)},
                "Monitor agent behavior closely"
            )

    def _audit_issuer(self, license_data: Dict):
        """Audita o emissor da licenca"""
        issuer = license_data.get("issuer", {})
        issuer_type = issuer.get("type", "unknown")

        if self.policy["require_human_issuer"]:
            if issuer_type == "automated" or issuer_type == "ai":
                self._add_finding(
                    "IL-050",
                    AuditSeverity.WARNING,
                    "Issuer",
                    "License was issued by automated system, not human",
                    {"issuer_type": issuer_type},
                    "Human confirmation recommended for full authorization"
                )

        if not issuer.get("id"):
            self._add_finding(
                "IL-051",
                AuditSeverity.WARNING,
                "Issuer",
                "Issuer ID is missing",
                {},
                "Add issuer identification for audit trail"
            )

    def _add_finding(
        self,
        finding_id: str,
        severity: AuditSeverity,
        category: str,
        description: str,
        evidence: Dict,
        recommendation: str
    ):
        """Adiciona um finding de auditoria"""
        self.findings.append(AuditFinding(
            finding_id=finding_id,
            severity=severity,
            category=category,
            description=description,
            evidence=evidence,
            recommendation=recommendation
        ))

    def _is_recent(self, timestamp: Optional[str], days: int) -> bool:
        """Verifica se timestamp e recente"""
        if not timestamp:
            return False
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt > datetime.now() - timedelta(days=days)
        except (ValueError, AttributeError):
            return False

    def _generate_recommendations(self) -> List[str]:
        """Gera lista de recomendacoes baseada nos findings"""
        recommendations = []
        for finding in self.findings:
            if finding.severity in {AuditSeverity.CRITICAL, AuditSeverity.VIOLATION}:
                recommendations.append(f"[{finding.finding_id}] {finding.recommendation}")
        return recommendations

    def _calculate_next_review(self, license_data: Dict) -> Optional[str]:
        """Calcula data da proxima revisao"""
        last_review = license_data.get("last_audit_date")
        frequency = self.policy["audit_frequency_days"]

        if last_review:
            try:
                last_dt = datetime.fromisoformat(last_review.replace("Z", "+00:00"))
                next_dt = last_dt + timedelta(days=frequency)
                return next_dt.isoformat()
            except (ValueError, AttributeError):
                pass

        # Se nao tem revisao anterior, revisar em 30 dias
        return (datetime.now() + timedelta(days=30)).isoformat()

    def _generate_forensic_hash(
        self,
        license_id: str,
        agent_id: str,
        status: LicenseStatus,
        findings: List[AuditFinding]
    ) -> str:
        """Gera hash forense do resultado"""
        data = {
            "license_id": license_id,
            "agent_id": agent_id,
            "status": status.value,
            "findings_count": len(findings),
            "finding_ids": [f.finding_id for f in findings],
            "timestamp": datetime.now().isoformat()
        }
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


# ============================================
# EXEMPLO DE USO
# ============================================

if __name__ == "__main__":
    auditor = IdentityLicenseAuditor()

    # Exemplo de licenca
    sample_license = {
        "license_id": "LIC-2026-COMP-001",
        "agent_id": "windi://agent/compliance",
        "status": "authorized",
        "issued_at": "2026-01-15T10:00:00Z",
        "expires_at": "2027-01-15T10:00:00Z",
        "scope": {
            "actions": ["validate", "audit", "report"],
            "isps": ["windi://isp/bundesregierung", "windi://isp/bafin"]
        },
        "constraints": {
            "max_operations_per_hour": 1000,
            "operation_mode": "active"
        },
        "issuer": {
            "type": "human",
            "id": "admin@windi.tech",
            "name": "WINDI Platform Admin"
        }
    }

    result = auditor.audit(
        sample_license,
        requested_action="validate",
        target_isp="windi://isp/bundesregierung"
    )

    print("\n" + "="*60)
    print("WINDI Compliance Agent - Identity License Audit")
    print("="*60)
    print(f"License: {result.license_id}")
    print(f"Agent: {result.agent_id}")
    print(f"Status: {result.current_status.value.upper()}")
    print(f"\nValidation Results:")
    print(f"  Status Valid: {result.status_valid}")
    print(f"  Temporal Valid: {result.temporal_valid}")
    print(f"  Scope Valid: {result.scope_valid}")
    print(f"  Constraints Satisfied: {result.constraints_satisfied}")

    print(f"\nFindings: {len(result.findings)}")
    print(f"  Critical: {result.critical_violations}")
    print(f"  Warnings: {result.warnings}")

    for finding in result.findings:
        icon = "!" if finding.severity == AuditSeverity.CRITICAL else \
               "?" if finding.severity == AuditSeverity.WARNING else "i"
        print(f"  [{icon}] {finding.finding_id}: {finding.description}")

    print(f"\nHuman Review Required: {result.human_review_required}")
    print(f"Next Review: {result.next_review_date}")
