"""
WINDI Email Renderer — STUB
============================
Wave3 implementation placeholder.

Renders email documents with:
- Subject line
- To/Cc/Bcc headers
- Body (HTML/plain)
- Attachments list

Status: STUB
"""


def render_email(document: dict, isp_profile: dict = None) -> dict:
    """
    Render an email document.

    STUB: Returns placeholder indicating Wave3 implementation needed.
    """
    return {
        "status": "stub",
        "type": "email",
        "renderer": "renderer_email",
        "message": "Email rendering not yet implemented. Scheduled for Wave3.",
        "document_id": document.get("id"),
        "isp_applied": isp_profile.get("id") if isp_profile else None,
    }
