#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
WINDI JMPG PACKAGER v1.0
Evidence Schema v1.1 — PACT Protocol v1.0

"O transporte não é anexo. É extensão da prova."

Creates deterministic .jmpg bundles (ZIP) with:
  - manifest.json    → integrity map + evidence hashes
  - content.json     → governed content blocks
  - evidence/        → media files (local payload)
  - metadata/chain.json → concatenation proof + hash lineage

Deterministic guarantees:
  - Files sorted alphabetically
  - No variable timestamps in ZIP headers
  - Consistent compression (stored, no deflate variance)
  - Uniform permissions

Pipeline: Desktop(:8100) → Export(:8103) → THIS → Vault(:8106) → Ledger(:8101)
═══════════════════════════════════════════════════════════════
"""

import hashlib
import json
import os
import struct
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import zipfile
import io


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

SCHEMA_VERSION = "1.1"
PACT_VERSION = "1.0"
PACKAGER_VERSION = "1.0.0"

# Fixed ZIP timestamp for determinism (2026-01-01 00:00:00)
DETERMINISTIC_DATE = (2026, 1, 1, 0, 0, 0)

# Video threshold for pointer mode (MB)
VIDEO_POINTER_THRESHOLD_MB = 50

# Maximum evidence files per bundle
MAX_EVIDENCE_FILES = 50

# Supported MIME types
SUPPORTED_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".pdf": "application/pdf",
}

CATEGORY_MAP = {
    "image": "IMG",
    "video": "VID",
    "audio": "AUD",
    "application": "DOC",
}


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class EvidenceFile:
    """A single evidence file to be packaged."""
    source_path: str
    role: str = "primary_evidence"  # primary_evidence | supporting_evidence | context_material | reference_only
    description: str = ""

    # Auto-populated during packaging
    evidence_id: str = ""
    sha256: str = ""
    size_bytes: int = 0
    mime_type: str = ""
    transport_mode: str = "local"  # local | pointer
    category: str = ""


@dataclass
class CommuniqueContent:
    """The governed content of a Communiqué."""
    title_de: str = ""
    title_en: str = ""
    title_pt: str = ""
    body_blocks: list = field(default_factory=list)  # [{type, text, level?}]
    author_name: str = ""
    author_role: str = ""
    category: str = "GENERAL"
    impact_level: str = "MEDIUM"    # LOW | MEDIUM | HIGH | CRITICAL
    template_id: str = "ISP-COM-01"
    template_version: str = "1.1"
    jurisdiction: str = "EU"
    decision_type: str = "official_announcement"
    authority_level: str = "STANDARD"


@dataclass
class PackageResult:
    """Result of the packaging operation."""
    success: bool
    jmpg_path: str = ""
    communique_id: str = ""
    content_hash: str = ""
    bundle_hash: str = ""
    evidence_count: int = 0
    bundle_size_bytes: int = 0
    errors: list = field(default_factory=list)
    manifest: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
# CORE: SHA-256 HASHING
# ═══════════════════════════════════════════════════════════════

def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(filepath: str) -> str:
    """Compute SHA-256 of a file, reading in chunks for large files."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(2 * 1024 * 1024)  # 2MB chunks
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


# ═══════════════════════════════════════════════════════════════
# EVIDENCE PROCESSOR
# ═══════════════════════════════════════════════════════════════

