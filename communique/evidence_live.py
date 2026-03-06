#!/usr/bin/env python3
"""
WINDI Evidence Package Builder v1.1
====================================
Captures evidence files, computes SHA-256 hashes, generates manifest.json,
and bundles everything into a .jmpg Evidence Package.

Usage:
  python3 evidence_live.py build --com COM-20260219-0001 --dir ./evidence_files/
  python3 evidence_live.py verify --package EV-20260219-0001.jmpg
  python3 evidence_live.py manifest --dir ./evidence_files/

Part of WINDI Communiqué Multimedia Infrastructure.
"AI processes. Human decides. WINDI guarantees."
"""

import os
import sys
import json
import hashlib
import zipfile
import argparse
from datetime import datetime, timezone
from pathlib import Path

# ─── CONFIGURATION ───────────────────────────────────────────────────────

SCHEMA_VERSION = "1.1.0"
SCHEMA_NAME = "windi-evidence-package-v1.1"

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".pdf": "application/pdf",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
}

TYPE_MAP = {
    "image": ["png", "jpg", "jpeg", "webp"],
    "video": ["mp4", "webm"],
    "document": ["pdf"],
    "audio": ["wav", "mp3", "ogg"],
}

PREFIX_MAP = {
    "image": "IMG",
    "video": "VID",
    "document": "DOC",
    "audio": "AUD",
}

MAX_SIZES = {
    "image": 10 * 1024 * 1024,       # 10 MB
    "video": 50 * 1024 * 1024,       # 50 MB
    "document": 20 * 1024 * 1024,    # 20 MB
    "audio": 30 * 1024 * 1024,       # 30 MB
}

SOURCE_TYPES = ["operator", "sentinel", "audit", "system", "external"]


# ─── CORE FUNCTIONS ──────────────────────────────────────────────────────

