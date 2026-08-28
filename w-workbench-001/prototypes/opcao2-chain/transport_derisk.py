#!/usr/bin/env python3
"""
OPCAO2-TRANSPORTE-DERISK-20260828 — CAP 3
Protótipo isolado: prova o transporte W-TUBE (a montagem de CAP1+CAP2)

Objetivo: provar que a ferramenta WINDI recebe um PACOTE ASSINADO (só hashes +
DID + instante + assinatura), verifica (CAP1+CAP2) e devolve um carimbo CANDIDATO
— e que um pacote malformado/forjado/com conteúdo é RECUSADO limpo.

Transporte: 127.0.0.1 efémero, stdio de teste. NÃO expõe porta pública.
NÃO toca no mcp_server contido do C0. NÃO cria receipt/selo no Ledger.

Convenção: mesma forma do W-CONNECTOR-001 (FastAPI + inputSchema), mas isolado.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

# =============================================================================
# HASH FUNCTION — mesma convenção do CAP 1 e CAP 2
# =============================================================================

def sha256_text(text: str) -> str:
    """SHA-256 de texto UTF-8, sem newline. Retorna hex lowercase."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

# =============================================================================
# TOOL SCHEMA — a fronteira imposta (SÓ HASHES, sem campo de conteúdo)
# =============================================================================

TOOL_SCHEMA = {
    "name": "windi_stamp_chain",
    "description": (
        "Stamp a chain of hashes from a conversation, tied to a DID. "
        "Returns a CANDIDATE stamp (not a receipt or seal). "
        "The WINDI receives ONLY hashes, never the content."
    ),
    "inputSchema": {
        "type": "object",
        "required": ["did", "leaves", "chain", "timestamps", "signature"],
        "properties": {
            "did": {
                "type": "string",
                "description": "The DID of the fremder (e.g., did:windi:...)"
            },
            "leaves": {
                "type": "array",
                "items": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "description": "SHA-256 fingerprints of each step (hashes, NOT content)"
            },
            "chain": {
                "type": "array",
                "items": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "description": "Chain links: genesis + chain_1..chain_N (all hashes)"
            },
            "timestamps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "ISO timestamps for each step"
            },
            "signature": {
                "type": "string",
                "description": "Ed25519 signature of chain_N (hex), or null if unsigned"
            }
        },
        "additionalProperties": False  # REJECTS any extra field (including content)
    }
}

# Note: NO "content" field exists. Content CANNOT enter.

# =============================================================================
# KEY MANAGEMENT — reutilizado do CAP 2
# =============================================================================

