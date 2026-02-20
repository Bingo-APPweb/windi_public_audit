#!/usr/bin/env python3
"""
WINDI SIP Layer 1 — Test Suite
Validates all cryptographic and identity functions locally.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sip_layer1 import (
    generate_salt, hash_passphrase, verify_passphrase,
    validate_passphrase_strength, log_event,
    setup_passphrase, verify_identity, show_status
)

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name}")
        failed += 1


print()
print("╔═══════════════════════════════════════════════════════╗")
print("║   🧪 WINDI SIP Layer 1 — Test Suite                   ║")
print("╚═══════════════════════════════════════════════════════╝")
print()

# --- Salt Generation ---
print("  📌 Salt Generation")
salt1 = generate_salt()
salt2 = generate_salt()
test("Salt has correct length (64 hex chars = 256 bits)", len(salt1) == 64)
test("Salts are unique", salt1 != salt2)
test("Salt is hex string", all(c in '0123456789abcdef' for c in salt1))
print()

# --- Hash Function ---
print("  📌 Hash Function")
salt = generate_salt()
h1 = hash_passphrase("Meu Dragão voa sobre Kempten", salt)
h2 = hash_passphrase("Meu Dragão voa sobre Kempten", salt)
h3 = hash_passphrase("Meu Dragão voa sobre Berlin", salt)
h4 = hash_passphrase("Meu Dragão voa sobre Kempten", generate_salt())
test("Hash is 64 hex chars (SHA-256)", len(h1) == 64)
test("Same input + same salt = same hash (deterministic)", h1 == h2)
test("Different input = different hash", h1 != h3)
test("Same input + different salt = different hash", h1 != h4)
print()

# --- Verification ---
print("  📌 Verification")
salt_v = generate_salt()
hash_v = hash_passphrase("Three Dragons Guard", salt_v)
test("Correct passphrase verifies", verify_passphrase("Three Dragons Guard", salt_v, hash_v))
test("Wrong passphrase fails", not verify_passphrase("Two Dragons Guard", salt_v, hash_v))
test("Empty passphrase fails", not verify_passphrase("", salt_v, hash_v))
test("Case sensitive", not verify_passphrase("three dragons guard", salt_v, hash_v))
print()

# --- Passphrase Strength ---
print("  📌 Passphrase Strength Validation")
valid1, issues1 = validate_passphrase_strength("Meu Dragão Voa Alto")
valid2, issues2 = validate_passphrase_strength("ab")
valid3, issues3 = validate_passphrase_strength("umapalavraso")  # 12 chars, 1 word, < 16
valid4, issues4 = validate_passphrase_strength("Der Drache fliegt Hoch über Kempten")
valid5, issues5 = validate_passphrase_strength("MeinDracheFliegtHoch")  # 20 chars, 1 word, >= 16
test("Multi-word phrase accepted", valid1)
test("Too short rejected", not valid2)
test("Short single word rejected (< 16 chars)", not valid3)
test("Long German multi-word accepted", valid4)
test("Long single word accepted (>= 16 chars)", valid5)
_, issues6 = validate_passphrase_strength("password is my code")
test("Weak pattern detected", any("password" in i.lower() for i in issues6))
print()

# --- Duress Detection ---
print("  📌 Duress Mechanism")
sovereign_salt = generate_salt()
duress_salt = generate_salt()
sovereign_hash = hash_passphrase("Minha Frase Soberana Real", sovereign_salt)
duress_hash = hash_passphrase("Frase de Emergencia Agora", duress_salt)

is_sovereign = verify_passphrase("Minha Frase Soberana Real", sovereign_salt, sovereign_hash)
is_duress = verify_passphrase("Frase de Emergencia Agora", duress_salt, duress_hash)
cross_check = verify_passphrase("Minha Frase Soberana Real", duress_salt, duress_hash)
test("Sovereign passphrase validates correctly", is_sovereign)
test("Duress passphrase validates correctly", is_duress)
test("Sovereign doesn't match duress hash (isolation)", not cross_check)
print()

# --- Forensic Ledger ---
print("  📌 Forensic Ledger")
with tempfile.TemporaryDirectory() as tmpdir:
    ledger_path = Path(tmpdir) / "test_ledger.jsonl"
    log_event("TEST_EVENT", {"test": True, "value": 42}, ledger_path)
    log_event("TEST_EVENT_2", {"test": True, "value": 99}, ledger_path)

    test("Ledger file created", ledger_path.exists())
    with open(ledger_path) as f:
        lines = f.readlines()
    test("Two events recorded", len(lines) == 2)
    entry = json.loads(lines[0])
    test("Event has timestamp", "timestamp" in entry)
    test("Event has correct type", entry["event_type"] == "TEST_EVENT")
    test("Event has protocol=SIP", entry["protocol"] == "SIP")
    test("Event has layer=1", entry["layer"] == 1)
print()

# --- Full Cycle (Non-Interactive) ---
print("  📌 Full Identity Cycle (Programmatic)")
with tempfile.TemporaryDirectory() as tmpdir:
    id_path = Path(tmpdir) / "identity.json"
    led_path = Path(tmpdir) / "ledger.jsonl"

    # Simulate setup (programmatic, not interactive)
    sov_salt = generate_salt()
    dur_salt = generate_salt()
    identity = {
        "protocol": "WINDI Sovereign Identity Protocol",
        "version": "1.0.0",
        "layer": 1,
        "status": "ACTIVE",
        "sovereign": {
            "algorithm": "SHA-256",
            "rounds": 100000,
            "salt": sov_salt,
            "hash": hash_passphrase("O Dragão Protege a Constituição", sov_salt)
        },
        "duress": {
            "algorithm": "SHA-256",
            "rounds": 100000,
            "salt": dur_salt,
            "hash": hash_passphrase("Socorro Estou Sob Pressão", dur_salt)
        }
    }
    with open(id_path, 'w') as f:
        json.dump(identity, f)

    test("Identity file created", id_path.exists())

    # Verify sovereign
    with open(id_path) as f:
        loaded = json.load(f)
    sov_ok = verify_passphrase(
        "O Dragão Protege a Constituição",
        loaded["sovereign"]["salt"],
        loaded["sovereign"]["hash"]
    )
    test("Sovereign passphrase verifies from file", sov_ok)

    # Verify duress
    dur_ok = verify_passphrase(
        "Socorro Estou Sob Pressão",
        loaded["duress"]["salt"],
        loaded["duress"]["hash"]
    )
    test("Duress passphrase verifies from file", dur_ok)

    # Wrong passphrase
    wrong = verify_passphrase(
        "Tentativa Errada Aqui",
        loaded["sovereign"]["salt"],
        loaded["sovereign"]["hash"]
    )
    test("Wrong passphrase fails verification", not wrong)
print()

# --- RESULTS ---
print("═══════════════════════════════════════════════════════")
total = passed + failed
print(f"  Resultado: {passed}/{total} testes passaram")
if failed == 0:
    print("  🐉 TODOS OS TESTES PASSARAM — SIP Layer 1 validado!")
else:
    print(f"  ⚠️  {failed} teste(s) falharam — revisar antes do deploy!")
print("═══════════════════════════════════════════════════════")
print()

sys.exit(0 if failed == 0 else 1)