def sha256_file(filepath):
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data):
    """Compute SHA-256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


def detect_type(filename):
    """Detect evidence type from file extension."""
    ext = Path(filename).suffix.lower().lstrip(".")
    for etype, extensions in TYPE_MAP.items():
        if ext in extensions:
            return etype
    return None


def get_image_dimensions(filepath):
    """Get image dimensions without PIL (reads PNG/JPEG headers)."""
    ext = Path(filepath).suffix.lower()
    try:
        with open(filepath, "rb") as f:
            data = f.read(32)
            if ext == ".png" and data[:8] == b"\x89PNG\r\n\x1a\n":
                w = int.from_bytes(data[16:20], "big")
                h = int.from_bytes(data[20:24], "big")
                return f"{w}x{h}"
            elif ext in (".jpg", ".jpeg"):
                f.seek(0)
                data = f.read()
                idx = 2
                while idx < len(data) - 9:
                    if data[idx] == 0xFF:
                        marker = data[idx + 1]
                        if marker in (0xC0, 0xC1, 0xC2):
                            h = int.from_bytes(data[idx+5:idx+7], "big")
                            w = int.from_bytes(data[idx+7:idx+9], "big")
                            return f"{w}x{h}"
                        elif marker == 0xD9:
                            break
                        else:
                            length = int.from_bytes(data[idx+2:idx+4], "big")
                            idx += 2 + length
                    else:
                        idx += 1
    except Exception:
        pass
    return "unknown"


def scan_directory(dirpath):
    """Scan a directory for evidence files and classify them."""
    files = []
    dirpath = Path(dirpath)

    if not dirpath.exists():
        print(f"  ✗ Directory not found: {dirpath}")
        sys.exit(1)

    # Counters per type
    counters = {"image": 0, "video": 0, "document": 0, "audio": 0}

    for filepath in sorted(dirpath.iterdir()):
        if filepath.is_dir() or filepath.name.startswith(".") or filepath.name == "manifest.json":
            continue

        etype = detect_type(filepath.name)
        if etype is None:
            print(f"  ⚠ Skipping unknown type: {filepath.name}")
            continue

        # Check size limits
        fsize = filepath.stat().st_size
        max_size = MAX_SIZES.get(etype, 0)
        if fsize > max_size:
            print(f"  ⚠ File too large ({fsize} > {max_size}): {filepath.name}")
            continue

        counters[etype] += 1
        prefix = PREFIX_MAP[etype]
        evidence_id = f"{prefix}-{counters[etype]:02d}"

        # Build standardized filename
        ext = filepath.suffix.lower()
        std_filename = f"{evidence_id}{ext}"

        file_info = {
            "id": evidence_id,
            "original_filename": filepath.name,
            "filename": std_filename,
            "type": etype,
            "mime_type": MIME_TYPES.get(ext, "application/octet-stream"),
            "sha256": sha256_file(filepath),
            "bytes": fsize,
            "path": str(filepath),
        }

        # Type-specific metadata
        if etype == "image":
            file_info["dimensions"] = get_image_dimensions(filepath)
        elif etype == "video":
            file_info["duration_seconds"] = None  # Requires ffprobe
            file_info["resolution"] = "unknown"

        files.append(file_info)

    return files, counters


def compute_content_hash(files):
    """Compute content_hash by concatenating individual file hashes."""
    combined = "".join(f["sha256"] for f in files)
    return sha256_bytes(combined.encode("utf-8"))


def build_manifest(files, counters, com_id, title="", category="INCIDENT",
                   impact="HIGH", source="operator", author_name="Jober Mögele Correa",
                   author_role="Chief Governance Officer"):
    """Build the official manifest.json following Schema v1.1."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")

    # Auto-generate evidence_id from communique_id
    ev_num = com_id.split("-")[-1] if com_id else "0001"
    evidence_id = f"EV-{date_part}-{ev_num}"

    content_hash = compute_content_hash(files)

    # Build evidence file entries with caption placeholders
    evidence_files = []
    for f in files:
        entry = {
            "id": f["id"],
            "filename": f["filename"],
            "type": f["type"],
            "mime_type": f["mime_type"],
            "sha256": f["sha256"],
            "bytes": f["bytes"],
            "caption": {
                "de": f"[Beschreibung für {f['id']}]",
                "en": f"[Caption for {f['id']}]",
                "pt": f"[Legenda para {f['id']}]"
            },
            "captured_at": now,
            "source": source,
            "source_detail": f"Captured by {source}"
        }
        if "dimensions" in f:
            entry["dimensions"] = f["dimensions"]
        if f["type"] == "video":
            entry["duration_seconds"] = f.get("duration_seconds")
            entry["resolution"] = f.get("resolution", "unknown")

        evidence_files.append(entry)

    total_bytes = sum(f["bytes"] for f in files)

    manifest = {
        "$schema": SCHEMA_NAME,
        "evidence_id": evidence_id,
        "version": SCHEMA_VERSION,
        "communique": {
            "id": com_id,
            "type": "COMMUNIQUE_MULTIMEDIA",
            "title": title,
            "category": category,
            "impact_level": impact
        },
        "created_at": now,
        "created_by": {
            "name": author_name,
            "role": author_role,
            "organization": "WINDI Publishing House"
        },
        "evidence": {
            "total_files": len(files),
            "total_bytes": total_bytes,
            "types": {
                "images": counters.get("image", 0),
                "videos": counters.get("video", 0),
                "documents": counters.get("document", 0),
                "audio": counters.get("audio", 0)
            },
            "files": evidence_files
        },
        "hashes": {
            "content_hash": content_hash,
            "content_hash_method": "SHA-256 of concatenated file hashes in manifest order",
            "bundle_hash": None,  # Computed after .jmpg creation
            "bundle_hash_method": "SHA-256 of final .jmpg binary",
            "chain_algorithm": "content_hash = SHA256(" + " + ".join(
                f"{f['id']}.sha256" for f in files
            ) + ")"
        },
        "ledger": {
            "receipt_id": None,  # Assigned by Ledger
            "receipt_type": "COMMUNIQUE_MULTIMEDIA",
            "ledger_status": "pending",
            "sealed_at": None
        },
        "governance": {
            "sge_score": None,
            "risk_level": "R3",
            "doc_type": "COMMUNIQUE",
            "impact_level": impact,
            "flow_status": "DRAFT",
            "department_code": "GOV"
        },
        "verification": {
            "verify_url": f"https://windi-domain.com/communique/{com_id}/verify",
            "evidence_verify_url": f"https://windi-domain.com/communique/{com_id}/evidence/verify",
            "immutable": False,
            "immutable_since": None
        }
    }

    return manifest


