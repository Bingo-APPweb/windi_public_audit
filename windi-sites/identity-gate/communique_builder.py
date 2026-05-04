"""
W-COMM-002 — Communiqué Builder
================================
§244 Sprint 3.1 — Evidence Distribution

"Email não é mais texto. Agora, email é prova."

Builds JMPG (ZIP) packages for forensic evidence distribution.
Envelope limit: 25KB (Spec Multimídia v1.1)

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
"""

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Any

ENVELOPE_LIMIT = 25_600  # 25KB hard cap (Spec Multimídia v1.1)
SCHEMA_VERSION = "windi.communique.v1"


def _sha256(data: bytes) -> str:
    """Compute SHA-256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


def build_communique_manifest(
    receipt_id: str,
    actor_did: str,
    actor_handle: str,
    artifact_type: str,
    artifact_title: str,
    artifact_url: str,
    artifact_sha256: str,
    receipt_sha256: str,
    html_sha256: str,
    size_bytes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Build manifest.json for Communiqué package.

    Schema: windi.communique.v1
    """
    return {
        "schema": SCHEMA_VERSION,
        "receipt_id": receipt_id,
        "issued_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "actor": {
            "did": actor_did,
            "handle": actor_handle
        },
        "artifact": {
            "type": artifact_type,
            "title": artifact_title,
            "url": artifact_url,
            "sha256": artifact_sha256
        },
        "files": [
            {"path": "evidence/receipt.json", "sha256": receipt_sha256},
            {"path": "evidence/artifact.html", "sha256": html_sha256}
        ],
        "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}",
        "envelope": {
            "limit_bytes": ENVELOPE_LIMIT,
            "size_bytes": size_bytes
        },
        "constitutional": {
            "principle": "AI processes. Human decides. WINDI guarantees.",
            "invariants": ["I1", "I9", "I11"]
        }
    }


def build_communique_jmpg(
    receipt: dict,
    artifact_html: str,
    actor_did: str,
    actor_handle: str,
    output_dir: Path,
    artifact_type: str = "microlog",
    artifact_title: str = "",
    artifact_url: str = ""
) -> Dict[str, Any]:
    """
    Build a COMMUNIQUÉ.JMPG (ZIP) from a sealed receipt and HTML snapshot.

    Fails hard if exceeds 25KB envelope.

    Args:
        receipt: The Ledger receipt dict
        artifact_html: HTML content snapshot (should be minimized)
        actor_did: DID of the sender
        actor_handle: Human-readable handle (@name)
        output_dir: Where to write the .jmpg file
        artifact_type: Type of artifact (microlog, site, doc)
        artifact_title: Title for the manifest
        artifact_url: Public URL of the artifact

    Returns:
        {
            "ok": True,
            "path": "/path/to/file.jmpg",
            "size_bytes": 12345,
            "receipt_id": "WINDI-...",
            "manifest": {...}
        }

    Raises:
        ValueError if envelope exceeded
    """
    receipt_id = receipt.get("receipt_id") or receipt.get("id")
    if not receipt_id:
        raise ValueError("Receipt must have receipt_id or id field")

    # Serialize components
    receipt_bytes = json.dumps(receipt, ensure_ascii=False, indent=2).encode("utf-8")
    html_bytes = artifact_html.encode("utf-8")

    # Compute hashes
    receipt_sha256 = _sha256(receipt_bytes)
    html_sha256 = _sha256(html_bytes)

    # Build manifest (without size_bytes first)
    manifest = build_communique_manifest(
        receipt_id=receipt_id,
        actor_did=actor_did,
        actor_handle=actor_handle,
        artifact_type=artifact_type,
        artifact_title=artifact_title or receipt.get("doc_name", "Untitled"),
        artifact_url=artifact_url,
        artifact_sha256=html_sha256,
        receipt_sha256=receipt_sha256,
        html_sha256=html_sha256,
        size_bytes=None
    )
    manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")

    # Build ZIP in memory first to measure size
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("evidence/receipt.json", receipt_bytes)
        z.writestr("evidence/artifact.html", html_bytes)
        z.writestr("manifest.json", manifest_bytes)

    size = buf.tell()

    # Hard envelope check
    if size > ENVELOPE_LIMIT:
        raise ValueError(
            f"COMMUNIQUÉ exceeds envelope: {size} bytes > {ENVELOPE_LIMIT} bytes. "
            f"Reduce HTML snapshot or compress receipt."
        )

    # Re-build with size_bytes filled in
    manifest["envelope"]["size_bytes"] = size
    manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")

    # Write to disk
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Safe filename
    safe_id = receipt_id.replace("/", "-").replace(":", "-")
    output_path = output_dir / f"evidence_{safe_id}.jmpg"

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("evidence/receipt.json", receipt_bytes)
        z.writestr("evidence/artifact.html", html_bytes)
        z.writestr("manifest.json", manifest_bytes)

    return {
        "ok": True,
        "path": str(output_path),
        "size_bytes": size,
        "receipt_id": receipt_id,
        "manifest": manifest,
        "envelope_usage": f"{size}/{ENVELOPE_LIMIT} bytes ({100*size//ENVELOPE_LIMIT}%)"
    }


def build_dispatch_mailto(
    receipt_id: str,
    title: str,
    content_snippet: str,
    artifact_url: str,
    verify_url: Optional[str] = None
) -> str:
    """
    Generate mailto: URL for V1 dispatch (opens email client).

    Returns:
        mailto: URL string ready for href or window.location
    """
    import urllib.parse

    if not verify_url:
        verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"

    subject = f"[VERIFIED] {title} — Ref: #{receipt_id}"

    body_lines = [
        "O documento abaixo foi processado sob governança constitucional",
        "e selado no Forensic Ledger.",
        "",
        f"Resumo da Evidência: {content_snippet[:200]}",
        f"Artefacto: {artifact_url}",
        "",
        "Status de Integridade: ⚓ SOVEREIGN (100%)",
        f"Receipt (verificação pública): {verify_url}",
        "",
        "—",
        "AI processes. Human decides. WINDI guarantees."
    ]
    body = "\n".join(body_lines)

    return f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"


# ═══════════════════════════════════════════════════════════════════════════
# CLI for testing
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    print("W-COMM-002 Communiqué Builder")
    print("Usage: python communique_builder.py <receipt_id> <html_path> <output_dir>")
    print()

    if len(sys.argv) < 4:
        print("Example:")
        print("  python communique_builder.py WINDI-MICROLOG-123 /path/to/artifact.html /tmp/communique/")
        sys.exit(1)

    receipt_id = sys.argv[1]
    html_path = Path(sys.argv[2])
    output_dir = Path(sys.argv[3])

    # Mock receipt for testing
    mock_receipt = {
        "receipt_id": receipt_id,
        "doc_name": "Test Microlog",
        "content_hash": "sha256:test",
        "actor": "did:windi:test",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    html_content = html_path.read_text(encoding="utf-8")

    result = build_communique_jmpg(
        receipt=mock_receipt,
        artifact_html=html_content,
        actor_did="did:windi:test",
        actor_handle="@test",
        output_dir=output_dir,
        artifact_type="microlog",
        artifact_title="Test Microlog"
    )

    print(f"Built: {result['path']}")
    print(f"Size: {result['envelope_usage']}")
