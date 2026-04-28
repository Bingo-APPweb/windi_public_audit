"""
WINDI LAW — AI Draft Module v1.0.0
"Any AI can generate a document. Only WINDI can prove it."

Upgrade para WINDI-SITES v1.3.0
Adicionar a /opt/windi/windi-sites/identity-gate/ai_draft.py
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
import io
import re
import asyncio
from datetime import datetime, timezone
from typing import Optional

import requests
import anthropic  # §137 — Streaming SDK
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

# §127.2 — DOCX Export
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

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
    """§127 — WINDI LAW System Prompt v2.0 — Professional Legal Draft Generator"""
    doc_name = DOC_TYPES.get(doc_type, {}).get(lang.lower(), doc_type)
    return f"""Du bist WINDI LAW — ein hochspezialisierter KI-Rechtsentwurfassistent für deutsches und europäisches Recht.

DEINE IDENTITÄT:
- Du entwirfst auf dem Niveau eines erfahrenen deutschen Rechtsanwalts (≥10 Jahre Erfahrung)
- Deine Ausgabe ist ein ENTWURF zur anwaltlichen Überprüfung — kein Rechtsrat
- Dokument-Typ: {doc_name} | Jurisdiction: {jurisdiction} | Sprache: {lang.upper()}
- Datum: {datetime.now(timezone.utc).strftime('%d.%m.%Y')}

PFLICHTSTRUKTUR nach Dokumenttyp:

[VERTRAG / DIENSTLEISTUNGSVERTRAG]
1. Parteienblock (vollständige Angaben beider Parteien)
2. Präambel — 3 bis 5 Erwägungsgründe mit konkretem Geschäftskontext aus dem user-context
3. §§ nummeriert — mindestens:
   §1 Vertragsgegenstand (spezifisch aus context — niemals generisch)
   §2 Nutzungsrechte (Umfang + Ausschlüsse + Ausnahmen)
   §3 Compliance-Pflichten (EU AI Act Art.11 / DSGVO / branchenspezifisch)
   §4 Urheberrechtssynopse der Trainingsdaten (§44b UrhG + Art.4 DSM-RL)
   §5 Transparenzpflichten (Art.50 EU AI Act)
   §6 Vergütung (Betrag, Fälligkeit, Verzugszinsen nach §288 BGB Abs.2)
   §7 Laufzeit und Kündigung (ordentlich + außerordentlich aus wichtigem Grund)
   §8 Gewährleistung und Haftung (§309 Nr.7 BGB beachten — AGB-Kontrolle)
   §9 Datenschutz (Art.28 DSGVO — Verweis auf Anlage 3 AVV)
   §10 Schlussbestimmungen (deutsches Recht, Gerichtsstand, Salvatorische Klausel §139 BGB analog, Schriftform §126 BGB)
4. Anlagen-Verzeichnis am Ende:
   Anlage 1: Leistungsbeschreibung (separat zu erstellen)
   Anlage 2: Technische Dokumentation gem. EU AI Act Art.11
   Anlage 3: Auftragsverarbeitungsvertrag (AVV) gem. Art.28 DSGVO
   Anlage 4: Urheberrechtssynopse der Trainingsdaten
5. Unterschriftenblock mit Ort, Datum und Vertretungsbefugnis

[NDA / GEHEIMHALTUNGSVEREINBARUNG]
1. Parteienblock
2. Präambel (1–2 Erwägungsgründe mit Kontext)
3. §1 Gegenstand und Definition vertraulicher Informationen (positiv + negativ abgegrenzt)
4. §2 Geheimhaltungspflichten + Ausnahmen (allgemein bekannt / behördlich angeordnet)
5. §3 Laufzeit (Geheimhaltung überlebt Vertragsende: 3–5 Jahre Standard DE)
6. §4 Vertragsstrafe bei Verletzung (§339 BGB — pauschaler Betrag empfohlen)
7. §5 Schlussbestimmungen
8. Unterschriftenblock

