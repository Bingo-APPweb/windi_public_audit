#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           WINDI VAULT BROADCAST v1.0.0                       ║
║   "O Correio Diplomático" — Export → Ledger → Vault          ║
║                                                              ║
║   Moves sealed binaries from Export Engine to Forensic Vault ║
║   ONLY after Ledger confirmation. No seal = no broadcast.    ║
║                                                              ║
║   "AI processes. Human decides. WINDI guarantees."           ║
╚══════════════════════════════════════════════════════════════╝

Integration point: communique_publisher.py
After register_in_ledger() returns receipt_id, call:
    broadcast_to_vault(package_id, receipt_id, source_path)

The Vault (:8106) becomes the immutable public archive.
Nginx serves /vault/multimedia/ as read-only static files.
"""

import os
import json
import shutil
import hashlib
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────
VAULT_BASE = os.environ.get("WINDI_VAULT_BASE", "/opt/windi/vault")
VAULT_MULTIMEDIA = os.path.join(VAULT_BASE, "multimedia")
VAULT_MANIFEST = os.path.join(VAULT_BASE, "broadcast_manifest.json")

LEDGER_URL = os.environ.get("WINDI_LEDGER_URL", "http://127.0.0.1:8101")
VAULT_PUBLIC_BASE = os.environ.get(
    "WINDI_VAULT_PUBLIC_URL",
    "https://admin.windia4desk.tech/vault/multimedia"
)

LOG_PATH = os.environ.get("WINDI_VAULT_LOG", "/opt/windi/logs/vault_broadcast.log")

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [VAULT-BROADCAST] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("vault_broadcast")


# ── Core Functions ─────────────────────────────────────────────

def verify_ledger_seal(receipt_id: str) -> dict:
    """
    Verify that a receipt exists and is sealed in the Forensic Ledger.
    Returns the receipt data if valid, raises ValueError if not.

    PRINCIPLE: No seal = no broadcast. The Ledger is the single source of truth.
    """
    url = f"{LEDGER_URL}/api/receipts/{receipt_id}"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # Unwrap potential double-nesting (known Ledger behavior)
        receipt = data.get("receipt", data)
        if isinstance(receipt, dict) and "receipt" in receipt:
            receipt = receipt["receipt"]

        status = receipt.get("status", "unknown")
        if status != "sealed":
            raise ValueError(
                f"Receipt {receipt_id} status is '{status}', not 'sealed'. "
                f"Broadcast DENIED — only sealed receipts can be broadcasted."
            )

        log.info(f"Ledger seal VERIFIED: {receipt_id} → status={status}")
        return receipt

    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Cannot reach Ledger at {LEDGER_URL}: {e}. "
            f"Broadcast ABORTED — Ledger unreachable."
        )


def compute_file_hash(filepath: str, algorithm: str = "sha256") -> str:
    """Compute SHA-256 hash of a file for integrity verification."""
    h = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def broadcast_to_vault(
    package_id: str,
    receipt_id: str,
    source_path: str,
    metadata: dict = None
) -> dict:
    """
    Broadcast a sealed binary to the Forensic Vault.

    FLOW:
    1. Verify Ledger seal exists and is valid
    2. Compute source file hash
    3. Copy to Vault multimedia directory
    4. Verify copied file hash matches
    5. Set read-only permissions
    6. Register in broadcast manifest
    7. Return public URL

    Args:
        package_id: JMPG package ID (e.g., "JMPG-20260219-A194B2E4")
        receipt_id: Ledger receipt ID (e.g., "VR-COM-ef5ef676e196")
        source_path: Path to the exported binary file
        metadata: Optional additional metadata dict

    Returns:
        dict with: vault_path, public_url, file_hash, broadcast_timestamp, receipt_id

    Raises:
        ValueError: If Ledger seal is invalid
        FileNotFoundError: If source file doesn't exist
        ConnectionError: If Ledger is unreachable
    """
    timestamp = datetime.now(timezone.utc)

    # ── Step 1: Verify Ledger Seal ────────────────────────────
    log.info(f"Broadcasting {package_id} → Vault (receipt: {receipt_id})")
    receipt = verify_ledger_seal(receipt_id)

    # ── Step 2: Validate Source File ──────────────────────────
    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"Source file not found: {source_path}. "
            f"Cannot broadcast a file that doesn't exist."
        )

    source_hash = compute_file_hash(source_path)
    file_size = os.path.getsize(source_path)
    file_ext = Path(source_path).suffix  # .jmpg, .pdf, .png, etc.

    log.info(f"Source: {source_path} ({file_size} bytes, hash={source_hash[:16]}...)")

    # ── Step 3: Determine Vault Filename ──────────────────────
    # Format: VR-{receipt_id_suffix}.{ext}
    # e.g., VR-COM-ef5ef676e196.jmpg
    vault_filename = f"{receipt_id}{file_ext}"

    # Create multimedia directory if it doesn't exist
    os.makedirs(VAULT_MULTIMEDIA, exist_ok=True)

    vault_path = os.path.join(VAULT_MULTIMEDIA, vault_filename)

    # ── Step 4: Copy to Vault ─────────────────────────────────
    if os.path.exists(vault_path):
        existing_hash = compute_file_hash(vault_path)
        if existing_hash == source_hash:
            log.info(f"File already in Vault with matching hash — skipping copy")
        else:
            raise ValueError(
                f"HASH CONFLICT: Vault already has {vault_filename} "
                f"with different hash ({existing_hash[:16]}... vs {source_hash[:16]}...). "
                f"This indicates tampering or collision. Broadcast DENIED."
            )
    else:
        shutil.copy2(source_path, vault_path)
        log.info(f"Copied to Vault: {vault_path}")

    # ── Step 5: Verify Copy Integrity ─────────────────────────
    vault_hash = compute_file_hash(vault_path)
    if vault_hash != source_hash:
        # Critical: copy corrupted — remove and abort
        os.remove(vault_path)
        raise RuntimeError(
            f"INTEGRITY FAILURE: Vault copy hash ({vault_hash[:16]}...) "
            f"doesn't match source ({source_hash[:16]}...). "
            f"Corrupted copy removed. Broadcast ABORTED."
        )

    log.info(f"Integrity verified: source_hash == vault_hash")

    # ── Step 6: Set Read-Only ─────────────────────────────────
    os.chmod(vault_path, 0o444)  # r--r--r-- (nobody can modify)
    log.info(f"Permissions set: 0444 (read-only)")

    # ── Step 7: Build Public URL ──────────────────────────────
    public_url = f"{VAULT_PUBLIC_BASE}/{vault_filename}"

    # ── Step 8: Register in Broadcast Manifest ────────────────
    broadcast_entry = {
        "package_id": package_id,
        "receipt_id": receipt_id,
        "vault_filename": vault_filename,
        "vault_path": vault_path,
        "public_url": public_url,
        "file_hash": source_hash,
        "file_size": file_size,
        "file_ext": file_ext,
        "ledger_status": receipt.get("status", "sealed"),
        "ledger_content_hash": receipt.get("content_hash", ""),
        "broadcast_timestamp": timestamp.isoformat(),
        "metadata": metadata or {}
    }

    _append_to_manifest(broadcast_entry)

    log.info(
        f"BROADCAST COMPLETE: {package_id} → {public_url} "
        f"(sealed by {receipt_id})"
    )

    return broadcast_entry


def _append_to_manifest(entry: dict):
    """Append a broadcast entry to the persistent manifest."""
    manifest = {"broadcasts": [], "version": "1.0.0"}

    if os.path.exists(VAULT_MANIFEST):
        try:
            with open(VAULT_MANIFEST, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, IOError):
            log.warning("Manifest corrupted or unreadable — creating new")

    manifest["broadcasts"].append(entry)
    manifest["last_updated"] = datetime.now(timezone.utc).isoformat()
    manifest["total_broadcasts"] = len(manifest["broadcasts"])

    with open(VAULT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    log.info(f"Manifest updated: {manifest['total_broadcasts']} total broadcasts")


def get_vault_url(receipt_id: str, ext: str = ".jmpg") -> str:
    """Quick helper to build Vault URL from receipt_id."""
    return f"{VAULT_PUBLIC_BASE}/{receipt_id}{ext}"


def list_broadcasts(limit: int = 20) -> list:
    """List recent broadcasts from manifest."""
    if not os.path.exists(VAULT_MANIFEST):
        return []

    with open(VAULT_MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    broadcasts = manifest.get("broadcasts", [])
    return broadcasts[-limit:]


# ── Integration Helper for communique_publisher.py ─────────────

def integrate_with_publisher(
    package_id: str,
    receipt_id: str,
    export_output_path: str,
    communique_id: str = None
) -> dict:
    """
    High-level integration function for communique_publisher.py.

    Call this AFTER register_in_ledger() succeeds.

    Usage in communique_publisher.py:

        from windi_vault_broadcast import integrate_with_publisher

        # After Ledger registration:
        receipt = register_in_ledger(content_hash, doc_type="communique", ...)
        receipt_id = receipt.get("receipt_id") or receipt.get("id")

        # Broadcast to Vault:
        broadcast = integrate_with_publisher(
            package_id=jmpg_result["package_id"],
            receipt_id=receipt_id,
            export_output_path=jmpg_result["output_path"],
            communique_id="COM-20260219-0001"
        )

        # Use in PDF/Feed:
        vault_url = broadcast["public_url"]

    Returns:
        dict with public_url, vault_path, file_hash, etc.
        On failure: dict with error key and fallback_url
    """
    try:
        result = broadcast_to_vault(
            package_id=package_id,
            receipt_id=receipt_id,
            source_path=export_output_path,
            metadata={
                "communique_id": communique_id,
                "integration": "communique_publisher",
                "pipeline": "PUBLISH → LEDGER → VAULT"
            }
        )

        log.info(
            f"Vault broadcast for {communique_id}: {result['public_url']}"
        )
        return result

    except (ValueError, ConnectionError, FileNotFoundError, RuntimeError) as e:
        log.error(f"Vault broadcast FAILED for {package_id}: {e}")
        return {
            "error": str(e),
            "package_id": package_id,
            "receipt_id": receipt_id,
            "fallback_url": None,
            "broadcast_status": "FAILED"
        }


# ── CLI for testing ────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════════╗
║              WINDI Vault Broadcast v1.0.0                    ║
║         "O Correio Diplomático" — Export → Vault             ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python3 windi_vault_broadcast.py test          — Self-test
    python3 windi_vault_broadcast.py list           — List broadcasts
    python3 windi_vault_broadcast.py broadcast \\
        <package_id> <receipt_id> <source_path>     — Manual broadcast

Environment:
    WINDI_VAULT_BASE     = /opt/windi/vault
    WINDI_LEDGER_URL     = http://127.0.0.1:8101
    WINDI_VAULT_PUBLIC_URL = https://admin.windia4desk.tech/vault/multimedia
""")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "test":
        print("Self-test: Checking Ledger connectivity...")
        try:
            req = urllib.request.Request(
                f"{LEDGER_URL}/health", method="GET"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                health = json.loads(resp.read().decode("utf-8"))
            print(f"Ledger reachable: {health.get('status', 'ok')}")
        except Exception as e:
            print(f"Ledger unreachable: {e}")

        print(f"Vault base: {VAULT_BASE}")
        print(f"Multimedia: {VAULT_MULTIMEDIA}")
        print(f"Public URL: {VAULT_PUBLIC_BASE}")

        if os.path.exists(VAULT_MANIFEST):
            broadcasts = list_broadcasts(5)
            print(f"Manifest: {len(broadcasts)} recent broadcasts")
            for b in broadcasts[-3:]:
                print(f"   -> {b['package_id']} ({b['broadcast_timestamp'][:10]})")
        else:
            print("No broadcasts yet")

        print("\nSelf-test complete")

    elif cmd == "list":
        broadcasts = list_broadcasts(20)
        if not broadcasts:
            print("No broadcasts found.")
        else:
            print(f"{'ID':<30} {'Receipt':<30} {'Date':<20} {'Size':>10}")
            print("-" * 94)
            for b in broadcasts:
                print(
                    f"{b['package_id']:<30} "
                    f"{b['receipt_id']:<30} "
                    f"{b['broadcast_timestamp'][:19]:<20} "
                    f"{b.get('file_size', 0):>10,}"
                )

    elif cmd == "broadcast" and len(sys.argv) >= 5:
        pkg_id = sys.argv[2]
        rcpt_id = sys.argv[3]
        src_path = sys.argv[4]
        result = broadcast_to_vault(pkg_id, rcpt_id, src_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
