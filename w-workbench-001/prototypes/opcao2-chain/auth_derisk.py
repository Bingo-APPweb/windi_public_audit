#!/usr/bin/env python3
"""
OPCAO2-AUTH-DERISK-20260828 — CAP 2
Protótipo isolado: prova a autenticação do carimbo (a cura do C0)

Objetivo: demonstrar que um carimbo sobre a cadeia do CAP 1 pode ser ligado ao
DID do fremder de forma NÃO FORJÁVEL — e que um pacote sem prova de posse do
DID é RECUSADO ou gravado como "caller_initiated", NUNCA "human_approved=True".

Esquema de assinatura: Ed25519 (mesmo que W-DID-001 usa — Ed25519VerificationKey2020).
Chaves: de TESTE, geradas aqui — nunca usar chaves reais do Berçário.
"""

import hashlib
import json
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

# =============================================================================
# HASH FUNCTION — mesma convenção do CAP 1
# =============================================================================

def sha256_text(text: str) -> str:
    """SHA-256 de texto UTF-8, sem newline. Retorna hex lowercase."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

# =============================================================================
# CHAIN LOGIC — reutilizada do CAP 1
# =============================================================================

def build_chain(steps: list[str], did: str) -> dict:
    """Constrói a cadeia de hashes (do CAP 1)."""
    chain_0 = sha256_text(did + "genesis")
    leaves = []
    chain = [chain_0]
    package_entries = []

    for i, content in enumerate(steps):
        leaf = sha256_text(content)
        leaves.append(leaf)
        prev_chain = chain[-1]
        new_chain = sha256_text(prev_chain + leaf)
        chain.append(new_chain)
        timestamp = datetime.now(timezone.utc).isoformat()
        package_entries.append({
            "step": i + 1,
            "leaf": leaf,
            "chain": new_chain,
            "timestamp": timestamp
        })

    return {
        "leaves": leaves,
        "chain": chain,
        "entries": package_entries
    }

# =============================================================================
# KEY MANAGEMENT — chaves de TESTE (Ed25519)
# =============================================================================

def generate_test_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey, str, str]:
    """
    Gera um par de chaves Ed25519 de TESTE.
    Retorna: (private_key, public_key, private_hex, public_hex)
    """
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Serializar para hex (para o output)
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    return private_key, public_key, private_bytes.hex(), public_bytes.hex()

def load_public_key_from_hex(hex_key: str) -> Ed25519PublicKey:
    """Carrega uma chave pública Ed25519 a partir de hex."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    return Ed25519PublicKey.from_public_bytes(bytes.fromhex(hex_key))

# =============================================================================
# SIGNATURE — o motor assina a cabeça da cadeia
# =============================================================================

def sign_chain_head(chain_head: str, private_key: Ed25519PrivateKey) -> str:
    """
    Assina a cabeça da cadeia (chain_N) com a chave privada do DID.
    Retorna: assinatura em hex.
    """
    message = chain_head.encode('utf-8')
    signature = private_key.sign(message)
    return signature.hex()

def verify_signature(chain_head: str, signature_hex: str, public_key: Ed25519PublicKey) -> bool:
    """
    Verifica a assinatura de chain_N contra a chave pública do DID.
    Retorna: True se válida, False se inválida.
    """
    try:
        message = chain_head.encode('utf-8')
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, message)
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False

# =============================================================================
# PACKAGE — o que vai ao WINDI (cadeia + DID + assinatura, SEM conteúdo)
# =============================================================================

def build_signed_package(chain_result: dict, did: str, signature: str) -> dict:
    """Constrói o pacote assinado que iria ao WINDI."""
    return {
        "did": did,
        "genesis": chain_result["chain"][0],
        "chain_head": chain_result["chain"][-1],
        "entries": chain_result["entries"],
        "signature": signature
    }

def build_unsigned_package(chain_result: dict, did: str) -> dict:
    """Constrói um pacote SEM assinatura (para testar caller_initiated)."""
    return {
        "did": did,
        "genesis": chain_result["chain"][0],
        "chain_head": chain_result["chain"][-1],
        "entries": chain_result["entries"],
        "signature": None  # Sem assinatura
    }

# =============================================================================
# VERIFIER — o papel do WINDI
# =============================================================================

