#!/usr/bin/env python3
"""
WINDI Capsule (.wcap) Validator
Schema: wcap-v0.1.0.json
Invariants: I9, I11, I12, I14, I16

Usage:
    python3 wcap_validator.py manifest.json
    python3 wcap_validator.py examples/wcap-welcome-hotel-kempten.json
"""

import json
import sys
import hashlib
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip3 install jsonschema")
    sys.exit(1)


SCHEMA_PATH = Path(__file__).parent / "wcap-v0.1.0.json"


def load_schema():
    """Load the .wcap JSON Schema."""
    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema not found at {SCHEMA_PATH}")
        sys.exit(1)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_manifest(path: str):
    """Load a manifest.json file."""
    manifest_path = Path(path)
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found at {manifest_path}")
        sys.exit(1)
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(manifest: dict, schema: dict) -> list:
    """Validate manifest against JSON Schema. Returns list of errors."""
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(manifest))
    return errors


def validate_i9_invariant(manifest: dict) -> list:
    """Extra validation: I9 must be in invariants list."""
    errors = []
    invariants = manifest.get("governance", {}).get("invariants", [])
    if "I9" not in invariants:
        errors.append("CONSTITUTIONAL VIOLATION: I9 (Prohibition of Autonomy Escalation) missing from invariants. This is IRREMEDIABLE.")
    if manifest.get("governance", {}).get("human_approved") is not True:
        errors.append("CONSTITUTIONAL VIOLATION: human_approved must be true. Auto-approval violates I9.")
    return errors


def validate_i16_privacy(manifest: dict) -> list:
    """Extra validation: I16 privacy fields must be true."""
    errors = []
    privacy = manifest.get("spatial", {}).get("privacy", {})
    if privacy.get("gps_never_uploaded") is not True:
        errors.append("CONSTITUTIONAL VIOLATION: gps_never_uploaded must be true. GPS tracking violates I16.")
    if privacy.get("zone_detection_local") is not True:
        errors.append("CONSTITUTIONAL VIOLATION: zone_detection_local must be true. Server-side geofencing violates I16.")
    return errors


def validate_i12_trilingual(manifest: dict) -> list:
    """Extra validation: All name/title fields must have de, en, pt."""
    errors = []
    required_langs = {"de", "en", "pt"}

    # Check capsule name
    name = manifest.get("name", {})
    if set(name.keys()) != required_langs:
        errors.append(f"I12 VIOLATION: Capsule name missing languages. Has: {set(name.keys())}, needs: {required_langs}")

    # Check zone names
    for zone in manifest.get("spatial", {}).get("zones", []):
        zone_name = zone.get("name", {})
        if set(zone_name.keys()) != required_langs:
            errors.append(f"I12 VIOLATION: Zone '{zone.get('zone_id')}' name missing languages.")

    # Check media titles
    for media in manifest.get("media", []):
        title = media.get("title", {})
        if set(title.keys()) != required_langs:
            errors.append(f"I12 VIOLATION: Media '{media.get('media_id')}' title missing languages.")

    return errors


def validate_version_compatibility(manifest: dict) -> list:
    """Validate version fields exist and are valid SemVer."""
    errors = []
    version = manifest.get("wcap_version", {})

    current = version.get("current", "")
    minimum = version.get("minimum_compatible", "")

    if not current:
        errors.append("Version error: wcap_version.current is required")
    if not minimum:
        errors.append("Version error: wcap_version.minimum_compatible is required")

    # Simple SemVer check
    import re
    semver_pattern = r"^[0-9]+\.[0-9]+\.[0-9]+$"
    if current and not re.match(semver_pattern, current):
        errors.append(f"Version error: '{current}' is not valid SemVer")
    if minimum and not re.match(semver_pattern, minimum):
        errors.append(f"Version error: '{minimum}' is not valid SemVer")

    return errors


def compute_canonical_hash(manifest: dict) -> str:
    """Compute SHA-256 of canonical JSON (excluding signature)."""
    manifest_copy = {k: v for k, v in manifest.items() if k != "signature"}
    canonical = json.dumps(manifest_copy, sort_keys=True, separators=(",", ":"))
    hash_bytes = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{hash_bytes}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 wcap_validator.py <manifest.json>")
        print("       python3 wcap_validator.py examples/wcap-welcome-hotel-kempten.json")
        sys.exit(1)

    manifest_path = sys.argv[1]
    print(f"\n=== WINDI Capsule Validator ===")
    print(f"Schema: wcap-v0.1.0")
    print(f"File: {manifest_path}\n")

    # Load
    schema = load_schema()
    manifest = load_manifest(manifest_path)

    all_errors = []

    # 1. JSON Schema validation
    print("[1/5] JSON Schema validation...")
    schema_errors = validate_schema(manifest, schema)
    if schema_errors:
        for err in schema_errors:
            all_errors.append(f"Schema: {err.message} at {list(err.path)}")
            print(f"  ERROR: {err.message}")
    else:
        print("  OK")

    # 2. Version compatibility
    print("[2/5] Version compatibility...")
    version_errors = validate_version_compatibility(manifest)
    all_errors.extend(version_errors)
    if version_errors:
        for err in version_errors:
            print(f"  ERROR: {err}")
    else:
        print("  OK")

    # 3. I9 Invariant (Human Approval)
    print("[3/5] I9 Invariant (Human Approval)...")
    i9_errors = validate_i9_invariant(manifest)
    all_errors.extend(i9_errors)
    if i9_errors:
        for err in i9_errors:
            print(f"  ERROR: {err}")
    else:
        print("  OK")

    # 4. I16 Privacy
    print("[4/5] I16 Invariant (GPS Privacy)...")
    i16_errors = validate_i16_privacy(manifest)
    all_errors.extend(i16_errors)
    if i16_errors:
        for err in i16_errors:
            print(f"  ERROR: {err}")
    else:
        print("  OK")

    # 5. I12 Trilingual
    print("[5/5] I12 Invariant (Trilingual)...")
    i12_errors = validate_i12_trilingual(manifest)
    all_errors.extend(i12_errors)
    if i12_errors:
        for err in i12_errors:
            print(f"  ERROR: {err}")
    else:
        print("  OK")

    # Compute canonical hash
    computed_hash = compute_canonical_hash(manifest)
    declared_hash = manifest.get("manifest_canonical_hash", "")

    print(f"\n--- Integrity ---")
    print(f"Computed hash: {computed_hash}")
    print(f"Declared hash: {declared_hash}")

    if declared_hash and declared_hash != "sha256:0000000000000000000000000000000000000000000000000000000000000000":
        if computed_hash == declared_hash:
            print("Hash verification: MATCH")
        else:
            print("Hash verification: MISMATCH (manifest may have been modified)")
            all_errors.append("Integrity: manifest_canonical_hash does not match computed hash")
    else:
        print("Hash verification: SKIPPED (placeholder hash)")

    # Summary
    print(f"\n=== RESULT ===")
    if all_errors:
        print(f"INVALID: {len(all_errors)} error(s) found")
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("VALID: Capsule passes all constitutional checks")
        print(f"\nCapsule ID: {manifest.get('capsule_id', 'N/A')}")
        print(f"Type: {manifest.get('type', 'N/A')}")
        print(f"Issuer: {manifest.get('issuer', {}).get('name', 'N/A')} ({manifest.get('issuer', {}).get('tier', 'N/A')})")
        print(f"Zones: {len(manifest.get('spatial', {}).get('zones', []))}")
        print(f"Media items: {len(manifest.get('media', []))}")
        sys.exit(0)


if __name__ == "__main__":
    main()