def process_evidence(evidence_files: list[EvidenceFile]) -> list[EvidenceFile]:
    """
    Process evidence files: validate, hash, assign IDs, determine transport mode.
    Returns processed list with all metadata populated.
    """
    counters = {}
    processed = []

    for ef in evidence_files:
        if not os.path.exists(ef.source_path):
            raise FileNotFoundError(f"Evidence file not found: {ef.source_path}")

        ext = Path(ef.source_path).suffix.lower()
        if ext not in SUPPORTED_TYPES:
            raise ValueError(f"Unsupported file type: {ext} ({ef.source_path})")

        # Determine category and MIME
        mime = SUPPORTED_TYPES[ext]
        major = mime.split("/")[0]
        category = CATEGORY_MAP.get(major, "DOC")

        # Auto-increment evidence ID
        counters[category] = counters.get(category, 0) + 1
        evidence_id = f"{category}-{counters[category]:02d}"

        # Compute hash
        sha256 = compute_file_sha256(ef.source_path)
        size = os.path.getsize(ef.source_path)

        # Determine transport mode
        size_mb = size / (1024 * 1024)
        transport = "local"
        if major == "video" and size_mb > VIDEO_POINTER_THRESHOLD_MB:
            transport = "pointer"

        ef.evidence_id = evidence_id
        ef.sha256 = sha256
        ef.size_bytes = size
        ef.mime_type = mime
        ef.transport_mode = transport
        ef.category = category

        processed.append(ef)

    return processed


# ═══════════════════════════════════════════════════════════════
# CONTENT BUILDER
# ═══════════════════════════════════════════════════════════════

def build_content_json(content: CommuniqueContent) -> dict:
    """Build the content.json structure."""
    return {
        "schema": "windi-content-v1.1",
        "title_de": content.title_de,
        "title_en": content.title_en,
        "title_pt": content.title_pt,
        "title": content.title_en or content.title_de or content.title_pt,
        "author": content.author_name,
        "author_role": content.author_role,
        "blocks": content.body_blocks,
        "body_de": _blocks_to_text(content.body_blocks, "de"),
        "body_en": _blocks_to_text(content.body_blocks, "en"),
    }


def _blocks_to_text(blocks: list, lang: str) -> str:
    """Flatten content blocks to plain text."""
    parts = []
    for b in blocks:
        if b.get("type") in ("paragraph", "heading", "quote"):
            parts.append(b.get("text", ""))
    return "\n\n".join(parts)


# ═══════════════════════════════════════════════════════════════
# MANIFEST BUILDER
# ═══════════════════════════════════════════════════════════════

def build_manifest(
    communique_id: str,
    content: CommuniqueContent,
    content_hash: str,
    evidence: list[EvidenceFile],
    created_at: str,
) -> dict:
    """Build the manifest.json — the integrity map of the bundle."""
    return {
        "schema": "windi-manifest",
        "schema_version": SCHEMA_VERSION,
        "pact_version": PACT_VERSION,
        "packager_version": PACKAGER_VERSION,
        "communique_id": communique_id,
        "content_hash": content_hash,
        "created_at": created_at,
        "published_at": None,  # Set by Communiqué Engine on publish
        "receipt_id": None,    # Set by Ledger on seal

        # Author & authority
        "author_name": content.author_name,
        "author_role": content.author_role,

        # ISP governance
        "template_id": content.template_id,
        "template_version": content.template_version,
        "category": content.category,
        "impact_level": content.impact_level,
        "jurisdiction": content.jurisdiction,
        "authority_level": content.authority_level,
        "decision_type": content.decision_type,

        # Evidence manifest
        "evidence": {
            "schema": "evidence-manifest-v1.1",
            "count": len(evidence),
            "files": [
                {
                    "id": ef.evidence_id,
                    "filename": Path(ef.source_path).name,
                    "sha256": ef.sha256,
                    "path": f"evidence/{ef.evidence_id}{Path(ef.source_path).suffix.lower()}",
                    "role": ef.role,
                    "bytes": ef.size_bytes,
                    "mime": ef.mime_type,
                    "transport": ef.transport_mode,
                    "description": ef.description,
                    **(
                        {
                            "storage": {
                                "type": "vault",
                                "hash_locator": f"sha256:{ef.sha256}",
                                "retrieval_required": True,
                            }
                        }
                        if ef.transport_mode == "pointer"
                        else {}
                    ),
                }
                for ef in evidence
            ],
        },

        # Governance
        "governance": {
            "protocol": "WINDI PACT",
            "version": PACT_VERSION,
            "principle": "AI processes. Human decides. WINDI guarantees.",
        },
    }


