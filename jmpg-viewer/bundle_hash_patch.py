#!/usr/bin/env python3
"""
WINDI JMPG Export Engine — Bundle Hash Patch
=============================================
Apply to: /opt/windi/export-engine/ (or wherever the export script lives)

This module provides the corrected hash flow:
1. content_hash = SHA-256(canonical JSON of blocks) — ALREADY WORKING
2. bundle_hash = SHA-256(final .jmpg bytes) — NEW

Usage:
    from bundle_hash_patch import sha256_file, sha256_bytes, create_deterministic_zip

After the ZIP is closed:
    bundle_hash = sha256_file(jmpg_path)
    # Register bundle_hash + size in Ledger
"""

import hashlib
import zipfile
import json
from pathlib import Path


# ============================================================
# CORE: Hash functions
# ============================================================

def sha256_bytes(data: bytes) -> str:
    """SHA-256 of raw bytes. Use for in-memory data."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    """SHA-256 of a file, reading in 1MB chunks. Memory-safe for large bundles."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj) -> str:
    """
    Reproduce Python's json.dumps(obj, separators=(',',':'), sort_keys=True).
    This is the canonical form for content_hash.
    """
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def content_hash_from_blocks(blocks: list) -> str:
    """Calculate content_hash from the blocks array (canonical form)."""
    return sha256_bytes(canonical_json(blocks).encode("utf-8"))


# ============================================================
# DETERMINISTIC ZIP (optional but recommended)
# ============================================================

FIXED_DT = (2026, 1, 1, 0, 0, 0)  # Fixed timestamp for reproducibility


def create_deterministic_zip(out_path: str, files: dict) -> tuple:
    """
    Create a .jmpg ZIP with deterministic properties.
    
    Args:
        out_path: Path for the output .jmpg file
        files: Dict of {arcname: bytes_or_str} to include in the ZIP
    
    Returns:
        (bundle_hash, bundle_size) calculated from the closed ZIP
    """
    sorted_names = sorted(files.keys())

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name in sorted_names:
            info = zipfile.ZipInfo(filename=name, date_time=FIXED_DT)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16  # Fixed permissions

            data = files[name]
            if isinstance(data, str):
                data = data.encode("utf-8")
            zf.writestr(info, data)

    # Calculate bundle_hash AFTER the ZIP is fully closed
    bundle_hash = sha256_file(out_path)
    bundle_size = Path(out_path).stat().st_size

    return bundle_hash, bundle_size


# ============================================================
# LEDGER REGISTRATION (enhanced payload)
# ============================================================

def build_ledger_payload(
    receipt_id: str,
    content_hash: str,
    bundle_hash: str,
    bundle_size: int,
    title: str = "",
    author: str = "",
    template: str = "",
    block_count: int = 0,
) -> dict:
    """
    Build the enhanced Ledger payload with both content_hash and bundle_hash.
    
    POST this to http://127.0.0.1:8101/api/receipts
    """
    return {
        "id": receipt_id,
        "doc_id": receipt_id,
        "action": "JMPG_EXPORT",
        "integrity_hash": content_hash,       # backwards compatible field
        "bundle_hash": bundle_hash,            # NEW: hash of final .jmpg bytes
        "size_bytes": bundle_size,             # NEW: for size validation
        "metadata_json": json.dumps({
            "title": title,
            "author": author,
            "template": template,
            "block_count": block_count,
            "content_hash": content_hash,      # also in metadata for reference
            "bundle_hash": bundle_hash,        # also in metadata for reference
            "hash_algorithm": "SHA-256",
        }),
    }


# ============================================================
# INTEGRATION EXAMPLE
# ============================================================