def verify_and_record(package: dict, public_key: Ed25519PublicKey, policy: str = "require_signature") -> dict:
    """
    Verifica o pacote e grava o registo com semântica HONESTA.

    policy:
    - "require_signature": recusa pacotes sem assinatura (default)
    - "allow_unsigned": aceita pacotes sem assinatura como "caller_initiated"

    Retorna: { accepted, record_field, reason }

    A CURA DO C0: NUNCA grava "human_approved=True" — grava o facto REAL:
    - "signed_by_did_holder" se assinatura válida
    - "caller_initiated" se sem assinatura (e policy permite)
    - RECUSADO se assinatura inválida
    """
    chain_head = package["chain_head"]
    signature = package.get("signature")

    # Caso 1: Sem assinatura
    if signature is None:
        if policy == "require_signature":
            return {
                "accepted": False,
                "record_field": None,
                "reason": "Assinatura ausente — pacote RECUSADO (policy: require_signature)"
            }
        else:  # allow_unsigned
            return {
                "accepted": True,
                "record_field": "caller_initiated",  # NUNCA human_approved=True
                "reason": "Sem assinatura — gravado como caller_initiated (não como human_approved)"
            }

    # Caso 2: Com assinatura — verificar
    is_valid = verify_signature(chain_head, signature, public_key)

    if is_valid:
        return {
            "accepted": True,
            "record_field": "signed_by_did_holder",  # Gesto verificável
            "reason": "Assinatura válida — gravado como signed_by_did_holder"
        }
    else:
        return {
            "accepted": False,
            "record_field": None,
            "reason": "Assinatura INVÁLIDA — pacote RECUSADO"
        }

# =============================================================================
# TRÊS PROVAS
# =============================================================================

