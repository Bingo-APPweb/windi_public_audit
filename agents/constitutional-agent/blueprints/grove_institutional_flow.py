"""
grove_institutional_flow.py
===================================================================
WINDI Grove Arena - Institutional Flow Simulator v1.0.0
===================================================================

IMPORTANTE - LEIA ANTES DE MODIFICAR:
=====================================

1. ESTE ARQUIVO E SPEC EXECUTAVEL - NAO E SERVICO
   Este arquivo e documentacao viva do Sovereign Flow.
   NAO deve virar endpoint, NAO deve rodar como servico.
   E o blueprint de referencia do fluxo institucional.

2. SUBSTITUIR MOCK DO LEDGER POR CHAMADA REAL
   A funcao ledger_post() abaixo e mock. Em producao:

   def ledger_post(payload: dict) -> dict:
       r = requests.post(
           "http://localhost:8101/api/receipts",
           json=payload,
           timeout=10
       )
       r.raise_for_status()
       return r.json()

3. CLIENT E CASE SAO FIXTURES DE TESTE
   Os dados "Muller & Partner GmbH", "DE298765432" etc. sao mock.
   Em producao esses campos vem do Wallet real (:8099) e do DID
   do usuario - NUNCA hardcoded.

4. APOS SUBSTITUICAO DO MOCK, RODAR SMOKE TEST COMPLETO

5. GATE HUMANO DEVE PERMANECER ANTES DE QUALQUER SEAL
   Invariante constitucional: AI propoe, humano decide.

===================================================================

Cenario: Empresa DE (Muller & Partner GmbH) contrata consultoria
completa via Grove Arena para analise de contrato com clausulas
de dados pessoais + submissao notarial + trilha de auditoria.

Fluxo completo:
  SEED  -> Registro da intencao
  ARENA -> W-LEGAL (x3) + W-COMPLY (x2)
  ARENA -> W-ARCH (x1) blueprint de decisao
  SEAL  -> W-NOTARY + W-AUDIT -> Virtue Receipt
  LEDGER -> POST :8101 -> QR -> /verify-public/

AI processes. Human decides. WINDI guarantees.
Kempten, Bavaria - 09.03.2026
"""

from __future__ import annotations

import json
import time
import hashlib
import uuid
from datetime import datetime, timezone
from dataclasses import asdict

# -- importa o engine que criamos --
from grove_honorarium_model import (
    HonorariumEngine,
    FlowPhase,
    IdentityMultiplier,
    DebitStatus,
    AGENT_REGISTRY,
)


# ---------------------------------------------
#  CLIENTE INSTITUCIONAL (FIXTURE DE TESTE)
# ---------------------------------------------
# ATENCAO: Em producao, estes dados vem do Wallet (:8099)
# e do DID do usuario. NUNCA hardcode em producao.

CLIENT = {
    "company":      "Muller & Partner GmbH",
    "vat_de":       "DE298765432",
    "contact":      "Dr. Katrin Muller",
    "email":        "k.mueller@mueller-partner.de",
    "wallet_id":    "WINDI-EMPRESA-MP-2026-001",
    "did":          "did:windi:de:muller-partner:2026",
    "identity":     IdentityMultiplier.EMPRESA,   # +20%, gera NF
    "balance":      5000.0,                        # creditos disponiveis
    "jurisdiction": "DE",
    "language":     "de",
}

CASE = {
    "ref":       "CASE-MP-20260309-001",
    "subject":   "Analise de Contrato SaaS - Clausulas GDPR + eIDAS + Transferencia de Dados",
    "doc_hash":  hashlib.sha256(b"Mustervertrag_SaaS_MuellerPartner_v3.pdf").hexdigest(),
    "doc_name":  "Mustervertrag_SaaS_MuellerPartner_v3.pdf",
    "pages":     47,
    "risk_flag": "Clausula 8.3 - transferencia para US sem SCCs adequadas",
}


# ---------------------------------------------
#  RENDERER - output limpo e narrativo
# ---------------------------------------------

def divider(char="=", n=64):
    print(char * n)

def section(title: str):
    print()
    divider()
    print(f"  {title}")
    divider()

