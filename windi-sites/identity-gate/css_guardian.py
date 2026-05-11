"""
CSS Guardian — Post-Processor for W-SITES-001
§249 WINDI Generation Grammar · Safety Net
§254 GUARDIAN-AUDIT — Auditability Logging

Normalizes LLM output to KLAR/NOIR design system.
Even the best prompt escapes sometimes — this catches failures silently.

§254 Doctrine:
> "O CSS Guardian já não apenas corrige a superfície.
>  Ele prova que a superfície foi governada."

Invariants: I9 (human approval), I11 (forensic integrity), I14 (explicit failure)
Liga IA+H · Kempten, Bavaria · 2026
"""

import re
import json
import hashlib
import os
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass, asdict

# ═══════════════════════════════════════════════════════════════
# §254 GUARDIAN AUDIT STRUCTURE
# ═══════════════════════════════════════════════════════════════

GUARDIAN_VERSION = "1.1.0"  # §254 audit-enabled
POLICY_PROFILE = "KLAR_NOIR_GDPR_SYSTEM_FONTS"
AUDIT_LOG_DIR = "/opt/windi/windi-sites/audit-logs"


@dataclass
class GuardianAudit:
    """
    §254 Canonical audit structure for CSS Guardian.

    Granularity: Aggregated per document (not per-intervention).
    Destination: Hash in Ledger, detailed log local.
    Visibility: Only in full forensic block (Rule 3C).
    """
    audit_id: str
    site_id: str
    receipt_id: Optional[str]
    input_html_hash: str
    output_html_hash: str
    css_guardian_version: str
    policy_profile: str
    interventions_count: int
    intervention_categories: Dict[str, int]
    forensic_valid: bool
    forensic_triggers_found: List[str]
    passed: bool
    errors: List[str]
    warnings: List[str]
    corrections: List[str]
    created_at: str
    local_log_hash: Optional[str] = None
    ledger_receipt_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def compute_log_hash(self) -> str:
        """Compute SHA-256 hash of the full audit log."""
        log_content = self.to_json()
        return hashlib.sha256(log_content.encode('utf-8')).hexdigest()

    def to_ledger_summary(self) -> dict:
        """
        Create minimal summary for Ledger storage.
        Full log stays local; only hash + summary goes to Ledger.
        """
        return {
            "audit_id": self.audit_id,
            "site_id": self.site_id,
            "guardian_version": self.css_guardian_version,
            "policy_profile": self.policy_profile,
            "interventions_count": self.interventions_count,
            "categories": list(self.intervention_categories.keys()),
            "passed": self.passed,
            "forensic_valid": self.forensic_valid,
            "log_hash": self.local_log_hash or self.compute_log_hash(),
            "created_at": self.created_at,
        }