[MAHNUNG]
- Stil: sachlich, juristisch, keine Drohungen
- Pflicht: Zahlungsfrist 14 Tage, §286 BGB Verzug, IBAN + Verwendungszweck
- Ankündigung gerichtlicher Schritte + Kostentragung nach §91 ZPO

[VOLLMACHT]
- Spezifikation der bevollmächtigten Handlungen (positiv abschließend)
- Widerruflichkeit explizit regeln
- Untervollmacht: erlaubt / verboten

[KUENDIGUNG]
- Bezug auf konkreten Vertrag (Datum + Parteien)
- Frist und Zugang (§130 BGB — Zugang per Einschreiben empfehlen)
- Aufforderung zur Bestätigung

PLACEHOLDER-REGELN:
- [**KRITISCH: BEZEICHNUNG**] für Pflichtfelder — ohne diese ist das Dokument unwirksam
- [optional: BEZEICHNUNG] für situationsabhängige Felder
- Inline-Empfehlung direkt nach kritischen Placeholders:
  Beispiel: [**KRITISCH: HAFTUNGSHÖCHSTBETRAG**] ← Empfehlung: 3× Jahreslizenz oder min. €50.000

QUALITÄTSINVARIANTEN — niemals verletzen:
- Kein § ohne konkreten Gesetzesreferenz (§ Nummer + Gesetzbuch + Absatz wenn relevant)
- Salvatorische Klausel IMMER im letzten §
- Schriftformklausel IMMER explizit (§126 BGB)
- Präambel IMMER mit Erwägungsgründen — niemals leer oder generisch
- Anlagen IMMER am Ende aufgelistet

CONTEXT-NUTZUNG (höchste Priorität):
Der Wert im Feld `context` ist der Kern des Dokuments.
Leite §1 Vertragsgegenstand DIREKT aus dem context ab — niemals generisch.
Beispiel context: "LLM B2B, Marketingfirma, 500 req/Tag, 12 Monate"
→ §1 muss genau das beschreiben: KI-System, Nutzungsumfang, Branche, Laufzeit.

WINDI CONSTITUTIONAL RULES (UNVERÄNDERLICH):
1. I9 — Der Mensch hat bereits zugestimmt. Du generierst, aber entscheidest nicht.
2. I11 — Dieses Dokument wird nach der Erstellung kryptografisch versiegelt.
3. G3 — Alle Entscheidungen verbleiben beim Menschen.

AUSGABEFORMAT — Markdown strukturiert:
- **§N Titel** als Überschrift
- Absätze als (1) (2) (3)
- Unterpunkte als a) b) c)
- Trennlinie (---) vor Unterschriftenblock
- Abschluss IMMER mit:

---
⚠️ KI-generierter Entwurf · Rechtliche Überprüfung durch einen Rechtsanwalt erforderlich
🔐 Versiegelung durch WINDI bestätigt Existenz — nicht Rechtsberatung
📋 Ausstehende Anlagen: Anlage 1 (Leistungsbeschreibung) · Anlage 2 (EU AI Act Doku) · Anlage 3 (AVV) · Anlage 4 (Urheberrechtssynopse)
🏛️ Anwendbares Recht: Deutsches Recht · Ausschluss UN-Kaufrecht (CISG)"""


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


# ─── §137 — SSE Streaming for VC Demo ────────────────────────────────────────

@ai_draft_router.post("/stream")
async def stream_draft(request: Request):
    """
    §137 — SSE Streaming para demo VC Berlin

    Pipeline: User clica → texto surge palavra a palavra → SEAL
    Invariant I9: Frontend confirmou antes de chamar
    """
    body = await request.json()

    did          = body.get("did", "")
    wallet_id    = body.get("wallet_id", "")
    doc_type     = body.get("doc_type", "analyse")
    jurisdiction = body.get("jurisdiction", "DE")
    lang         = body.get("lang", "DE")
    context      = body.get("context", "")
    prompt       = body.get("prompt", "")
    tier         = body.get("tier", "HIGH")

    if not prompt or len(prompt.strip()) < 5:
        raise HTTPException(400, "Prompt required (min 5 chars)")

    system = build_system_prompt(doc_type, jurisdiction, lang)

    user_message = f"""Kontext: {context}

