"""
WINDI LAW — AI Draft Module v1.0.0
"Any AI can generate a document. Only WINDI can prove it."

Upgrade para WINDI-LAW v1.3.0
Adicionar a /opt/windi/windi-law/identity-gate/ai_draft.py
Registar em identity_gate.py: app.include_router(ai_draft_router)

Invariants: I9 (humano aprova) · I11 (hash imutável) · G3 (decisão humana)
Pipeline: INPUT → I9 gate → LLM → DRAFT → I9 seal → HASH → LEDGER → VERIFY
"""

import os
import time
import hashlib
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

logger = logging.getLogger(__name__)

ai_draft_router = APIRouter(prefix="/ai-draft", tags=["AI Draft"])

# ─── Config ──────────────────────────────────────────────────────────────────

LEDGER_URL = os.getenv("LEDGER_URL", "http://127.0.0.1:8101/api/receipts")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://windi-domain.com")

# LLM routing: HIGH → Claude · FREE/MED → Mistral
ROUTING = {
    "HIGH": "claude-sonnet-4-20250514",
    "MED":  "mistral-small-latest",
    "FREE": "mistral-small-latest",
}

# ─── Legal Document Templates ─────────────────────────────────────────────────

DOC_TYPES = {
    "nda":         {"de": "Geheimhaltungsvereinbarung (NDA)", "en": "Non-Disclosure Agreement", "pt": "Acordo de Confidencialidade"},
    "vertrag":     {"de": "Dienstleistungsvertrag",           "en": "Service Agreement",          "pt": "Contrato de Prestação de Serviços"},
    "vollmacht":   {"de": "Vollmacht",                        "en": "Power of Attorney",          "pt": "Procuração"},
    "mahnung":     {"de": "Mahnung",                          "en": "Dunning Letter",             "pt": "Carta de Cobrança"},
    "kuendigung":  {"de": "Kündigung",                        "en": "Termination Notice",         "pt": "Rescisão"},
    "klausel":     {"de": "Vertragsklausel",                  "en": "Contract Clause",            "pt": "Cláusula Contratual"},
    "stellungnahme":{"de":"Stellungnahme",                    "en": "Legal Statement",            "pt": "Declaração Jurídica"},
    "gutachten":   {"de": "Rechtsgutachten",                  "en": "Legal Opinion",              "pt": "Parecer Jurídico"},
}

JURISDICTIONS = ["DE", "EU", "PT", "INT"]

# ─── System Prompt — Legal AI ─────────────────────────────────────────────────

def build_system_prompt(doc_type: str, jurisdiction: str, lang: str) -> str:
    doc_name = DOC_TYPES.get(doc_type, {}).get(lang.lower(), doc_type)
    return f"""Du bist ein spezialisierter KI-Assistent für juristische Dokumentenerstattung im WINDI Legal System.

DEINE ROLLE:
- Erstelle präzise, professionelle juristische Dokumente
- Dokument-Typ: {doc_name}
- Jurisdiction: {jurisdiction}
- Ausgabe-Sprache: {lang.upper()}

WINDI CONSTITUTIONAL RULES (UNVERÄNDERLICH):
1. I9 — Der Mensch hat bereits zugestimmt. Du generierst, aber entscheidest nicht.
2. I11 — Dieses Dokument wird nach der Erstellung kryptografisch versiegelt.
3. G3 — Alle Entscheidungen verbleiben beim Menschen.
4. Disclaimer IMMER am Ende: "⚠️ KI-generierter Entwurf. Rechtliche Überprüfung durch einen Anwalt erforderlich. Versiegelung durch WINDI bestätigt Existenz, nicht Rechtsberatung."

STRUKTUR-REGELN:
- Verwende professionelle juristische Sprache
- Klare Abschnitte mit §-Nummerierung (DE/EU) oder Artigos (PT)
- Platzhalter in [ECKIGEN KLAMMERN] für fehlende Daten
- Datum: {datetime.now(timezone.utc).strftime('%d.%m.%Y')}
- Kein Markdown außer für Struktur — reines Textformat für Versiegelung

QUALITÄTSSTANDARD:
- Niveau eines erfahrenen Rechtsanwalts
- Vollständig, klar, ohne Lücken
- Alle wesentlichen Klauseln enthalten"""


# ─── Models ───────────────────────────────────────────────────────────────────

class DraftRequest(BaseModel):
    did: str
    wallet_id: str
    doc_type: str          # nda | vertrag | vollmacht | ...
    jurisdiction: str      # DE | EU | PT | INT
    lang: str = "DE"       # DE | EN | PT
    tier: str = "FREE"     # FREE | MED | HIGH
    context: str           # Kontext: Parteien, Zweck, spezifische Anforderungen
    doc_name: Optional[str] = None

class SealRequest(BaseModel):
    did: str
    wallet_id: str
    draft_id: str
    draft_text: str
    doc_name: str
    doc_type: str = "nda"
    jurisdiction: str = "DE"
    tier: str = "FREE"


