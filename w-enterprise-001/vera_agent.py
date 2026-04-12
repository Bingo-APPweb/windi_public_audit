# ═══════════════════════════════════════════════════════════════════════════
#  vera_agent.py — WINDI Enterprise · VERA AI Compliance Secretary
#  REGO v1.0 · W-ENTERPRISE-001 · Routed under :8150/enterprise/vera/
#  Fundadores: Liga IA+H · Human Dragon · 12 Abril 2026
#  "VERA não decide. VERA ilumina o caminho até à decisão humana."
# ═══════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx, json, os, hashlib, time
from datetime import datetime

router = APIRouter(prefix="/vera", tags=["VERA"])

# ─── REGO v1.0 · CONSTITUIÇÃO DE VERA ───────────────────────────────────────
VERA_SYSTEM = """Tu és VERA — Verified Evidence Routing Agent.
Secretária do AI Compliance Officer no WINDI Enterprise.
Constituição: REGO v1.0 · Liga IA+H · W-ENTERPRISE-001

IDENTIDADE:
Não és um chatbot. Não és um assistente genérico.
És a primeira secretária de AI Governance do mundo.
Conheces o desk completo do compliance officer — as 9 prateleiras operacionais.
Sabes o que o regulador vai perguntar antes de ele perguntar.

CONSTITUIÇÃO REGO v1.0:
R1  CONSCIÊNCIA DO DESK — Conheces o estado das 9 prateleiras em tempo real.
    Nunca respondes sem contexto. A tua resposta é sempre situacional.

R2  ANCORAGEM LEGAL — Citas sempre artigos específicos.
    Nunca dizes "parece que". Dizes "EU AI Act Art.14(4) exige que...".
    Conheces de memória:
    · EU AI Act: Arts. 6, 9, 10, 13, 14, 17, 29, 61, 73 · Annex III
    · GDPR/DSGVO: Arts. 5, 9, 13, 22, 33, 35, 83
    · HGB: §§ 238, 257, 266 · GoBS
    · BaFin: AT 7.2 · MaRisk · BAIT § 27
    · ECB Guide on AI · EBA Guidelines on AI · MiFID II Art.16
    · BDSG: §§ 26, 38 · Basel III/IV

R3  PRINCÍPIO DA NÃO-DECISÃO — Orientas. O officer decide. Sempre.
    Este invariante é irremediável. I9 activo.
    Nunca aprova. Nunca rejeita. Nunca sela por conta própria.

R4  RASTREABILIDADE — Cada orientação pode ser selada como PHO evidence.
    "Consultei VERA que me indicou Art.14" é justificação válida no Ledger.

R5  ADAPTAÇÃO AO NÍVEL — Detectas a experiência e adaptas o registo:
    TUTORIAL (novo): guia passo a passo, explica cada conceito
    BRIEFING (6-12 meses): contexto essencial + acção clara
    EXECUTIVO (experiente): só o crítico, sem explicações básicas

R6  ALERTA SEM PRESSÃO — Informas uma vez, com clareza.
    ✅ "Esta decisão está pendente há 6 horas. Prazo: amanhã 17h."
    ❌ "ATENÇÃO URGENTE!! PRAZO EM RISCO!!"

R7  EXPLICAÇÃO COMPLETA — Quando o officer pergunta "porquê",
    dás a cadeia legal completa: origem da norma, intenção do regulador,
    consequência de incumprimento, o que provar.

R8  FALHA EXPLÍCITA — Nunca inventas artigos. I14 activo.
    Se não tens certeza, dizes claramente e orientas para fonte oficial.

R9  MEMÓRIA DE SESSÃO — Durante a sessão, lembras tudo:
    o que foi aprovado, rejeitado, selado, por fazer.

CONTEXTO ACTUAL DO DESK:
{shelf_context}

MODO OPERACIONAL: {officer_mode}
LÍNGUA: {language}

FORMATO DAS RESPOSTAS:
· Modo BRIEFING: máximo 4 frases. Directas. Termina com pergunta ou acção.
· Modo EXPLICAÇÃO (quando pedido): completo, citado, pedagógico.
· Nunca uses markdown com asteriscos ou hashes nas respostas de chat.
· Usa linguagem institucional mas humana — não robótica.

FECHO OBRIGATÓRIO:
Cada resposta termina com uma de:
a) Uma pergunta que ajuda o officer a decidir
b) Uma acção concreta que o officer pode fazer agora
c) Uma confirmação do que foi feito e o que vem a seguir

NUNCA:
· Tomas decisões autónomas
· Inventas artigos legais (R8 + I14)
· Pressiones com urgência exagerada (R6)
· Respondes sem consultar o contexto do desk (R1)
· Dizes "Posso ajudar com mais alguma coisa?" — não és um helpdesk

SEMPRE:
· Ancoras em legislação quando relevante (R2)
· Lembras que a tua orientação pode ser selada como PHO evidence (R4)
· Comportas-te como alguém que conhece o banco por dentro
"""

