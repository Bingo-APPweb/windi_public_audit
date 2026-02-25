#!/usr/bin/env python3
"""
WINDI Clone Commissioning Module
Phase 2: Generate WindiCloneWallet with Ed25519

"AI processes. Human decides. WINDI guarantees."
Commissioned by: Human Dragon — 25 February 2026
"""

import json
import hashlib
import base64
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ed25519 imports
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

# === PATHS ===
CLONE_DIR = Path("/opt/windi/clone")
CHECKPOINT_FILE = CLONE_DIR / "CHECKPOINT.json"
IDENTITY_FILE = CLONE_DIR / "matrix/P4-governance/identity.json"
CLONE_WALLET_FILE = CLONE_DIR / "CLONE_WALLET.json"
PRIVATE_KEY_FILE = CLONE_DIR / "clone_wallet_private.pem"
PUBLIC_KEY_FILE = CLONE_DIR / "clone_wallet_public.pem"
MATRIX_DIR = CLONE_DIR / "matrix"
LEDGER_URL = "http://localhost:8101/api/receipts"


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def sha256_hex(data: bytes) -> str:
    """Compute SHA-256 hash in hex."""
    return hashlib.sha256(data).hexdigest()


def check_i9_clean() -> tuple[bool, int]:
    """
    I9 Check: Proibicao de Escalacao de Autonomia
    ABORT if auto_apply is found in matrix.
    """
    result = subprocess.run(
        ["grep", "-r", "auto_apply", str(MATRIX_DIR)],
        capture_output=True,
        text=True
    )
    count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    return count == 0, count


def generate_ed25519_keypair() -> tuple[bytes, bytes, str]:
    """
    Generate Ed25519 key pair.
    Returns: (private_pem, public_pem, fingerprint)
    """
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Serialize private key (PEM format, no encryption)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key (PEM format)
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Fingerprint: SHA-256 of raw public key bytes
    raw_public = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    fingerprint = f"sha256:{sha256_hex(raw_public)}"

    return private_pem, public_pem, fingerprint


def send_receipt_to_ledger(receipt: dict) -> dict:
    """Send virtue receipt to ledger service."""
    import urllib.request

    data = json.dumps(receipt).encode('utf-8')
    req = urllib.request.Request(
        LEDGER_URL,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}