# ─── LLM Calls ────────────────────────────────────────────────────────────────

def call_claude(system: str, user_message: str) -> tuple[str, int]:
    """Call Anthropic Claude API"""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(500, "ANTHROPIC_API_KEY not configured")

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role": "user", "content": user_message}],
        },
        timeout=60,
    )
    if resp.status_code != 200:
        logger.error(f"Claude API error: {resp.status_code} {resp.text}")
        raise HTTPException(502, f"Claude API error: {resp.status_code}")

    data = resp.json()
    text = data["content"][0]["text"]
    tokens = data.get("usage", {}).get("output_tokens", 0)
    return text, tokens


def call_mistral(system: str, user_message: str) -> tuple[str, int]:
    """Call Mistral API"""
    if not MISTRAL_API_KEY:
        raise HTTPException(500, "MISTRAL_API_KEY not configured")

    resp = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "mistral-small-latest",
            "max_tokens": 4096,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        },
        timeout=60,
    )
    if resp.status_code != 200:
        logger.error(f"Mistral API error: {resp.status_code} {resp.text}")
        raise HTTPException(502, f"Mistral API error: {resp.status_code}")

    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("completion_tokens", 0)
    return text, tokens


def route_and_generate(tier: str, system: str, user_msg: str) -> tuple[str, str, int]:
    """Route to correct LLM and return (text, model_used, tokens)

    CANONICAL STRATEGY (04 Apr 2026):
    - < 500 users: ALL tiers → Claude (Anthropic)
    - ≥ 500 users: FREE/MED → Mistral, HIGH → Claude

    Current: Claude for all (phase 1)
    """
    # Phase 1: Anthropic para todos os tiers até 500 users
    text, tokens = call_claude(system, user_msg)
    return text, "claude-sonnet-4-20250514", tokens


# ─── Endpoints ────────────────────────────────────────────────────────────────

@ai_draft_router.get("/doc-types")
async def get_doc_types():
    """Lista tipos de documentos disponíveis — sem autenticação"""
    return {
        "doc_types": DOC_TYPES,
        "jurisdictions": JURISDICTIONS,
        "routing": {
            "ALL_TIERS": "claude-sonnet-4-20250514 (phase 1: <500 users)",
            "threshold": "≥500 users → FREE/MED=Mistral, HIGH=Claude",
        },
        "constitutional_note": "I9: human approves before generation · I11: auto-sealed after review · G3: all decisions remain human"
    }