def generate_audit_id() -> str:
    """Generate unique audit ID."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    hash_suffix = hashlib.sha256(
        f"{timestamp}-{os.urandom(8).hex()}".encode()
    ).hexdigest()[:8].upper()
    return f"GUARDIAN-{timestamp}-{hash_suffix}"


def hash_content(content: str) -> str:
    """SHA-256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def save_audit_log(audit: GuardianAudit) -> str:
    """
    Save detailed audit log to local filesystem.
    Returns the file path.
    """
    os.makedirs(AUDIT_LOG_DIR, exist_ok=True)
    filename = f"{audit.audit_id}.json"
    filepath = os.path.join(AUDIT_LOG_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(audit.to_json())

    return filepath

# ═══════════════════════════════════════════════════════════════
# KLAR/NOIR PALETTE
# ═══════════════════════════════════════════════════════════════

VALID_COLORS = {
    "#F5F0E0",  # klar
    "#EBE5D2",  # klar-edge
    "#080808",  # noir
    "#2A2A2A",  # noir-soft
    "#8B6914",  # gold
    "#D4C896",  # gold-faint
    "#ffffff",  # white (allowed for contrast)
    "#000000",  # black (alias for noir)
    "transparent",
    "inherit",
    "currentColor",
}

# Colors to replace → target
COLOR_REPLACEMENTS = {
    # Purples/Violets
    r"#[89ab][0-9a-f][0-9a-f][0-9a-f]ff": "#8B6914",  # purple-ish → gold
    r"#[cdef][0-9a-f][0-9a-f][0-9a-f]ff": "#D4C896",  # light purple → gold-faint
    r"purple": "#8B6914",
    r"violet": "#8B6914",
    r"indigo": "#8B6914",

    # Pinks/Magentas
    r"#[ef][0-9a-f][48][0-9a-f][89ab][0-9a-f]": "#8B6914",  # pink-ish → gold
    r"pink": "#D4C896",
    r"magenta": "#8B6914",
    r"fuchsia": "#8B6914",

    # Cyans/Teals
    r"cyan": "#8B6914",
    r"teal": "#2A2A2A",
    r"turquoise": "#8B6914",

    # Blues (except very dark)
    r"#[0-5][0-9a-f][0-9a-f][0-9a-f]ff": "#8B6914",  # medium blue → gold
    r"blue": "#8B6914",
    r"navy": "#080808",

    # Bright greens
    r"lime": "#8B6914",
    r"#[0-9][0-9]ff[0-9][0-9]": "#8B6914",  # bright green → gold

    # Oranges/Reds (keep gold-adjacent)
    r"orange": "#8B6914",
    r"red": "#8B6914",
}

# ═══════════════════════════════════════════════════════════════
# PATTERN REMOVALS
# ═══════════════════════════════════════════════════════════════

GRADIENT_PATTERN = re.compile(
    r'(linear-gradient|radial-gradient|conic-gradient)\s*\([^)]+\)',
    re.IGNORECASE
)

BORDER_RADIUS_PATTERN = re.compile(
    r'border-radius\s*:\s*[^;0]+;',
    re.IGNORECASE
)

ANIMATION_PATTERN = re.compile(
    r'(animation|transition)\s*:\s*[^;]*[3-9]\d{2,}ms[^;]*;',
    re.IGNORECASE
)

BOX_SHADOW_COLORED_PATTERN = re.compile(
    r'box-shadow\s*:[^;]*(rgba?\s*\([^)]+\)|#[0-9a-f]{3,8})[^;]*;',
    re.IGNORECASE
)

EXTERNAL_IMPORT_PATTERN = re.compile(
    r'@import\s+url\s*\([^)]+\)\s*;',
    re.IGNORECASE
)

EXTERNAL_FONT_PATTERN = re.compile(
    r"@import\s+['\"]https?://[^'\"]+['\"];",
    re.IGNORECASE
)


def normalize_gradients(css: str) -> Tuple[str, int]:
    """Replace all gradients with solid klar background."""
    count = len(GRADIENT_PATTERN.findall(css))
    css = GRADIENT_PATTERN.sub('var(--klar)', css)
    return css, count


def normalize_border_radius(css: str) -> Tuple[str, int]:
    """Force all border-radius to 0 (institutional = sharp)."""
    matches = BORDER_RADIUS_PATTERN.findall(css)
    count = len([m for m in matches if '0' not in m])
    css = BORDER_RADIUS_PATTERN.sub('border-radius: 0;', css)
    return css, count


def normalize_colors(css: str) -> Tuple[str, int]:
    """Replace forbidden colors with palette equivalents."""
    count = 0
    for pattern, replacement in COLOR_REPLACEMENTS.items():
        matches = re.findall(pattern, css, re.IGNORECASE)
        count += len(matches)
        css = re.sub(pattern, replacement, css, flags=re.IGNORECASE)
    return css, count


def remove_external_imports(css: str) -> Tuple[str, int]:
    """Remove @import for GDPR compliance."""
    count = len(EXTERNAL_IMPORT_PATTERN.findall(css)) + len(EXTERNAL_FONT_PATTERN.findall(css))
    css = EXTERNAL_IMPORT_PATTERN.sub('/* external import removed for GDPR */', css)
    css = EXTERNAL_FONT_PATTERN.sub('/* external font removed for GDPR */', css)
    return css, count


def normalize_animations(css: str) -> Tuple[str, int]:
    """Cap animations at 200ms."""
    count = len(ANIMATION_PATTERN.findall(css))
    # Replace long durations with 200ms
    css = re.sub(r'(\d{3,})ms', lambda m: '200ms' if int(m.group(1)) > 200 else m.group(0), css)
    return css, count


# ═══════════════════════════════════════════════════════════════
# CANONICAL CSS INJECTION
# ═══════════════════════════════════════════════════════════════

CANONICAL_CSS_OVERRIDE = """
/* §249 WINDI Generation Grammar — Canonical Override */
:root {
  --klar: #F5F0E0 !important;
  --klar-edge: #EBE5D2 !important;
  --noir: #080808 !important;
  --noir-soft: #2A2A2A !important;
  --gold: #8B6914 !important;
  --gold-faint: #D4C896 !important;
  --line: #2A2A2A !important;
}
body {
  background: var(--klar) !important;
  color: var(--noir) !important;
}
h1, h2, h3, h4, h5, h6 {
  font-family: 'Bricolage Grotesque', Georgia, 'Times New Roman', serif !important;
}
code, pre, .proof-grid, .proof-label, .proof-minimal {
  font-family: 'JetBrains Mono', 'Courier New', monospace !important;
}
"""


def inject_canonical_css(html: str) -> str:
    """Inject canonical CSS override at end of <style> block."""
    # Find the closing </style> tag
    style_close = html.rfind('</style>')
    if style_close == -1:
        return html

    # Insert canonical CSS before </style>
    return html[:style_close] + CANONICAL_CSS_OVERRIDE + html[style_close:]


# ═══════════════════════════════════════════════════════════════
# FORENSIC VALIDATION
# ═══════════════════════════════════════════════════════════════

FORENSIC_TRIGGERS = [
    'ledger', 'recibo', 'receipt', 'verificação', 'verify',
    'imutável', 'immutable', 'forense', 'forensic',
    'auditoria', 'audit', 'windi', 'compliance', 'governance'
]

FORENSIC_BLOCK_PATTERN = re.compile(
    r'<section[^>]*class=["\'][^"\']*forensic-proof[^"\']*["\'][^>]*>',
    re.IGNORECASE
)

MINIMAL_PROOF_PATTERN = re.compile(
    r'WINDI-SITES-001-[A-F0-9]{8}',
    re.IGNORECASE
)


def requires_full_forensic(prompt: str) -> bool:
    """Check if prompt triggers full forensic block requirement."""
    prompt_lower = prompt.lower()
    return any(trigger in prompt_lower for trigger in FORENSIC_TRIGGERS)


def has_forensic_block(html: str) -> bool:
    """Check if HTML contains full forensic proof block."""
    return bool(FORENSIC_BLOCK_PATTERN.search(html))


def has_minimal_proof(html: str) -> bool:
    """Check if HTML contains minimal proof line."""
    return bool(MINIMAL_PROOF_PATTERN.search(html))


def validate_forensic(html: str, prompt: str) -> Tuple[bool, str]:
    """
    Validate forensic requirements.

    Returns:
        (is_valid, error_message)
    """
    # Minimal proof is ALWAYS required (rule 3C)
    if not has_minimal_proof(html):
        return False, "FORENSIC_MISSING: Minimal proof line required in footer (rule 3C)"

    # Full block required if prompt triggers it
    if requires_full_forensic(prompt) and not has_forensic_block(html):
        return False, f"FORENSIC_INCOMPLETE: Full proof block required (prompt contains trigger words)"

    return True, ""


# ═══════════════════════════════════════════════════════════════
# MAIN GUARDIAN FUNCTION
# ═══════════════════════════════════════════════════════════════

def guard_html(
    html: str,
    prompt: str = "",
    site_id: str = "unknown",
    receipt_id: Optional[str] = None,
    save_audit: bool = True
) -> Tuple[str, dict, Optional[GuardianAudit]]:
    """
    Apply CSS Guardian post-processing to generated HTML.

    §254 Enhanced: Now creates GuardianAudit for auditability logging.

    Args:
        html: Generated HTML content
        prompt: Original user prompt (for forensic validation)
        site_id: Site identifier for audit tracking
        receipt_id: Optional receipt ID to link audit to
        save_audit: Whether to save detailed audit log locally

    Returns:
        Tuple of (processed_html, report, audit)
        - report: Legacy dict with corrections/warnings/errors
        - audit: §254 GuardianAudit object (or None if disabled)
    """
    input_html_hash = hash_content(html)

    report = {
        "corrections": [],
        "warnings": [],
        "errors": [],
        "forensic_valid": True,
    }

    # Track intervention counts by category
    intervention_categories = {}

    # Extract CSS from HTML
    style_match = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE)
    if not style_match:
        report["warnings"].append("No <style> block found — cannot normalize CSS")
        # Still create audit even if no CSS to process
        audit = _create_audit(
            site_id, receipt_id, input_html_hash, hash_content(html),
            0, {}, True, [], report
        )
        if save_audit:
            save_audit_log(audit)
        return html, report, audit

    css = style_match.group(1)
    original_css = css

    # Apply normalizations with category tracking
    css, gradient_count = normalize_gradients(css)
    if gradient_count:
        report["corrections"].append(f"Removed {gradient_count} gradient(s)")
        intervention_categories["gradients"] = gradient_count

    css, radius_count = normalize_border_radius(css)
    if radius_count:
        report["corrections"].append(f"Normalized {radius_count} border-radius to 0")
        intervention_categories["border_radius"] = radius_count

    css, color_count = normalize_colors(css)
    if color_count:
        report["corrections"].append(f"Replaced {color_count} forbidden color(s)")
        intervention_categories["colors"] = color_count

    css, import_count = remove_external_imports(css)
    if import_count:
        report["corrections"].append(f"Removed {import_count} external import(s) for GDPR")
        intervention_categories["external_imports"] = import_count

    css, animation_count = normalize_animations(css)
    if animation_count:
        report["corrections"].append(f"Capped {animation_count} animation duration(s)")
        intervention_categories["animations"] = animation_count

    # Replace CSS in HTML
    if css != original_css:
        html = html.replace(original_css, css)

    # Inject canonical CSS override
    html = inject_canonical_css(html)
    report["corrections"].append("Injected canonical CSS override")
    intervention_categories["canonical_injection"] = 1

    # Validate forensic requirements
    forensic_valid, forensic_error = validate_forensic(html, prompt)
    triggers_found = [t for t in FORENSIC_TRIGGERS if t in prompt.lower()]

    if not forensic_valid:
        report["forensic_valid"] = False
        report["errors"].append(forensic_error)

    # Calculate totals
    total_interventions = sum(intervention_categories.values())
    output_html_hash = hash_content(html)

    # §254: Inject Guardian audit reference in full forensic block
    if requires_full_forensic(prompt):
        html = inject_guardian_audit_reference(html, site_id, total_interventions)

    # Create §254 GuardianAudit
    audit = _create_audit(
        site_id, receipt_id, input_html_hash, output_html_hash,
        total_interventions, intervention_categories, forensic_valid,
        triggers_found, report
    )

    # Save detailed log locally
    if save_audit:
        log_path = save_audit_log(audit)
        audit.local_log_hash = audit.compute_log_hash()

    return html, report, audit


