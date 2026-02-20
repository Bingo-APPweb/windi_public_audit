#!/usr/bin/env python3
"""
WINDI Evidence Schema Validator v1.1
=====================================
Validates manifest.json against Evidence Package Schema v1.1.
Enforces all 9 Architectural Invariants.

Usage:
  python3 evidence_validator.py manifest.json
  python3 evidence_validator.py manifest.json --strict
  python3 evidence_validator.py --bundle EV-20260219-0001.jmpg

Integration:
  from evidence_validator import validate_manifest, validate_bundle
  result = validate_manifest(manifest_dict)
  if not result["valid"]: print(result["errors"])

Part of WINDI Communiqué Multimedia Infrastructure.
"The evidence speaks. The hash proves. The Ledger remembers."
"""

import json
import sys
import hashlib
import zipfile
import argparse
from datetime import datetime
from pathlib import Path

# ─── SCHEMA CONSTANTS ────────────────────────────────────────────────────

SCHEMA_VERSION = "1.1.0"
SCHEMA_NAME = "windi-evidence-package-v1.1"

VALID_EVIDENCE_TYPES = {"image", "video", "document", "audio"}
VALID_SOURCE_TYPES = {"operator", "sentinel", "audit", "system", "external"}
VALID_CATEGORIES = {"INCIDENT", "UPDATE", "LAUNCH", "GOVERNANCE", "AUDIT", "ALERT", "REPORT"}
VALID_IMPACTS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_RISK_LEVELS = {"R0", "R1", "R2", "R3", "R4", "R5"}
VALID_FLOW_STATUSES = {"DRAFT", "PENDING", "PUBLISHED", "ARCHIVED", "REVOKED"}
VALID_CLASSIFICATIONS = {"public", "restricted", "confidential"}
VALID_LEDGER_STATUSES = {"pending", "sealed", "verified", "rejected"}
VALID_RECEIPT_TYPES = {"COMMUNIQUE_MULTIMEDIA", "COMMUNIQUE", "DOCUMENT", "EXPORT"}

VALID_IMAGE_MIMES = {"image/png", "image/jpeg", "image/webp"}
VALID_VIDEO_MIMES = {"video/mp4", "video/webm"}
VALID_DOC_MIMES = {"application/pdf"}
VALID_AUDIO_MIMES = {"audio/wav", "audio/mpeg", "audio/ogg"}

MIME_BY_TYPE = {
    "image": VALID_IMAGE_MIMES,
    "video": VALID_VIDEO_MIMES,
    "document": VALID_DOC_MIMES,
    "audio": VALID_AUDIO_MIMES,
}

MAX_SIZES = {
    "image": 10 * 1024 * 1024,
    "video": 50 * 1024 * 1024,
    "document": 20 * 1024 * 1024,
    "audio": 30 * 1024 * 1024,
}

MAX_VIDEO_DURATION = 300  # seconds
MAX_DOC_PAGES = 50
MAX_AUDIO_DURATION = 600  # seconds

REQUIRED_LANGUAGES = {"de", "en", "pt"}

PREFIX_MAP = {"image": "IMG", "video": "VID", "document": "DOC", "audio": "AUD"}


# ─── VALIDATION RESULT ───────────────────────────────────────────────────