def run_proofs():
    """Executa as três provas observáveis."""

    # Dados de exemplo (mesmos do CAP 1)
    DID = "did:windi:test-fremder-001"
    STEPS = [
        "Ola como podes me ajudar com minhas ideias??",
        "Quero criar uma aplicação para rastrear gastos.",
        "Aqui está o resultado final: app de gastos com dashboard."
    ]

    print("=" * 70)
    print("OPCAO2-AUTH-DERISK-20260828 — CAP 2 · Protótipo Isolado")
    print("Esquema de assinatura: Ed25519 (Ed25519VerificationKey2020)")
    print("=" * 70)
    print()

    # Gerar chaves de TESTE
    priv_key, pub_key, priv_hex, pub_hex = generate_test_keypair()
    priv_key_2, pub_key_2, _, pub_hex_2 = generate_test_keypair()  # Outra chave para testes de forja

    print("Chaves de TESTE (Ed25519):")
    print(f"  DID: {DID}")
    print(f"  Chave pública (hex): {pub_hex}")
    print(f"  (Chave privada de teste — NUNCA partilhar em produção)")
    print()

    # Construir a cadeia (reutilizando CAP 1)
    chain_result = build_chain(STEPS, DID)
    chain_head = chain_result["chain"][-1]
    print(f"Chain head (chain_3): {chain_head}")
    print()

    # =========================================================================
    # PROVA (a) — POSITIVA: assinatura válida
    # =========================================================================
    print("-" * 70)
    print("PROVA (a) — POSITIVA: assinatura válida do DID")
    print("-" * 70)
    print()

    signature = sign_chain_head(chain_head, priv_key)
    print(f"Assinatura (hex): {signature}")
    print()

    package_signed = build_signed_package(chain_result, DID, signature)
    result_a = verify_and_record(package_signed, pub_key)

    print(f"Verificação: {'PASS' if result_a['accepted'] else 'FAIL'}")
    print(f"Campo de registo: {result_a['record_field']}")
    print(f"Razão: {result_a['reason']}")
    print()

    # =========================================================================
    # PROVA (b) — FORJA: 3 sub-casos
    # =========================================================================
    print("-" * 70)
    print("PROVA (b) — FORJA: adulteração detectada (3 sub-casos)")
    print("-" * 70)
    print()

    # Sub-caso b.1: Alterar chain_head
    print("Teste b.1: Alterar chain_head (simular cadeia adulterada)")
    tampered_chain_head = sha256_text("valor_adulterado")
    package_b1 = {**package_signed, "chain_head": tampered_chain_head}
    result_b1 = verify_and_record(package_b1, pub_key)
    print(f"  Verificação: {'PASS' if result_b1['accepted'] else 'FAIL (detectou)'}")
    print(f"  Razão: {result_b1['reason']}")
    print()

    # Sub-caso b.2: Assinar com outra chave
    print("Teste b.2: Assinar com outra chave (impostor)")
    signature_wrong_key = sign_chain_head(chain_head, priv_key_2)
    package_b2 = {**package_signed, "signature": signature_wrong_key}
    result_b2 = verify_and_record(package_b2, pub_key)  # Verifica com a chave original
    print(f"  Verificação: {'PASS' if result_b2['accepted'] else 'FAIL (detectou)'}")
    print(f"  Razão: {result_b2['reason']}")
    print()

    # Sub-caso b.3: Remover assinatura (com policy require_signature)
    print("Teste b.3: Remover assinatura (policy: require_signature)")
    package_b3 = build_unsigned_package(chain_result, DID)
    result_b3 = verify_and_record(package_b3, pub_key, policy="require_signature")
    print(f"  Verificação: {'PASS' if result_b3['accepted'] else 'FAIL (recusou)'}")
    print(f"  Razão: {result_b3['reason']}")
    print()

    # =========================================================================
    # PROVA (c) — HONESTIDADE: campo de registo nos dois casos
    # =========================================================================
    print("-" * 70)
    print("PROVA (c) — HONESTIDADE: campo de registo NUNCA mente")
    print("-" * 70)
    print()

    print("Caso c.1: Pacote COM assinatura válida")
    print(f"  Campo gravado: {result_a['record_field']}")
    print(f"  human_approved=True forjado? {'SIM (BUG!)' if result_a['record_field'] == 'human_approved' else 'NÃO (correcto)'}")
    print()

    print("Caso c.2: Pacote SEM assinatura (policy: allow_unsigned)")
    result_c2 = verify_and_record(package_b3, pub_key, policy="allow_unsigned")
    print(f"  Aceite: {result_c2['accepted']}")
    print(f"  Campo gravado: {result_c2['record_field']}")
    print(f"  human_approved=True forjado? {'SIM (BUG!)' if result_c2['record_field'] == 'human_approved' else 'NÃO (correcto)'}")
    print(f"  Razão: {result_c2['reason']}")
    print()

    # =========================================================================
    # VETOR DE EXEMPLO (para verificação independente do observador)
    # =========================================================================
    print("-" * 70)
    print("VETOR DE EXEMPLO (para verificação independente)")
    print("-" * 70)
    print()
    print(f"chain_head: {chain_head}")
    print(f"public_key (hex): {pub_hex}")
    print(f"signature (hex): {signature}")
    print()
    print("Para verificar: Ed25519.verify(signature, chain_head.encode('utf-8'), public_key)")
    print()

    # =========================================================================
    # RESUMO
    # =========================================================================
    print("=" * 70)
    print("RESUMO DAS TRÊS PROVAS")
    print("=" * 70)
    print()
    print(f"(a) POSITIVA — assinatura válida:       {'PASS' if result_a['accepted'] else 'FAIL'}")
    print(f"(b.1) FORJA — chain adulterada:         {'PASS (detectou)' if not result_b1['accepted'] else 'FAIL'}")
    print(f"(b.2) FORJA — chave errada:             {'PASS (detectou)' if not result_b2['accepted'] else 'FAIL'}")
    print(f"(b.3) FORJA — sem assinatura:           {'PASS (recusou)' if not result_b3['accepted'] else 'FAIL'}")
    print(f"(c.1) HONESTIDADE — com assinatura:     {'PASS' if result_a['record_field'] == 'signed_by_did_holder' else 'FAIL'}")
    print(f"(c.2) HONESTIDADE — sem assinatura:     {'PASS' if result_c2['record_field'] == 'caller_initiated' else 'FAIL'}")
    print()

    all_pass = (
        result_a['accepted'] and
        not result_b1['accepted'] and
        not result_b2['accepted'] and
        not result_b3['accepted'] and
        result_a['record_field'] == 'signed_by_did_holder' and
        result_c2['record_field'] == 'caller_initiated'
    )
    print(f"VEREDICTO GLOBAL: {'PASS — Autenticação do carimbo de-riscada (cura C0 provada)' if all_pass else 'FAIL'}")
    print()

if __name__ == "__main__":
    run_proofs()
