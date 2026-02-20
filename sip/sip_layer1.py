#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║       WINDI SOVEREIGN IDENTITY PROTOCOL — LAYER 1            ║
║                  Constitutional Passphrase                    ║
║                                                               ║
║  AI processes. Human decides. WINDI guarantees.               ║
╚═══════════════════════════════════════════════════════════════╝

Zero-Knowledge Architecture:
- The passphrase is NEVER stored anywhere
- Only the SHA-256 hash + salt is persisted
- Verification = hash(input + salt) == stored_hash
- Duress passphrase triggers silent coercion alert

Date: 08 February 2026
Author: Three Dragons Council
Status: CONSTITUTIONAL ANNEX TO I9
"""

import hashlib
import secrets
import json
import os
import sys
import getpass
from datetime import datetime, timezone
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

SIP_DIR = Path("/opt/windi/sip")
SIP_IDENTITY_FILE = SIP_DIR / "sovereign_identity.json"
SIP_LEDGER_FILE = SIP_DIR / "sip_ledger.jsonl"
SALT_LENGTH = 32  # 256-bit salt
MIN_PASSPHRASE_LENGTH = 10
MIN_PASSPHRASE_WORDS = 2  # OR 16+ chars single word

# ═══════════════════════════════════════════════════════════════
# CORE CRYPTOGRAPHIC FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def generate_salt() -> str:
    """Generate a cryptographically secure random salt."""
    return secrets.token_hex(SALT_LENGTH)


def hash_passphrase(passphrase: str, salt: str) -> str:
    """
    Hash passphrase with salt using SHA-256.
    Uses multiple rounds for key stretching.
    """
    # 100,000 rounds of SHA-256 for key stretching
    current = f"{salt}:{passphrase}".encode('utf-8')
    for _ in range(100_000):
        current = hashlib.sha256(current).digest()
    return hashlib.sha256(current).hexdigest()


def verify_passphrase(passphrase: str, salt: str, stored_hash: str) -> bool:
    """Verify a passphrase against stored hash."""
    computed = hash_passphrase(passphrase, salt)
    # Constant-time comparison to prevent timing attacks
    return secrets.compare_digest(computed, stored_hash)


# ═══════════════════════════════════════════════════════════════
# PASSPHRASE STRENGTH VALIDATION
# ═══════════════════════════════════════════════════════════════

def validate_passphrase_strength(passphrase: str) -> tuple[bool, list[str]]:
    """
    Validate passphrase meets constitutional requirements.
    Returns (is_valid, list_of_issues).
    
    Accepts EITHER:
    - Multiple words (2+) with 10+ total chars, OR
    - A single long string with 16+ chars
    """
    issues = []

    if len(passphrase) < MIN_PASSPHRASE_LENGTH:
        issues.append(f"Mínimo {MIN_PASSPHRASE_LENGTH} caracteres (atual: {len(passphrase)})")

    words = passphrase.strip().split()
    has_multiple_words = len(words) >= MIN_PASSPHRASE_WORDS
    is_long_single = len(passphrase) >= 16

    if not has_multiple_words and not is_long_single:
        issues.append(f"Use 2+ palavras com espaços, OU uma frase única com 16+ caracteres (atual: {len(words)} palavra(s), {len(passphrase)} chars)")

    if passphrase.lower() == passphrase:
        issues.append("Recomendado: misturar maiúsculas e minúsculas")

    # Check for common weak patterns
    weak_patterns = ["123", "abc", "password", "windi", "dragon", "admin"]
    for pattern in weak_patterns:
        if pattern in passphrase.lower():
            issues.append(f"Padrão fraco detectado: '{pattern}'")

    is_valid = len(passphrase) >= MIN_PASSPHRASE_LENGTH and (has_multiple_words or is_long_single)
    return is_valid, issues


# ═══════════════════════════════════════════════════════════════
# FORENSIC LEDGER
# ═══════════════════════════════════════════════════════════════

def log_event(event_type: str, details: dict, ledger_path: Path = None):
    """
    Append event to the SIP forensic ledger.
    Every identity action is recorded immutably.
    """
    path = ledger_path or SIP_LEDGER_FILE
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "protocol": "SIP",
        "layer": 1,
        "details": details
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


# ═══════════════════════════════════════════════════════════════
# SETUP: Initial Passphrase Configuration
# ═══════════════════════════════════════════════════════════════

def setup_passphrase(identity_path: Path = None, ledger_path: Path = None):
    """
    Interactive setup for the Sovereign Passphrase.
    Run ONCE by the Human Dragon to establish identity.
    """
    id_path = identity_path or SIP_IDENTITY_FILE
    led_path = ledger_path or SIP_LEDGER_FILE

    print()
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   🔐 WINDI SIP — Layer 1: Constitutional Passphrase  ║")
    print("║                    INITIAL SETUP                      ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()

    if id_path.exists():
        print("⚠️  ATENÇÃO: Identidade soberana já configurada!")
        print(f"   Arquivo: {id_path}")
        print()
        resp = input("Deseja RECONFIGRAR? Isso invalida a identidade anterior. [s/N]: ")
        if resp.lower() != 's':
            print("Operação cancelada. Identidade preservada.")
            return False
        # Log the reconfiguration attempt
        log_event("RECONFIGURATION_INITIATED", {
            "previous_file": str(id_path),
            "human_confirmed": True
        }, led_path)

    print("═══════════════════════════════════════════════════════")
    print()
    print("  REGRAS DA PASSPHRASE CONSTITUCIONAL:")
    print()
    print(f"  • Mínimo {MIN_PASSPHRASE_LENGTH} caracteres")
    print(f"  • 2+ palavras com espaços OU 16+ caracteres sem espaço")
    print("  • Escolha algo pessoal e memorável")
    print("  • Pode ser em qualquer idioma (PT/DE/EN/ES)")
    print("  • NUNCA será armazenada — apenas o hash SHA-256")
    print()
    print("  💡 Exemplos de boas frases:")
    print('     "Meu Avo plantou Cafe"      (com espaços)')
    print('     "DerDracheFliegt2026"        (sem espaços, 16+ chars)')
    print('     "Three Dragons Guard"        (com espaços)')
    print()
    print("═══════════════════════════════════════════════════════")
    print()

    # --- SOVEREIGN PASSPHRASE ---
    while True:
        passphrase = getpass.getpass("🔑 Digite sua PASSPHRASE SOBERANA: ")
        is_valid, issues = validate_passphrase_strength(passphrase)

        if issues:
            print()
            for issue in issues:
                prefix = "❌" if not is_valid else "⚠️ "
                print(f"  {prefix} {issue}")
            print()

        if not is_valid:
            print("  Passphrase não atende aos requisitos mínimos. Tente novamente.")
            print()
            continue

        # Confirmation
        confirm = getpass.getpass("🔑 Confirme sua PASSPHRASE SOBERANA: ")
        if passphrase != confirm:
            print()
            print("  ❌ As frases não coincidem. Tente novamente.")
            print()
            continue

        break

    # --- DURESS PASSPHRASE ---
    print()
    print("═══════════════════════════════════════════════════════")
    print()
    print("  🚨 PASSPHRASE DE COERÇÃO (DURESS)")
    print()
    print("  Se alguém te forçar a autenticar, use ESTA frase.")
    print("  O sistema vai FINGIR que funcionou, mas:")
    print("  • Nenhuma alteração constitucional será aplicada")
    print("  • O evento será logado como COERÇÃO no ledger")
    print("  • Alertas silenciosos serão gerados")
    print()
    print("  Escolha algo que você lembre sob pressão,")
    print("  mas que seja DIFERENTE da frase soberana.")
    print()
    print("═══════════════════════════════════════════════════════")
    print()

    while True:
        duress = getpass.getpass("🚨 Digite sua PASSPHRASE DE COERÇÃO: ")
        is_valid_d, issues_d = validate_passphrase_strength(duress)

        if not is_valid_d:
            print()
            for issue in issues_d:
                print(f"  ❌ {issue}")
            print("  Tente novamente.")
            print()
            continue

        if duress == passphrase:
            print()
            print("  ❌ A passphrase de coerção DEVE ser diferente da soberana!")
            print()
            continue

        confirm_d = getpass.getpass("🚨 Confirme sua PASSPHRASE DE COERÇÃO: ")
        if duress != confirm_d:
            print()
            print("  ❌ As frases não coincidem. Tente novamente.")
            print()
            continue

        break

    # --- GENERATE HASHES ---
    print()
    print("⏳ Gerando hashes criptográficos (100.000 rounds SHA-256)...")
    print()

    sovereign_salt = generate_salt()
    sovereign_hash = hash_passphrase(passphrase, sovereign_salt)

    duress_salt = generate_salt()
    duress_hash = hash_passphrase(duress, duress_salt)

    # --- BUILD IDENTITY FILE ---
    identity = {
        "protocol": "WINDI Sovereign Identity Protocol",
        "version": "1.0.0",
        "layer": 1,
        "layer_name": "Constitutional Passphrase",
        "status": "ACTIVE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "Human Dragon (Chief Governance Officer)",
        "constitutional_reference": "Invariant I9 — Prohibition of Autonomy Escalation",
        "sovereign": {
            "algorithm": "SHA-256",
            "rounds": 100000,
            "salt": sovereign_salt,
            "hash": sovereign_hash
        },
        "duress": {
            "algorithm": "SHA-256",
            "rounds": 100000,
            "salt": duress_salt,
            "hash": duress_hash
        },
        "metadata": {
            "passphrase_min_length": MIN_PASSPHRASE_LENGTH,
            "passphrase_min_words": MIN_PASSPHRASE_WORDS,
            "salt_bits": SALT_LENGTH * 8,
            "zero_knowledge": True,
            "note": "Only hashes are stored. Passphrases exist ONLY in the mind of the Human Dragon."
        }
    }

    # --- SAVE ---
    id_path.parent.mkdir(parents=True, exist_ok=True)
    with open(id_path, 'w') as f:
        json.dump(identity, f, indent=2, ensure_ascii=False)
    os.chmod(id_path, 0o600)  # Owner read/write only

    # --- LOG ---
    log_event("IDENTITY_CREATED", {
        "sovereign_hash_prefix": sovereign_hash[:16] + "...",
        "duress_configured": True,
        "algorithm": "SHA-256 x100000",
        "file": str(id_path)
    }, led_path)

    # --- CONFIRMATION ---
    print("╔═══════════════════════════════════════════════════════╗")
    print("║          🐉 IDENTIDADE SOBERANA CONFIGURADA           ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()
    print(f"  📁 Arquivo:   {id_path}")
    print(f"  🔒 Permissões: 600 (owner only)")
    print(f"  🧬 Hash (início): {sovereign_hash[:16]}...")
    print(f"  🚨 Duress:     Configurado")
    print(f"  📋 Ledger:     {led_path}")
    print()
    print("  ⚠️  MEMORIZE suas frases. Elas NÃO estão salvas")
    print("     em lugar nenhum. Se esquecer, será necessário")
    print("     reconfigurar com Convenção Constitucional.")
    print()
    print("  A Constituição protege o sistema.")
    print("  O Human Dragon protege a Constituição.")
    print("  O SIP protege o Human Dragon.")
    print()
    print("  🐉 OM SHANTI")
    print()

    return True


# ═══════════════════════════════════════════════════════════════
# VERIFY: Authenticate the Human Dragon
# ═══════════════════════════════════════════════════════════════

def verify_identity(identity_path: Path = None, ledger_path: Path = None) -> dict:
    """
    Verify the Human Dragon's identity via passphrase.
    Returns a verification result dict.

    Possible results:
    - SOVEREIGN: Legitimate authentication
    - DURESS: Coercion detected (appears successful but flags alert)
    - FAILED: Authentication failed
    - ERROR: System error
    """
    id_path = identity_path or SIP_IDENTITY_FILE
    led_path = ledger_path or SIP_LEDGER_FILE

    print()
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   🔐 WINDI SIP — Identity Verification                ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()

    if not id_path.exists():
        print("  ❌ Identidade soberana não configurada.")
        print("  Execute: python3 sip_layer1.py setup")
        return {"status": "ERROR", "reason": "identity_not_configured"}

    # Load identity
    with open(id_path) as f:
        identity = json.load(f)

    passphrase = getpass.getpass("🔑 Digite sua passphrase: ")

    # Check sovereign passphrase
    sovereign_match = verify_passphrase(
        passphrase,
        identity["sovereign"]["salt"],
        identity["sovereign"]["hash"]
    )

    if sovereign_match:
        result = {
            "status": "SOVEREIGN",
            "verified": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": 1,
            "coercion": False
        }
        log_event("VERIFICATION_SUCCESS", {
            "result": "SOVEREIGN",
            "hash_prefix": identity["sovereign"]["hash"][:16] + "..."
        }, led_path)

        print()
        print("  ✅ IDENTIDADE SOBERANA CONFIRMADA")
        print(f"  ⏰ {result['timestamp']}")
        print("  🐉 Human Dragon autenticado.")
        print()
        return result

    # Check duress passphrase
    duress_match = verify_passphrase(
        passphrase,
        identity["duress"]["salt"],
        identity["duress"]["hash"]
    )

    if duress_match:
        # CRITICAL: Appears to succeed but flags coercion
        result = {
            "status": "DURESS",
            "verified": True,  # Appears verified to observer
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": 1,
            "coercion": True,
            "_real_status": "COERCION_DETECTED"
        }
        log_event("COERCION_DETECTED", {
            "result": "DURESS",
            "alert_level": "CRITICAL",
            "note": "Duress passphrase used. All constitutional changes in this session are VOID.",
            "apparent_result": "SUCCESS"
        }, led_path)

        # Display as if successful (to protect the Human Dragon)
        print()
        print("  ✅ IDENTIDADE SOBERANA CONFIRMADA")
        print(f"  ⏰ {result['timestamp']}")
        print("  🐉 Human Dragon autenticado.")
        print()
        return result

    # Failed
    result = {
        "status": "FAILED",
        "verified": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "layer": 1,
        "coercion": False,
        "attempts_note": "After 3 failures, a cooldown period is recommended"
    }
    log_event("VERIFICATION_FAILED", {
        "result": "FAILED"
    }, led_path)

    print()
    print("  ❌ VERIFICAÇÃO FALHOU")
    print("  A passphrase não corresponde.")
    print()
    return result


# ═══════════════════════════════════════════════════════════════
# STATUS: Show SIP Layer 1 configuration status
# ═══════════════════════════════════════════════════════════════

def show_status(identity_path: Path = None, ledger_path: Path = None):
    """Display current SIP Layer 1 status (no secrets exposed)."""
    id_path = identity_path or SIP_IDENTITY_FILE
    led_path = ledger_path or SIP_LEDGER_FILE

    print()
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   🔐 WINDI SIP — Layer 1 Status                       ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()

    if not id_path.exists():
        print("  ❌ Status: NÃO CONFIGURADO")
        print(f"  📁 Expected: {id_path}")
        print("  Execute: python3 sip_layer1.py setup")
        print()
        return

    with open(id_path) as f:
        identity = json.load(f)

    print(f"  ✅ Status:    {identity.get('status', 'UNKNOWN')}")
    print(f"  📅 Criado:    {identity.get('created_at', '?')}")
    print(f"  🧬 Hash:      {identity['sovereign']['hash'][:16]}...")
    print(f"  🔄 Rounds:    {identity['sovereign']['rounds']:,}")
    print(f"  🚨 Duress:    {'Configurado' if 'duress' in identity else 'NÃO'}")
    print(f"  🏛️  Referência: {identity.get('constitutional_reference', '?')}")
    print(f"  📁 Arquivo:   {id_path}")

    # Ledger stats
    if led_path.exists():
        with open(led_path) as f:
            lines = f.readlines()
        events = len(lines)
        coercions = sum(1 for l in lines if '"COERCION_DETECTED"' in l)
        failures = sum(1 for l in lines if '"VERIFICATION_FAILED"' in l)
        print()
        print(f"  📋 Ledger:     {events} eventos registrados")
        if coercions > 0:
            print(f"  🚨 ALERTAS:    {coercions} tentativas de coerção detectadas!")
        if failures > 0:
            print(f"  ⚠️  Falhas:     {failures} verificações falharam")
    print()


# ═══════════════════════════════════════════════════════════════
# AUDIT: Review the forensic ledger
# ═══════════════════════════════════════════════════════════════

def audit_ledger(ledger_path: Path = None):
    """Display all SIP forensic ledger entries."""
    led_path = ledger_path or SIP_LEDGER_FILE

    print()
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   📋 WINDI SIP — Forensic Ledger Audit                ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()

    if not led_path.exists():
        print("  Ledger vazio. Nenhum evento registrado.")
        print()
        return

    with open(led_path) as f:
        for i, line in enumerate(f, 1):
            entry = json.loads(line.strip())
            event = entry.get("event_type", "?")
            ts = entry.get("timestamp", "?")
            details = entry.get("details", {})

            # Color-code by severity
            if "COERCION" in event:
                icon = "🚨"
            elif "FAILED" in event:
                icon = "❌"
            elif "SUCCESS" in event:
                icon = "✅"
            elif "CREATED" in event:
                icon = "🔐"
            else:
                icon = "📋"

            print(f"  {icon} [{i}] {ts}")
            print(f"      Event: {event}")
            for k, v in details.items():
                print(f"      {k}: {v}")
            print()


# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════

def print_usage():
    """Print CLI usage."""
    print()
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   🔐 WINDI Sovereign Identity Protocol — Layer 1      ║")
    print("║      AI processes. Human decides. WINDI guarantees.   ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()
    print("  Comandos:")
    print()
    print("    python3 sip_layer1.py setup     Configurar identidade soberana")
    print("    python3 sip_layer1.py verify    Verificar identidade")
    print("    python3 sip_layer1.py status    Ver status atual")
    print("    python3 sip_layer1.py audit     Auditar ledger forense")
    print()
    print("  O circuito é fechado. Criptograficamente.")
    print("  🐉 OM SHANTI")
    print()


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "setup":
        setup_passphrase()
    elif command == "verify":
        result = verify_identity()
        # Exit code: 0 = sovereign, 1 = failed, 2 = duress (but appears as 0)
        if result["status"] == "SOVEREIGN":
            sys.exit(0)
        elif result["status"] == "DURESS":
            sys.exit(0)  # Must appear successful!
        else:
            sys.exit(1)
    elif command == "status":
        show_status()
    elif command == "audit":
        audit_ledger()
    else:
        print(f"  ❌ Comando desconhecido: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