def export_jmpg_with_bundle_hash(
    content_blocks: list,
    title: str,
    author: str,
    template: str,
    out_path: str,
    receipt_id: str,
) -> dict:
    """
    Complete export flow with dual-hash integrity.
    
    Returns dict with all hash info for the response.
    """
    # 1. Content hash (deterministic, independent of packaging)
    c_hash = content_hash_from_blocks(content_blocks)

    # 2. Build all files for the bundle
    manifest = {
        "jmpg_version": "JMPG-1.0",
        "engine_version": "1.1.0",  # bumped for bundle_hash support
        "package_id": receipt_id,
        "title": title,
        "author": author,
        "template": template,
        "content_hash": c_hash,
        "media_count": 0,
        "integrity": {
            "algorithm": "SHA-256",
            "content_hash": c_hash,
            # NOTE: bundle_hash is NOT here — it lives in the Ledger only
        },
        "governance": {
            "receipt_id": receipt_id,
        },
    }

    content = {
        "version": "JMPG-1.0",
        "blocks": content_blocks,
        "block_count": len(content_blocks),
        "content_hash": c_hash,
    }

    receipt_data = {
        "receipt_id": receipt_id,
        "content_hash": c_hash,
        # bundle_hash will be added to Ledger separately
    }

    hash_txt = (
        f"WINDI JMPG Integrity Record\n"
        f"{'='*40}\n"
        f"Package:      {receipt_id}\n"
        f"Title:        {title}\n"
        f"Content Hash: {c_hash}\n"
        f"Algorithm:    SHA-256\n"
        f"{'='*40}\n"
        f"Bundle hash: verify against Forensic Ledger\n"
    )

    preview = f"# {title}\n"

    # 3. Create deterministic ZIP
    files = {
        "manifest.json": json.dumps(manifest, indent=2, ensure_ascii=False),
        "content.json": json.dumps(content, indent=2, ensure_ascii=False),
        "receipt.json": json.dumps(receipt_data, indent=2, ensure_ascii=False),
        "hash.txt": hash_txt,
        "preview.txt": preview,
    }

    bundle_hash, bundle_size = create_deterministic_zip(out_path, files)

    # 4. Build Ledger payload (to POST to :8101)
    ledger_payload = build_ledger_payload(
        receipt_id=receipt_id,
        content_hash=c_hash,
        bundle_hash=bundle_hash,
        bundle_size=bundle_size,
        title=title,
        author=author,
        template=template,
        block_count=len(content_blocks),
    )

    return {
        "receipt_id": receipt_id,
        "content_hash": c_hash,
        "bundle_hash": bundle_hash,
        "bundle_size": bundle_size,
        "ledger_payload": ledger_payload,
    }


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    import tempfile
    import os

    print("=== WINDI JMPG Bundle Hash Patch — Self-Test ===\n")

    blocks = [
        {"type": "heading", "content": "Test Document", "level": 1},
        {"type": "paragraph", "content": "Hash alignment test."},
    ]

    with tempfile.NamedTemporaryFile(suffix=".jmpg", delete=False) as f:
        tmp_path = f.name

    try:
        result = export_jmpg_with_bundle_hash(
            content_blocks=blocks,
            title="Self-Test",
            author="patch-test",
            template="generic",
            out_path=tmp_path,
            receipt_id="TEST-20260218-PATCH01",
        )

        print(f"Receipt ID:   {result['receipt_id']}")
        print(f"Content Hash: {result['content_hash']}")
        print(f"Bundle Hash:  {result['bundle_hash']}")
        print(f"Bundle Size:  {result['bundle_size']} bytes")

        # Verify: re-read and hash
        verify_hash = sha256_file(tmp_path)
        print(f"\nVerify Hash:  {verify_hash}")
        print(f"Match:        {'✅ PASS' if verify_hash == result['bundle_hash'] else '❌ FAIL'}")

        # Determinism test: create again
        result2 = export_jmpg_with_bundle_hash(
            content_blocks=blocks,
            title="Self-Test",
            author="patch-test",
            template="generic",
            out_path=tmp_path,
            receipt_id="TEST-20260218-PATCH01",
        )
        print(f"\nDeterminism:  {'✅ IDENTICAL' if result['bundle_hash'] == result2['bundle_hash'] else '❌ DIFFERENT'}")
        print(f"  Hash 1: {result['bundle_hash']}")
        print(f"  Hash 2: {result2['bundle_hash']}")

    finally:
        os.unlink(tmp_path)

    print("\n=== Self-Test Complete ===")
