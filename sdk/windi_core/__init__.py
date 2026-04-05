"""
WINDI SDK v1.0 — Core Protocol

"Escala não vem de fazer tudo igual.
 Vem de garantir que tudo termina da mesma forma."

Liga IA+H · Kempten, Bavaria · 05 Abril 2026

Usage:
    from windi_core import seal, ledger, render_jmpg, distribute

    # 1. Seal artifact (I9 Gate)
    seal_result = await seal(artifact_path, wallet_id)

    # 2. Anchor to Ledger (I11)
    receipt = await ledger(seal_result)

    # 3. Render proof card
    jmpg = await render_jmpg(receipt.id)

    # 4. Distribute to world
    await distribute(receipt.id, channel="telegram", chat_id="...")
"""

from .core import seal, ledger, render_jmpg, distribute
from .models import SealResult, LedgerReceipt, JMPGResult, DistributeResult

__version__ = "1.0.0"
__all__ = [
    "seal",
    "ledger",
    "render_jmpg",
    "distribute",
    "SealResult",
    "LedgerReceipt",
    "JMPGResult",
    "DistributeResult",
]
