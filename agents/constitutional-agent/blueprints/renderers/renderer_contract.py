"""
WINDI Contract Renderer — STUB
===============================
Wave3 implementation placeholder.

Renders contract documents with:
- Parties block
- Preamble
- Clauses (numbered)
- Signature blocks
- Annexes

Status: STUB
"""


def render_contract(document: dict, isp_profile: dict = None) -> dict:
    """
    Render a contract document.

    STUB: Returns placeholder indicating Wave3 implementation needed.
    """
    return {
        "status": "stub",
        "type": "contract",
        "renderer": "renderer_contract",
        "message": "Contract rendering not yet implemented. Scheduled for Wave3.",
        "document_id": document.get("id"),
        "isp_applied": isp_profile.get("id") if isp_profile else None,
    }
