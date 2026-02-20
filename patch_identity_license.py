#!/usr/bin/env python3
"""
WINDI ISP Identity License Patcher
====================================
Adds identity_license to 8 HIGH/MEDIUM profiles missing it.
After patch → re-run audit → expect Grade A (95+).

Invariante I9: This script is HUMAN-INITIATED.
               Run manually after review. No auto_apply.

Usage:
  python3 patch_identity_license.py --dry-run    # Preview changes
  python3 patch_identity_license.py --apply       # Apply changes
  python3 patch_identity_license.py --apply --audit  # Apply + re-run audit

Version: 1.0.0 | 08 Feb 2026
"""

import json
import os
import sys
import shutil
import hashlib
from datetime import datetime, timezone

# ─── Configuration ───────────────────────────────────────────────
ISP_BASE = "/opt/windi/isp"
BACKUP_DIR = "/opt/windi/backups"
AGENT_SCRIPT = "/opt/windi/agents/isp-manager/isp_manager_agent.py"

# The 8 profiles missing identity_license (from audit 08 Feb 2026)
PROFILES_TO_PATCH = {
    # HIGH (3) — regulatory/financial authorities → status: authorized
    "bafin": {
        "governance_level": "HIGH",
        "license": {
            "status": "authorized",
            "type": "regulatory_authority",
            "jurisdiction": "DE",
            "issuing_body": "Bundesanstalt für Finanzdienstleistungsaufsicht",
            "valid_from": "2026-02-08",
            "review_cycle": "annual",
            "disclaimer": {
                "de": "Dieses Profil dient ausschließlich der Dokumentengovernance. Es stellt keine Autorisierung durch die BaFin dar.",
                "en": "This profile serves document governance only. It does not represent authorization by BaFin.",
                "pt": "Este perfil serve apenas para governança de documentos. Não representa autorização pela BaFin."
            }
        }
    },
    "bis-regulatory": {
        "governance_level": "HIGH",
        "license": {
            "status": "authorized",
            "type": "international_regulatory",
            "jurisdiction": "INT",
            "issuing_body": "Bank for International Settlements",
            "valid_from": "2026-02-08",
            "review_cycle": "annual",
            "disclaimer": {
                "de": "Dieses Profil dient ausschließlich der Dokumentengovernance. Es stellt keine Autorisierung durch die BIS dar.",
                "en": "This profile serves document governance only. It does not represent authorization by BIS.",
                "pt": "Este perfil serve apenas para governança de documentos. Não representa autorização pelo BIS."
            }
        }
    },
    "ecb": {
        "governance_level": "HIGH",
        "license": {
            "status": "authorized",
            "type": "central_bank",
            "jurisdiction": "EU",
            "issuing_body": "European Central Bank",
            "valid_from": "2026-02-08",
            "review_cycle": "annual",
            "disclaimer": {
                "de": "Dieses Profil dient ausschließlich der Dokumentengovernance. Es stellt keine Autorisierung durch die EZB dar.",
                "en": "This profile serves document governance only. It does not represent authorization by ECB.",
                "pt": "Este perfil serve apenas para governança de documentos. Não representa autorização pelo BCE."
            }
        }
    },
    # MEDIUM (5) — government/public bodies → status: model_only
    "aok": {
        "governance_level": "MEDIUM",
        "license": {
            "status": "model_only",
            "type": "public_health_insurance",
            "jurisdiction": "DE",
            "issuing_body": "AOK Bundesverband",
            "valid_from": "2026-02-08",
            "review_cycle": "annual",
            "disclaimer": {
                "de": "Dieses Profil dient ausschließlich der Dokumentengovernance. Modellprofil ohne institutionelle Autorisierung.",
                "en": "This profile serves document governance only. Model profile without institutional authorization.",
                "pt": "Este perfil serve apenas para governança de documentos. Perfil modelo sem autorização institucional."
            }
        }
    },
    "bundesagentur": {
        "governance_level": "MEDIUM",
        "license": {
            "status": "model_only",
            "type": "federal_agency",
            "jurisdiction": "DE",
            "issuing_body": "Bundesagentur für Arbeit",
            "valid_from": "2026-02-08",
            "review_cycle": "annual",
            "disclaimer": {
                "de": "Dieses Profil dient ausschließlich der Dokumentengovernance. Modellprofil ohne institutionelle Autorisierung.",
                "en": "This profile serves document governance only. Model profile without institutional authorization.",
                "pt": "Este perfil serve apenas para governança de documentos. Perfil modelo sem autorização institucional."
            }
        }
    },
    "bundesregierung": {
        "governance_level": "MEDIUM",
        "license": {
            "status": "model_only",
            "type": "federal_government",
            "jurisdiction": "DE",
            "issuing_body": "Bundesregierung der Bundesrepublik Deutschland",
            "valid_from": "2026-02-08",
            "review_cycle": "annual",
            "disclaimer": {
                "de": "Dieses Profil dient ausschließlich der Dokumentengovernance. Modellprofil ohne institutionelle Autorisierung.",
                "en": "This profile serves document governance only. Model profile without institutional authorization.",
                "pt": "Este perfil serve apenas para governança de documentos. Perfil modelo sem autorização institucional."
            }
        }
    },
    "bayern": {
        "governance_level": "MEDIUM",
        "license": {
            "status": "model_only",
            "type": "state_government",
            "jurisdiction": "DE-BY",
            "issuing_body": "Freistaat Bayern",
            "valid_from": "2026-02-08",
            "review_cycle": "annual",
            "disclaimer": {
                "de": "Dieses Profil dient ausschließlich der Dokumentengovernance. Modellprofil ohne institutionelle Autorisierung.",
                "en": "This profile serves document governance only. Model profile without institutional authorization.",
                "pt": "Este perfil serve apenas para governança de documentos. Perfil modelo sem autorização institucional."
            }
        }
    },
    "sparkasse": {
        "governance_level": "MEDIUM",
        "license": {
            "status": "model_only",
            "type": "financial_institution",
            "jurisdiction": "DE",
            "issuing_body": "Deutscher Sparkassen- und Giroverband",
            "valid_from": "2026-02-08",
            "review_cycle": "annual",
            "disclaimer": {
                "de": "Dieses Profil dient ausschließlich der Dokumentengovernance. Modellprofil ohne institutionelle Autorisierung.",
                "en": "This profile serves document governance only. Model profile without institutional authorization.",
                "pt": "Este perfil serve apenas para governança de documentos. Perfil modelo sem autorização institucional."
            }
        }
    }
}