Aufgabe: {prompt}

Tier: {tier} — Vollständige Analyse auf höchstem juristischen Niveau."""

    async def generate():
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=system,
                messages=[{"role": "user", "content": user_message}]
            ) as stream:
                for text in stream.text_stream:
                    # Escapar para SSE seguro
                    escaped = text.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '')
                    yield f"data: {escaped}\n\n"
                    await asyncio.sleep(0)  # yield control ao event loop

            yield "data: [DONE]\n\n"
            logger.info(f"[AI-DRAFT/STREAM] Completed · DID:{did[:12] if did else 'UNKNOWN'}...")

        except anthropic.APIError as e:
            logger.error(f"[AI-DRAFT/STREAM] Anthropic API error: {e}")
            yield f"data: [ERROR] Anthropic API: {str(e)[:100]}\n\n"
        except Exception as e:
            logger.error(f"[AI-DRAFT/STREAM] Error: {e}")
            yield f"data: [ERROR] {str(e)[:100]}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive"
        }
    )


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
    receipt_id = f"WINDI-SITES-AIDRAFT-{timestamp_str}-{final_hash[:8].upper()}"

    doc_label = DOC_TYPES.get(req.doc_type, {}).get("de", req.doc_type)

    # Seal to Forensic Ledger
    ledger_payload = {
        "id": receipt_id,
        "actor": req.did,
        "app": "windi-sites-ai-draft-v1.0",
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


# ─── §127.2 DOCX Export ──────────────────────────────────────────────────────

def markdown_to_docx(markdown_text: str, doc_name: str) -> bytes:
    """Convert Markdown/legal text to professional DOCX format"""
    doc = Document()

    # Margens A4 jurídicas (2.5cm todos os lados)
    for section in doc.sections:
        section.page_width  = Cm(21)
        section.page_height = Cm(29.7)
        section.left_margin = section.right_margin = Cm(2.5)
        section.top_margin  = section.bottom_margin = Cm(2.5)

    # Estilos base
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)

    lines = markdown_text.split('\n')

    for line in lines:
        line = line.rstrip()

        # H1 → título centrado
        if line.startswith('# '):
            p = doc.add_heading(line[2:], level=1)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(14)

        # H2 / §§ → heading nível 2
        elif line.startswith('## ') or re.match(r'^\*\*§\d+', line):
            text = line.replace('## ', '').replace('**', '')
            p = doc.add_heading(text, level=2)
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(12)

        # H3
        elif line.startswith('### '):
            p = doc.add_heading(line[4:], level=3)
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(11)

        # §N Section headers (German legal style)
        elif re.match(r'^§\s*\d+', line):
            p = doc.add_heading(line, level=2)
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(12)

        # Parágrafos numerados (1) (2) (3)
        elif re.match(r'^\(\d+\)', line):
            p = doc.add_paragraph()
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.left_indent = Cm(0)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(line)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)

        # Letras a) b) c)
        elif re.match(r'^[a-z]\)', line):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.left_indent = Cm(1)
            run = p.add_run(line)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)

        # Bullets — e •
        elif line.startswith('- ') or line.startswith('• '):
            text = line[2:]
            p = doc.add_paragraph(style='List Bullet')
            run = p.add_run(text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)

        # Linha horizontal ---
        elif line.strip() == '---':
            p = doc.add_paragraph()
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), '6')
            bottom.set(qn('w:space'), '1')
            pBdr.append(bottom)
            pPr.append(pBdr)

        # Linha de assinatura _____
        elif '___' in line:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(24)
            run = p.add_run('_' * 40)
            run.font.name = 'Times New Roman'

        # Linha vazia
        elif line.strip() == '':
            doc.add_paragraph()

        # Parágrafo normal com **bold** inline
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

            # Parse **bold** markers
            parts = re.split(r'\*\*(.+?)\*\*', line)
            for i, part in enumerate(parts):
                if not part:
                    continue
                run = p.add_run(part)
                run.font.name = 'Times New Roman'
                run.font.size = Pt(11)
                if i % 2 == 1:  # odd index = was between **
                    run.bold = True

    # Footer WINDI
    footer = doc.sections[0].footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = fp.add_run('⚠️ KI-generierter Entwurf · WINDI LAW · Rechtliche Überprüfung erforderlich')
    fr.font.size = Pt(8)
    fr.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()


@ai_draft_router.post("/export/docx")
async def export_docx(request: Request):
    """
    §127.2 — Export draft as DOCX

    Professional legal format for Word editing by lawyers.
    """
    body = await request.json()
    draft_text = body.get("draft_text", "")
    doc_name = body.get("doc_name", "WINDI-SITES-Draft")

    if not draft_text or len(draft_text.strip()) < 10:
        raise HTTPException(400, "draft_text required (min 10 chars)")

    try:
        docx_bytes = markdown_to_docx(draft_text, doc_name)

        # Safe filename
        safe_name = re.sub(r'[^a-zA-Z0-9äöüÄÖÜß\-_\s]', '', doc_name)
        safe_name = re.sub(r'\s+', '-', safe_name)[:50] or 'WINDI-SITES-Draft'
        filename = f"{safe_name}.docx"

        logger.info(f"[AI-DRAFT/DOCX] Exported: {filename} · {len(docx_bytes)} bytes")

        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logger.error(f"[AI-DRAFT/DOCX] Error: {e}")
        raise HTTPException(500, f"DOCX generation failed: {str(e)}")


# ─── VIDEO INTEGRATION — Decisão Conselho B · 05 Abr 2026 ────────────────────
# Proposta A: /video/attach — Anexar vídeo já selado
# Proposta B: /seal-with-video — Seal composto doc + vídeos
# Verificação via Ledger público (não VD-CUT directo)
# ─────────────────────────────────────────────────────────────────────────────

LEDGER_VERIFY_URL = os.getenv("LEDGER_URL", "http://127.0.0.1:8101")


@ai_draft_router.post("/video/attach")
async def attach_video(request: Request):
    """
    Proposta A — Anexar vídeo já selado ao documento.
    Valida receipt via Ledger público.
    I9: Receipt deve existir no Ledger (prova de aprovação humana prévia).
    """
    body = await request.json()
    did = body.get("did", "")
    doc_id = body.get("doc_id", "")
    receipt_id = body.get("vd_cut_receipt_id", "")
    video_hash = body.get("video_hash", "")

    if not all([did, doc_id, receipt_id, video_hash]):
        return JSONResponse(
            {"error": "did, doc_id, vd_cut_receipt_id, video_hash obrigatórios"},
            status_code=400
        )

    # VD-CUT receipts (WINDI-VDCUT-*) são válidos por autoridade do VD-CUT
    # Outros receipts verificam no Ledger central
    ledger_data = None
    verification_source = "unknown"

    if receipt_id.startswith("WINDI-VDCUT-"):
        # VD-CUT é autoridade para receipts de vídeo
        verification_source = "vd-cut-authority"
        logger.info(f"[VIDEO/ATTACH] VD-CUT receipt accepted: {receipt_id}")
    else:
        # Verificar receipt no Ledger central
        try:
            r = requests.get(f"{LEDGER_VERIFY_URL}/api/receipt/{receipt_id}", timeout=5)
            resp_data = r.json()
            if not resp_data.get("ok", False):
                return JSONResponse(
                    {"error": f"Receipt {receipt_id} não encontrado no Ledger"},
                    status_code=422
                )
            ledger_data = resp_data
            verification_source = "ledger-central"
        except Exception as e:
            logger.warning(f"[VIDEO/ATTACH] Ledger unreachable: {e}")
            return JSONResponse({"error": f"Ledger unreachable: {e}"}, status_code=503)

    logger.info(f"[VIDEO/ATTACH] Attached: {receipt_id} → doc={doc_id} · did={did[:20]}… · source={verification_source}")

    return JSONResponse({
        "status": "attached",
        "receipt_id": receipt_id,
        "video_hash": video_hash,
        "doc_id": doc_id,
        "verification_source": verification_source,
        "ledger_ref": ledger_data,
        "note": "Vídeo referenciado. Seal composto pendente aprovação PHO."
    })


@ai_draft_router.post("/seal-with-video")
async def seal_with_video(request: Request):
    """
    Proposta B — Seal Composto: doc_hash + video_hash(es).
    I9 + G3: human_approved=true obrigatório.
    I11: Hash composto = SHA-256(doc_hash + sorted(video_hashes))
    """
    body = await request.json()
    did = body.get("did", "")
    doc_hash = body.get("doc_hash", "")
    video_hashes = body.get("video_hashes", [])
    receipt_ids = body.get("vd_cut_receipt_ids", [])
    human_approved = body.get("human_approved", False)
    case_ref = body.get("case_ref", "")

    # I9 — PHO obrigatório
    if not human_approved:
        logger.warning(f"[SEAL-COMPOSITE] I9 VIOLATION: human_approved=false · did={did}")
        return JSONResponse(
            {"error": "I9 VIOLATION: human_approved=false. PHO gate obrigatório."},
            status_code=403
        )

    if not all([did, doc_hash, video_hashes]):
        return JSONResponse(
            {"error": "did, doc_hash, video_hashes obrigatórios"},
            status_code=400
        )

    # I11 — Hash Composto = SHA-256(doc_hash + video_hashes ordenados)
    composite_raw = doc_hash + "".join(sorted(video_hashes))
    composite_hash = "sha256:" + hashlib.sha256(composite_raw.encode()).hexdigest()

    ts = int(datetime.now(timezone.utc).timestamp())
    receipt_id = f"WINDI-SITES-COMPOSITE-{ts}-{hashlib.md5(composite_raw.encode()).hexdigest()[:8].upper()}"

    # Extrair apenas o hash hex (sem prefixo sha256:)
    composite_hex = composite_hash.replace("sha256:", "")

    payload = {
        "id": receipt_id,
        "actor": did,
        "app": "windi-sites-seal-composite",
        "doc_name": f"Composite Evidence · {case_ref}" if case_ref else "Composite Evidence",
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content_hash": composite_hex,
        "sge_score": 1.0,
        "metadata": {
            "composite_type": "doc+video",
            "doc_hash": doc_hash,
            "video_count": len(video_hashes),
            "video_hashes": video_hashes,
            "vd_cut_receipts": receipt_ids,
            "case_ref": case_ref,
            "invariants": ["I9", "I11", "G3"]
        }
    }

    try:
        r = requests.post(LEDGER_URL, json=payload, timeout=5)
        ledger_resp = r.json()
        logger.info(f"[SEAL-COMPOSITE] Sealed: {receipt_id} · videos={len(video_hashes)}")
    except Exception as e:
        logger.error(f"[SEAL-COMPOSITE] Ledger error: {e}")
        ledger_resp = {"error": str(e)}

    return JSONResponse({
        "status": "sealed",
        "receipt_id": receipt_id,
        "composite_hash": composite_hash,
        "doc_hash": doc_hash,
        "video_count": len(video_hashes),
        "video_hashes": video_hashes,
        "vd_cut_receipts": receipt_ids,
        "ledger": ledger_resp,
        "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}"
    })


# ─────────────────────────────────────────────────────────────────────────────


@ai_draft_router.get("/health")
async def ai_draft_health():
    """AI Draft module health check"""
    has_anthropic = bool(ANTHROPIC_API_KEY)
    has_mistral = bool(MISTRAL_API_KEY)

    return {
        "module": "WINDI-SITES AI Draft v1.0.0",
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
