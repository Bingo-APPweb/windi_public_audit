# WINDI Compliance Agent - Integration Module
"""
Modulos de integracao com outros componentes WINDI:

- isp_manager_client: Consulta perfis institucionais (ISP)
- governance_api_client: Interage com a API de governanca
- forensic_ledger_writer: Registra evidencias no ledger forense
"""

__version__ = "1.0.0"
__all__ = [
    "ISPManagerClient",
    "GovernanceAPIClient",
    "ForensicLedgerWriter"
]