def step(icon: str, label: str, detail: str = ""):
    print(f"\n  {icon}  {label}")
    if detail:
        for line in detail.strip().split("\n"):
            print(f"      {line.strip()}")

def receipt_line(label: str, value: str, color_hint: str = ""):
    pad = 28
    print(f"  {label:<{pad}} {value}")

def agent_line(icon, name, tier, credits_raw, mult, credits_final, eur):
    print(f"  {icon}  {name:<14} [{tier:<10}]  "
          f"{credits_raw:>3}cr x {mult} = {credits_final:>6}cr  ->  EUR{eur:.4f}")


# ---------------------------------------------
#  LEDGER - MOCK vs PRODUCAO
# ---------------------------------------------
#
# MOCK ATUAL (para testes locais):
# --------------------------------

LEDGER_STORE: list[dict] = []   # simula SQLite do Forensic Ledger

def ledger_post(payload: dict) -> dict:
    """
    MOCK do POST /api/receipts em :8101.

    ============================================================
    EM PRODUCAO, SUBSTITUIR POR:
    ============================================================

    import requests

    def ledger_post(payload: dict) -> dict:
        r = requests.post(
            "http://localhost:8101/api/receipts",
            json=payload,
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    ============================================================
    """
    ts = datetime.now(timezone.utc).isoformat()
    receipt_id = payload.get("id", f"WINDI-{uuid.uuid4().hex[:12].upper()}")

    # simula o formato de resposta real do Forensic Ledger
    response = {
        "status":       "sealed",
        "receipt_id":   receipt_id,
        "hash":         hashlib.sha256(
                            json.dumps(payload, sort_keys=True).encode()
                        ).hexdigest(),
        "timestamp":    ts,
        "verify_url":   f"https://windi-domain.com/verify-public/?id={receipt_id}",
        "qr_payload":   f"WINDI:{receipt_id}|{hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]}",
        "governance":   payload.get("governance_level", "HIGH"),
    }
    LEDGER_STORE.append({"payload": payload, "response": response})
    return response


# ---------------------------------------------
#  FLUXO PRINCIPAL
# ---------------------------------------------