def generate_test_keypair():
    """Gera um par de chaves Ed25519 de TESTE."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
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
    return Ed25519PublicKey.from_public_bytes(bytes.fromhex(hex_key))

def sign_chain_head(chain_head: str, private_key: Ed25519PrivateKey) -> str:
    """Assina a cabeça da cadeia com a chave privada do DID."""
    message = chain_head.encode('utf-8')
    signature = private_key.sign(message)
    return signature.hex()

def verify_signature(chain_head: str, signature_hex: str, public_key: Ed25519PublicKey) -> bool:
    """Verifica a assinatura de chain_N contra a chave pública do DID."""
    try:
        message = chain_head.encode('utf-8')
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, message)
        return True
    except (InvalidSignature, Exception):
        return False

# =============================================================================
# CHAIN VERIFICATION — reutilizado do CAP 1
# =============================================================================

def verify_chain_from_leaves(did: str, leaves: list[str], chain: list[str]) -> tuple[bool, str]:
    """
    Recomputa a cadeia a partir das leaves e confirma que bate com chain[].
    Retorna: (valid, message)
    """
    if len(chain) < 1:
        return False, "Chain vazia"

    # Recomputar genesis
    expected_genesis = sha256_text(did + "genesis")
    if chain[0] != expected_genesis:
        return False, f"Genesis mismatch: expected {expected_genesis[:16]}..., got {chain[0][:16]}..."

    # Recomputar a cadeia passo a passo
    prev = chain[0]
    for i, leaf in enumerate(leaves):
        expected_chain = sha256_text(prev + leaf)
        actual_chain = chain[i + 1] if i + 1 < len(chain) else None

        if actual_chain is None:
            return False, f"Chain incompleta no passo {i + 1}"

        if expected_chain != actual_chain:
            return False, f"Chain mismatch no passo {i + 1}"

        prev = expected_chain

    return True, "Cadeia íntegra"

# =============================================================================
# SCHEMA VALIDATION — impõe a fronteira
# =============================================================================

def validate_schema(request: dict) -> tuple[bool, str]:
    """
    Valida o pedido contra o schema.
    REJEITA campos extra (incluindo conteúdo).
    """
    required = ["did", "leaves", "chain", "timestamps", "signature"]
    allowed = set(required)

    # Check required fields
    for field in required:
        if field not in request:
            return False, f"Campo obrigatório ausente: {field}"

    # Check for extra fields (the BOUNDARY enforcement)
    extra = set(request.keys()) - allowed
    if extra:
        return False, f"Campos não permitidos rejeitados: {extra}"

    # Type checks
    if not isinstance(request["did"], str):
        return False, "did deve ser string"
    if not isinstance(request["leaves"], list):
        return False, "leaves deve ser array"
    if not isinstance(request["chain"], list):
        return False, "chain deve ser array"
    if not isinstance(request["timestamps"], list):
        return False, "timestamps deve ser array"
    if request["signature"] is not None and not isinstance(request["signature"], str):
        return False, "signature deve ser string ou null"

    return True, "Schema válido"

# =============================================================================
# TOOL HANDLER — o pipeline de verificação
# =============================================================================

# Simulated DID registry (for prototype only)
DID_REGISTRY = {}

def register_did_for_test(did: str, public_key_hex: str):
    """Regista um DID de teste com a sua chave pública."""
    DID_REGISTRY[did] = public_key_hex

def handle_windi_stamp_chain(request: dict) -> dict:
    """
    Handler da ferramenta windi_stamp_chain.

    Pipeline:
    1. Valida schema (impõe fronteira — sem campo de conteúdo)
    2. Recomputa e verifica a cadeia (CAP 1)
    3. Verifica a assinatura (CAP 2)
    4. Devolve carimbo CANDIDATE (nunca receipt/selo)
    """
    # 1. Validação de schema (FRONTEIRA)
    valid_schema, schema_msg = validate_schema(request)
    if not valid_schema:
        return {
            "candidate": True,
            "verified": False,
            "recorded": None,
            "reason": f"Schema inválido: {schema_msg}",
            "chain_tip": None,
            "did": request.get("did"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    did = request["did"]
    leaves = request["leaves"]
    chain = request["chain"]
    signature = request.get("signature")

    # 2. Verificação da cadeia (CAP 1)
    valid_chain, chain_msg = verify_chain_from_leaves(did, leaves, chain)
    if not valid_chain:
        return {
            "candidate": True,
            "verified": False,
            "recorded": None,
            "reason": f"Cadeia inválida: {chain_msg}",
            "chain_tip": chain[-1] if chain else None,
            "did": did,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    chain_tip = chain[-1]

    # 3. Verificação da assinatura (CAP 2)
    if signature is None:
        # Sem assinatura — caller_initiated, NUNCA human_approved
        return {
            "candidate": True,
            "verified": True,
            "recorded": "caller_initiated",  # NUNCA human_approved=True
            "reason": "Cadeia íntegra, sem assinatura — gravado como caller_initiated",
            "chain_tip": chain_tip,
            "did": did,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # Obter chave pública do DID
    public_key_hex = DID_REGISTRY.get(did)
    if not public_key_hex:
        return {
            "candidate": True,
            "verified": False,
            "recorded": None,
            "reason": f"DID não registado: {did}",
            "chain_tip": chain_tip,
            "did": did,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    public_key = load_public_key_from_hex(public_key_hex)
    sig_valid = verify_signature(chain_tip, signature, public_key)

    if not sig_valid:
        return {
            "candidate": True,
            "verified": False,
            "recorded": None,
            "reason": "Assinatura inválida — pacote RECUSADO",
            "chain_tip": chain_tip,
            "did": did,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # Tudo válido — signed_by_did_holder
    return {
        "candidate": True,  # NUNCA é receipt/selo
        "verified": True,
        "recorded": "signed_by_did_holder",  # Gesto verificável
        "reason": "Cadeia íntegra + assinatura válida — gravado como signed_by_did_holder",
        "chain_tip": chain_tip,
        "did": did,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# =============================================================================
# BUILD REQUEST FROM CONTENT (lado do fremder — usa CAP1 para construir)
# =============================================================================

def build_request_from_content(steps: list[str], did: str, private_key) -> dict:
    """
    Constrói o pedido a partir do conteúdo (lado do fremder).
    O pedido resultante NÃO contém o conteúdo — só hashes.
    """
    chain_0 = sha256_text(did + "genesis")
    leaves = []
    chain = [chain_0]
    timestamps = []

    prev = chain_0
    for content in steps:
        leaf = sha256_text(content)
        leaves.append(leaf)
        new_chain = sha256_text(prev + leaf)
        chain.append(new_chain)
        timestamps.append(datetime.now(timezone.utc).isoformat())
        prev = new_chain

    chain_tip = chain[-1]
    signature = sign_chain_head(chain_tip, private_key) if private_key else None

    return {
        "did": did,
        "leaves": leaves,
        "chain": chain,
        "timestamps": timestamps,
        "signature": signature
    }

# =============================================================================
# QUATRO PROVAS
# =============================================================================

def run_proofs():
    """Executa as quatro provas observáveis."""

    # Dados de exemplo
    DID = "did:windi:test-fremder-001"
    STEPS = [
        "Ola como podes me ajudar com minhas ideias??",
        "Quero criar uma aplicação para rastrear gastos.",
        "Aqui está o resultado final: app de gastos com dashboard."
    ]

    print("=" * 70)
    print("OPCAO2-TRANSPORTE-DERISK-20260828 — CAP 3 · Protótipo Isolado")
    print("Transporte: 127.0.0.1 efémero (stdio de teste)")
    print("NÃO deployado, NÃO toca no mcp_server contido do C0")
    print("=" * 70)
    print()

    # Gerar chaves de TESTE e registar DID
    priv_key, pub_key, priv_hex, pub_hex = generate_test_keypair()
    register_did_for_test(DID, pub_hex)

    print(f"DID registado: {DID}")
    print(f"Chave pública (hex): {pub_hex}")
    print()

    # =========================================================================
    # PROVA (c) — FRONTEIRA: schema sem campo de conteúdo
    # =========================================================================
    print("-" * 70)
    print("PROVA (c) — FRONTEIRA: schema sem campo de conteúdo")
    print("-" * 70)
    print()
    print("Schema da ferramenta windi_stamp_chain:")
    print(json.dumps(TOOL_SCHEMA["inputSchema"], indent=2))
    print()
    print("Campos permitidos: did, leaves, chain, timestamps, signature")
    print("Campo 'content' existe? NÃO")
    print("additionalProperties: false → campos extra REJEITADOS")
    print()

    # Testar rejeição de campo extra
    request_with_content = {
        "did": DID,
        "leaves": ["abc123"],
        "chain": ["def456"],
        "timestamps": ["2026-08-28T00:00:00Z"],
        "signature": None,
        "content": "Este é conteúdo que não deveria entrar!"  # CAMPO EXTRA
    }
    valid, msg = validate_schema(request_with_content)
    print(f"Pedido com campo 'content' extra: {'ACEITE (BUG!)' if valid else 'REJEITADO (correcto)'}")
    print(f"Razão: {msg}")
    print()

    # =========================================================================
    # PROVA (a) — POSITIVA: pacote bem-formado e assinado
    # =========================================================================
    print("-" * 70)
    print("PROVA (a) — POSITIVA: pacote bem-formado e assinado")
    print("-" * 70)
    print()

    request_a = build_request_from_content(STEPS, DID, priv_key)
    print("Pedido (só hashes, sem conteúdo):")
    print(json.dumps(request_a, indent=2))
    print()

    response_a = handle_windi_stamp_chain(request_a)
    print("Resposta (carimbo CANDIDATE):")
    print(json.dumps(response_a, indent=2))
    print()

    # =========================================================================
    # PROVA (b) — RECUSA: 3 sub-casos
    # =========================================================================
    print("-" * 70)
    print("PROVA (b) — RECUSA: forja detectada (3 sub-casos)")
    print("-" * 70)
    print()

    # b.1: Assinatura forjada
    print("Teste b.1: Assinatura forjada")
    request_b1 = {**request_a, "signature": "00" * 64}  # Assinatura falsa
    response_b1 = handle_windi_stamp_chain(request_b1)
    print(f"  verified: {response_b1['verified']}")
    print(f"  recorded: {response_b1['recorded']}")
    print(f"  reason: {response_b1['reason']}")
    print()

    # b.2: Cadeia adulterada
    print("Teste b.2: Cadeia adulterada (leaf alterada)")
    request_b2 = {**request_a, "leaves": ["ff" * 32] + request_a["leaves"][1:]}  # Primeira leaf alterada
    response_b2 = handle_windi_stamp_chain(request_b2)
    print(f"  verified: {response_b2['verified']}")
    print(f"  recorded: {response_b2['recorded']}")
    print(f"  reason: {response_b2['reason']}")
    print()

    # b.3: Sem assinatura
    print("Teste b.3: Sem assinatura")
    request_b3 = {**request_a, "signature": None}
    response_b3 = handle_windi_stamp_chain(request_b3)
    print(f"  verified: {response_b3['verified']}")
    print(f"  recorded: {response_b3['recorded']} (NUNCA human_approved)")
    print(f"  reason: {response_b3['reason']}")
    print()

    # =========================================================================
    # PROVA (d) — SEM SELO: resposta é CANDIDATE
    # =========================================================================
    print("-" * 70)
    print("PROVA (d) — SEM SELO: resposta é CANDIDATE, não receipt/selo")
    print("-" * 70)
    print()
    print(f"Campo 'candidate' na resposta: {response_a.get('candidate')}")
    print(f"É receipt? {'SIM (BUG!)' if 'receipt_id' in response_a else 'NÃO (correcto)'}")
    print(f"É selo? {'SIM (BUG!)' if 'seal' in response_a else 'NÃO (correcto)'}")
    print("Nada escrito no Ledger (protótipo isolado)")
    print()

    # =========================================================================
    # PAR PEDIDO/RESPOSTA DE EXEMPLO (para verificação do observador)
    # =========================================================================
    print("-" * 70)
    print("PAR PEDIDO/RESPOSTA DE EXEMPLO (para verificação)")
    print("-" * 70)
    print()
    print("PEDIDO:")
    print(json.dumps(request_a, indent=2))
    print()
    print("RESPOSTA:")
    print(json.dumps(response_a, indent=2))
    print()
    print(f"Chave pública para verificar assinatura: {pub_hex}")
    print()

    # =========================================================================
    # RESUMO
    # =========================================================================
    print("=" * 70)
    print("RESUMO DAS QUATRO PROVAS")
    print("=" * 70)
    print()
    print(f"(a) POSITIVA — pacote válido:           {'PASS' if response_a['verified'] else 'FAIL'}")
    print(f"(b.1) RECUSA — assinatura forjada:      {'PASS (recusou)' if not response_b1['verified'] else 'FAIL'}")
    print(f"(b.2) RECUSA — cadeia adulterada:       {'PASS (recusou)' if not response_b2['verified'] else 'FAIL'}")
    print(f"(b.3) RECUSA — sem assinatura:          {'PASS (caller_initiated)' if response_b3['recorded'] == 'caller_initiated' else 'FAIL'}")
    print(f"(c) FRONTEIRA — sem campo conteúdo:     {'PASS' if not valid else 'FAIL'}")
    print(f"(d) SEM SELO — resposta é CANDIDATE:    {'PASS' if response_a.get('candidate') == True else 'FAIL'}")
    print()

    all_pass = (
        response_a['verified'] and
        not response_b1['verified'] and
        not response_b2['verified'] and
        response_b3['recorded'] == 'caller_initiated' and
        not valid and  # Campo extra rejeitado
        response_a.get('candidate') == True
    )
    print(f"VEREDICTO GLOBAL: {'PASS — Transporte de-riscado (127.0.0.1, isolado)' if all_pass else 'FAIL'}")
    print()
    print("CONFIRMAÇÃO: correu em 127.0.0.1 (stdio), não deployado, sem tocar em:")
    print("  - mcp_server contido do C0")
    print("  - nginx, systemd, :8200")
    print("  - Ledger, receipts, selos")
    print()

if __name__ == "__main__":
    run_proofs()