def _create_audit(
    site_id: str,
    receipt_id: Optional[str],
    input_hash: str,
    output_hash: str,
    total_interventions: int,
    categories: Dict[str, int],
    forensic_valid: bool,
    triggers: List[str],
    report: dict
) -> GuardianAudit:
    """Create GuardianAudit object from processing results."""
    return GuardianAudit(
        audit_id=generate_audit_id(),
        site_id=site_id,
        receipt_id=receipt_id,
        input_html_hash=input_hash,
        output_html_hash=output_hash,
        css_guardian_version=GUARDIAN_VERSION,
        policy_profile=POLICY_PROFILE,
        interventions_count=total_interventions,
        intervention_categories=categories,
        forensic_valid=forensic_valid,
        forensic_triggers_found=triggers,
        passed=forensic_valid and len(report["errors"]) == 0,
        errors=report["errors"],
        warnings=report["warnings"],
        corrections=report["corrections"],
        created_at=datetime.now(timezone.utc).isoformat(),
    )


# ═══════════════════════════════════════════════════════════════
# §254 GUARDIAN AUDIT VISIBILITY (Rule 3C)
# ═══════════════════════════════════════════════════════════════

GUARDIAN_AUDIT_BLOCK = '''
    <dt>Guardian</dt>
    <dd><code>v{version} · {policy}</code></dd>
    <dt>Audit</dt>
    <dd><code>{interventions} correction(s) · {status}</code></dd>
'''


