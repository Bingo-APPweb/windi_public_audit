#!/usr/bin/env python3
"""
WINDI Compliance Agent - Main Agent
====================================

O Sentinela de Conformidade do WINDI Platform.

Este agente valida a integridade da governanca documental
sem tomar decisoes ou executar acoes.

Funcionalidades:
- Validacao de Virtue Receipts
- Verificacao de SGE Scores
- Auditoria de Identity Licenses
- Verificacao do Invariante I9 (decisao humana)
- Avaliacao de conformidade com politicas

Principios:
- ADVISORY ONLY: Sugere, nunca executa
- ZERO KNOWLEDGE: Opera com metadados, nao dados sensiveis
- HUMAN MEDIATED: Toda acao requer humano
- FORENSIC LOGGING: Tudo e registrado

"AI processes. Human decides. WINDI guarantees."
"""

import os
import sys
import json
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from flask import Flask, jsonify, request

# Importar modulos da capsule
from capsule.virtue_receipt_validator import VirtueReceiptValidator, VirtueReceiptValidationResult
from capsule.sge_score_checker import SGEScoreChecker, SGECheckResult
from capsule.identity_license_auditor import IdentityLicenseAuditor, IdentityLicenseAuditResult
from capsule.i9_human_decision_verifier import I9HumanDecisionVerifier, I9VerificationResult

# Importar integracoes
from integration.isp_manager_client import ISPManagerClient
from integration.forensic_ledger_writer import ForensicLedgerWriter


# ============================================
# CONFIGURACAO
# ============================================

__version__ = "1.0.0"
__agent_name__ = "WINDI Compliance Agent"
__agent_id__ = "windi://agent/compliance"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ComplianceCheckResult:
    """Resultado consolidado de verificacao de conformidade"""
    document_id: str
    isp_id: Optional[str]
    timestamp: str
    overall_status: str  # compliant, non_compliant, partial, unknown
    virtue_receipt: Optional[Dict]
    sge_score: Optional[Dict]
    identity_license: Optional[Dict]
    i9_verification: Optional[Dict]
    policy_evaluation: Optional[Dict]
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    human_review_required: bool
    forensic_hash: str

    def to_dict(self) -> Dict:
        return asdict(self)