def run_institutional_flow():

    engine  = HonorariumEngine()
    session = f"SESS-{uuid.uuid4().hex[:10].upper()}"
    all_receipts: list[dict] = []
    total_credits_spent: float = 0.0
    timeline: list[dict] = []

    # ==========================================
    #  CABECALHO
    # ==========================================

    print()
    divider("=")
    print("  WINDI Grove Arena - Institutional Flow Simulator v1.0.0")
    print("  AI processes. Human decides. WINDI guarantees.")
    divider("=")

    print(f"\n  Cliente:   {CLIENT['company']}")
    print(f"  VAT:       {CLIENT['vat_de']}")
    print(f"  DID:       {CLIENT['did']}")
    print(f"  Sessao:    {session}")
    print(f"  Saldo:     {CLIENT['balance']:.0f} creditos disponiveis")
    print(f"\n  Caso:      {CASE['ref']}")
    print(f"  Assunto:   {CASE['subject']}")
    print(f"  Doc hash:  {CASE['doc_hash'][:32]}...")
    print(f"  [!] Risco: {CASE['risk_flag']}")


    # ==========================================
    #  FASE 1 - SEED (EUR0)
    # ==========================================

    section("FASE 1 - SEED - Registro de Intencao  [EUR0]")

    seed_id = f"SEED-{uuid.uuid4().hex[:10].upper()}"
    seed_ts = datetime.now(timezone.utc).isoformat()

    step("SEED", "Intencao registrada", f"""
        seed_id:    {seed_id}
        wallet:     {CLIENT['wallet_id']}
        caso:       {CASE['ref']}
        timestamp:  {seed_ts}
        custo:      0 creditos (SEED e sempre gratuito)
    """)

    seed_ledger = ledger_post({
        "id":               seed_id,
        "actor":            CLIENT["wallet_id"],
        "app":              "grove-arena",
        "doc_name":         f"SEED - {CASE['ref']}",
        "doc_type":         "doc",
        "governance_level": "MEDIUM",
        "metadata": {
            "phase":     "seed",
            "case_ref":  CASE["ref"],
            "subject":   CASE["subject"],
            "doc_hash":  CASE["doc_hash"],
        },
        "timestamp": seed_ts,
    })

    step("LINK", "Ledger SEED selado",
         f"Receipt: {seed_ledger['receipt_id']}\n"
         f"Hash:    {seed_ledger['hash'][:32]}...\n"
         f"URL:     {seed_ledger['verify_url']}")

    timeline.append({"phase": "SEED", "receipt_id": seed_ledger["receipt_id"], "credits": 0})


    # ==========================================
    #  FASE 2 - ARENA - W-LEGAL x 3 rodadas
    # ==========================================

    section("FASE 2a - ARENA - W-LEGAL  [3 rodadas juridicas]")

    step("LEGAL", "W-LEGAL-001 convocado para analise contratual", f"""
        Tarefa:  Analisar 47 paginas do Mustervertrag_SaaS
        Foco:    Clausula 8.3 - transferencia US sem SCCs
        Rodadas: 3 (apuracao + analise profunda + parecer final)
        Modelo:  claude-sonnet-4 (tier EMPRESA HIGH)
    """)

    est_legal = engine.estimate(
        session_id = session,
        wallet_id  = CLIENT["wallet_id"],
        agents     = ["W-LEGAL-001"],
        phase      = FlowPhase.ARENA,
        identity   = CLIENT["identity"],
        rounds     = 3,
    )

    print()
    agent_line("LEGAL", "Legal", "elite",
               est_legal.line_items[0].credits_raw,
               CLIENT["identity"].value,
               est_legal.line_items[0].credits_final,
               est_legal.line_items[0].eur_value)
    print(f"\n  {'Estimativa:':<28} {est_legal.total_credits} creditos = EUR{est_legal.total_eur:.4f}")
    print(f"  {'Estimate hash:':<28} {est_legal.hash_sha256[:32]}...")

    # simula tempo de processamento
    step("WAIT", "Processando 3 rodadas juridicas...", "")
    time.sleep(0.3)

    # W-LEGAL produz parecer
    legal_output = {
        "rodada_1": "Mapeamento de clausulas criticas: 8.3, 12.1, 15.4",
        "rodada_2": "Analise GDPR Art.46 - ausencia de SCCs para US. Risco ALTO.",
        "rodada_3": "Parecer: contrato inadmissivel sem adendo de SCCs + DPA atualizado.",
        "recomendacao": "REJECT_AS_IS - exige revisao antes de assinar",
    }

    step("OK", "Parecer juridico emitido", json.dumps(legal_output, ensure_ascii=False, indent=2))

    receipt_legal = engine.consume(est_legal, wallet_balance=CLIENT["balance"])
    CLIENT["balance"] -= receipt_legal.credits_debited
    total_credits_spent += receipt_legal.credits_debited

    ledger_legal = ledger_post({
        **receipt_legal.ledger_payload,
        "id": f"GRV-LEGAL-{uuid.uuid4().hex[:10].upper()}",
        "metadata": {
            **receipt_legal.ledger_payload.get("metadata", {}),
            "case_ref":    CASE["ref"],
            "legal_output": legal_output,
            "doc_hash":    CASE["doc_hash"],
        },
    })

    step("LINK", "Receipt LEGAL selado no Ledger",
         f"ID:    {ledger_legal['receipt_id']}\n"
         f"Hash:  {ledger_legal['hash'][:32]}...\n"
         f"URL:   {ledger_legal['verify_url']}\n"
         f"QR:    {ledger_legal['qr_payload']}")

    all_receipts.append(ledger_legal)
    timeline.append({"phase": "ARENA/LEGAL", "receipt_id": ledger_legal["receipt_id"],
                     "credits": receipt_legal.credits_debited})


    # ==========================================
    #  FASE 2b - ARENA - W-COMPLY x 2 rodadas
    # ==========================================

    section("FASE 2b - ARENA - W-COMPLY  [2 rodadas normativas]")

    step("COMPLY", "W-COMPLY-001 convocado para verificacao GDPR + eIDAS", f"""
        Tarefa:  Validar conformidade com GDPR Art.44-49 + eIDAS Reg.910/2014
        Foco:    Transferencia internacional + assinatura eletronica
        Rodadas: 2 (scan + relatorio normativo)
        Modelo:  mistral-medium (tier EMPRESA - MED suficiente para rules)
    """)

    est_comply = engine.estimate(
        session_id = session,
        wallet_id  = CLIENT["wallet_id"],
        agents     = ["W-COMPLY-001"],
        phase      = FlowPhase.ARENA,
        identity   = CLIENT["identity"],
        rounds     = 2,
    )

    print()
    agent_line("COMPLY", "Compliance", "elite",
               est_comply.line_items[0].credits_raw,
               CLIENT["identity"].value,
               est_comply.line_items[0].credits_final,
               est_comply.line_items[0].eur_value)
    print(f"\n  {'Estimativa:':<28} {est_comply.total_credits} creditos = EUR{est_comply.total_eur:.4f}")

    time.sleep(0.2)

    comply_output = {
        "gdpr_art44":  "FAIL - sem mecanismo de transferencia valido para US",
        "gdpr_art46":  "FAIL - SCCs ausentes (Decisao 2021/914 nao referenciada)",
        "eidas_qes":   "PASS - formato de assinatura compativel com Reg.910/2014",
        "bcr_status":  "N/A - empresa US sem BCR aprovadas",
        "verdict":     "NON_COMPLIANT",
        "action":      "Adicionar Addendum SCCs + nomeacao DPO contratual",
    }

    step("OK", "Relatorio normativo emitido", json.dumps(comply_output, ensure_ascii=False, indent=2))

    receipt_comply = engine.consume(est_comply, wallet_balance=CLIENT["balance"])
    CLIENT["balance"] -= receipt_comply.credits_debited
    total_credits_spent += receipt_comply.credits_debited

    ledger_comply = ledger_post({
        **receipt_comply.ledger_payload,
        "id": f"GRV-COMPLY-{uuid.uuid4().hex[:10].upper()}",
        "metadata": {
            **receipt_comply.ledger_payload.get("metadata", {}),
            "case_ref":      CASE["ref"],
            "comply_output": comply_output,
        },
    })

    step("LINK", "Receipt COMPLY selado",
         f"ID:    {ledger_comply['receipt_id']}\n"
         f"Hash:  {ledger_comply['hash'][:32]}...\n"
         f"URL:   {ledger_comply['verify_url']}")

    all_receipts.append(ledger_comply)
    timeline.append({"phase": "ARENA/COMPLY", "receipt_id": ledger_comply["receipt_id"],
                     "credits": receipt_comply.credits_debited})


    # ==========================================
    #  FASE 2c - ARENA - W-ARCH x 1 rodada
    # ==========================================

    section("FASE 2c - ARENA - W-ARCH  [1 rodada - blueprint de decisao]")

    step("ARCH", "W-ARCH-001 convocado para sintetizar e estruturar decisao", f"""
        Tarefa:  Consolidar pareceres Legal + Comply em blueprint executivo
        Output:  Roadmap de acoes + prioridades + responsaveis
        Rodadas: 1 (sintese estrategica)
        Modelo:  claude-sonnet-4 (Arquitec sempre HIGH - raciocinio complexo)
    """)

    est_arch = engine.estimate(
        session_id = session,
        wallet_id  = CLIENT["wallet_id"],
        agents     = ["W-ARCH-001"],
        phase      = FlowPhase.ARENA,
        identity   = CLIENT["identity"],
        rounds     = 1,
    )

    print()
    agent_line("ARCH", "Arquitec", "narrativo",
               est_arch.line_items[0].credits_raw,
               CLIENT["identity"].value,
               est_arch.line_items[0].credits_final,
               est_arch.line_items[0].eur_value)
    print(f"\n  {'Estimativa:':<28} {est_arch.total_credits} creditos = EUR{est_arch.total_eur:.4f}")

    time.sleep(0.4)

    arch_blueprint = {
        "decisao":    "REJECT_AND_RENEGOTIATE",
        "prioridade": "ALTA",
        "acoes": [
            {"ordem": 1, "acao": "Solicitar SCCs atualizadas (Decisao 2021/914) ao fornecedor US"},
            {"ordem": 2, "acao": "Nomear DPO contratual com clausula de responsabilidade"},
            {"ordem": 3, "acao": "Adicionar Addendum GDPR Art.46(2)(c) ao contrato"},
            {"ordem": 4, "acao": "Resubmeter para analise WINDI apos revisoes"},
        ],
        "prazo_estimado":  "15 dias uteis",
        "responsavel":     "Dr. Katrin Muller + Departamento Juridico",
        "risco_residual":  "BAIXO apos implementacao",
        "invariante":      "Human Dragon aprova blueprint - Arquitec propoe, nunca executa",
    }

    step("OK", "Blueprint executivo emitido", json.dumps(arch_blueprint, ensure_ascii=False, indent=2))

    receipt_arch = engine.consume(est_arch, wallet_balance=CLIENT["balance"])
    CLIENT["balance"] -= receipt_arch.credits_debited
    total_credits_spent += receipt_arch.credits_debited

    ledger_arch = ledger_post({
        **receipt_arch.ledger_payload,
        "id": f"GRV-ARCH-{uuid.uuid4().hex[:10].upper()}",
        "metadata": {
            **receipt_arch.ledger_payload.get("metadata", {}),
            "case_ref":      CASE["ref"],
            "arch_blueprint": arch_blueprint,
        },
    })

    step("LINK", "Receipt ARCH selado",
         f"ID:    {ledger_arch['receipt_id']}\n"
         f"Hash:  {ledger_arch['hash'][:32]}...\n"
         f"URL:   {ledger_arch['verify_url']}")

    all_receipts.append(ledger_arch)
    timeline.append({"phase": "ARENA/ARCH", "receipt_id": ledger_arch["receipt_id"],
                     "credits": receipt_arch.credits_debited})


    # ==========================================
    #  GATE HUMANO - invariante constitucional
    # ==========================================

    section("GATE HUMANO - Invariante Constitucional")

    print("""
  +-------------------------------------------------------------+
  |                                                             |
  |   AI processes. Human decides. WINDI guarantees.           |
  |                                                             |
  |   Os 3 pareceres da Arena estao prontos.                   |
  |   Nenhum ato juridico foi praticado ainda.                 |
  |                                                             |
  |   Aguardando decisao de: Dr. Katrin Muller                 |
  |   Opcoes:                                                   |
  |     [S] SELAR - aceitar pareceres e submeter ao Cartorio   |
  |     [R] REVISAR - solicitar nova rodada na Arena           |
  |     [X] CANCELAR - encerrar sem seal                       |
  |                                                             |
  |   >>> Decisao humana simulada: [S] SELAR                   |
  |                                                             |
  +-------------------------------------------------------------+
    """)

    time.sleep(0.5)


    # ==========================================
    #  FASE 3a - SEAL - W-NOTARY
    # ==========================================

    section("FASE 3a - SEAL - W-NOTARY  [autenticacao notarial]")

    step("NOTARY", "W-NOTARY-001 autenticando o ato consultivo", f"""
        Tarefa:  Autenticar todos os pareceres Arena como ato notarial WINDI
        Ancoras: {len(all_receipts)} receipts Arena + doc hash original
        Modelo:  mistral-medium (notarial e deterministico)
    """)

    est_notary = engine.estimate(
        session_id = session,
        wallet_id  = CLIENT["wallet_id"],
        agents     = ["W-NOTARY-001"],
        phase      = FlowPhase.SEAL,
        identity   = CLIENT["identity"],
    )

    print()
    agent_line("NOTARY", "Notary", "estrutural",
               est_notary.line_items[0].credits_raw,
               CLIENT["identity"].value,
               est_notary.line_items[0].credits_final,
               est_notary.line_items[0].eur_value)
    print(f"\n  {'Estimativa Seal:':<28} {est_notary.total_credits} creditos = EUR{est_notary.total_eur:.4f}")

    time.sleep(0.2)

    # gera hash da cadeia completa de evidencias
    chain_data = json.dumps([r["hash"] for r in all_receipts], sort_keys=True)
    evidence_chain_hash = hashlib.sha256(chain_data.encode()).hexdigest()

    notary_seal = {
        "ato":              "CONSULTA_JURIDICA_WINDI",
        "case_ref":         CASE["ref"],
        "doc_original":     CASE["doc_hash"],
        "evidence_chain":   evidence_chain_hash,
        "receipts_ancored": [r["receipt_id"] for r in all_receipts],
        "seal_type":        "WINDI_NOTARIAL_v1",
        "jurisdiction":     "DE/EU",
        "timestamp":        datetime.now(timezone.utc).isoformat(),
    }

    receipt_notary = engine.consume(est_notary, wallet_balance=CLIENT["balance"])
    CLIENT["balance"] -= receipt_notary.credits_debited
    total_credits_spent += receipt_notary.credits_debited

    notary_receipt_id = f"WINDI-NOTARY-{uuid.uuid4().hex[:12].upper()}"
    ledger_notary = ledger_post({
        "id":               notary_receipt_id,
        "actor":            CLIENT["wallet_id"],
        "app":              "grove-arena",
        "doc_name":         f"Ato Notarial - {CASE['ref']}",
        "doc_type":         "doc",
        "governance_level": "HIGH",
        "metadata":         notary_seal,
        "timestamp":        notary_seal["timestamp"],
    })

    step("OK", "Ato notarial selado",
         f"Seal ID:        {ledger_notary['receipt_id']}\n"
         f"Evidence chain: {evidence_chain_hash[:32]}...\n"
         f"Ancoras:        {len(all_receipts)} receipts Arena\n"
         f"QR:             {ledger_notary['qr_payload']}\n"
         f"URL publica:    {ledger_notary['verify_url']}")

    all_receipts.append(ledger_notary)
    timeline.append({"phase": "SEAL/NOTARY", "receipt_id": ledger_notary["receipt_id"],
                     "credits": receipt_notary.credits_debited})


    # ==========================================
    #  FASE 3b - SEAL - W-AUDIT
    # ==========================================

    section("FASE 3b - SEAL - W-AUDIT  [trilha forense completa]")

    step("AUDIT", "W-AUDIT-001 gerando trilha forense self-hashing", f"""
        Tarefa:  Auditar toda a cadeia de evidencias da sessao
        Scope:   SEED + 3xARENA + NOTARY -> relatorio imutavel
        Modelo:  mistral-small (read-only - sem geracao criativa)
        Regra:   "proof of the proof is also proof"
    """)

    est_audit = engine.estimate(
        session_id = session,
        wallet_id  = CLIENT["wallet_id"],
        agents     = ["W-AUDIT-001"],
        phase      = FlowPhase.SEAL,
        identity   = CLIENT["identity"],
    )

    print()
    agent_line("AUDIT", "Auditor", "estrutural",
               est_audit.line_items[0].credits_raw,
               CLIENT["identity"].value,
               est_audit.line_items[0].credits_final,
               est_audit.line_items[0].eur_value)

    time.sleep(0.2)

    audit_report = {
        "session_id":      session,
        "case_ref":        CASE["ref"],
        "total_receipts":  len(all_receipts),
        "chain_integrity": "VALID",
        "phases_covered":  ["SEED", "ARENA/LEGAL", "ARENA/COMPLY", "ARENA/ARCH", "SEAL/NOTARY"],
        "hash_chain": [r["hash"][:16] + "..." for r in all_receipts],
        "anomalies":       [],
        "verdict":         "TRILHA_INTEGRA",
        "auditor_note":    "Todos os atos computacionais tem receita verificavel. Nenhuma lacuna detectada.",
        "self_hash":       "",  # preenchido abaixo
    }

    # o proprio relatorio se auto-hasha
    audit_report["self_hash"] = hashlib.sha256(
        json.dumps({k: v for k, v in audit_report.items() if k != "self_hash"},
                   sort_keys=True).encode()
    ).hexdigest()

    receipt_audit = engine.consume(est_audit, wallet_balance=CLIENT["balance"])
    CLIENT["balance"] -= receipt_audit.credits_debited
    total_credits_spent += receipt_audit.credits_debited

    audit_receipt_id = f"WINDI-AUDIT-{uuid.uuid4().hex[:12].upper()}"
    ledger_audit = ledger_post({
        "id":               audit_receipt_id,
        "actor":            CLIENT["wallet_id"],
        "app":              "grove-arena",
        "doc_name":         f"Trilha Forense - {CASE['ref']}",
        "doc_type":         "doc",
        "governance_level": "HIGH",
        "metadata":         audit_report,
        "timestamp":        datetime.now(timezone.utc).isoformat(),
    })

    step("OK", "Trilha forense selada - self-hashing completo",
         f"Audit ID:   {ledger_audit['receipt_id']}\n"
         f"Self-hash:  {audit_report['self_hash'][:32]}...\n"
         f"Integridade: {audit_report['chain_integrity']}\n"
         f"Veredicto:   {audit_report['verdict']}\n"
         f"URL:         {ledger_audit['verify_url']}")

    all_receipts.append(ledger_audit)
    timeline.append({"phase": "SEAL/AUDIT", "receipt_id": ledger_audit["receipt_id"],
                     "credits": receipt_audit.credits_debited})


    # ==========================================
    #  VIRTUE RECEIPT FINAL (trilingue PT/DE/EN)
    # ==========================================

    section("VIRTUE RECEIPT FINAL - Trilingue PT/DE/EN")

    virtue_receipt_id = f"WINDI-VR-{uuid.uuid4().hex[:14].upper()}"
    final_hash = hashlib.sha256(
        json.dumps([r["hash"] for r in all_receipts], sort_keys=True).encode()
    ).hexdigest()
    final_ts = datetime.now(timezone.utc).isoformat()

    print(f"""
  +==============================================================+
  |          WINDI VIRTUE RECEIPT - {virtue_receipt_id[:26]}
  +==============================================================+
  |                                                              |
  |  [PT] PORTUGUES                                              |
  |  Este documento certifica que a consultoria juridica         |
  |  solicitada por {CLIENT['company']:<24} foi         |
  |  integralmente processada, auditada e selada pelo            |
  |  sistema WINDI Grove Arena em conformidade com os            |
  |  principios constitucionais da plataforma.                   |
  |                                                              |
  |  [DE] DEUTSCH                                                |
  |  Dieses Dokument bestatigt, dass die Rechtsberatung          |
  |  fur {CLIENT['company']:<28} vollstandig    |
  |  verarbeitet, gepruft und durch das WINDI Grove Arena        |
  |  System gemass den Verfassungsgrundsatzen versiegelt wurde.  |
  |                                                              |
  |  [EN] ENGLISH                                                |
  |  This document certifies that legal consultancy              |
  |  for {CLIENT['company']:<28} was fully        |
  |  processed, audited and sealed by the WINDI Grove Arena      |
  |  system in compliance with constitutional principles.        |
  |                                                              |
  +==============================================================+
  |  DADOS DO ATO / AKTDATEN / ACT DATA                         |
  +==============================================================+""")

    receipt_line("  |  Caso / Fall / Case", CASE["ref"])
    receipt_line("  |  Cliente / Kunde / Client", CLIENT["company"])
    receipt_line("  |  DID", CLIENT["did"])
    receipt_line("  |  Sessao / Session", session)
    receipt_line("  |  Data / Datum / Date", final_ts[:19] + "Z")
    receipt_line("  |  Virtue Receipt ID", virtue_receipt_id)

    print("  +==============================================================+")
    receipt_line("  |  Fase SEED", f"1 receipt - EUR0.00")
    receipt_line("  |  Fase ARENA (Legal x3)", f"{timeline[1]['credits']} creditos")
    receipt_line("  |  Fase ARENA (Comply x2)", f"{timeline[2]['credits']} creditos")
    receipt_line("  |  Fase ARENA (Arch x1)", f"{timeline[3]['credits']} creditos")
    receipt_line("  |  Fase SEAL (Notary)", f"{timeline[4]['credits']} creditos")
    receipt_line("  |  Fase SEAL (Audit)", f"{timeline[5]['credits']} creditos")
    print("  +==============================================================+")
    receipt_line(f"  |  TOTAL CREDITOS", f"{total_credits_spent:.1f} creditos")
    receipt_line(f"  |  TOTAL EUR", f"EUR{total_credits_spent * 0.01:.4f}")
    receipt_line(f"  |  Saldo restante", f"{CLIENT['balance']:.1f} creditos")
    print("  +==============================================================+")
    print(f"  |  SHA-256 Final: {final_hash[:46]}")
    print(f"  |  QR:  WINDI:{virtue_receipt_id}|{final_hash[:16]}")
    print(f"  |  URL: https://windi-domain.com/verify-public/?id={virtue_receipt_id[:20]}...")
    print("  +==============================================================+")
    print("  |  AI processes. Human decides. WINDI guarantees.             |")
    print("  +==============================================================+")

    # Sela o Virtue Receipt no Ledger
    ledger_vr = ledger_post({
        "id":               virtue_receipt_id,
        "actor":            CLIENT["wallet_id"],
        "app":              "grove-arena",
        "doc_name":         f"Virtue Receipt - {CASE['ref']}",
        "doc_type":         "doc",
        "governance_level": "HIGH",
        "metadata": {
            "case_ref":         CASE["ref"],
            "client_did":       CLIENT["did"],
            "session":          session,
            "total_credits":    total_credits_spent,
            "total_eur":        round(total_credits_spent * 0.01, 4),
            "receipts_count":   len(all_receipts),
            "final_hash":       final_hash,
            "arch_blueprint":   arch_blueprint,
            "audit_verdict":    audit_report["verdict"],
            "i18n":             ["PT", "DE", "EN"],
        },
        "timestamp": final_ts,
    })


    # ==========================================
    #  SUMARIO EXECUTIVO
    # ==========================================

    section("SUMARIO EXECUTIVO DA SESSAO")

    print(f"\n  {'Agentes convocados:':<32} 5 (Legal, Comply, Arch, Notary, Audit)")
    print(f"  {'Receipts no Ledger:':<32} {len(all_receipts) + 1} (inclui Virtue Receipt)")
    print(f"  {'Fases completadas:':<32} SEED -> ARENA -> [GATE HUMANO] -> SEAL")
    print()
    print(f"  {'Creditos gastos:':<32} {total_credits_spent:.1f}")
    print(f"  {'Valor em EUR:':<32} EUR{total_credits_spent * 0.01:.4f}")
    print(f"  {'Valor consultoria fisica:':<32} EUR3.000 - EUR8.000 (estimativa mercado DE)")
    print(f"  {'Fator de eficiencia:':<32} ~{int(3000 / (total_credits_spent * 0.01))}x mais barato")
    print()
    print(f"  {'Decisao humana aplicada:':<32} [OK] Dr. Katrin Muller [SELAR]")
    print(f"  {'Invariante respeitada:':<32} [OK] AI propoe, humano decide")
    print(f"  {'Trilha forense:':<32} [OK] INTEGRA - {len(all_receipts)} elos verificaveis")
    print(f"  {'Virtue Receipt:':<32} [OK] {virtue_receipt_id}")
    print()

    # timeline visual
    print("  TIMELINE DA SESSAO:\n")
    for i, ev in enumerate(timeline):
        bar = "#" * min(int(ev["credits"] * 2), 40)
        print(f"  {i+1}. [{ev['phase']:<16}] {bar} {ev['credits']}cr")

    print()
    divider()
    print("  [OK] Fluxo institucional completo.")
    print("  Proximos passos reais:")
    print("    1. requests.post('http://localhost:8101/api/receipts', json=ledger_payload)")
    print("    2. Bridge 'Selar' no UI Grove -> dispara FlowPhase.SEAL")
    print("    3. i18n PT/DE/EN no Virtue Receipt via W-COMM-001")
    divider()


# ---------------------------------------------
#  ENTRY POINT
# ---------------------------------------------

if __name__ == "__main__":
    run_institutional_flow()