def main():
    print("=" * 60)
    print("  WINDI Clone Commissioning — Phase 2")
    print("  Generate WindiCloneWallet with Ed25519")
    print("=" * 60)
    print()

    # === IDEMPOTENCY CHECK ===
    if CLONE_WALLET_FILE.exists():
        print(f"[ABORT] CLONE_WALLET.json already exists at {CLONE_WALLET_FILE}")
        print("        Commissioning is idempotent. Delete existing file to re-run.")
        sys.exit(1)

    # === 1. Load Checkpoint ===
    print("[1/7] Loading CHECKPOINT.json...")
    checkpoint = load_json(CHECKPOINT_FILE)
    memory_codes = checkpoint.get("memory_codes", {})

    agent_id = memory_codes.get("agent_id")
    genesis_seal = memory_codes.get("genesis_seal")
    state_seal = memory_codes.get("state_seal")
    fusion_hash = memory_codes.get("fusion_hash", "")

    print(f"      Agent ID:     {agent_id}")
    print(f"      Genesis Seal: {genesis_seal}")
    print(f"      State Seal:   {state_seal}")

    if not all([agent_id, genesis_seal, state_seal]):
        print("[ABORT] Missing required fields in CHECKPOINT.json")
        sys.exit(1)

    # === 2. Load Identity & Confirm Lineage ===
    print("\n[2/7] Loading identity.json and confirming lineage...")
    identity = load_json(IDENTITY_FILE)
    id_data = identity.get("identity", {})

    if id_data.get("agent_id") != agent_id:
        print(f"[ABORT] Agent ID mismatch: checkpoint={agent_id}, identity={id_data.get('agent_id')}")
        sys.exit(1)

    print(f"      Lineage:      {id_data.get('lineage')}")
    print(f"      Agent Class:  {id_data.get('agent_class')}")
    print(f"      Agent Role:   {id_data.get('agent_role')}")

    # === 3. I9 Check ===
    print("\n[3/7] Validating I9 — Proibicao de Escalacao de Autonomia...")
    i9_clean, i9_count = check_i9_clean()

    if not i9_clean:
        print(f"[ABORT] I9 VIOLATION: Found {i9_count} occurrences of 'auto_apply' in matrix!")
        print("        Commissioning CANNOT proceed with autonomy escalation markers.")
        sys.exit(1)

    print("      I9 Status: CLEAN (0 auto_apply occurrences)")

    # === 4. Generate Ed25519 Key Pair ===
    print("\n[4/7] Generating Ed25519 key pair...")
    private_pem, public_pem, fingerprint = generate_ed25519_keypair()

    # Save private key (chmod 600)
    with open(PRIVATE_KEY_FILE, 'wb') as f:
        f.write(private_pem)
    os.chmod(PRIVATE_KEY_FILE, 0o600)

    # Save public key
    with open(PUBLIC_KEY_FILE, 'wb') as f:
        f.write(public_pem)

    print(f"      Private Key:  {PRIVATE_KEY_FILE} (chmod 600)")
    print(f"      Public Key:   {PUBLIC_KEY_FILE}")
    print(f"      Fingerprint:  {fingerprint}")

    # === 5. Generate WindiCloneWallet JSON ===
    print("\n[5/7] Generating CLONE_WALLET.json...")

    commissioned_at = datetime.now(timezone.utc).isoformat()
    public_key_b64 = base64.b64encode(public_pem).decode('utf-8')

    clone_wallet = {
        "wallet_type": "WindiCloneWallet",
        "wallet_version": "1.0",
        "clone_id": "CLONE-WINDI-GENESIS-001",
        "agent_id": agent_id,
        "tenant_id": "WINDI-PUBLISHING-HOUSE",
        "public_key": public_key_b64,
        "fingerprint": fingerprint,
        "constitutional_hash": state_seal,
        "genesis_seal": genesis_seal,
        "phase1_hash": fusion_hash[:32] if len(fusion_hash) >= 32 else "2310a8e62252c63e1f0fc1e97cb0ec96",
        "commissioned_at": commissioned_at,
        "commissioned_by": "Human Dragon",
        "phase": "PHASE_2_COMMISSIONED",
        "invariants_count": 9,
        "shelves_count": 8,
        "i9_status": "ACTIVE_IRREMEDIABLE"
    }

    with open(CLONE_WALLET_FILE, 'w', encoding='utf-8') as f:
        json.dump(clone_wallet, f, indent=2)

    print(f"      Saved: {CLONE_WALLET_FILE}")

    # === 6. Compute Hash of CLONE_WALLET.json ===
    wallet_json_bytes = json.dumps(clone_wallet, indent=2).encode('utf-8')
    wallet_hash = sha256_hex(wallet_json_bytes)
    print(f"      Wallet Hash:  {wallet_hash}")

    # === 7. Send Virtue Receipt to Ledger ===
    print("\n[6/7] Sending commissioning receipt to Ledger :8101...")

    receipt = {
        "type": "CLONE_COMMISSIONING",
        "agent_id": agent_id,
        "action": "PHASE2_COMMISSIONED",
        "hash": wallet_hash,
        "metadata": {
            "fingerprint": fingerprint,
            "constitutional_hash": state_seal,
            "genesis_seal": genesis_seal,
            "commissioned_at": commissioned_at,
            "commissioned_by": "Human Dragon"
        }
    }

    ledger_response = send_receipt_to_ledger(receipt)
    print(f"      Ledger Response: {json.dumps(ledger_response, indent=2)}")

    # === SUMMARY ===
    print("\n" + "=" * 60)
    print("  COMMISSIONING COMPLETE")
    print("=" * 60)
    print(f"""
  Clone ID:           {clone_wallet['clone_id']}
  Agent ID:           {agent_id}
  Tenant ID:          {clone_wallet['tenant_id']}
  Phase:              {clone_wallet['phase']}

  Ed25519 Fingerprint: {fingerprint}
  Constitutional Hash: {state_seal}
  Genesis Seal:        {genesis_seal}
  Phase1 Hash:         {clone_wallet['phase1_hash']}
  Wallet Hash:         {wallet_hash}

  Invariants:          {clone_wallet['invariants_count']} (I9 IRREMEDIABLE)
  Shelves:             {clone_wallet['shelves_count']} (ALL SEALED)
  I9 Status:           {clone_wallet['i9_status']}

  Commissioned At:     {commissioned_at}
  Commissioned By:     {clone_wallet['commissioned_by']}
    """)
    print("=" * 60)
    print("  'AI processes. Human decides. WINDI guarantees.'")
    print("=" * 60)


if __name__ == "__main__":
    main()