@ai_draft_router.post("/generate")
async def generate_draft(req: DraftRequest):
    """
    WINDI LAW — AI Draft Generator

    Pipeline: I9 confirmed (frontend) → LLM → DRAFT_ID → return
    O seal acontece num passo separado (humano revisa primeiro)

    Invariant I9: O frontend JÁ confirmou aprovação humana antes de chamar este endpoint.
    Invariant G3: O humano irá rever e decidir antes de selar.
    """
    # Validate inputs
    if not req.did or not req.wallet_id:
        raise HTTPException(401, "DID e Wallet obrigatórios · I9: identity required")

    if req.doc_type not in DOC_TYPES:
        raise HTTPException(400, f"doc_type inválido. Disponíveis: {list(DOC_TYPES.keys())}")

    if req.jurisdiction not in JURISDICTIONS:
        raise HTTPException(400, f"Jurisdiction inválida. Disponíveis: {JURISDICTIONS}")

    if not req.context or len(req.context.strip()) < 20:
        raise HTTPException(400, "Context muito curto. Forneça detalhes sobre as partes e objectivo.")

    # Build prompts
    system = build_system_prompt(req.doc_type, req.jurisdiction, req.lang)
    doc_label = DOC_TYPES[req.doc_type].get(req.lang.lower(), req.doc_type)

    user_message = f"""Erstelle ein vollständiges {doc_label} für folgende Situation:

{req.context}

Anforderungen:
- Jurisdiction: {req.jurisdiction}
- Sprache: {req.lang}
- Vollständig und professionell
- Alle relevanten Klauseln
- Platzhalter für fehlende Informationen

Erstelle jetzt das vollständige Dokument:"""

    # Generate via routed LLM
    start = time.time()
    draft_text, model_used, tokens = route_and_generate(req.tier, system, user_message)
    elapsed = round(time.time() - start, 2)

    # Generate draft_id (not sealed yet — human reviews first)
    draft_id = f"DRAFT-LAW-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"

    # Preview hash (not final — text may be edited before seal)
    preview_hash = hashlib.sha256(draft_text.encode()).hexdigest()

    logger.info(f"[AI-DRAFT] {draft_id} · {req.doc_type} · {req.jurisdiction} · {model_used} · {tokens}tok · {elapsed}s · DID:{req.did[:12]}...")

    return {
        "draft_id": draft_id,
        "draft_text": draft_text,
        "doc_type": req.doc_type,
        "doc_label": doc_label,
        "jurisdiction": req.jurisdiction,
        "lang": req.lang,
        "model_used": model_used,
        "tokens": tokens,
        "elapsed_seconds": elapsed,
        "preview_hash": preview_hash,
        "status": "DRAFT_READY",
        "next_step": "Human review → confirm → POST /ai-draft/seal",
        "constitutional": {
            "I9": "CONFIRMED — human approved generation",
            "G3": "PENDING — human must review before seal",
            "I11": "PENDING — will be sealed on /seal endpoint",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@ai_draft_router.post("/seal")
async def seal_draft(req: SealRequest):
    """
    WINDI LAW — AI Draft Sealer

    Pipeline: Human reviews draft → confirms → this endpoint seals to Ledger

    Invariant G3: Human confirmed seal (frontend I9 modal already shown)
    Invariant I11: Hash calculado do texto FINAL (após edições do humano)
    """
    if not req.did or not req.wallet_id:
        raise HTTPException(401, "DID e Wallet obrigatórios · G3: identity required for seal")

    if not req.draft_text or len(req.draft_text.strip()) < 50:
        raise HTTPException(400, "draft_text muito curto para selar")

    # Compute FINAL hash (text as reviewed/edited by human)
    final_hash = hashlib.sha256(req.draft_text.encode("utf-8")).hexdigest()

    # Receipt ID
    timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    receipt_id = f"WINDI-LAW-AIDRAFT-{timestamp_str}-{final_hash[:8].upper()}"

    doc_label = DOC_TYPES.get(req.doc_type, {}).get("de", req.doc_type)

    # Seal to Forensic Ledger
    ledger_payload = {
        "id": receipt_id,
        "actor": req.did,
        "app": "windi-law-ai-draft-v1.0",
        "doc_name": req.doc_name,
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content_hash": final_hash,
        "sge_score": 0.95,  # AI-generated legal document, high governance
        "jurisdiction": req.jurisdiction,
        "isp_context": f"AI Draft · {doc_label} · I9+G3 CONFIRMED",
        "declaration": "operator",
        "tags": ["AI-DRAFT", "I9-APPROVED", "G3-CONFIRMED", f"TIER-{req.tier}"],
        "metadata": {
            "draft_id": req.draft_id,
            "tier": req.tier,
            "doc_label": doc_label,
            "invariants": ["I9", "I11", "G3"],
            "eu_ai_act": "Art. 14 — human oversight confirmed",
            "positioning": "Any AI generates. Only WINDI proves."
        },
    }

    try:
        ledger_resp = requests.post(LEDGER_URL, json=ledger_payload, timeout=10)
        ledger_data = ledger_resp.json()
        ledger_ok = ledger_resp.status_code in (200, 201)
    except Exception as e:
        logger.error(f"[AI-DRAFT/SEAL] Ledger error: {e}")
        raise HTTPException(503, f"Ledger unavailable: {e}")

    if not ledger_ok:
        raise HTTPException(502, f"Ledger rejected seal: {ledger_data}")

    verify_url = f"{BASE_URL}/verify-public/?id={receipt_id}"

    logger.info(f"[AI-DRAFT/SEAL] {receipt_id} · {final_hash[:16]}... · DID:{req.did[:12]}... · SEALED ✅")

    return {
        "receipt_id": receipt_id,
        "hash": final_hash,
        "verify_url": verify_url,
        "doc_name": req.doc_name,
        "doc_type": req.doc_type,
        "doc_label": doc_label,
        "jurisdiction": req.jurisdiction,
        "did": req.did,
        "status": "SEALED",
        "constitutional": {
            "I9":  "CONFIRMED — human approved generation",
            "G3":  "CONFIRMED — human approved seal",
            "I11": f"SEALED — {final_hash}",
        },
        "ledger": ledger_data,
        "qr_url": verify_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Any AI can generate a document. Only WINDI can prove it.",
    }


@ai_draft_router.get("/health")
async def ai_draft_health():
    """AI Draft module health check"""
    has_anthropic = bool(ANTHROPIC_API_KEY)
    has_mistral = bool(MISTRAL_API_KEY)

    return {
        "module": "WINDI-LAW AI Draft v1.0.0",
        "status": "healthy" if has_anthropic else "degraded",
        "llm_routing": {
            "ALL_TIERS": f"claude-sonnet-4-20250514 · {'✅' if has_anthropic else '❌ ANTHROPIC_API_KEY missing'}",
            "strategy": "<500 users → Claude all | ≥500 users → FREE/MED=Mistral, HIGH=Claude",
            "phase": "1 (Anthropic only)",
        },
        "pipeline": "INPUT → I9(human) → LLM → DRAFT → G3(human review) → HASH → LEDGER → VERIFY",
        "positioning": "Harvey writes. WINDI proves.",
        "doc_types": len(DOC_TYPES),
        "jurisdictions": JURISDICTIONS,
        "invariants": ["I9", "I11", "G3"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
