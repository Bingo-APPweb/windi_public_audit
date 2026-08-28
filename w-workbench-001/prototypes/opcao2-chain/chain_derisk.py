#!/usr/bin/env python3
"""
OPCAO2-CHAIN-DERISK-20260828 — CAP 1
Protótipo isolado: prova a matemática da cadeia de hashes (Opção 2)

Objetivo: demonstrar que uma cadeia de hashes pode ser construída do lado do
fremder e verificada pela sequência, entregando ao WINDI SÓ impressões digitais
(hashes) + DID + instante — NUNCA o conteúdo.

Convenção de hash: SHA-256 do texto UTF-8 SEM newline (mesma que playground usa).
"""

import hashlib
import json
from datetime import datetime, timezone

# =============================================================================
# HASH FUNCTION — mesma convenção do playground (UTF-8, sem newline)
# =============================================================================

def sha256_text(text: str) -> str:
    """SHA-256 de texto UTF-8, sem newline. Retorna hex lowercase."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def sha256_bytes(data: bytes) -> str:
    """SHA-256 de bytes. Retorna hex lowercase."""
    return hashlib.sha256(data).hexdigest()

# =============================================================================
# CHAIN LOGIC — o coração da Opção 2
# =============================================================================

def build_chain(steps: list[str], did: str) -> dict:
    """
    Constrói a cadeia de hashes a partir de uma lista de passos (conteúdos).

    Retorna:
    - leaves: lista de impressões digitais (SHA-256 de cada passo)
    - chain: lista de links da cadeia (cada um liga ao anterior + leaf)
    - package: o que iria ao WINDI (SÓ hashes + DID + instante, SEM conteúdo)
    """
    # Âncora à identidade: chain_0 = SHA256(DID || "genesis")
    chain_0 = sha256_text(did + "genesis")

    leaves = []
    chain = [chain_0]
    package_entries = []

    for i, content in enumerate(steps):
        # leaf_i = SHA256(conteudo_i) — a "impressão digital" de cada passo
        leaf = sha256_text(content)
        leaves.append(leaf)

        # chain_i = SHA256(chain_{i-1} || leaf_i) — liga ordem + passo anterior
        prev_chain = chain[-1]
        new_chain = sha256_text(prev_chain + leaf)
        chain.append(new_chain)

        # Pacote: só hashes + instante (o instante é simulado para o protótipo)
        timestamp = datetime.now(timezone.utc).isoformat()
        package_entries.append({
            "step": i + 1,
            "leaf": leaf,
            "chain": new_chain,
            "timestamp": timestamp
        })

    package = {
        "did": did,
        "genesis": chain_0,
        "entries": package_entries
    }

    return {
        "leaves": leaves,
        "chain": chain,
        "package": package
    }

# =============================================================================
# VERIFIER — o papel do WINDI (recebe SÓ o pacote, recomputa e verifica)
# =============================================================================

def verify_chain(package: dict) -> tuple[bool, str]:
    """
    Verifica a cadeia a partir do pacote (SÓ hashes + DID + instante).
    Recomputa a cadeia pela ordem e confirma que bate.

    Retorna: (valid, message)
    """
    did = package["did"]
    genesis = package["genesis"]
    entries = package["entries"]

    # Recomputar genesis
    expected_genesis = sha256_text(did + "genesis")
    if genesis != expected_genesis:
        return False, f"Genesis mismatch: expected {expected_genesis}, got {genesis}"

    # Recomputar a cadeia passo a passo
    prev_chain = genesis
    for entry in entries:
        step = entry["step"]
        leaf = entry["leaf"]
        expected_chain = entry["chain"]

        # Recomputar chain_i = SHA256(chain_{i-1} || leaf_i)
        computed_chain = sha256_text(prev_chain + leaf)

        if computed_chain != expected_chain:
            return False, f"Chain mismatch at step {step}: expected {expected_chain}, computed {computed_chain}"

        prev_chain = computed_chain

    return True, "Sequência íntegra — cadeia verificada"

# =============================================================================
# TRÊS PROVAS
# =============================================================================

def run_proofs():
    """Executa as três provas observáveis."""

    # Dados de exemplo: 3 passos de uma conversa
    DID = "did:windi:test-fremder-001"
    STEPS = [
        "Ola como podes me ajudar com minhas ideias??",
        "Quero criar uma aplicação para rastrear gastos.",
        "Aqui está o resultado final: app de gastos com dashboard."
    ]

    print("=" * 70)
    print("OPCAO2-CHAIN-DERISK-20260828 — CAP 1 · Protótipo Isolado")
    print("=" * 70)
    print()
    print(f"DID: {DID}")
    print(f"Passos de exemplo: {len(STEPS)}")
    print()

    # =========================================================================
    # PROVA (a) — POSITIVA: cadeia recomputada bate
    # =========================================================================
    print("-" * 70)
    print("PROVA (a) — POSITIVA: construir e verificar cadeia íntegra")
    print("-" * 70)
    print()

    result = build_chain(STEPS, DID)
    leaves = result["leaves"]
    chain = result["chain"]
    package = result["package"]

    print("Leaves (impressões digitais de cada passo):")
    for i, leaf in enumerate(leaves):
        print(f"  leaf_{i+1}: {leaf}")
    print()

    print("Chain (links da cadeia):")
    for i, c in enumerate(chain):
        label = "genesis" if i == 0 else f"chain_{i}"
        print(f"  {label}: {c}")
    print()

    print("Pacote que iria ao WINDI (SÓ hashes + DID + instante):")
    print(json.dumps(package, indent=2))
    print()

    valid, msg = verify_chain(package)
    print(f"Verificação: {'PASS' if valid else 'FAIL'} — {msg}")
    print()

    # =========================================================================
    # PROVA (b) — TAMPER: reordenar OU editar um passo -> falha
    # =========================================================================
    print("-" * 70)
    print("PROVA (b) — TAMPER: adulteração detectada")
    print("-" * 70)
    print()

    # Teste 1: Reordenar passos 2 e 3
    print("Teste b.1: Reordenar passos 2 e 3 no pacote")
    tampered_package_1 = {
        "did": package["did"],
        "genesis": package["genesis"],
        "entries": [
            package["entries"][0],
            package["entries"][2],  # passo 3 no lugar do 2
            package["entries"][1],  # passo 2 no lugar do 3
        ]
    }
    valid_1, msg_1 = verify_chain(tampered_package_1)
    print(f"  Verificação: {'PASS' if valid_1 else 'FAIL'} — {msg_1}")
    print()

    # Teste 2: Editar o leaf de um passo (simular conteúdo alterado)
    print("Teste b.2: Editar o leaf do passo 2 (simular conteúdo alterado)")
    tampered_package_2 = {
        "did": package["did"],
        "genesis": package["genesis"],
        "entries": [
            package["entries"][0],
            {
                "step": 2,
                "leaf": sha256_text("Conteúdo falso que não foi dito"),  # leaf diferente
                "chain": package["entries"][1]["chain"],  # chain original (vai falhar)
                "timestamp": package["entries"][1]["timestamp"]
            },
            package["entries"][2],
        ]
    }
    valid_2, msg_2 = verify_chain(tampered_package_2)
    print(f"  Verificação: {'PASS' if valid_2 else 'FAIL'} — {msg_2}")
    print()

    # =========================================================================
    # PROVA (c) — FRONTEIRA: zero conteúdo no pacote
    # =========================================================================
    print("-" * 70)
    print("PROVA (c) — FRONTEIRA: o pacote não contém conteúdo")
    print("-" * 70)
    print()

    package_str = json.dumps(package)
    content_found = []
    for step in STEPS:
        if step in package_str:
            content_found.append(step)

    print(f"Conteúdos de exemplo:")
    for i, step in enumerate(STEPS):
        print(f"  Passo {i+1}: \"{step[:50]}...\"")
    print()

    print(f"Grep dos conteúdos no pacote: {len(content_found)} hits")
    if content_found:
        print(f"  ALERTA: Conteúdo encontrado no pacote!")
        for c in content_found:
            print(f"    - \"{c[:50]}...\"")
    else:
        print("  PASS — Zero conteúdo no pacote. Só hashes atravessam.")
    print()

    # =========================================================================
    # RESUMO
    # =========================================================================
    print("=" * 70)
    print("RESUMO DAS TRÊS PROVAS")
    print("=" * 70)
    print()
    print(f"(a) POSITIVA — cadeia íntegra:      {'PASS' if valid else 'FAIL'}")
    print(f"(b.1) TAMPER — reordenar:           {'PASS (detectou)' if not valid_1 else 'FAIL'}")
    print(f"(b.2) TAMPER — editar leaf:         {'PASS (detectou)' if not valid_2 else 'FAIL'}")
    print(f"(c) FRONTEIRA — zero conteúdo:      {'PASS' if len(content_found) == 0 else 'FAIL'}")
    print()

    all_pass = valid and not valid_1 and not valid_2 and len(content_found) == 0
    print(f"VEREDICTO GLOBAL: {'PASS — Matemática da Opção 2 de-riscada' if all_pass else 'FAIL'}")
    print()

if __name__ == "__main__":
    run_proofs()