def bundle_jmpg(manifest, evidence_dir, output_path):
    """Create .jmpg bundle (ZIP) with evidence files and manifest."""
    evidence_dir = Path(evidence_dir)
    output_path = Path(output_path)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write manifest
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

        # Write evidence files with standardized names
        for fentry in manifest["evidence"]["files"]:
            # Find original file
            original = None
            for fp in evidence_dir.iterdir():
                if sha256_file(fp) == fentry["sha256"]:
                    original = fp
                    break
            if original:
                zf.write(original, f"evidence/{fentry['filename']}")
            else:
                print(f"  ⚠ File not found for {fentry['id']}: {fentry['sha256'][:16]}...")

        # Write capture log
        capture_log = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tool": "evidence_live.py v1.1",
            "files_bundled": len(manifest["evidence"]["files"]),
        }
        zf.writestr("metadata/capture_log.json", json.dumps(capture_log, indent=2))

        # Write chain verification data
        chain = {
            "content_hash": manifest["hashes"]["content_hash"],
            "individual_hashes": {
                f["id"]: f["sha256"] for f in manifest["evidence"]["files"]
            },
            "algorithm": manifest["hashes"]["chain_algorithm"]
        }
        zf.writestr("metadata/chain.json", json.dumps(chain, indent=2))

    # Compute bundle_hash
    bundle_hash = sha256_file(output_path)
    manifest["hashes"]["bundle_hash"] = bundle_hash

    # Rewrite manifest with bundle_hash inside the zip
    with zipfile.ZipFile(output_path, "a") as zf:
        # Remove old manifest and add updated one
        # Note: ZIP doesn't support in-place update, but adding same name
        # will create duplicate — we handle this by writing bundle_hash separately
        zf.writestr("metadata/bundle_hash.txt", bundle_hash)

    print(f"  ✓ Bundle created: {output_path}")
    print(f"  ✓ Bundle hash: {bundle_hash}")
    print(f"  ✓ Content hash: {manifest['hashes']['content_hash']}")

    return bundle_hash


def verify_package(package_path):
    """Verify an existing .jmpg Evidence Package."""
    package_path = Path(package_path)

    if not package_path.exists():
        print(f"  ✗ Package not found: {package_path}")
        return False

    print(f"\n{'='*60}")
    print(f"  WINDI Evidence Package Verification")
    print(f"{'='*60}\n")

    # Compute bundle hash
    bundle_hash = sha256_file(package_path)
    print(f"  Bundle Hash: {bundle_hash}")

    try:
        with zipfile.ZipFile(package_path, "r") as zf:
            # Read manifest
            manifest = json.loads(zf.read("manifest.json"))
            print(f"  Evidence ID: {manifest['evidence_id']}")
            print(f"  Communiqué: {manifest['communique']['id']}")
            print(f"  Schema: {manifest['$schema']}")
            print(f"  Files: {manifest['evidence']['total_files']}")
            print()

            # Verify individual file hashes
            all_ok = True
            file_hashes = []

            for fentry in manifest["evidence"]["files"]:
                fpath = f"evidence/{fentry['filename']}"
                try:
                    data = zf.read(fpath)
                    computed = sha256_bytes(data)
                    expected = fentry["sha256"]
                    match = computed == expected
                    file_hashes.append(computed)

                    status = "✓" if match else "✗"
                    color = "" if match else " *** MISMATCH ***"
                    print(f"  {status} {fentry['id']}: {computed[:16]}...{color}")

                    if not match:
                        all_ok = False
                except KeyError:
                    print(f"  ✗ {fentry['id']}: FILE MISSING from bundle")
                    all_ok = False

            # Verify content hash
            combined = "".join(file_hashes)
            computed_content = sha256_bytes(combined.encode("utf-8"))
            expected_content = manifest["hashes"]["content_hash"]
            content_match = computed_content == expected_content

            print()
            print(f"  Content Hash:")
            print(f"    Expected: {expected_content}")
            print(f"    Computed: {computed_content}")
            print(f"    Match: {'✓' if content_match else '✗ MISMATCH'}")

            # Check stored bundle hash
            try:
                stored_bundle = zf.read("metadata/bundle_hash.txt").decode().strip()
                print(f"\n  Stored Bundle Hash: {stored_bundle}")
                print(f"  Current Bundle Hash: {bundle_hash}")
                # Note: bundle_hash changes if zip is modified, so this is informational
            except KeyError:
                print(f"\n  ⚠ No stored bundle_hash found in metadata")

            print(f"\n{'='*60}")
            if all_ok and content_match:
                print(f"  ✓ VERIFICATION: PASSED — All evidence intact")
            else:
                print(f"  ✗ VERIFICATION: FAILED — Evidence integrity compromised")
            print(f"{'='*60}\n")

            return all_ok and content_match

    except Exception as e:
        print(f"  ✗ Error reading package: {e}")
        return False