def compute_hash(data):
    """SHA-256 hash of JSON data for audit trail."""
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=False).encode('utf-8')
    ).hexdigest()[:16]


def load_profile(profile_id):
    """Load a profile.json, handling nested directory structures."""
    # Try direct path first
    path = os.path.join(ISP_BASE, profile_id, "profile.json")
    if os.path.isfile(path):
        return path

    # Some profiles might have different directory names
    for dirname in os.listdir(ISP_BASE):
        dirpath = os.path.join(ISP_BASE, dirname)
        if os.path.isdir(dirpath):
            # Check if dirname matches or contains profile_id
            if dirname == profile_id or profile_id in dirname:
                candidate = os.path.join(dirpath, "profile.json")
                if os.path.isfile(candidate):
                    return candidate

    return None


def patch_profile(profile_id, license_config, dry_run=True):
    """Add identity_license to a profile.json."""
    filepath = load_profile(profile_id)

    if not filepath:
        print(f"  ❌ {profile_id}: profile.json not found")
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            profile = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"  ❌ {profile_id}: Error reading - {e}")
        return False

    # Check if already has identity_license
    if "identity_license" in profile:
        existing = profile["identity_license"]
        status = existing.get("status", "unknown") if isinstance(existing, dict) else str(existing)
        print(f"  ⚠️  {profile_id}: Already has identity_license (status: {status}) — skipping")
        return True

    # Compute pre-patch hash
    pre_hash = compute_hash(profile)

    # Add identity_license
    profile["identity_license"] = license_config["license"]

    # Update metadata if exists
    if "metadata" in profile:
        profile["metadata"]["last_modified"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        profile["metadata"]["patch_note"] = "Added identity_license (ISP-W003 fix)"

    # Compute post-patch hash
    post_hash = compute_hash(profile)

    level = license_config["governance_level"]
    status = license_config["license"]["status"]

    if dry_run:
        print(f"  🔍 {profile_id} [{level}]: Would add identity_license (status: {status})")
        print(f"      Path: {filepath}")
        print(f"      Hash: {pre_hash} → {post_hash}")
        return True
    else:
        # Backup original
        backup_name = f"{profile_id}_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.bak"
        backup_path = os.path.join(BACKUP_DIR, "isp_license_patch", backup_name)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(filepath, backup_path)

        # Write patched profile
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

        print(f"  ✅ {profile_id} [{level}]: identity_license added (status: {status})")
        print(f"      Backup: {backup_path}")
        print(f"      Hash: {pre_hash} → {post_hash}")
        return True


def run_audit():
    """Re-run ISP Manager Agent audit."""
    import subprocess
    print("\n" + "═" * 55)
    print("  Re-running ISP Manager Agent Audit...")
    print("═" * 55 + "\n")

    try:
        result = subprocess.run(
            ["python3", AGENT_SCRIPT, "audit"],
            capture_output=True,
            text=True,
            timeout=120
        )
        print(result.stdout)
        if result.stderr:
            print(f"[stderr] {result.stderr}")

        # Check for Grade A
        if "Grade: A" in result.stdout or "Grade A" in result.stdout:
            print("\n🏆 GRADE A ACHIEVED! 🐉🐉🐉")
        elif "Grade:" in result.stdout:
            for line in result.stdout.split('\n'):
                if "Grade:" in line:
                    print(f"\n📊 Result: {line.strip()}")
                    break
    except Exception as e:
        print(f"❌ Audit failed: {e}")


def main():
    # Parse args
    dry_run = True
    do_audit = False

    if "--apply" in sys.argv:
        dry_run = False
    if "--audit" in sys.argv:
        do_audit = True
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("═" * 55)
    print("  WINDI ISP Identity License Patcher")
    print(f"  {'DRY RUN' if dry_run else 'APPLYING CHANGES'}")
    print(f"  Time: {timestamp}")
    print("═" * 55)
    print()
    print(f"  Target: {len(PROFILES_TO_PATCH)} profiles (3 HIGH + 5 MEDIUM)")
    print(f"  ISP Base: {ISP_BASE}")
    print(f"  I9: Human-initiated. No auto_apply.")
    print()

    if not dry_run:
        print("  ⚠️  This will MODIFY profile.json files!")
        print("  ⚠️  Backups will be created in /opt/windi/backups/isp_license_patch/")
        print()

    success = 0
    failed = 0

    print("─── HIGH Profiles ─────────────────────────────────")
    for pid in ["bafin", "bis-regulatory", "ecb"]:
        if patch_profile(pid, PROFILES_TO_PATCH[pid], dry_run):
            success += 1
        else:
            failed += 1

    print()
    print("─── MEDIUM Profiles ───────────────────────────────")
    for pid in ["aok", "bundesagentur", "bundesregierung", "bayern", "sparkasse"]:
        if patch_profile(pid, PROFILES_TO_PATCH[pid], dry_run):
            success += 1
        else:
            failed += 1

    print()
    print("═" * 55)
    print(f"  Results: {success} patched, {failed} failed")
    print("═" * 55)

    if dry_run:
        print()
        print("  This was a DRY RUN. To apply:")
        print("  python3 patch_identity_license.py --apply")
        print("  python3 patch_identity_license.py --apply --audit")
    elif do_audit:
        run_audit()

    print()
    print("  🐉 I9 Enforced: Human decided. Script executed.")
    print()


if __name__ == "__main__":
    main()