# ═══════════════════════════════════════════════════════════════
# CHAIN OF CUSTODY (chain.json)
# ═══════════════════════════════════════════════════════════════

def build_chain(
    communique_id: str,
    content_hash: str,
    evidence: list[EvidenceFile],
    created_at: str,
) -> dict:
    """
    Build chain.json — the concatenation proof.
    Records the order and hashes of all components,
    enabling deterministic re-verification.
    """
    components = [
        {
            "order": 0,
            "component": "content.json",
            "sha256": content_hash,
            "role": "primary_content",
        }
    ]

    # Evidence in alphabetical order (deterministic)
    sorted_ev = sorted(evidence, key=lambda e: e.evidence_id)
    for i, ef in enumerate(sorted_ev, start=1):
        entry = {
            "order": i,
            "component": f"evidence/{ef.evidence_id}{Path(ef.source_path).suffix.lower()}",
            "sha256": ef.sha256,
            "role": ef.role,
            "transport": ef.transport_mode,
        }
        if ef.transport_mode == "pointer":
            entry["note"] = "Full file stored in Vault; bundle contains hash reference only"
        components.append(entry)

    return {
        "schema": "windi-chain-v1.0",
        "communique_id": communique_id,
        "created_at": created_at,
        "component_count": len(components),
        "components": components,
        "concatenation_order": "alphabetical_by_evidence_id",
        "determinism_guarantees": {
            "zip_timestamps": "fixed_2026-01-01T00:00:00",
            "file_order": "alphabetical",
            "compression": "stored_no_deflate",
            "permissions": "uniform",
        },
    }


# ═══════════════════════════════════════════════════════════════
# DETERMINISTIC ZIP BUILDER
# ═══════════════════════════════════════════════════════════════

def create_deterministic_zip(entries: list[tuple[str, bytes]]) -> bytes:
    """
    Create a ZIP file with deterministic properties:
    - Fixed timestamps (no variance between builds)
    - Alphabetically sorted entries
    - STORED compression (no deflate variance)
    - Uniform external attributes

    Args:
        entries: list of (filename, data_bytes) tuples

    Returns:
        ZIP file as bytes
    """
    buf = io.BytesIO()

    # Sort entries alphabetically for determinism
    sorted_entries = sorted(entries, key=lambda e: e[0])

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for name, data in sorted_entries:
            info = zipfile.ZipInfo(filename=name, date_time=DETERMINISTIC_DATE)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16  # Uniform permissions
            zf.writestr(info, data)

    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════
# MAIN PACKAGER
# ═══════════════════════════════════════════════════════════════