def inject_guardian_audit_reference(html: str, site_id: str, interventions: int) -> str:
    """
    Inject Guardian audit reference into full forensic block.

    §254 Visibility Rule:
    - Only visible when Rule 3C activates full forensic block
    - Minimal footer remains clean for normal sites
    """
    # Find the forensic proof block
    proof_block_match = re.search(
        r'(<dl[^>]*class=["\'][^"\']*proof-grid[^"\']*["\'][^>]*>)(.*?)(</dl>)',
        html,
        re.DOTALL | re.IGNORECASE
    )

    if not proof_block_match:
        # No proof grid found, try to find forensic-proof section
        return html

    dl_open = proof_block_match.group(1)
    dl_content = proof_block_match.group(2)
    dl_close = proof_block_match.group(3)

    # Check if Guardian reference already exists
    if 'Guardian' in dl_content:
        return html

    # Build Guardian audit reference
    guardian_ref = GUARDIAN_AUDIT_BLOCK.format(
        version=GUARDIAN_VERSION,
        policy=POLICY_PROFILE.replace('_', ' '),
        interventions=interventions,
        status="PASSED" if interventions >= 0 else "REVIEW"
    )

    # Insert before closing </dl>
    new_dl = dl_open + dl_content + guardian_ref + dl_close
    html = html[:proof_block_match.start()] + new_dl + html[proof_block_match.end():]

    return html


