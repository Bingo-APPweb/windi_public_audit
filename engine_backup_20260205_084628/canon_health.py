# engine/canon_health.py
# WINDI Canon Health Checker - Integrity and Freshness Monitor
# Status: PENDENTE | Prioridade: BAIXA
# "Canon envelhece. Revisão periódica é governança."

import hashlib
import yaml
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass 
class CanonHealthReport:
    """Relatório de saúde do Canon."""
    canon_version: str
    frozen_date: str
    age_days: int
    status: str              # "FRESH" | "AGING" | "REVIEW_RECOMMENDED" | "STALE" | "INVALID"
    integrity_valid: bool    # Hash confere?
    warnings: List[str]
    recommendations: List[str]
    checked_at: str


class CanonHealthChecker:
    """
    Monitora frescor e integridade do Canon.
    
    PRINCÍPIO: O Canon é vivo, mas controlado.
    - Frozen significa "não muda sem processo"
    - Não significa "nunca revisa"
    - Governança exige revisão periódica
    
    THRESHOLDS (ajustáveis por contexto):
    - FRESH: < 90 dias (operação normal)
    - AGING: 90-180 dias (atenção)
    - REVIEW_RECOMMENDED: 180-365 dias (agendar revisão)
    - STALE: > 365 dias (ação urgente)
    """
    
    DEFAULT_THRESHOLDS = {
        "fresh_days": 90,
        "aging_days": 180,
        "review_days": 365,
    }
    
    def __init__(self, thresholds: Dict[str, int] = None):
        """
        Args:
            thresholds: Dict com fresh_days, aging_days, review_days
        """
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS
    
    def check(
        self,
        canon: Dict[str, Any],
        verify_hash: bool = True
    ) -> CanonHealthReport:
        """
        Avalia saúde do Canon.
        
        Args:
            canon: Dict do Canon carregado
            verify_hash: Se True, verifica integridade do hash
            
        Returns:
            CanonHealthReport com status e recomendações
        """
        checked_at = datetime.utcnow().isoformat()
        warnings = []
        recommendations = []
        
        # Extract metadata
        canon_version = canon.get("canon_version", "unknown")
        frozen_str = canon.get("frozen_date", "")
        stored_hash = canon.get("canon_hash", "")
        
        # Parse frozen date
        frozen_date = self._parse_date(frozen_str)
        
        if frozen_date is None:
            return CanonHealthReport(
                canon_version=canon_version,
                frozen_date=frozen_str,
                age_days=-1,
                status="INVALID",
                integrity_valid=False,
                warnings=["Cannot parse frozen_date"],
                recommendations=["Fix canon metadata - frozen_date format should be YYYY-MM-DD"],
                checked_at=checked_at
            )
        
        # Calculate age
        age = (datetime.utcnow() - frozen_date).days
        
        # Determine status based on age
        status, age_warnings, age_recommendations = self._evaluate_age(age)
        warnings.extend(age_warnings)
        recommendations.extend(age_recommendations)
        
        # Verify integrity
        integrity_valid = True
        if verify_hash and stored_hash:
            integrity_valid = self.verify_integrity(canon, stored_hash)
            if not integrity_valid:
                status = "COMPROMISED"
                warnings.append("CRITICAL: Canon hash mismatch - possible tampering")
                recommendations.append("URGENT: Investigate canon modification")
                recommendations.append("Restore from known-good backup")
        
        return CanonHealthReport(
            canon_version=canon_version,
            frozen_date=frozen_str,
            age_days=age,
            status=status,
            integrity_valid=integrity_valid,
            warnings=warnings,
            recommendations=recommendations,
            checked_at=checked_at
        )
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in various formats."""
        formats = [
            "%Y-%m-%d",
            "%d-%b-%Y",
            "%Y/%m/%d",
            "%d/%m/%Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return None
    
    def _evaluate_age(self, age_days: int) -> tuple:
        """
        Avalia idade do Canon.
        
        Returns:
            (status, warnings, recommendations)
        """
        warnings = []
        recommendations = []
        
        if age_days < self.thresholds["fresh_days"]:
            status = "FRESH"
            
        elif age_days < self.thresholds["aging_days"]:
            status = "AGING"
            warnings.append(f"Canon is {age_days} days old")
            recommendations.append("Consider scheduling review in next quarter")
            
        elif age_days < self.thresholds["review_days"]:
            status = "REVIEW_RECOMMENDED"
            warnings.append(f"Canon is {age_days} days old - review recommended")
            recommendations.append("Schedule Canon review with GPT Auditor")
            recommendations.append("Assess if any invariants need updating")
            
        else:
            status = "STALE"
            warnings.append(f"Canon is {age_days} days old - STALE")
            recommendations.append("URGENT: Canon audit required")
            recommendations.append("Review all invariants for current applicability")
            recommendations.append("Consider freezing new version after audit")
        
        return status, warnings, recommendations
    
    def verify_integrity(
        self,
        canon: Dict[str, Any],
        stored_hash: str
    ) -> bool:
        """
        Verifica se Canon não foi alterado após freeze.
        
        Args:
            canon: Canon dict atual
            stored_hash: Hash armazenado no momento do freeze
            
        Returns:
            True se íntegro, False se modificado
        """
        # Remove o próprio hash para recalcular
        canon_copy = {k: v for k, v in canon.items() if k != "canon_hash"}
        
        # Serializa de forma determinística
        canonical_yaml = yaml.dump(canon_copy, sort_keys=True, allow_unicode=True)
        
        # Calcula hash
        current_hash = hashlib.sha256(canonical_yaml.encode()).hexdigest()
        
        # Compara (pode ser hash completo ou truncado)
        if len(stored_hash) < 64:
            # Hash truncado - compara prefixo
            return current_hash.startswith(stored_hash) or current_hash[:len(stored_hash)] == stored_hash
        
        return current_hash == stored_hash
    
    def generate_review_checklist(self, canon: Dict[str, Any]) -> List[str]:
        """
        Gera checklist para revisão do Canon.
        
        Returns:
            Lista de itens a verificar na revisão
        """
        checklist = [
            "☐ Verificar se todos os invariantes (I1-I8) ainda são aplicáveis",
            "☐ Verificar se guardrails (G1-G8) cobrem novos cenários",
            "☐ Avaliar se risk_markers multilíngues estão atualizados",
            "☐ Confirmar se scope.prohibited_use está completo",
            "☐ Verificar compliance com regulações vigentes (EU AI Act, GDPR)",
            "☐ Avaliar se Decision Boundary templates precisam ajuste",
            "☐ Revisar data_retention policies",
            "☐ Confirmar audit_requirements adequados",
            "☐ Validar com GPT Auditor (auditoria hostil)",
            "☐ Documentar todas as mudanças propostas",
            "☐ Obter sign-off do Human Architect",
            "☐ Freeze nova versão com novo hash",
        ]
        
        return checklist
    
    def format_report(self, report: CanonHealthReport) -> str:
        """Format report for display."""
        icons = {
            "FRESH": "✅",
            "AGING": "🟡",
            "REVIEW_RECOMMENDED": "🟠",
            "STALE": "🔴",
            "INVALID": "❌",
            "COMPROMISED": "🚨"
        }
        
        icon = icons.get(report.status, "❓")
        
        lines = [
            f"{icon} CANON HEALTH: {report.status}",
            f"Version: {report.canon_version}",
            f"Frozen: {report.frozen_date}",
            f"Age: {report.age_days} days",
            f"Integrity: {'✅ Valid' if report.integrity_valid else '❌ INVALID'}",
        ]
        
        if report.warnings:
            lines.append("\nWarnings:")
            for w in report.warnings:
                lines.append(f"  ⚠️ {w}")
        
        if report.recommendations:
            lines.append("\nRecommendations:")
            for r in report.recommendations:
                lines.append(f"  → {r}")
        
        return "\n".join(lines)


# Singleton
_checker = None

def get_canon_checker() -> CanonHealthChecker:
    """Get singleton health checker."""
    global _checker
    if _checker is None:
        _checker = CanonHealthChecker()
    return _checker


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("WINDI CANON HEALTH CHECKER - Module loaded")
    print("=" * 60)
    
    checker = CanonHealthChecker()
    
    # Test with mock canon
    mock_canon = {
        "canon_version": "1.2.0",
        "frozen_date": "2026-01-22",
        "canon_hash": "abc123"
    }
    
    report = checker.check(mock_canon, verify_hash=False)
    
    print(f"\nTest report:")
    print(checker.format_report(report))
    
    print("\n" + "=" * 60)
    print("Canon envelhece. Revisão periódica é governança.")
    print("=" * 60)
