"""
W-MAIL-DACP-MILTER — Footer Templates
Spec: §227 Section 6
"""

from datetime import datetime
from typing import Optional

VERIFY_BASE_URL = "https://windi-domain.com/verify-public/web/verify.html"
API_BASE_URL = "https://windi-domain.com/api/receipts"


def generate_plain_footer(
    proof_id: str,
    sealed_at: Optional[datetime] = None
) -> str:
    """
    Generate plain text DACP footer.
    Spec: §227 Section 6.1
    """
    if sealed_at is None:
        sealed_at = datetime.utcnow()

    verify_url = f"{VERIFY_BASE_URL}?id={proof_id}"
    api_url = f"{API_BASE_URL}/{proof_id}"
    sealed_at_iso = sealed_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    return f"""
---
WINDI DACP-v1 PROOF
Proof-ID: {proof_id}
Verify:   {verify_url}
API:      {api_url}
Sealed:   {sealed_at_iso}
"""


def generate_html_footer(
    proof_id: str,
    sealed_at: Optional[datetime] = None
) -> str:
    """
    Generate HTML DACP footer with invariant marker.
    Spec: §227 Section 6.2

    The data-windi-dacp="v1" attribute is the canonical strip anchor.
    """
    if sealed_at is None:
        sealed_at = datetime.utcnow()

    verify_url = f"{VERIFY_BASE_URL}?id={proof_id}"
    api_url = f"{API_BASE_URL}/{proof_id}"

    return f'''
<div data-windi-dacp="v1" style="margin-top:24px;padding:16px;border-top:1px solid #ccc;font-family:monospace;font-size:12px;color:#666">
  <strong>WINDI DACP-v1 PROOF</strong><br>
  Proof-ID: <code>{proof_id}</code><br>
  Verify: <a href="{verify_url}">{verify_url}</a><br>
  API: <a href="{api_url}">{api_url}</a>
</div>
'''


def has_dacp_footer(body: str) -> bool:
    """Check if body already contains DACP footer (plain text marker)"""
    return "WINDI DACP-v1 PROOF" in body


def has_dacp_html_footer(html: str) -> bool:
    """Check if HTML already contains DACP footer (data attribute marker)"""
    return 'data-windi-dacp="v1"' in html
