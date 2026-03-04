"""
WINDI Letter Renderer — STUB
=============================
Wave3 implementation placeholder.

Renders formal letters with:
- Letterhead (ISP-defined)
- Salutation
- Body
- Closing
- Signature block

Status: STUB
"""


def render_letter(document: dict, isp_profile: dict = None) -> dict:
    """
    Render a letter document.

    STUB: Returns placeholder indicating Wave3 implementation needed.
    """
    return {
        "status": "stub",
        "type": "letter",
        "renderer": "renderer_letter",
        "message": "Letter rendering not yet implemented. Scheduled for Wave3.",
        "document_id": document.get("id"),
        "isp_applied": isp_profile.get("id") if isp_profile else None,
    }