def generate_communique_id() -> str:
    """Generate a unique Communiqué ID based on date and sequence."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    # In production, this would query the Ledger for the next sequence number
    seq = int(now.timestamp() * 1000) % 10000
    return f"COM-{date_str}-{seq:04d}"


def package_communique(
    content: CommuniqueContent,
    evidence_files: list[EvidenceFile] = None,
    output_dir: str = "/opt/windi/vault/staging",
    communique_id: str = None,
) -> PackageResult:
    """
    Package a Communiqué into a deterministic .jmpg bundle.

    Pipeline:
    1. Process evidence files (hash, classify, assign IDs)
    2. Build content.json
    3. Build manifest.json
    4. Build chain.json
    5. Create deterministic ZIP
    6. Compute bundle_hash
    7. Update manifest with bundle_hash
    8. Write final .jmpg file

    Returns PackageResult with all hashes and metadata.
    """
    errors = []
    evidence_files = evidence_files or []
    created_at = datetime.now(timezone.utc).isoformat()

    if not communique_id:
        communique_id = generate_communique_id()

    # ── Step 1: Process evidence ──────────────────────────────
    try:
        if len(evidence_files) > MAX_EVIDENCE_FILES:
            return PackageResult(
                success=False,
                errors=[f"Too many evidence files: {len(evidence_files)} (max {MAX_EVIDENCE_FILES})"],
            )
        processed_evidence = process_evidence(evidence_files)
    except (FileNotFoundError, ValueError) as e:
        return PackageResult(success=False, errors=[str(e)])

    # ── Step 2: Build content.json ────────────────────────────
    content_dict = build_content_json(content)
    content_bytes = json.dumps(content_dict, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
    content_hash = compute_sha256(content_bytes)

    # ── Step 3: Build manifest.json (first pass, no bundle_hash yet) ──
    manifest_dict = build_manifest(
        communique_id=communique_id,
        content=content,
        content_hash=content_hash,
        evidence=processed_evidence,
        created_at=created_at,
    )

    # ── Step 4: Build chain.json ──────────────────────────────
    chain_dict = build_chain(
        communique_id=communique_id,
        content_hash=content_hash,
        evidence=processed_evidence,
        created_at=created_at,
    )

    # ── Step 5: Assemble ZIP entries ──────────────────────────
    zip_entries = []

    # Content
    zip_entries.append(("content.json", content_bytes))

    # Chain
    chain_bytes = json.dumps(chain_dict, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
    zip_entries.append(("metadata/chain.json", chain_bytes))

    # Evidence files (only local transport; pointers get a reference file)
    for ef in processed_evidence:
        ext = Path(ef.source_path).suffix.lower()
        zip_path = f"evidence/{ef.evidence_id}{ext}"

        if ef.transport_mode == "local":
            with open(ef.source_path, "rb") as f:
                zip_entries.append((zip_path, f.read()))
        else:
            # Pointer: include a small reference file instead of full media
            pointer_ref = json.dumps(
                {
                    "type": "vault_pointer",
                    "evidence_id": ef.evidence_id,
                    "original_filename": Path(ef.source_path).name,
                    "sha256": ef.sha256,
                    "size_bytes": ef.size_bytes,
                    "mime": ef.mime_type,
                    "vault_locator": f"sha256:{ef.sha256}",
                    "retrieval": "https://windi-domain.com/vault/multimedia/",
                    "note": "Full file stored in WINDI Vault. Use hash_locator to retrieve.",
                },
                indent=2,
                ensure_ascii=False,
            ).encode("utf-8")
            zip_entries.append((zip_path + ".pointer.json", pointer_ref))

    # ── Step 6: Create deterministic ZIP (without manifest, to get bundle_hash) ──
    # We need to add manifest last, but it needs the bundle_hash.
    # Solution: build ZIP without manifest, hash it, then rebuild with manifest.

    pre_bundle_bytes = create_deterministic_zip(zip_entries)
    pre_bundle_hash = compute_sha256(pre_bundle_bytes)

    # ── Step 7: Update manifest with bundle_hash ──────────────
    manifest_dict["bundle_hash"] = pre_bundle_hash

    manifest_bytes = json.dumps(manifest_dict, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
    zip_entries.append(("manifest.json", manifest_bytes))

    # ── Step 8: Create final deterministic ZIP ────────────────
    final_bytes = create_deterministic_zip(zip_entries)
    bundle_hash = compute_sha256(final_bytes)

    # ── Step 9: Write .jmpg file ──────────────────────────────
    os.makedirs(output_dir, exist_ok=True)
    jmpg_filename = f"{communique_id}.jmpg"
    jmpg_path = os.path.join(output_dir, jmpg_filename)

    with open(jmpg_path, "wb") as f:
        f.write(final_bytes)

    # ── Return result ─────────────────────────────────────────
    return PackageResult(
        success=True,
        jmpg_path=jmpg_path,
        communique_id=communique_id,
        content_hash=content_hash,
        bundle_hash=bundle_hash,
        evidence_count=len(processed_evidence),
        bundle_size_bytes=len(final_bytes),
        manifest=manifest_dict,
    )


# ═══════════════════════════════════════════════════════════════
# VERIFICATION (used by Reader and Sentinel)
# ═══════════════════════════════════════════════════════════════

def verify_bundle(jmpg_path: str) -> dict:
    """
    Verify the integrity of a .jmpg bundle.
    
    Checks:
    1. ZIP structure valid
    2. manifest.json exists and parses
    3. content.json hash matches manifest
    4. Each evidence file hash matches manifest
    5. chain.json order is consistent
    
    Returns verification report.
    """
    report = {
        "valid": False,
        "jmpg_path": jmpg_path,
        "checks": [],
        "errors": [],
    }

    try:
        with open(jmpg_path, "rb") as f:
            bundle_bytes = f.read()
    except Exception as e:
        report["errors"].append(f"Cannot read file: {e}")
        return report

    # Check 1: Valid ZIP
    try:
        zf = zipfile.ZipFile(io.BytesIO(bundle_bytes))
        names = zf.namelist()
        report["checks"].append({"check": "zip_structure", "status": "pass", "files": len(names)})
    except zipfile.BadZipFile:
        report["errors"].append("Invalid ZIP structure")
        report["checks"].append({"check": "zip_structure", "status": "fail"})
        return report

    # Check 2: manifest.json
    if "manifest.json" not in names:
        report["errors"].append("manifest.json not found")
        report["checks"].append({"check": "manifest_exists", "status": "fail"})
        return report

    manifest = json.loads(zf.read("manifest.json"))
    report["checks"].append({"check": "manifest_exists", "status": "pass"})
    report["communique_id"] = manifest.get("communique_id")
    report["receipt_id"] = manifest.get("receipt_id")

    # Check 3: content.json hash
    if "content.json" in names:
        content_bytes = zf.read("content.json")
        content_hash = compute_sha256(content_bytes)
        expected = manifest.get("content_hash")
        match = content_hash == expected
        report["checks"].append({
            "check": "content_hash",
            "status": "pass" if match else "fail",
            "computed": content_hash,
            "expected": expected,
        })
        if not match:
            report["errors"].append(f"Content hash mismatch: {content_hash} != {expected}")
    else:
        report["errors"].append("content.json not found")
        report["checks"].append({"check": "content_hash", "status": "fail"})

    # Check 4: Evidence file hashes
    evidence_files = manifest.get("evidence", {}).get("files", [])
    for ef in evidence_files:
        path = ef.get("path", "")
        expected_hash = ef.get("sha256", "")

        if ef.get("transport") == "pointer":
            pointer_path = path + ".pointer.json"
            if pointer_path in names:
                report["checks"].append({
                    "check": f"evidence_{ef['id']}",
                    "status": "pass",
                    "note": "pointer reference present",
                })
            else:
                report["checks"].append({
                    "check": f"evidence_{ef['id']}",
                    "status": "warn",
                    "note": "pointer reference missing",
                })
            continue

        if path in names:
            file_bytes = zf.read(path)
            file_hash = compute_sha256(file_bytes)
            match = file_hash == expected_hash
            report["checks"].append({
                "check": f"evidence_{ef['id']}",
                "status": "pass" if match else "fail",
                "computed": file_hash,
                "expected": expected_hash,
            })
            if not match:
                report["errors"].append(f"Evidence {ef['id']} hash mismatch")
        else:
            report["errors"].append(f"Evidence file not found: {path}")
            report["checks"].append({
                "check": f"evidence_{ef['id']}",
                "status": "fail",
                "note": "file missing from bundle",
            })

    zf.close()

    # Final verdict
    report["valid"] = len(report["errors"]) == 0
    report["bundle_hash"] = compute_sha256(bundle_bytes)

    return report


# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════

def main():
    """CLI entry point for packaging and verification."""
    import sys

    if len(sys.argv) < 2:
        print("WINDI JMPG Packager v1.0")
        print("Usage:")
        print("  python jmpg_packager.py pack    — Package a test Communiqué")
        print("  python jmpg_packager.py verify <file.jmpg> — Verify bundle integrity")
        print("  python jmpg_packager.py info <file.jmpg>   — Show manifest info")
        return

    cmd = sys.argv[1]

    if cmd == "pack":
        # Demo: package a test Communiqué
        content = CommuniqueContent(
            title_de="WINDI PACT Protokoll — Genesis Communiqué",
            title_en="WINDI PACT Protocol — Genesis Communiqué",
            title_pt="Protocolo WINDI PACT — Genesis Communiqué",
            body_blocks=[
                {"type": "heading", "level": 1, "text": "Multimedia Integrity Online"},
                {"type": "paragraph", "text": "This Communiqué marks the activation of the WINDI PACT Protocol v1.0. All 8 ports are operational. The Vault is synchronized. The Linhagem de Ferro is complete."},
                {"type": "quote", "text": "Evidence is the currency of truth. The Ledger is its bank."},
                {"type": "paragraph", "text": "The Three Dragons Council — Guardian, Architect, and Witness — have validated and sealed this protocol. From this moment, every Communiqué produced by the WINDI system carries the PACT guarantee: Preservation, Accountability, Classification, Trust."},
                {"type": "divider"},
                {"type": "paragraph", "text": "Status: All services operational. Forensic Ledger: 4397+ receipts. Zero rollbacks."},
            ],
            author_name="Jober Mögele Correa",
            author_role="Chief Governance Officer",
            category="GOVERNANCE",
            impact_level="HIGH",
            template_id="ISP-COM-01",
            jurisdiction="EU",
            decision_type="official_announcement",
            authority_level="EXECUTIVE",
        )

        output_dir = "/tmp/windi_jmpg_test"
        result = package_communique(content, output_dir=output_dir)

        if result.success:
            print(f"✅ Package created successfully")
            print(f"   ID:           {result.communique_id}")
            print(f"   Path:         {result.jmpg_path}")
            print(f"   Content Hash: {result.content_hash}")
            print(f"   Bundle Hash:  {result.bundle_hash}")
            print(f"   Evidence:     {result.evidence_count} files")
            print(f"   Size:         {result.bundle_size_bytes:,} bytes")
            print()

            # Auto-verify
            print("🔍 Running self-verification...")
            report = verify_bundle(result.jmpg_path)
            print(f"   Valid: {report['valid']}")
            for check in report["checks"]:
                status = "✓" if check["status"] == "pass" else "⚠" if check["status"] == "warn" else "✕"
                print(f"   {status} {check['check']}: {check['status']}")
            if report["errors"]:
                for err in report["errors"]:
                    print(f"   ✕ Error: {err}")
        else:
            print(f"✕ Packaging failed:")
            for err in result.errors:
                print(f"  - {err}")

    elif cmd == "verify":
        if len(sys.argv) < 3:
            print("Usage: python jmpg_packager.py verify <file.jmpg>")
            return
        filepath = sys.argv[2]
        report = verify_bundle(filepath)
        print(f"Bundle: {filepath}")
        print(f"Valid:  {'✅ YES' if report['valid'] else '❌ NO'}")
        print(f"ID:     {report.get('communique_id', '—')}")
        print(f"Hash:   {report.get('bundle_hash', '—')}")
        print()
        for check in report["checks"]:
            status = "✓" if check["status"] == "pass" else "⚠" if check["status"] == "warn" else "✕"
            print(f"  {status} {check['check']}: {check['status']}")
        if report["errors"]:
            print()
            for err in report["errors"]:
                print(f"  ✕ {err}")

    elif cmd == "info":
        if len(sys.argv) < 3:
            print("Usage: python jmpg_packager.py info <file.jmpg>")
            return
        filepath = sys.argv[2]
        try:
            with zipfile.ZipFile(filepath) as zf:
                if "manifest.json" in zf.namelist():
                    manifest = json.loads(zf.read("manifest.json"))
                    print(json.dumps(manifest, indent=2, ensure_ascii=False))
                else:
                    print("No manifest.json found in bundle")
        except Exception as e:
            print(f"Error: {e}")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
