#!/usr/bin/env python3
"""
WINDI Compliance Agent - SGE Score Checker
===========================================

Verifica a coerencia e integridade do SGE Score
(Semantic Governance Entropy) em relacao ao perfil
institucional (ISP) e ao nivel de risco declarado.

O SGE Score representa a "entropia de governanca" do documento:
- Score alto (80-100): Alta conformidade, baixa entropia
- Score medio (50-79): Conformidade parcial, atencao necessaria
- Score baixo (0-49): Baixa conformidade, revisao urgente

Principios:
- Valida coerencia, nao calcula scores
- Compara com baseline do ISP
- Detecta anomalias estatisticas
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


class SGEValidationStatus(Enum):
    """Status da validacao do SGE Score"""
    COHERENT = "coherent"           # Score coerente com ISP e risk
    INCOHERENT = "incoherent"       # Score nao bate com contexto
    ANOMALOUS = "anomalous"         # Desvio estatistico detectado
    MISSING = "missing"             # Score ausente
    OUT_OF_RANGE = "out_of_range"   # Fora do range valido


class RiskScoreCoherence(Enum):
    """Coerencia entre risk level e SGE score"""
    ALIGNED = "aligned"
    MISALIGNED = "misaligned"
    SEVERELY_MISALIGNED = "severely_misaligned"


@dataclass
class SGECheckResult:
    """Resultado da verificacao do SGE Score"""
    document_id: str
    sge_score: Optional[float]
    declared_risk: str
    isp_id: str
    validation_status: SGEValidationStatus
    risk_coherence: RiskScoreCoherence
    isp_baseline_deviation: float  # Em desvios padrao
    checks_passed: List[str]
    checks_failed: List[str]
    anomaly_indicators: List[str]
    recommendations: List[str]
    forensic_hash: str
    timestamp: str
    human_review_required: bool

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "validation_status": self.validation_status.value,
            "risk_coherence": self.risk_coherence.value
        }


class SGEScoreChecker:
    """
    Verificador de SGE Score

    Valida:
    1. Range do score (0-100)
    2. Coerencia com risk level declarado
    3. Coerencia com baseline do ISP
    4. Deteccao de anomalias estatisticas
    """

    # Mapeamento: risk level -> faixa esperada de SGE score
    RISK_SCORE_EXPECTATIONS = {
        "low": {"min": 75, "max": 100, "typical": 85},
        "medium": {"min": 50, "max": 85, "typical": 67},
        "high": {"min": 25, "max": 60, "typical": 42},
        "critical": {"min": 0, "max": 40, "typical": 20}
    }

    # Baseline padrao por tipo de ISP (pode ser sobrescrito)
    ISP_BASELINES = {
        "government": {"mean": 82, "std": 8, "min_expected": 70},
        "financial": {"mean": 88, "std": 6, "min_expected": 75},
        "healthcare": {"mean": 85, "std": 7, "min_expected": 72},
        "corporate": {"mean": 75, "std": 10, "min_expected": 60},
        "default": {"mean": 70, "std": 12, "min_expected": 50}
    }

    def __init__(self, isp_baselines: Optional[Dict] = None):
        """
        Inicializa o checker com baselines opcionais.

        Args:
            isp_baselines: Baselines customizados por ISP ID
        """
        self.custom_baselines = isp_baselines or {}

    def check(
        self,
        document_id: str,
        sge_score: Optional[float],
        declared_risk: str,
        isp_id: str,
        isp_type: str = "default",
        historical_scores: Optional[List[float]] = None
    ) -> SGECheckResult:
        """
        Verifica coerencia do SGE Score.

        Args:
            document_id: ID do documento
            sge_score: Score SGE declarado (0-100)
            declared_risk: Nivel de risco declarado
            isp_id: ID do perfil institucional
            isp_type: Tipo do ISP para baseline
            historical_scores: Scores historicos para deteccao de anomalia

        Returns:
            SGECheckResult com status e detalhes
        """
        checks_passed = []
        checks_failed = []
        anomaly_indicators = []
        recommendations = []

        # 1. Verificar presenca do score
        if sge_score is None:
            return self._missing_score_result(document_id, declared_risk, isp_id)

        # 2. Verificar range (0-100)
        range_valid = self._check_range(sge_score)
        if range_valid:
            checks_passed.append("SGE-001: Score within valid range (0-100)")
        else:
            checks_failed.append("SGE-001: Score OUT OF RANGE")
            return self._out_of_range_result(
                document_id, sge_score, declared_risk, isp_id
            )

        # 3. Verificar coerencia com risk level
        risk_coherence = self._check_risk_coherence(sge_score, declared_risk)
        if risk_coherence == RiskScoreCoherence.ALIGNED:
            checks_passed.append(f"SGE-002: Score coherent with {declared_risk} risk")
        elif risk_coherence == RiskScoreCoherence.MISALIGNED:
            checks_failed.append(f"SGE-002: Score misaligned with {declared_risk} risk")
            recommendations.append(
                f"Review risk classification - score {sge_score} unusual for {declared_risk} risk"
            )
        else:
            checks_failed.append(f"SGE-002: Score SEVERELY misaligned with risk")
            anomaly_indicators.append("Risk-score severe mismatch")

        # 4. Verificar baseline do ISP
        baseline = self._get_baseline(isp_id, isp_type)
        deviation = self._calculate_deviation(sge_score, baseline)

        if abs(deviation) <= 2:
            checks_passed.append(f"SGE-003: Score within ISP baseline ({deviation:.1f}σ)")
        elif abs(deviation) <= 3:
            checks_failed.append(f"SGE-003: Score deviates from ISP baseline ({deviation:.1f}σ)")
            recommendations.append("Score deviates from institutional baseline - review needed")
        else:
            checks_failed.append(f"SGE-003: Score ANOMALOUS vs ISP baseline ({deviation:.1f}σ)")
            anomaly_indicators.append(f"Statistical outlier: {deviation:.1f} standard deviations")

        # 5. Verificar contra historico (se disponivel)
        if historical_scores and len(historical_scores) >= 5:
            hist_anomaly = self._check_historical_anomaly(sge_score, historical_scores)
            if hist_anomaly:
                anomaly_indicators.append(hist_anomaly)
                checks_failed.append("SGE-004: Historical anomaly detected")
            else:
                checks_passed.append("SGE-004: Consistent with historical pattern")

        # Determinar status final
        status = self._determine_status(
            checks_failed, anomaly_indicators, risk_coherence
        )

        # Gerar hash forense
        forensic_hash = self._generate_forensic_hash(
            document_id, sge_score, declared_risk, isp_id, status
        )

        return SGECheckResult(
            document_id=document_id,
            sge_score=sge_score,
            declared_risk=declared_risk,
            isp_id=isp_id,
            validation_status=status,
            risk_coherence=risk_coherence,
            isp_baseline_deviation=deviation,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            anomaly_indicators=anomaly_indicators,
            recommendations=recommendations,
            forensic_hash=forensic_hash,
            timestamp=datetime.now().isoformat(),
            human_review_required=status != SGEValidationStatus.COHERENT
        )

    def _check_range(self, score: float) -> bool:
        """Verifica se score esta no range valido"""
        return 0 <= score <= 100

    def _check_risk_coherence(
        self, score: float, risk: str
    ) -> RiskScoreCoherence:
        """Verifica coerencia entre score e risk level"""
        risk_lower = risk.lower()
        if risk_lower not in self.RISK_SCORE_EXPECTATIONS:
            return RiskScoreCoherence.MISALIGNED

        expected = self.RISK_SCORE_EXPECTATIONS[risk_lower]

        if expected["min"] <= score <= expected["max"]:
            return RiskScoreCoherence.ALIGNED

        # Calcular distancia da faixa esperada
        if score < expected["min"]:
            distance = expected["min"] - score
        else:
            distance = score - expected["max"]

        if distance > 20:
            return RiskScoreCoherence.SEVERELY_MISALIGNED
        return RiskScoreCoherence.MISALIGNED

    def _get_baseline(self, isp_id: str, isp_type: str) -> Dict:
        """Obtem baseline para o ISP"""
        # Primeiro tenta baseline customizado pelo ID
        if isp_id in self.custom_baselines:
            return self.custom_baselines[isp_id]

        # Depois pelo tipo
        if isp_type in self.ISP_BASELINES:
            return self.ISP_BASELINES[isp_type]

        return self.ISP_BASELINES["default"]

    def _calculate_deviation(self, score: float, baseline: Dict) -> float:
        """Calcula desvio do score em relacao ao baseline (em sigmas)"""
        mean = baseline["mean"]
        std = baseline["std"]
        if std == 0:
            return 0
        return (score - mean) / std

    def _check_historical_anomaly(
        self, current: float, historical: List[float]
    ) -> Optional[str]:
        """Detecta anomalia em relacao ao historico"""
        if len(historical) < 5:
            return None

        # Calcula estatisticas do historico
        mean = sum(historical) / len(historical)
        variance = sum((x - mean) ** 2 for x in historical) / len(historical)
        std = variance ** 0.5

        if std == 0:
            std = 1

        # Z-score do valor atual
        z_score = abs(current - mean) / std

        if z_score > 3:
            return f"Score {current} is {z_score:.1f}σ from historical mean {mean:.1f}"
        return None

    def _determine_status(
        self,
        checks_failed: List[str],
        anomalies: List[str],
        risk_coherence: RiskScoreCoherence
    ) -> SGEValidationStatus:
        """Determina status final da validacao"""
        if anomalies:
            return SGEValidationStatus.ANOMALOUS
        if risk_coherence == RiskScoreCoherence.SEVERELY_MISALIGNED:
            return SGEValidationStatus.INCOHERENT
        if checks_failed:
            return SGEValidationStatus.INCOHERENT
        return SGEValidationStatus.COHERENT

    def _missing_score_result(
        self, doc_id: str, risk: str, isp_id: str
    ) -> SGECheckResult:
        """Resultado para score ausente"""
        return SGECheckResult(
            document_id=doc_id,
            sge_score=None,
            declared_risk=risk,
            isp_id=isp_id,
            validation_status=SGEValidationStatus.MISSING,
            risk_coherence=RiskScoreCoherence.MISALIGNED,
            isp_baseline_deviation=0,
            checks_passed=[],
            checks_failed=["SGE-000: SGE Score is MISSING"],
            anomaly_indicators=["No score available for validation"],
            recommendations=["SGE Score must be calculated before governance approval"],
            forensic_hash=self._generate_forensic_hash(doc_id, None, risk, isp_id, SGEValidationStatus.MISSING),
            timestamp=datetime.now().isoformat(),
            human_review_required=True
        )

    def _out_of_range_result(
        self, doc_id: str, score: float, risk: str, isp_id: str
    ) -> SGECheckResult:
        """Resultado para score fora do range"""
        return SGECheckResult(
            document_id=doc_id,
            sge_score=score,
            declared_risk=risk,
            isp_id=isp_id,
            validation_status=SGEValidationStatus.OUT_OF_RANGE,
            risk_coherence=RiskScoreCoherence.SEVERELY_MISALIGNED,
            isp_baseline_deviation=0,
            checks_passed=[],
            checks_failed=[f"SGE-001: Score {score} is OUT OF VALID RANGE (0-100)"],
            anomaly_indicators=["Invalid score value - possible data corruption"],
            recommendations=["Investigate score calculation - value is invalid"],
            forensic_hash=self._generate_forensic_hash(doc_id, score, risk, isp_id, SGEValidationStatus.OUT_OF_RANGE),
            timestamp=datetime.now().isoformat(),
            human_review_required=True
        )

    def _generate_forensic_hash(
        self,
        doc_id: str,
        score: Optional[float],
        risk: str,
        isp_id: str,
        status: SGEValidationStatus
    ) -> str:
        """Gera hash forense do resultado"""
        data = {
            "document_id": doc_id,
            "sge_score": score,
            "declared_risk": risk,
            "isp_id": isp_id,
            "validation_status": status.value,
            "timestamp": datetime.now().isoformat()
        }
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


# ============================================
# EXEMPLO DE USO
# ============================================

if __name__ == "__main__":
    checker = SGEScoreChecker()

    # Teste 1: Score coerente
    result = checker.check(
        document_id="DOC-2026-001",
        sge_score=85,
        declared_risk="low",
        isp_id="windi://isp/bundesregierung",
        isp_type="government"
    )

    print("\n" + "="*60)
    print("WINDI Compliance Agent - SGE Score Check")
    print("="*60)
    print(f"Document: {result.document_id}")
    print(f"SGE Score: {result.sge_score}")
    print(f"Risk Level: {result.declared_risk}")
    print(f"Status: {result.validation_status.value.upper()}")
    print(f"Risk Coherence: {result.risk_coherence.value}")
    print(f"Baseline Deviation: {result.isp_baseline_deviation:.2f}σ")

    print(f"\nChecks Passed: {len(result.checks_passed)}")
    for check in result.checks_passed:
        print(f"  ✓ {check}")

    if result.checks_failed:
        print(f"\nChecks Failed: {len(result.checks_failed)}")
        for check in result.checks_failed:
            print(f"  ✗ {check}")

    print(f"\nHuman Review Required: {result.human_review_required}")