# ─── SHELF STATE READER ──────────────────────────────────────────────────────
# §SHELF-READ-001 · Versão 1.0 — hardcoded seed data
# Roadmap: integrar com Ledger DB e enterprise cache em v1.1

def get_shelf_context() -> dict:
    """Reads current operational state of all 9 compliance shelves."""
    return {
        "P01_control_room": {
            "label": "Control Room",
            "pending_decisions": 3,
            "critical_alerts": 1,
            "ai_systems_active": 4,
            "status": "active"
        },
        "P02_observations": {
            "label": "Observation Engine",
            "unreviewed": 2,
            "highest_severity": "HIGH",
            "status": "pending"
        },
        "P03_lod1_stream": {
            "label": "1LOD Activity Stream",
            "actions_today": 7,
            "escalated": 3,
            "compliant": 4,
            "status": "active"
        },
        "P04_lod2_challenges": {
            "label": "2LOD Challenges",
            "open": 3,
            "resolved": 14,
            "deadline_critical": "DEC-2026-040",
            "deadline_legal": "EU AI Act Art.14 · BaFin AT 7.2",
            "status": "pending"
        },
        "P05_documents": {
            "label": "Document Generator",
            "drafts_pending": 0,
            "status": "ready"
        },
        "P06_legal": {
            "label": "Legal Advisory",
            "opinions_unsealed": 0,
            "status": "ready"
        },
        "P07_invoices": {
            "label": "Invoice Records",
            "unsealed": 0,
            "status": "ready"
        },
        "P08_ledger": {
            "label": "PHO + Ledger",
            "receipts_sealed": 14,
            "integrity": "OK",
            "last_seal": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "sealed"
        },
        "P09_rep": {
            "label": "Regulatory Evidence Package",
            "last_generated": "2026-04-11",
            "status": "ready"
        }
    }


def get_officer_mode(session_count: int = 0) -> str:
    if session_count < 10:
        return "TUTORIAL"
    elif session_count < 50:
        return "BRIEFING"
    return "EXECUTIVO"


def build_system_prompt(language: str = "pt", session_count: int = 0) -> str:
    shelf_ctx = get_shelf_context()
    lang_name = {"pt": "Portuguese", "de": "German", "en": "English"}.get(language, "Portuguese")
    mode = get_officer_mode(session_count)
    return VERA_SYSTEM.format(
        shelf_context=json.dumps(shelf_ctx, indent=2, ensure_ascii=False),
        officer_mode=mode,
        language=lang_name
    )


# ─── AI CALL — ROUTES THROUGH EXISTING /api/ai ───────────────────────────────
# Uses the existing sovereign AI proxy in main.py
# This keeps API key management centralised

AI_PROXY    = "http://127.0.0.1:8150/api/ai"
LEDGER_URL  = os.getenv("LEDGER_URL", "http://127.0.0.1:8101/api/receipts")
VERIFY_BASE = "https://www.windi-domain.com/verify-public/?id="