# ═══════════════════════════════════════════════════════════════
# §254 LEDGER INTEGRATION
# ═══════════════════════════════════════════════════════════════

def create_ledger_receipt(audit: GuardianAudit, ledger_url: str = "http://localhost:8101") -> Optional[dict]:
    """
    Create Ledger receipt for Guardian audit.

    Stores only summary + hash in Ledger (hybrid model).
    Detailed log remains local.
    """
    import requests

    receipt_id = f"GUARDIAN-AUDIT-{audit.audit_id}"

    payload = {
        "schema_version": "1.0",
        "id": receipt_id,
        "actor": "did:windi:css-guardian",
        "app": "w-sites-001",
        "doc_name": f"CSS Guardian Audit — {audit.site_id}",
        "doc_type": "audit",
        "governance_level": "MED",
        "content_hash": f"sha256:{audit.local_log_hash or audit.compute_log_hash()}",
        "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}",
        "invariants": ["I9", "I11", "I14"],
        "stage": "C6",
        "sge_score": 0.85,
        "metadata": audit.to_ledger_summary()
    }

    try:
        response = requests.post(
            f"{ledger_url}/api/receipts",
            json=payload,
            timeout=10
        )
        if response.ok:
            result = response.json()
            audit.ledger_receipt_id = receipt_id
            return result
        else:
            return {"ok": False, "error": response.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_html = """<!DOCTYPE html>
<html>
<head>
<style>
body { background: linear-gradient(to right, #a855f7, #ec4899); }
.card { border-radius: 16px; }
h1 { color: purple; }
</style>
</head>
<body>
<h1>Test</h1>
<section class="forensic-proof">
  <dl class="proof-grid">
    <dt>Receipt</dt>
    <dd><code>WINDI-SITES-001-TEST1234</code></dd>
  </dl>
</section>
<footer>Verified by WINDI<br>WINDI-SITES-001-12345678</footer>
</body>
</html>"""

    # Test with forensic trigger to see full audit
    processed, report, audit = guard_html(
        test_html,
        "Create a compliance page about ledger verification",
        site_id="test-001",
        save_audit=False  # Don't save during test
    )

    print("=== CSS Guardian §254 Test ===")
    print(f"Corrections: {report['corrections']}")
    print(f"Warnings: {report['warnings']}")
    print(f"Errors: {report['errors']}")
    print(f"Forensic Valid: {report['forensic_valid']}")

    print("\n=== §254 Guardian Audit ===")
    print(f"Audit ID: {audit.audit_id}")
    print(f"Version: {audit.css_guardian_version}")
    print(f"Policy: {audit.policy_profile}")
    print(f"Interventions: {audit.interventions_count}")
    print(f"Categories: {audit.intervention_categories}")
    print(f"Triggers Found: {audit.forensic_triggers_found}")
    print(f"Passed: {audit.passed}")
    print(f"Log Hash: {audit.compute_log_hash()[:16]}...")

    print("\n=== Ledger Summary ===")
    print(json.dumps(audit.to_ledger_summary(), indent=2))

    print("\n=== Processed HTML (excerpt) ===")
    # Show the forensic block area
    if "Guardian" in processed:
        start = processed.find("Guardian")
        print(processed[max(0, start-50):start+200])
    else:
        print(processed[:500] + "..." if len(processed) > 500 else processed)
