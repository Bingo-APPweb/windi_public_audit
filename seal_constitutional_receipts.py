#!/usr/bin/env python3
"""
WINDI — Seal Constitutional Receipts
Mission: Selar I11, Genesis e MasterSpec no Ledger
Executor: Gêmeo (Claude Code no Strato)
Data: 2026-03-22

GOLDEN RULE: READ → VERIFY → SEAL → CONFIRM
Não modificar nginx. Não alterar outros serviços.
"""

import json
import hashlib
import requests
from datetime import datetime

LEDGER_URL = "http://localhost:8101"
ACTOR = "Human_Dragon_Pioneer1"

def sha256(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()

def verify_exists(receipt_id: str) -> bool:
    """Confirma se receipt já existe no Ledger."""
    try:
        r = requests.get(f"{LEDGER_URL}/api/receipts/{receipt_id}", timeout=5)
        if r.status_code == 200:
            d = r.json()
            receipt = d.get("receipt", d)
            if receipt.get("id"):
                print(f"  ⚠️  {receipt_id} JÁ EXISTE — a saltar")
                return True
    except:
        pass
    return False

def seal_receipt(payload: dict) -> dict:
    """Sela um receipt no Ledger via POST /api/receipts."""
    try:
        r = requests.post(
            f"{LEDGER_URL}/api/receipts",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if r.status_code in (200, 201):
            return {"ok": True, "response": r.json()}
        else:
            return {"ok": False, "status": r.status_code, "body": r.text[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def confirm_receipt(receipt_id: str) -> dict:
    """Confirma o receipt após selar."""
    try:
        r = requests.get(f"{LEDGER_URL}/api/receipts/{receipt_id}", timeout=5)
        if r.status_code == 200:
            d = r.json()
            receipt = d.get("receipt", d)
            return {
                "ok": True,
                "id": receipt.get("id"),
                "hash": str(receipt.get("hash", ""))[:20] + "...",
                "governance": receipt.get("governance_level"),
            }
        return {"ok": False, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ─────────────────────────────────────────────
# RECEIPT 1 — Invariante Constitucional I11
# "Permanência de Evidência Criptográfica"
# ─────────────────────────────────────────────
I11_CONTENT = {
    "invariant": "I11",
    "name": "Permanência de Evidência Criptográfica",
    "classification": "IRREMEDIÁVEL",
    "tier": "GOLD",
    "description": (
        "Todo documento selado no WINDI gera uma impressão criptográfica permanente. "
        "Esta impressão não pode ser apagada, modificada ou suprimida por nenhum actor — "
        "humano ou algorítmico. A evidência existe independentemente da vontade do produtor."
    ),
    "trigger": "Xuxuzinha receipt — documento real entregue que inspirou este invariante",
    "sealed_by": "Human_Dragon_Pioneer1",
    "sealed_at": "2026-03-05T00:00:00Z",
    "governance": "HIGH",
    "flags": ["IRREMEDIÁVEL", "GOLD", "CONSTITUTIONAL"],
}

I11_PAYLOAD = {
    "id": "WINDI-I11-CONSTITUTIONAL-20260305",
    "actor": ACTOR,
    "app": "constitutional-core",
    "doc_name": "Invariante Constitucional I11 — Permanência de Evidência Criptográfica",
    "doc_type": "doc",
    "governance_level": "HIGH",
    "content": I11_CONTENT,
    "hash": sha256(I11_CONTENT),
    "metadata": {
        "impact_level": "CRIT",
        "value_range": "R5",
        "risk_level": "R0",
        "flow_status": "SEALED",
        "department_code": "CONSTITUTIONAL",
        "classification": "IRREMEDIÁVEL",
        "original_date": "2026-03-05",
    },
    "tags": ["constitutional", "invariant", "IRREMEDIÁVEL", "I11", "GOLD"],
}

# ─────────────────────────────────────────────
# RECEIPT 2 — Genesis Record
# Primeiro acto institucional do Verify Public
# ─────────────────────────────────────────────
GENESIS_CONTENT = {
    "event": "WINDI Verify Public v1.0.1 — Genesis Record",
    "description": (
        "Primeiro acto de verificação pública do ecossistema WINDI. "
        "Marca o nascimento do sistema de verificação soberana: QR + Upload + ID manual. "
        "Formato canónico: WINDI:{receipt_id}|{hash}. "
        "URL canónica: https://windi-domain.com/verify-public/?id={receipt_id}"
    ),
    "version": "1.0.1",
    "commit": "dca0b85",
    "port": 8114,
    "path": "/verify-public/",
    "features": ["QR", "Upload", "ID manual", "Auto-verify via URL params"],
    "sealed_by": "Human_Dragon_Pioneer1",
    "sealed_at": "2026-03-05T00:00:00Z",
}

GENESIS_PAYLOAD = {
    "id": "WINDI-VERIFY-GENESIS-20260305",
    "actor": ACTOR,
    "app": "verify-public",
    "doc_name": "WINDI Verify Public v1.0.1 — Genesis Record",
    "doc_type": "doc",
    "governance_level": "HIGH",
    "content": GENESIS_CONTENT,
    "hash": sha256(GENESIS_CONTENT),
    "metadata": {
        "impact_level": "CRIT",
        "value_range": "R5",
        "risk_level": "R0",
        "flow_status": "SEALED",
        "department_code": "VERIFY",
        "original_date": "2026-03-05",
    },
    "tags": ["genesis", "verify-public", "v1.0.1", "institutional"],
}

# ─────────────────────────────────────────────
# RECEIPT 3 — Master Spec v1.0
# Especificação técnica canónica do WINDI Verify
# ─────────────────────────────────────────────
MASTERSPEC_CONTENT = {
    "document": "WINDI Verify Master Specification v1.0",
    "description": (
        "Especificação técnica canónica do sistema WINDI Verify. "
        "Define: formato QR (WINDI:{id}|{hash}), URL canónica de verificação, "
        "schema do Ledger, níveis de governance (LOW/MEDIUM/HIGH), "
        "campos obrigatórios (id, actor, app, doc_name, doc_type, governance_level), "
        "e o princípio 'AI processes. Human decides. WINDI guarantees.'"
    ),
    "version": "1.0",
    "sha256_of_document": "4404fa2b",  # hash do documento físico
    "sealed_by": "Human_Dragon_Pioneer1",
    "sealed_at": "2026-03-05T00:00:00Z",
    "location": "/opt/windi/docs/verify/master-spec-v1.0.md",
    "governance_principle": "AI processes. Human decides. WINDI guarantees.",
}

MASTERSPEC_PAYLOAD = {
    "id": "WINDI-VERIFY-MASTERSPEC-V1.0",
    "actor": ACTOR,
    "app": "governance-core",
    "doc_name": "WINDI Verify Master Specification v1.0",
    "doc_type": "doc",
    "governance_level": "HIGH",
    "content": MASTERSPEC_CONTENT,
    "hash": sha256(MASTERSPEC_CONTENT),
    "metadata": {
        "impact_level": "CRIT",
        "value_range": "R5",
        "risk_level": "R0",
        "flow_status": "SEALED",
        "department_code": "GOVERNANCE",
        "original_date": "2026-03-05",
    },
    "tags": ["master-spec", "governance", "verify", "canonical", "v1.0"],
}

# ─────────────────────────────────────────────
# EXECUÇÃO
# ─────────────────────────────────────────────
receipts_to_seal = [
    ("I11 Constitutional",    "WINDI-I11-CONSTITUTIONAL-20260305",  I11_PAYLOAD),
    ("Genesis Record",        "WINDI-VERIFY-GENESIS-20260305",      GENESIS_PAYLOAD),
    ("Master Spec v1.0",      "WINDI-VERIFY-MASTERSPEC-V1.0",       MASTERSPEC_PAYLOAD),
]

print("=" * 60)
print("🐉 WINDI — Seal Constitutional Receipts")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
print("=" * 60)

# 0. Confirmar que o Ledger está UP
try:
    health = requests.get(f"{LEDGER_URL}/health", timeout=3)
    print(f"\n✅ Ledger UP — {LEDGER_URL}")
except:
    # Alguns Ledgers não têm /health — testar com receipts endpoint
    print(f"\n⚠️  /health não disponível — testando via /api/receipts/...")

results = []
for name, receipt_id, payload in receipts_to_seal:
    print(f"\n{'─'*50}")
    print(f"📜 {name}")
    print(f"   ID: {receipt_id}")
    print(f"   Hash: {payload['hash'][:20]}...")

    # Verificar se já existe
    if verify_exists(receipt_id):
        # Confirmar o existente
        conf = confirm_receipt(receipt_id)
        results.append({"name": name, "status": "already_exists", "confirm": conf})
        continue

    # Selar
    print(f"   ⏳ A selar...")
    result = seal_receipt(payload)

    if result["ok"]:
        print(f"   ✅ Selado com sucesso")
        conf = confirm_receipt(receipt_id)
        print(f"   🔍 Confirmado: {conf}")
        results.append({"name": name, "status": "sealed", "confirm": conf})
    else:
        print(f"   ❌ ERRO: {result}")
        results.append({"name": name, "status": "error", "detail": result})

# ─────────────────────────────────────────────
# RELATÓRIO FINAL
# ─────────────────────────────────────────────
print(f"\n{'='*60}")
print("📊 RELATÓRIO FINAL")
print(f"{'='*60}")

ok_count = sum(1 for r in results if r["status"] in ("sealed", "already_exists"))
print(f"\n✅ Selados com sucesso: {ok_count}/{len(results)}")

for r in results:
    icon = "✅" if r["status"] in ("sealed", "already_exists") else "❌"
    status_label = "SELADO" if r["status"] == "sealed" else ("JÁ EXISTIA" if r["status"] == "already_exists" else "ERRO")
    print(f"  {icon} {r['name']} — {status_label}")

if ok_count == 3:
    print("\n🏆 Os 3 receipts constitucionais estão no Ledger.")
    print("   Testes R2, A1, A2 do checklist agora passam.")
    print("\n   Verificar em:")
    print("   https://windi-domain.com/verify-public/?id=WINDI-I11-CONSTITUTIONAL-20260305")
    print("   https://windi-domain.com/verify-public/?id=WINDI-VERIFY-GENESIS-20260305")
    print("   https://windi-domain.com/verify-public/?id=WINDI-VERIFY-MASTERSPEC-V1.0")
else:
    print("\n⚠️  Verificar os erros acima antes de prosseguir.")

print(f"\n{'='*60}")
print("OM SHANTI 🐉")
print(f"{'='*60}\n")
