# WINDI Compliance Agent - Capsule Module
"""
Capsule: Nucleo de validacao do Compliance Agent

Cada modulo valida um aspecto especifico da governanca WINDI:
- virtue_receipt_validator: Integridade do recibo etico
- sge_score_checker: Coerencia do score de governanca
- identity_license_auditor: Validade da licenca institucional
- i9_human_decision_verifier: Prova de decisao humana

Principios:
- ADVISORY ONLY: Sugere, nunca executa
- ZERO KNOWLEDGE: Trabalha com hashes, nunca dados sensiveis
- DETERMINISTIC: Regras explicaveis, auditaveis
"""

__version__ = "1.0.0"
__all__ = [
    "VirtueReceiptValidator",
    "SGEScoreChecker",
    "IdentityLicenseAuditor",
    "I9HumanDecisionVerifier"
]