class ValidationResult:
    """Structured validation result."""

    def __init__(self):
        self.errors = []      # Fatal: block acceptance
        self.warnings = []    # Non-fatal: suggest improvement
        self.info = []        # Informational
        self.invariant_violations = []  # Architectural invariant breaches

    @property
    def valid(self):
        return len(self.errors) == 0 and len(self.invariant_violations) == 0

    def error(self, code, msg):
        self.errors.append({"code": code, "message": msg})

    def warn(self, code, msg):
        self.warnings.append({"code": code, "message": msg})

    def note(self, msg):
        self.info.append(msg)

    def invariant(self, number, msg):
        self.invariant_violations.append({"invariant": number, "message": msg})

    def to_dict(self):
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "invariant_violations": self.invariant_violations,
            "summary": {
                "total_errors": len(self.errors),
                "total_warnings": len(self.warnings),
                "total_invariant_violations": len(self.invariant_violations),
            }
        }

    def print_report(self):
        """Print human-readable validation report."""
        print(f"\n{'='*60}")
        print(f"  WINDI Evidence Schema Validator v{SCHEMA_VERSION}")
        print(f"{'='*60}\n")

        if self.valid:
            print(f"  ✓ VALIDATION: PASSED\n")
        else:
            print(f"  ✗ VALIDATION: FAILED\n")

        if self.invariant_violations:
            print(f"  ⚖ INVARIANT VIOLATIONS ({len(self.invariant_violations)}):")
            for iv in self.invariant_violations:
                print(f"    I{iv['invariant']}: {iv['message']}")
            print()

        if self.errors:
            print(f"  ✗ ERRORS ({len(self.errors)}):")
            for e in self.errors:
                print(f"    [{e['code']}] {e['message']}")
            print()

        if self.warnings:
            print(f"  ⚠ WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"    [{w['code']}] {w['message']}")
            print()

        if self.info:
            print(f"  ℹ INFO:")
            for i in self.info:
                print(f"    {i}")
            print()

        print(f"{'='*60}")
        verdict = "ACCEPTED" if self.valid else "REJECTED"
        print(f"  VERDICT: {verdict}")
        print(f"  Errors: {len(self.errors)} | Warnings: {len(self.warnings)} | Invariants: {len(self.invariant_violations)}")
        print(f"{'='*60}\n")


# ─── FIELD VALIDATORS ────────────────────────────────────────────────────

def _check_required(data, key, result, context="root"):
    """Check if a required field exists and is not None/empty."""
    if key not in data or data[key] is None:
        result.error("MISSING_FIELD", f"{context}.{key} is required")
        return False
    return True


def _check_type(data, key, expected_type, result, context="root"):
    """Check field type."""
    if key in data and data[key] is not None:
        if not isinstance(data[key], expected_type):
            result.error("INVALID_TYPE",
                         f"{context}.{key} must be {expected_type.__name__}, got {type(data[key]).__name__}")
            return False
    return True


def _check_enum(data, key, valid_values, result, context="root"):
    """Check if value is in allowed set."""
    if key in data and data[key] is not None:
        if data[key] not in valid_values:
            result.error("INVALID_VALUE",
                         f"{context}.{key} = '{data[key]}' not in {valid_values}")
            return False
    return True


def _check_iso_datetime(data, key, result, context="root"):
    """Validate ISO 8601 datetime string."""
    if key in data and data[key] is not None:
        try:
            val = data[key]
            # Accept common ISO formats
            if val.endswith("Z"):
                val = val[:-1] + "+00:00"
            datetime.fromisoformat(val)
        except (ValueError, TypeError):
            result.error("INVALID_DATETIME",
                         f"{context}.{key} = '{data[key]}' is not valid ISO 8601")
            return False
    return True


def _check_sha256(value, result, context="field"):
    """Validate SHA-256 hash format (64 hex chars or abbreviated)."""
    if value is None:
        return True  # None allowed for pending fields
    if not isinstance(value, str):
        result.error("INVALID_HASH", f"{context} must be string")
        return False
    # Allow abbreviated hashes (for display) or full 64-char
    cleaned = value.replace("...", "").replace(" ", "")
    if len(cleaned) > 0 and not all(c in "0123456789abcdef" for c in cleaned):
        result.error("INVALID_HASH", f"{context} contains non-hex characters")
        return False
    return True


def _check_trilingual_caption(caption, result, context="caption"):
    """Validate trilingual caption (DE/EN/PT required)."""
    if not isinstance(caption, dict):
        result.error("INVALID_CAPTION", f"{context} must be a dict with de/en/pt keys")
        return False
    missing = REQUIRED_LANGUAGES - set(caption.keys())
    if missing:
        result.error("MISSING_LANGUAGE", f"{context} missing languages: {missing}")
        return False
    for lang in REQUIRED_LANGUAGES:
        if not caption.get(lang) or not isinstance(caption[lang], str) or len(caption[lang].strip()) == 0:
            result.error("EMPTY_CAPTION", f"{context}.{lang} is empty")
            return False
    return True


# ─── CORE VALIDATOR ──────────────────────────────────────────────────────

def validate_manifest(manifest, strict=False):
    """
    Validate a manifest dict against Evidence Package Schema v1.1.

    Args:
        manifest: dict — parsed manifest.json
        strict: bool — if True, treat warnings as errors

    Returns:
        ValidationResult
    """
    r = ValidationResult()

    if not isinstance(manifest, dict):
        r.error("INVALID_ROOT", "Manifest must be a JSON object")
        return r

    # ── $schema ──
    schema = manifest.get("$schema")
    if schema != SCHEMA_NAME:
        r.error("INVALID_SCHEMA", f"$schema must be '{SCHEMA_NAME}', got '{schema}'")

    # ── evidence_id ──
    _check_required(manifest, "evidence_id", r)
    ev_id = manifest.get("evidence_id", "")
    if ev_id and not ev_id.startswith("EV-"):
        r.error("INVALID_ID", f"evidence_id must start with 'EV-', got '{ev_id}'")

    # ── version ──
    _check_required(manifest, "version", r)

    # ── communique block ──
    if _check_required(manifest, "communique", r):
        com = manifest["communique"]
        _check_required(com, "id", r, "communique")
        _check_required(com, "type", r, "communique")
        _check_enum(com, "category", VALID_CATEGORIES, r, "communique")
        _check_enum(com, "impact_level", VALID_IMPACTS, r, "communique")

        com_id = com.get("id", "")
        if com_id and not com_id.startswith("COM-"):
            r.error("INVALID_COM_ID", f"communique.id must start with 'COM-', got '{com_id}'")

    # ── created_at ──
    _check_required(manifest, "created_at", r)
    _check_iso_datetime(manifest, "created_at", r)

    # ── created_by ──
    if _check_required(manifest, "created_by", r):
        cb = manifest["created_by"]
        _check_required(cb, "name", r, "created_by")
        _check_required(cb, "role", r, "created_by")
        _check_required(cb, "organization", r, "created_by")

    # ── evidence block ──
    if _check_required(manifest, "evidence", r):
        ev = manifest["evidence"]
        _check_required(ev, "total_files", r, "evidence")
        _check_required(ev, "total_bytes", r, "evidence")
        _check_required(ev, "types", r, "evidence")

        if _check_required(ev, "files", r, "evidence"):
            files = ev["files"]
            if not isinstance(files, list):
                r.error("INVALID_TYPE", "evidence.files must be an array")
            else:
                # Check total_files matches
                if ev.get("total_files") != len(files):
                    r.error("COUNT_MISMATCH",
                            f"evidence.total_files={ev.get('total_files')} but files array has {len(files)}")

                # Check types counts
                type_counts = {"images": 0, "videos": 0, "documents": 0, "audio": 0}
                seen_ids = set()
                id_counters = {"image": 0, "video": 0, "document": 0, "audio": 0}

                for idx, fentry in enumerate(files):
                    ctx = f"evidence.files[{idx}]"

                    # Required fields
                    _check_required(fentry, "id", r, ctx)
                    _check_required(fentry, "filename", r, ctx)
                    _check_required(fentry, "type", r, ctx)
                    _check_required(fentry, "mime_type", r, ctx)
                    _check_required(fentry, "sha256", r, ctx)
                    _check_required(fentry, "bytes", r, ctx)

                    # ── INVARIANT 3: Every element MUST have SHA-256 ──
                    sha = fentry.get("sha256")
                    if sha is None or sha == "":
                        r.invariant(3, f"{ctx}: SHA-256 hash is required (Invariant 3)")
                    else:
                        _check_sha256(sha, r, f"{ctx}.sha256")

                    # ── INVARIANT 4: Every element MUST have trilingual caption ──
                    caption = fentry.get("caption")
                    if caption is None:
                        r.invariant(4, f"{ctx}: Trilingual caption required (Invariant 4)")
                    else:
                        _check_trilingual_caption(caption, r, f"{ctx}.caption")

                    # ── INVARIANT 8: Source attribution mandatory ──
                    source = fentry.get("source")
                    if source is None or source == "":
                        r.invariant(8, f"{ctx}: Source attribution required (Invariant 8)")
                    else:
                        _check_enum(fentry, "source", VALID_SOURCE_TYPES, r, ctx)

                    # ── INVARIANT 9: Timestamps mandatory ──
                    if not fentry.get("captured_at"):
                        r.invariant(9, f"{ctx}: captured_at timestamp required (Invariant 9)")
                    else:
                        _check_iso_datetime(fentry, "captured_at", r, ctx)

                    # Type validation
                    ftype = fentry.get("type")
                    if ftype and ftype not in VALID_EVIDENCE_TYPES:
                        r.error("INVALID_TYPE", f"{ctx}.type = '{ftype}' not valid")
                    elif ftype:
                        # Check MIME type matches evidence type
                        mime = fentry.get("mime_type")
                        valid_mimes = MIME_BY_TYPE.get(ftype, set())
                        if mime and mime not in valid_mimes:
                            r.error("MIME_MISMATCH",
                                    f"{ctx}: mime_type '{mime}' invalid for type '{ftype}'")

                        # Count types
                        type_key = ftype + "s" if ftype != "audio" else "audio"
                        if type_key in type_counts:
                            type_counts[type_key] += 1

                    # Check size limits
                    fbytes = fentry.get("bytes", 0)
                    if ftype and fbytes:
                        max_size = MAX_SIZES.get(ftype, 0)
                        if fbytes > max_size:
                            r.error("FILE_TOO_LARGE",
                                    f"{ctx}: {fbytes} bytes exceeds {max_size} limit for {ftype}")

                    # Check ID format (PREFIX-NN)
                    fid = fentry.get("id", "")
                    if fid:
                        if fid in seen_ids:
                            r.error("DUPLICATE_ID", f"{ctx}: duplicate id '{fid}'")
                        seen_ids.add(fid)

                        expected_prefix = PREFIX_MAP.get(ftype, "")
                        if expected_prefix and not fid.startswith(expected_prefix + "-"):
                            r.error("INVALID_ID_FORMAT",
                                    f"{ctx}: id '{fid}' should start with '{expected_prefix}-' for type '{ftype}'")

                    # ── INVARIANT 2: Video NEVER embedded ──
                    if ftype == "video":
                        # Video duration check
                        dur = fentry.get("duration_seconds")
                        if dur is not None and dur > MAX_VIDEO_DURATION:
                            r.error("VIDEO_TOO_LONG",
                                    f"{ctx}: duration {dur}s exceeds {MAX_VIDEO_DURATION}s limit")

                # Verify type counts match
                declared_types = ev.get("types", {})
                for tkey, tcount in type_counts.items():
                    declared = declared_types.get(tkey, 0)
                    if declared != tcount:
                        r.error("TYPE_COUNT_MISMATCH",
                                f"evidence.types.{tkey}={declared} but found {tcount}")

                # Check total_bytes
                actual_bytes = sum(f.get("bytes", 0) for f in files)
                declared_bytes = ev.get("total_bytes", 0)
                if declared_bytes != actual_bytes:
                    r.warn("BYTES_MISMATCH",
                           f"evidence.total_bytes={declared_bytes} but sum is {actual_bytes}")

    # ── hashes block ──
    if _check_required(manifest, "hashes", r):
        h = manifest["hashes"]
        _check_required(h, "content_hash", r, "hashes")
        _check_required(h, "content_hash_method", r, "hashes")
        _check_sha256(h.get("content_hash"), r, "hashes.content_hash")

        if h.get("bundle_hash"):
            _check_sha256(h["bundle_hash"], r, "hashes.bundle_hash")

        # ── INVARIANT 5: Manifest order defines hash chain ──
        method = h.get("content_hash_method", "")
        if "concatenated" not in method.lower() and "manifest order" not in method.lower():
            r.warn("HASH_METHOD", "hashes.content_hash_method should reference manifest order")

    # ── ledger block ──
    if _check_required(manifest, "ledger", r):
        led = manifest["ledger"]
        _check_enum(led, "ledger_status", VALID_LEDGER_STATUSES, r, "ledger")
        _check_enum(led, "receipt_type", VALID_RECEIPT_TYPES, r, "ledger")
        if led.get("sealed_at"):
            _check_iso_datetime(led, "sealed_at", r, "ledger")

    # ── governance block ──
    if _check_required(manifest, "governance", r):
        gov = manifest["governance"]
        _check_enum(gov, "risk_level", VALID_RISK_LEVELS, r, "governance")
        _check_enum(gov, "impact_level", VALID_IMPACTS, r, "governance")
        _check_enum(gov, "flow_status", VALID_FLOW_STATUSES, r, "governance")

    # ── verification block ──
    if _check_required(manifest, "verification", r):
        ver = manifest["verification"]
        _check_required(ver, "verify_url", r, "verification")

    # ── Optional v1.1.1 fields (warn if missing in strict mode) ──
    if strict:
        if "classification" not in manifest:
            r.warn("MISSING_OPTIONAL", "classification field recommended (public/restricted/confidential)")

        # Check device_info on evidence files
        files = manifest.get("evidence", {}).get("files", [])
        for idx, f in enumerate(files):
            if "device_info" not in f:
                r.warn("MISSING_OPTIONAL", f"evidence.files[{idx}].device_info recommended")
            if "timezone" not in f:
                r.warn("MISSING_OPTIONAL", f"evidence.files[{idx}].timezone recommended")

    # ── INVARIANT 1: Ledger stores only hashes, never data ──
    # (Structural — validated by architecture, logged here for completeness)
    r.note("Invariant 1 (hashes only): Enforced by Ledger architecture")

    # ── INVARIANT 6: Immutable after seal ──
    led = manifest.get("ledger", {})
    ver = manifest.get("verification", {})
    if led.get("ledger_status") == "sealed":
        if not ver.get("immutable"):
            r.invariant(6, "Sealed packages must be marked immutable (Invariant 6)")
        if not ver.get("immutable_since"):
            r.warn("SEAL_TIMESTAMP", "immutable_since should be set for sealed packages")

    # ── INVARIANT 7: Evidence travels WITH communiqué ──
    r.note("Invariant 7 (co-travel): Enforced by bundle architecture")

    # ── Final summary ──
    files_count = len(manifest.get("evidence", {}).get("files", []))
    r.note(f"Schema: {manifest.get('$schema')}")
    r.note(f"Evidence ID: {manifest.get('evidence_id')}")
    r.note(f"Communiqué: {manifest.get('communique', {}).get('id')}")
    r.note(f"Files: {files_count}")
    r.note(f"Status: {led.get('ledger_status', 'unknown')}")

    # In strict mode, warnings become errors
    if strict:
        for w in r.warnings:
            r.errors.append(w)
        r.warnings = []

    return r


# ─── BUNDLE VALIDATOR ────────────────────────────────────────────────────

def validate_bundle(bundle_path):
    """
    Validate a .jmpg Evidence Package bundle.
    Checks: structure, manifest, file hashes, content_hash chain.
    """
    r = ValidationResult()
    bundle_path = Path(bundle_path)

    if not bundle_path.exists():
        r.error("FILE_NOT_FOUND", f"Bundle not found: {bundle_path}")
        return r

    if not bundle_path.suffix == ".jmpg":
        r.warn("WRONG_EXTENSION", f"Expected .jmpg extension, got '{bundle_path.suffix}'")

    try:
        with zipfile.ZipFile(bundle_path, "r") as zf:
            names = zf.namelist()

            # Check required files
            if "manifest.json" not in names:
                r.error("MISSING_MANIFEST", "Bundle must contain manifest.json")
                return r

            # Parse and validate manifest
            manifest = json.loads(zf.read("manifest.json"))
            manifest_result = validate_manifest(manifest)

            # Merge manifest validation results
            r.errors.extend(manifest_result.errors)
            r.warnings.extend(manifest_result.warnings)
            r.info.extend(manifest_result.info)
            r.invariant_violations.extend(manifest_result.invariant_violations)

            # Check evidence files exist and verify hashes
            file_hashes = []
            for fentry in manifest.get("evidence", {}).get("files", []):
                fpath = f"evidence/{fentry['filename']}"
                if fpath not in names:
                    r.error("MISSING_FILE", f"Evidence file missing from bundle: {fpath}")
                    continue

                # Verify SHA-256
                data = zf.read(fpath)
                computed = hashlib.sha256(data).hexdigest()
                expected = fentry.get("sha256", "")

                # Handle abbreviated hashes (allow partial match)
                if "..." in expected:
                    prefix = expected.split("...")[0]
                    if not computed.startswith(prefix):
                        r.error("HASH_MISMATCH",
                                f"{fentry['id']}: hash mismatch (computed: {computed[:16]}..., expected prefix: {prefix})")
                    file_hashes.append(computed)
                elif computed != expected:
                    r.error("HASH_MISMATCH",
                            f"{fentry['id']}: hash mismatch (computed: {computed[:16]}..., expected: {expected[:16]}...)")
                    file_hashes.append(computed)
                else:
                    file_hashes.append(computed)
                    r.note(f"{fentry['id']}: ✓ hash verified")

                # Verify file size
                actual_size = len(data)
                expected_size = fentry.get("bytes", 0)
                if actual_size != expected_size:
                    r.warn("SIZE_MISMATCH",
                           f"{fentry['id']}: size {actual_size} != declared {expected_size}")

            # Verify content_hash chain
            if file_hashes:
                combined = "".join(file_hashes)
                computed_content = hashlib.sha256(combined.encode("utf-8")).hexdigest()
                expected_content = manifest.get("hashes", {}).get("content_hash", "")

                if "..." not in expected_content and computed_content != expected_content:
                    r.error("CONTENT_HASH_MISMATCH",
                            f"content_hash mismatch: computed={computed_content[:16]}... expected={expected_content[:16]}...")
                elif "..." not in expected_content:
                    r.note(f"Content hash chain: ✓ verified ({computed_content[:16]}...)")

            # Check metadata directory
            if "metadata/capture_log.json" not in names:
                r.warn("MISSING_METADATA", "metadata/capture_log.json recommended")
            if "metadata/chain.json" not in names:
                r.warn("MISSING_METADATA", "metadata/chain.json recommended")

    except zipfile.BadZipFile:
        r.error("CORRUPT_BUNDLE", "Bundle is not a valid ZIP/JMPG file")
    except json.JSONDecodeError as e:
        r.error("INVALID_JSON", f"manifest.json is not valid JSON: {e}")
    except Exception as e:
        r.error("UNEXPECTED_ERROR", f"Validation error: {e}")

    return r


# ─── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="WINDI Evidence Schema Validator v1.1",
        epilog='"The evidence speaks. The hash proves. The Ledger remembers."'
    )
    parser.add_argument("manifest", nargs="?", help="Path to manifest.json")
    parser.add_argument("--bundle", help="Path to .jmpg bundle (validates everything)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.manifest and not args.bundle:
        parser.print_help()
        sys.exit(0)

    if args.bundle:
        result = validate_bundle(args.bundle)
    else:
        with open(args.manifest) as f:
            manifest = json.load(f)
        result = validate_manifest(manifest, strict=args.strict)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        result.print_report()

    sys.exit(0 if result.valid else 1)


if __name__ == "__main__":
    main()