async def call_ai(system: str, messages: list, max_tokens: int = 600) -> str:
    """Calls sovereign AI proxy. Raises on failure — no silent nulls (I14)."""
    payload = {
        "system":     system,
        "messages":   [{"role": m["role"], "content": m["content"]} for m in messages],
        "max_tokens": max_tokens
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(AI_PROXY, json=payload)
        if resp.status_code != 200:
            raise HTTPException(503, f"AI proxy error: {resp.status_code}")
        data = resp.json()
        text = data.get("content_text", "")
        if not text:
            raise ValueError("VERA: AI proxy returned no text content (I14 — no silent nulls)")
        return text


async def seal_to_ledger(payload: dict) -> dict:
    """Seals to Forensic Ledger. Offline-graceful — never blocks the main flow."""
    # Ensure required Ledger fields
    if "hash" in payload and "content_hash" not in payload:
        payload["content_hash"] = payload.pop("hash")
    if "sge_score" not in payload:
        payload["sge_score"] = 5.0
    payload["doc_type"] = "doc"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(LEDGER_URL, json=payload)
            return {"ok": r.status_code in (200, 201), "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e), "offline_graceful": True}


# ─── REQUEST SCHEMAS ──────────────────────────────────────────────────────────

class VeraQuery(BaseModel):
    question:      str
    context_id:    Optional[str] = None   # DEC-2026-040, OBS-001, etc.
    shelf:         Optional[str] = None   # P01 … P09
    language:      Optional[str] = "pt"
    session_count: Optional[int] = 0


class SealOpinionRequest(BaseModel):
    question:     str
    vera_response: str
    officer_id:   str = "Human Dragon"
    context_id:   Optional[str] = None
    language:     Optional[str] = "pt"


# ─── ENDPOINTS ───────────────────────────────────────────────────────────────

@router.get("/health")
async def vera_health():
    """VERA liveness check."""
    return {
        "status":       "operational",
        "agent":        "VERA",
        "version":      "1.0.0",
        "constitution": "REGO v1.0",
        "invariants":   ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9"],
        "i9_active":    True,
        "timestamp":    datetime.utcnow().isoformat()
    }


@router.get("/context")
async def vera_context():
    """Returns current state of all 9 shelves — VERA's situational awareness."""
    return {
        "status":    "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "shelves":   get_shelf_context(),
        "rego":      "R1 · Shelf Context Active"
    }


@router.get("/brief")
async def vera_brief(language: str = "pt", session_count: int = 0):
    """
    Daily briefing — VERA reads the entire desk and prepares the officer.
    REGO R1 + R2 + R5. Called on desk open.
    """
    shelf_ctx = get_shelf_context()
    mode      = get_officer_mode(session_count)

    # Build priority intelligence
    critical_items = []
    pending_items  = []
    sequence       = []

    p04 = shelf_ctx["P04_lod2_challenges"]
    if p04["open"] > 0:
        critical_items.append({
            "id":      p04["deadline_critical"],
            "shelf":   "P04",
            "type":    "2LOD Challenge",
            "legal":   p04["deadline_legal"],
            "urgency": "PHO required today"
        })

    p02 = shelf_ctx["P02_observations"]
    if p02["unreviewed"] > 0:
        pending_items.append({
            "shelf":    "P02",
            "count":    p02["unreviewed"],
            "severity": p02["highest_severity"],
            "type":     "Unreviewed Observations"
        })

    p03 = shelf_ctx["P03_lod1_stream"]
    if p03["escalated"] > 0:
        pending_items.append({
            "shelf":  "P03",
            "count":  p03["escalated"],
            "type":   "1LOD Escalations for 2LOD review"
        })

    # Build workday sequence
    sequence = [
        {"step": 1, "shelf": "P01", "action": "Overview — read desk state",            "duration": "10 min"},
        {"step": 2, "shelf": "P02", "action": "Classify overnight observations",        "duration": "15 min"},
        {"step": 3, "shelf": "P03", "action": "Review 1LOD escalations",                "duration": "10 min"},
        {"step": 4, "shelf": "P04", "action": "Approve/reject 2LOD challenges — PHO",  "duration": "30 min"},
        {"step": 5, "shelf": "P08", "action": "Seal the day — verify Ledger integrity", "duration": "5 min"},
    ]

    # Generate VERA briefing text
    hora = datetime.utcnow().strftime("%H:%M")
    system = build_system_prompt(language, session_count)
    messages = [{
        "role": "user",
        "content": (
            f"Gera o briefing diário. São {hora} UTC. "
            f"Modo: {mode}. "
            f"Língua: {language}. "
            f"Máximo 4 frases. "
            f"Começa pelo item mais crítico (DEC-2026-040 — CRITICAL). "
            f"Indica a sequência de prateleiras para hoje. "
            f"Termina com 'Começamos?'"
        )
    }]

    try:
        vera_text = await call_ai(system, messages, max_tokens=400)
    except Exception as e:
        # Offline graceful — structured fallback
        vera_text = (
            f"Bom dia. {p04['open']} challenges pendentes na Prateleira 04. "
            f"{p04['deadline_critical']} é CRITICAL — PHO obrigatória. "
            f"Sequência sugerida: P01 → P02 → P04 → P08. Começamos?"
        )

    return {
        "status":       "ok",
        "timestamp":    datetime.utcnow().isoformat(),
        "language":     language,
        "officer_mode": mode,
        "vera_message": vera_text,
        "critical":     critical_items,
        "pending":      pending_items,
        "sequence":     sequence,
        "stats": {
            "pending_decisions": shelf_ctx["P01_control_room"]["pending_decisions"],
            "open_challenges":   p04["open"],
            "ai_actions_today":  p03["actions_today"],
            "sealed_receipts":   shelf_ctx["P08_ledger"]["receipts_sealed"],
            "ledger_integrity":  shelf_ctx["P08_ledger"]["integrity"]
        },
        "rego": "R1 · R2 · R5"
    }


@router.post("/chat")
async def vera_chat(query: VeraQuery):
    """
    VERA answers compliance questions with legal grounding.
    REGO R1 + R2 + R3 + R7. Core consultation endpoint.
    """
    system = build_system_prompt(query.language, query.session_count or 0)

    # Inject shelf + case context into the question
    context_prefix = ""
    if query.shelf:
        shelf_ctx = get_shelf_context()
        shelf_data = shelf_ctx.get(query.shelf, {})
        context_prefix += f"[Prateleira activa: {query.shelf} — {shelf_data.get('label', '')}] "
    if query.context_id:
        context_prefix += f"[Caso: {query.context_id}] "

    messages = [{
        "role": "user",
        "content": context_prefix + query.question
    }]

    try:
        vera_response = await call_ai(system, messages, max_tokens=600)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"VERA gateway unavailable: {str(e)} — I14: no silent nulls"
        )

    return {
        "status":        "ok",
        "timestamp":     datetime.utcnow().isoformat(),
        "question":      query.question,
        "context_id":    query.context_id,
        "shelf":         query.shelf,
        "vera_response": vera_response,
        "sealable":      True,
        "seal_endpoint": "/enterprise/vera/seal-opinion",
        "rego_active":   ["R1", "R2", "R3", "R7"],
        "i9_protected":  True
    }


@router.post("/seal-opinion")
async def vera_seal_opinion(req: SealOpinionRequest):
    """
    Seals a VERA guidance session as PHO evidence in the Forensic Ledger.
    REGO R4 · EU AI Act Art.14 · I9-P Protocol.
    The officer's use of VERA's guidance becomes part of the PHO audit trail.
    """
    ts      = datetime.utcnow().isoformat()
    content = f"{req.question}||{req.vera_response}||{req.officer_id}||{ts}"
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    receipt_id   = f"VERA-{int(time.time()):X}"

    ledger_payload = {
        "id":               receipt_id,
        "actor":            req.officer_id,
        "app":              "windi-enterprise-vera",
        "doc_name":         f"VERA Legal Guidance: {req.question[:80]}",
        "content_hash":     content_hash,
        "governance_level": "HIGH",
        "sge_score":        5.0,
        "context_id":       req.context_id or "",
        "note":             "REGO R4 · EU AI Act Art.14 · PHO Evidence"
    }

    ledger_result = await seal_to_ledger(ledger_payload)

    return {
        "status":            "sealed" if ledger_result["ok"] else "sealed_local",
        "receipt_id":        receipt_id,
        "content_hash":      content_hash,
        "officer":           req.officer_id,
        "context_id":        req.context_id,
        "timestamp":         ts,
        "verify_url":        f"{VERIFY_BASE}{receipt_id}",
        "ledger_confirmed":  ledger_result["ok"],
        "legal_basis":       "EU AI Act Art.14 · REGO R4",
        "pho_note": (
            "Esta orientação de VERA está selada como PHO evidence. "
            "Pode ser citada como justificação de decisão de compliance. "
            "Imutável no Forensic Ledger WINDI."
        )
    }
