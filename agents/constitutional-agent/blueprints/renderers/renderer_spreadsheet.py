"""
WINDI Spreadsheet Renderer — STUB
==================================
Wave3 implementation placeholder.

Renders spreadsheet documents with:
- Sheets
- Cells with formulas
- Styling
- Charts metadata

Status: STUB
"""


def render_spreadsheet(document: dict, isp_profile: dict = None) -> dict:
    """
    Render a spreadsheet document.

    STUB: Returns placeholder indicating Wave3 implementation needed.
    """
    return {
        "status": "stub",
        "type": "spreadsheet",
        "renderer": "renderer_spreadsheet",
        "message": "Spreadsheet rendering not yet implemented. Scheduled for Wave3.",
        "document_id": document.get("id"),
        "isp_applied": isp_profile.get("id") if isp_profile else None,
    }
