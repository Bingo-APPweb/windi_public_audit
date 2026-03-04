"""
WINDI Document Renderers — Stub Registry
==========================================

Document Intelligence Hub workers.
Each renderer transforms document content into its output format.

LIVE renderers:
- renderer_communique (integrated in communique_blueprint)
- renderer_invoice (Export Engine :8103, SEALED)

STUB renderers (Wave3):
- renderer_letter
- renderer_email
- renderer_contract
- renderer_report
- renderer_presentation
- renderer_spreadsheet

Principle: "1 agent + N ISPs + N renderers = clean architecture"
"""

from .renderer_letter import render_letter
from .renderer_email import render_email
from .renderer_contract import render_contract
from .renderer_report import render_report
from .renderer_presentation import render_presentation
from .renderer_spreadsheet import render_spreadsheet

__all__ = [
    "render_letter",
    "render_email",
    "render_contract",
    "render_report",
    "render_presentation",
    "render_spreadsheet",
]