class WindiComplianceAgent:
    """
    WINDI Compliance Agent - O Sentinela de Conformidade

    Orquestra todos os modulos de validacao para fornecer
    uma visao consolidada da conformidade documental.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o agente.

        Args:
            config_path: Caminho para arquivo de configuracao
        """
        self.config = self._load_config(config_path)
        self.start_time = datetime.now()

        # Inicializar componentes
        self.virtue_validator = VirtueReceiptValidator()
        self.sge_checker = SGEScoreChecker()
        self.license_auditor = IdentityLicenseAuditor()
        self.i9_verifier = I9HumanDecisionVerifier()

        # Integracoes
        self.isp_client = ISPManagerClient(
            base_url=self.config.get("isp_manager_url", "http://localhost:8800")
        )
        self.ledger = ForensicLedgerWriter(
            ledger_path=self.config.get("ledger_path", "data/forensic_ledger"),
            agent_id=__agent_id__
        )

        # Carregar politicas
        self.policies = self._load_policies()

        # Flask app
        self.app = Flask(__name__)
        self._setup_routes()

        logger.info(f"{__agent_name__} v{__version__} initialized")

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Carrega configuracao"""
        default_config = {
            "port": 8850,
            "isp_manager_url": "http://localhost:8800",
            "governance_api_url": "http://localhost:8080",
            "ledger_path": "data/forensic_ledger",
            "log_level": "INFO"
        }

        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return {**default_config, **yaml.safe_load(f)}

        return default_config

    def _load_policies(self) -> Dict:
        """Carrega politicas de conformidade"""
        policies = {}
        policy_dir = Path(__file__).parent / "policy"

        for policy_file in policy_dir.glob("*.yaml"):
            try:
                with open(policy_file, 'r') as f:
                    policy_name = policy_file.stem
                    policies[policy_name] = yaml.safe_load(f)
                    logger.info(f"Loaded policy: {policy_name}")
            except (yaml.YAMLError, IOError) as e:
                logger.error(f"Error loading policy {policy_file}: {e}")

        return policies

    def _setup_routes(self):
        """Configura rotas da API"""

        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "healthy",
                "agent": __agent_name__,
                "version": __version__,
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
            })

        @self.app.route('/api/v1/validate/full', methods=['POST'])
        def validate_full():
            """Validacao completa de conformidade"""
            data = request.get_json()
            result = self.validate_document(data)
            return jsonify(result.to_dict())

        @self.app.route('/api/v1/validate/virtue-receipt', methods=['POST'])
        def validate_virtue_receipt():
            """Valida apenas Virtue Receipt"""
            data = request.get_json()
            result = self.virtue_validator.validate(data)
            return jsonify(result.to_dict())

        @self.app.route('/api/v1/validate/sge-score', methods=['POST'])
        def validate_sge_score():
            """Valida apenas SGE Score"""
            data = request.get_json()
            result = self.sge_checker.check(
                document_id=data.get("document_id", "unknown"),
                sge_score=data.get("sge_score"),
                declared_risk=data.get("risk_level", "medium"),
                isp_id=data.get("isp_id", "default"),
                isp_type=data.get("isp_type", "default")
            )
            return jsonify(result.to_dict())

        @self.app.route('/api/v1/validate/identity-license', methods=['POST'])
        def validate_identity_license():
            """Audita Identity License"""
            data = request.get_json()
            result = self.license_auditor.audit(
                license_data=data.get("license", {}),
                requested_action=data.get("action"),
                target_isp=data.get("isp_id")
            )
            return jsonify(result.to_dict())

        @self.app.route('/api/v1/validate/i9', methods=['POST'])
        def validate_i9():
            """Verifica Invariante I9"""
            data = request.get_json()
            result = self.i9_verifier.verify(
                document_id=data.get("document_id", "unknown"),
                decision_data=data.get("decision"),
                ai_action_taken=data.get("ai_action")
            )
            return jsonify(result.to_dict())

        @self.app.route('/api/v1/policies', methods=['GET'])
        def list_policies():
            """Lista politicas carregadas"""
            return jsonify({
                "policies": list(self.policies.keys()),
                "count": len(self.policies)
            })

        @self.app.route('/api/v1/invariants', methods=['GET'])
        def list_invariants():
            """Lista invariantes WINDI"""
            invariants_policy = self.policies.get("windi_invariants", {})
            return jsonify({
                "invariants": invariants_policy.get("invariants", {}),
                "count": len(invariants_policy.get("invariants", {}))
            })

        @self.app.route('/api/v1/ledger/verify', methods=['GET'])
        def verify_ledger():
            """Verifica integridade do ledger"""
            result = self.ledger.verify_chain_integrity()
            return jsonify(result)

    def validate_document(self, document_data: Dict) -> ComplianceCheckResult:
        """
        Executa validacao completa de conformidade.

        Args:
            document_data: Dados do documento incluindo:
                - document_id
                - virtue_receipt
                - governance_metadata
                - identity_license
                - human_decision

        Returns:
            ComplianceCheckResult consolidado
        """
        document_id = document_data.get("document_id", "unknown")
        isp_id = document_data.get("isp_id")

        critical_issues = []
        warnings = []
        recommendations = []

        results = {
            "virtue_receipt": None,
            "sge_score": None,
            "identity_license": None,
            "i9_verification": None,
            "policy_evaluation": None
        }

        # 1. Validar Virtue Receipt
        virtue_receipt = document_data.get("virtue_receipt")
        if virtue_receipt:
            vr_result = self.virtue_validator.validate(virtue_receipt)
            results["virtue_receipt"] = vr_result.to_dict()

            if vr_result.critical_failures:
                critical_issues.extend(vr_result.critical_failures)
            recommendations.extend(vr_result.recommendations)

        # 2. Validar SGE Score
        gov_metadata = document_data.get("governance_metadata", {})
        if gov_metadata.get("sge_score") is not None:
            sge_result = self.sge_checker.check(
                document_id=document_id,
                sge_score=gov_metadata.get("sge_score"),
                declared_risk=gov_metadata.get("risk_level", "medium"),
                isp_id=isp_id or "default",
                isp_type=document_data.get("isp_type", "default")
            )
            results["sge_score"] = sge_result.to_dict()

            if sge_result.anomaly_indicators:
                warnings.extend(sge_result.anomaly_indicators)
            recommendations.extend(sge_result.recommendations)

        # 3. Auditar Identity License
        identity_license = document_data.get("identity_license")
        if identity_license:
            license_result = self.license_auditor.audit(
                license_data=identity_license,
                target_isp=isp_id
            )
            results["identity_license"] = license_result.to_dict()

            if license_result.critical_violations > 0:
                critical_issues.append(f"Identity license has {license_result.critical_violations} critical violations")
            if license_result.warnings > 0:
                warnings.append(f"Identity license has {license_result.warnings} warnings")
            recommendations.extend(license_result.recommendations)

        # 4. Verificar I9 (Decisao Humana)
        human_decision = document_data.get("human_decision")
        i9_result = self.i9_verifier.verify(
            document_id=document_id,
            decision_data=human_decision,
            ai_action_taken=document_data.get("ai_action")
        )
        results["i9_verification"] = i9_result.to_dict()

        if not i9_result.human_accountability_confirmed:
            critical_issues.append("I9 VIOLATION: Human decision not confirmed")
        if i9_result.requires_immediate_action:
            critical_issues.extend(i9_result.critical_failures)
        warnings.extend(i9_result.warnings)

        # 5. Avaliar conformidade com ISP
        if isp_id:
            isp_validation = self.isp_client.validate_against_isp(
                isp_id=isp_id,
                document_metadata=gov_metadata
            )
            results["policy_evaluation"] = isp_validation

            if not isp_validation.get("valid"):
                for check in isp_validation.get("checks", []):
                    if not check.get("passed"):
                        warnings.append(f"ISP check failed: {check.get('check')}")

        # Determinar status geral
        if critical_issues:
            overall_status = "non_compliant"
        elif warnings:
            overall_status = "partial"
        elif all(r is not None for r in results.values()):
            overall_status = "compliant"
        else:
            overall_status = "unknown"

        # Gerar hash forense
        import hashlib
        forensic_data = {
            "document_id": document_id,
            "status": overall_status,
            "critical_count": len(critical_issues),
            "warning_count": len(warnings),
            "timestamp": datetime.now().isoformat()
        }
        forensic_hash = hashlib.sha256(
            json.dumps(forensic_data, sort_keys=True).encode()
        ).hexdigest()

        # Registrar no ledger
        self.ledger.write(
            record_type="compliance_check",
            document_id=document_id,
            isp_id=isp_id,
            payload={
                "status": overall_status,
                "critical_issues": len(critical_issues),
                "warnings": len(warnings),
                "i9_confirmed": i9_result.human_accountability_confirmed
            }
        )

        return ComplianceCheckResult(
            document_id=document_id,
            isp_id=isp_id,
            timestamp=datetime.now().isoformat(),
            overall_status=overall_status,
            virtue_receipt=results["virtue_receipt"],
            sge_score=results["sge_score"],
            identity_license=results["identity_license"],
            i9_verification=results["i9_verification"],
            policy_evaluation=results["policy_evaluation"],
            critical_issues=critical_issues,
            warnings=warnings,
            recommendations=recommendations,
            human_review_required=bool(critical_issues) or overall_status != "compliant",
            forensic_hash=forensic_hash
        )

    def start(self, host: str = "0.0.0.0", port: int = None):
        """Inicia o agente"""
        port = port or self.config.get("port", 8850)

        print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║             WINDI Compliance Agent                        ║
    ║              O Sentinela de Conformidade                  ║
    ║                    v{__version__}                              ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  "AI processes. Human decides. WINDI guarantees."         ║
    ║                                                           ║
    ║  Endpoints:                                               ║
    ║    POST /api/v1/validate/full         Full compliance     ║
    ║    POST /api/v1/validate/virtue-receipt                   ║
    ║    POST /api/v1/validate/sge-score                        ║
    ║    POST /api/v1/validate/identity-license                 ║
    ║    POST /api/v1/validate/i9           Human decision      ║
    ║    GET  /api/v1/invariants            WINDI invariants    ║
    ║    GET  /api/v1/ledger/verify         Chain integrity     ║
    ╚═══════════════════════════════════════════════════════════╝
        """)

        logger.info(f"Starting {__agent_name__} on {host}:{port}")
        self.app.run(host=host, port=port, threaded=True)


# ============================================
# MAIN
# ============================================

def main():
    """Ponto de entrada"""
    config_path = os.environ.get("COMPLIANCE_CONFIG", "config/compliance_config.yaml")
    agent = WindiComplianceAgent(config_path)

    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