# ─── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="WINDI Evidence Package Builder v1.1",
        epilog='"AI processes. Human decides. WINDI guarantees."'
    )
    sub = parser.add_subparsers(dest="command")

    # build command
    build_p = sub.add_parser("build", help="Build .jmpg from evidence directory")
    build_p.add_argument("--com", required=True, help="Communiqué ID (e.g. COM-20260219-0001)")
    build_p.add_argument("--dir", required=True, help="Directory with evidence files")
    build_p.add_argument("--title", default="", help="Communiqué title")
    build_p.add_argument("--category", default="INCIDENT", help="Category")
    build_p.add_argument("--impact", default="HIGH", help="Impact level")
    build_p.add_argument("--source", default="operator", help="Source type")
    build_p.add_argument("--output", default=None, help="Output .jmpg path")

    # verify command
    verify_p = sub.add_parser("verify", help="Verify .jmpg Evidence Package")
    verify_p.add_argument("--package", required=True, help="Path to .jmpg file")

    # manifest command
    manifest_p = sub.add_parser("manifest", help="Generate manifest.json only")
    manifest_p.add_argument("--com", required=True, help="Communiqué ID")
    manifest_p.add_argument("--dir", required=True, help="Directory with evidence files")
    manifest_p.add_argument("--output", default="manifest.json", help="Output manifest path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    print(f"\n  🐉 WINDI Evidence Package Builder v{SCHEMA_VERSION}")
    print(f"  ─────────────────────────────────────────\n")

    if args.command == "build":
        print(f"  Scanning: {args.dir}")
        files, counters = scan_directory(args.dir)
        print(f"  Found: {len(files)} evidence files")
        for etype, count in counters.items():
            if count > 0:
                print(f"    {etype}: {count}")

        manifest = build_manifest(
            files, counters, args.com,
            title=args.title, category=args.category,
            impact=args.impact, source=args.source
        )

        # Determine output path
        output = args.output or f"{manifest['evidence_id']}.jmpg"

        print(f"\n  Building bundle: {output}")
        bundle_hash = bundle_jmpg(manifest, args.dir, output)

        # Save final manifest
        manifest_path = output.replace(".jmpg", "_manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Manifest saved: {manifest_path}")

        print(f"\n  ─────────────────────────────────────────")
        print(f"  Evidence ID:  {manifest['evidence_id']}")
        print(f"  Communiqué:   {args.com}")
        print(f"  Content Hash: {manifest['hashes']['content_hash']}")
        print(f"  Bundle Hash:  {bundle_hash}")
        print(f"  Files:        {len(files)}")
        print(f"  Total Size:   {manifest['evidence']['total_bytes']:,} bytes")
        print(f"\n  READY FOR LEDGER REGISTRATION")
        print(f"  ─────────────────────────────────────────\n")

    elif args.command == "verify":
        verify_package(args.package)

    elif args.command == "manifest":
        print(f"  Scanning: {args.dir}")
        files, counters = scan_directory(args.dir)
        manifest = build_manifest(files, counters, args.com)

        with open(args.output, "w") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Manifest saved: {args.output}")
        print(f"  Content Hash: {manifest['hashes']['content_hash']}")


if __name__ == "__main__":
    main()
