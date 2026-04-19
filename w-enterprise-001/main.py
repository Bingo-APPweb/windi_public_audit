"""
W-ENTERPRISE-001 · main.py — COMPLETE v3.1 + VERA
Port: 8150 · Path: /opt/windi/w-enterprise-001/
Deployed: 12 Apr 2026 · VERA: 12 Apr 2026

Routes:
  GET  /              → static dashboard (index.html)
  GET  /health        → service health
  POST /api/ai        → sovereign AI proxy (server-side key)
  GET  /api/decisions → decision list
  POST /api/pho/approve → PHO approval + Ledger seal
  POST /api/generate  → document generator
  POST /api/analyse   → observation engine (vision)
  POST /api/legal     → legal advisory (multi-turn)
  POST /api/invoice   → invoice seal
  POST /api/rep       → regulatory evidence package seal
  GET  /api/audit     → audit log

VERA Routes (via vera_agent.py):
  GET  /enterprise/vera/health      → VERA liveness
  GET  /enterprise/vera/context     → 9 shelves state
  GET  /enterprise/vera/brief       → daily briefing
  POST /enterprise/vera/chat        → contextual Q&A
  POST /enterprise/vera/seal-opinion → seal guidance as PHO

Invariants: I1 · I9 · I11 · I14
VERA Constitution: REGO v1.0 (R1-R9)
"""

import os, time, json, hashlib, uuid, logging, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any, List
from dotenv import load_dotenv

# §191-B — Genesis DB for DID existential validation
GENESIS_DB_PATH = Path("/opt/windi/did-genesis/did_genesis.db")

# Load .env before reading any env vars
load_dotenv(Path(__file__).parent / ".env")

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator

# ── VERA Agent Import ─────────────────────────────────────────────────────
from vera_agent import router as vera_router

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [W-ENT] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)
log = logging.getLogger("windi-enterprise")

# ── Canvas Integration §166 ───────────────────────────────────────────────
try:
    from canvas_integration import (
        enterprise_generate_cover,
        enterprise_generate_pho_cert
    )
    CANVAS_AVAILABLE = True
    log.info("[CANVAS] W-CANVAS-001 integration loaded")
except ImportError as e:
    CANVAS_AVAILABLE = False
    log.warning(f"[CANVAS] Integration unavailable: {e}")

# ── Config ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_MODEL          = os.getenv("AI_MODEL", "claude-sonnet-4-20250514")
AI_MAX_TOKENS     = int(os.getenv("AI_MAX_TOKENS", "1000"))
LEDGER_URL        = os.getenv("LEDGER_URL", "http://127.0.0.1:8101/api/receipts")
SERVICE_VERSION   = "3.1.0"
STATIC_DIR        = Path(__file__).parent / "static"

# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="W-Enterprise-001",
    version=SERVICE_VERSION,
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.windi-domain.com", "https://windi-domain.com", "http://localhost:8150"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# ── VERA Router ───────────────────────────────────────────────────────────
app.include_router(vera_router)

# ── VERA v1.2 — Sovereign Instructor + Routing + IAT-001 + DID Gate ───────
try:
    from routing_engine import create_routing_router
    from agent_transfer_protocol import create_context_router
    from vera_instructor import create_instructor_router
    from vera_did_gate import create_did_gate_router

    app.include_router(create_routing_router())
    app.include_router(create_context_router())
    app.include_router(create_instructor_router())
    app.include_router(create_did_gate_router())

    log.info("[VERA v1.2] Routing Engine: LOADED")
    log.info("[VERA v1.2] IAT-001 Protocol: LOADED")
    log.info("[VERA v1.2] Instructor Engine: LOADED")
    log.info("[VERA v1.2] DID Gate: LOADED — EVANGELHO ACTIVO")
    log.info("[VERA v1.2] REGO v1.2 · R10 + R11 + R12 + 3 LEIS DID: ACTIVE")
except Exception as e:
    log.warning(f"[VERA v1.2] Partial load — some modules unavailable: {e}")
    log.info("[VERA v1.2] Core VERA v1.1 still operational — I14 declared")

# ── Static files ──────────────────────────────────────────────────────────
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ════════════════════════════════════════════════════════
#  §191-B — DID EXISTENTIAL VALIDATION
# ════════════════════════════════════════════════════════
def did_exists_in_genesis(did: str) -> bool:
    """
    §191-B FIX 1: Query Genesis DB to verify DID actually exists.
    Returns True if DID is found and active in Genesis registry.
    """
    if not GENESIS_DB_PATH.exists():
        return True  # Graceful degradation if Genesis unavailable

    try:
        conn = sqlite3.connect(str(GENESIS_DB_PATH), timeout=3)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM identities WHERE LOWER(did) = LOWER(?) AND status = 'active' LIMIT 1",
            (did,)
        )
        exists = cursor.fetchone() is not None
        if not exists:
            cursor.execute(
                "SELECT 1 FROM did_aliases WHERE LOWER(alias_actor) = LOWER(?) AND status = 'active' LIMIT 1",
                (did,)
            )
            exists = cursor.fetchone() is not None
        conn.close()
        return exists
    except Exception:
        return True  # Fail open


# ════════════════════════════════════════════════════════
#  SCHEMAS
# ════════════════════════════════════════════════════════
class AIMessage(BaseModel):
    role: str
    content: Any  # str or list (vision)

class AIRequest(BaseModel):
    system:     Optional[str]        = None
    messages:   List[AIMessage]
    max_tokens: Optional[int]        = None
    model:      Optional[str]        = None

class PHOApproval(BaseModel):
    """
    §191-A + §191-B: PHO Approval requires sovereign identity that EXISTS.
    "Human decides" = verified human with DID in Genesis, not anonymous.
    Art. 14 EU AI Act.
    """
    decision_id: str
    actor:       str  # REQUIRED — no default, DID validation below
    note:        Optional[str] = None

    @validator('actor')
    def actor_must_be_valid_did(cls, v):
        """§191-A + §191-B: Lei I — 'Human decides' requires verifiable, EXISTING identity."""
        if not v or not v.strip():
            raise ValueError('[I9] actor required — PHO approval requires identity')
        v = v.strip()
        forbidden = {"anon", "anonymous", "unknown", "system", "bot", "test"}
        if v.lower() in forbidden:
            raise ValueError(f'[I9] actor "{v}" forbidden — use DID (did:windi:*) or email')
        if not (v.startswith("did:windi:") or ("@" in v and "." in v)):
            raise ValueError('[I9] actor must be DID (did:windi:*) or email — Art. 14 EU AI Act')

        # §191-B FIX 1: DID Existential Validation
        if v.startswith("did:windi:"):
            if not did_exists_in_genesis(v):
                raise ValueError(f'[I-XVI] actor DID not found in Genesis Registry — Lei I · {v}')

        return v

class DocGenRequest(BaseModel):
    doc_type:     str   # privacy_policy | ai_risk | dpia | audit_report | compliance_policy | gdpr_notice
    company:      str
    jurisdiction: str   # DE | EU | PT | INT
    doc_language: str   # de | en | pt
    context:      Optional[str] = ""
    actor:        str = "Human Dragon"

class ObsRequest(BaseModel):
    obs_type:    str   # camera | document | incident | meeting | system | financial
    description: str
    severity:    str   # low | medium | high | critical
    location:    Optional[str] = ""
    image_b64:   Optional[str] = None  # base64 jpeg/png
    actor:       str = "Human Dragon"

class LegalRequest(BaseModel):
    question:    str
    history:     Optional[List[dict]] = []
    language:    str = "en"  # de | en | pt
    actor:       str = "Human Dragon"

class InvoiceRequest(BaseModel):
    invoice_number: str
    from_name:      str
    from_vat:       str
    to_name:        str
    to_vat:         Optional[str] = ""
    to_address:     Optional[str] = ""
    date:           str
    due_date:       str
    lines:          List[dict]   # [{desc, qty, price}]
    notes:          Optional[str] = ""
    actor:          str = "Human Dragon"

class REPRequest(BaseModel):
    decisions:    List[dict]
    pho_receipts: List[dict]
    audit_log:    List[dict]
    actor:        str = "Human Dragon"


# ════════════════════════════════════════════════════════
#  UTILITIES
# ════════════════════════════════════════════════════════
def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def receipt_id(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000):X}"[-16:]

async def seal_ledger(payload: dict) -> dict:
    """Send receipt to Forensic Ledger :8101. Offline-graceful — never blocks."""
    # Ensure required Ledger fields
    if "hash" in payload and "content_hash" not in payload:
        payload["content_hash"] = payload.pop("hash")
    if "sge_score" not in payload:
        payload["sge_score"] = 5.0  # Default neutral score
    # Ledger only accepts "doc" as doc_type (canonical WINDI format)
    payload["doc_type"] = "doc"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(LEDGER_URL, json=payload)
            result = r.json() if r.status_code in (200, 201) else {"sealed": False, "error": r.status_code}
            if r.status_code in (200, 201):
                log.info(f"[LEDGER] Sealed {payload.get('id','?')} → {r.status_code}")
            else:
                log.warning(f"[LEDGER] Failed {payload.get('id','?')} → {r.status_code}: {r.text[:100]}")
            return result
    except Exception as e:
        log.warning(f"Ledger offline: {e}")
        return {"sealed": False, "error": "ledger_offline"}

async def call_anthropic(system: str, messages: list, max_tokens: int = None, model: str = None) -> str:
    """Server-side Anthropic call — API key never leaves backend."""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(503, "ANTHROPIC_API_KEY not set in .env")
    payload = {
        "model": model or AI_MODEL,
        "max_tokens": max_tokens or AI_MAX_TOKENS,
        "system": system,
        "messages": messages,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        )
    if resp.status_code != 200:
        raise HTTPException(502, f"Anthropic error {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    return data.get("content", [{}])[0].get("text", "")


# ════════════════════════════════════════════════════════
#  IN-MEMORY STORES (production: replace with SQLite)
# ════════════════════════════════════════════════════════
DECISIONS_DB = [
    {"id":"DEC-2026-041","title":"Customer segmentation AI deployment","system":"Guardian","risk":"HIGH","date":"2026-04-12","status":"pending","desc":"Deploy ML model for automated customer risk scoring. Affects ~12.000 customers."},
    {"id":"DEC-2026-040","title":"Automated sanctions screening update","system":"Witness","risk":"CRITICAL","date":"2026-04-11","status":"pending","desc":"Update real-time sanctions list processing. OFAC + EU sanctions databases."},
    {"id":"DEC-2026-039","title":"ESG compliance report generation","system":"Architect","risk":"MEDIUM","date":"2026-04-10","status":"pending","desc":"AI-generated quarterly ESG compliance report for regulatory submission to BaFin."},
    {"id":"DEC-2026-038","title":"GDPR consent management platform","system":"Guardian","risk":"HIGH","date":"2026-04-09","status":"approved","receipt":"BD09970F","hash":"4a2b8c91"},
    {"id":"DEC-2026-037","title":"Internal audit trail automation","system":"Witness","risk":"LOW","date":"2026-04-08","status":"approved","receipt":"42B5CE89","hash":"7f3d1a05"},
]

PHO_DB = [
    {"id":"BD09970F","decision":"DEC-2026-038","actor":"Human Dragon","date":"2026-04-09T14:32:11Z","hash":"4a2b8c91d3e7f"},
    {"id":"42B5CE89","decision":"DEC-2026-037","actor":"Human Dragon","date":"2026-04-08T09:15:44Z","hash":"7f3d1a0529bc4"},
]

AUDIT_DB = []


# ════════════════════════════════════════════════════════
#  ROUTES — STATIC + HEALTH
# ════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return HTMLResponse(content=index.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>W-Enterprise-001</h1><p>static/index.html not found</p>", status_code=503)


@app.get("/desk", response_class=HTMLResponse)
@app.get("/desk.html", response_class=HTMLResponse)
async def desk_page():
    """
    Full Enterprise Desk with VERA Chat Panel.
    §186 · VERA v1.2 · Erdbeere Protocol · 9 Shelves
    """
    desk = STATIC_DIR / "desk.html"
    if desk.exists():
        return HTMLResponse(content=desk.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>W-Enterprise-001</h1><p>desk.html not found</p>", status_code=503)


@app.get("/operator", response_class=HTMLResponse)
async def operator_page():
    """
    Capacity Amplifier Module — Operator of Verifiable Systems (OVS)
    Standalone page for Berlin pitch and onboarding.
    §160 · F1 · Trilingual (PT/DE/EN) · NOIR/KLAR
    """
    operator = STATIC_DIR / "operator.html"
    if operator.exists():
        return HTMLResponse(content=operator.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>W-Enterprise-001</h1><p>operator.html not found</p>", status_code=503)


@app.get("/health")
async def health():
    return {
        "service":    "W-Enterprise-001",
        "version":    SERVICE_VERSION,
        "status":     "operational",
        "port":       8150,
        "ledger":     LEDGER_URL,
        "ai_model":   AI_MODEL,
        "ai_ready":   bool(ANTHROPIC_API_KEY),
        "invariants": ["I1","I9","I11","I14"],
        "timestamp":  now_iso(),
    }


# ════════════════════════════════════════════════════════
#  ROUTE — SOVEREIGN AI PROXY
# ════════════════════════════════════════════════════════
@app.post("/api/ai")
async def sovereign_ai(req: AIRequest):
    """
    Sovereign AI proxy. API key stays server-side — never in browser.
    Invariant I9: prompt passed through unchanged, no autonomous escalation.
    Invariant I14: Explicit Failure — errors surface, no silent nulls.
    """
    msgs = []
    for m in req.messages:
        if isinstance(m.content, str):
            msgs.append({"role": m.role, "content": m.content})
        elif isinstance(m.content, list):
            msgs.append({"role": m.role, "content": m.content})
        else:
            msgs.append({"role": m.role, "content": str(m.content)})

    text = await call_anthropic(
        system     = req.system or "",
        messages   = msgs,
        max_tokens = req.max_tokens,
        model      = req.model,
    )

    # Log to audit
    AUDIT_DB.insert(0, {
        "event": f"AI Proxy Call: {len(text)} chars",
        "module": "AI",
        "ts": now_iso()[:16],
        "receipt": None
    })

    log.info(f"[AI] {len(text)} chars returned")
    return {"content_text": text, "model": req.model or AI_MODEL}


# ════════════════════════════════════════════════════════
#  ROUTE — DECISIONS + PHO
# ════════════════════════════════════════════════════════
@app.get("/api/decisions")
async def get_decisions():
    return {"decisions": DECISIONS_DB, "pho_receipts": PHO_DB}

@app.post("/api/pho/approve")
async def pho_approve(body: PHOApproval):
    dec = next((d for d in DECISIONS_DB if d["id"] == body.decision_id), None)
    if not dec:
        raise HTTPException(404, f"Decision {body.decision_id} not found")
    if dec["status"] == "approved":
        raise HTTPException(409, "Already approved")

    h = sha256(body.decision_id + (body.note or "") + now_iso())
    rid = receipt_id("PHO")
    dec["status"]  = "approved"
    dec["receipt"] = rid
    dec["hash"]    = h[:8]
    entry = {"id": rid, "decision": body.decision_id, "actor": body.actor, "date": now_iso(), "hash": h[:13]}
    PHO_DB.insert(0, entry)
    AUDIT_DB.insert(0, {"event": f"PHO Approved: {dec['title']}", "module": "DECISIONS", "ts": now_iso()[:16], "receipt": rid})

    ledger = await seal_ledger({
        "id": rid, "actor": body.actor, "app": "windi-enterprise-decisions",
        "doc_name": dec["title"], "doc_type": "decision",
        "governance_level": "HIGH", "hash": h,
        "note": f"PHO approval · {body.note or 'no note'} · EU AI Act Art.14"
    })
    log.info(f"[PHO] Approved {body.decision_id} → {rid}")
    return {"receipt_id": rid, "hash": h[:8], "ledger": ledger}


# ════════════════════════════════════════════════════════
#  ROUTE — DOCUMENT GENERATOR
# ════════════════════════════════════════════════════════
DOC_TYPE_LABELS = {
    "privacy_policy":    "Privacy Policy / Datenschutzerklärung (GDPR Art.13)",
    "ai_risk":           "AI Risk Assessment (EU AI Act Art.9)",
    "dpia":              "Data Protection Impact Assessment — DPIA (GDPR Art.35)",
    "audit_report":      "Internal Audit Report",
    "compliance_policy": "Compliance Policy",
    "gdpr_notice":       "GDPR Breach Notification (GDPR Art.33/34)",
}

@app.post("/api/generate")
async def generate_document(body: DocGenRequest):
    label   = DOC_TYPE_LABELS.get(body.doc_type, body.doc_type)
    lang    = {"de":"German","en":"English","pt":"Portuguese"}.get(body.doc_language, "English")
    context = body.context or "Standard corporate compliance document."

    system = f"""You are WINDI's AI Compliance Expert. Generate a professional {label} for {body.company}.
Language: {lang}. Jurisdiction: {body.jurisdiction}. Legal basis: GDPR/DSGVO, EU AI Act, HGB (as applicable).
Return ONLY valid JSON (no markdown, no preamble):
{{"title":"...","date":"{datetime.now().date()}","company":"{body.company}","jurisdiction":"{body.jurisdiction}","type":"{body.doc_type}","sections":[{{"heading":"...","content":"..."}}],"legal_bases":["..."],"summary":"..."}}
Include 4-6 sections with realistic, legally-grounded content (3-5 sentences each)."""

    raw = await call_anthropic(system=system, messages=[{"role":"user","content":f"Generate the {label}. Context: {context}"}])
    try:
        doc = json.loads(raw.replace("```json","").replace("```","").strip())
    except Exception:
        doc = {"title": label, "sections": [{"heading":"Content","content": raw[:800]}], "legal_bases":[], "summary":"", "company": body.company, "date": str(datetime.now().date())}

    doc_hash = sha256(json.dumps(doc))
    rid = receipt_id("DOC")
    AUDIT_DB.insert(0, {"event": f"Document Generated: {doc.get('title','—')}", "module":"DOCS", "ts": now_iso()[:16], "receipt": rid})
    ledger = await seal_ledger({
        "id": rid, "actor": body.actor, "app": "windi-enterprise-docs",
        "doc_name": doc.get("title", label), "doc_type": "document",
        "governance_level": "HIGH", "hash": doc_hash,
    })
    log.info(f"[DOC] Generated {body.doc_type} for {body.company}")
    return {"doc": doc, "hash": doc_hash, "receipt_id": rid, "ledger": ledger}


# ════════════════════════════════════════════════════════
#  ROUTE — OBSERVATION ENGINE
# ════════════════════════════════════════════════════════
@app.post("/api/analyse")
async def analyse_observation(body: ObsRequest):
    lang = {"de":"German","en":"English","pt":"Portuguese"}.get("en","English")

    system = f"""You are WINDI's AI Compliance Observer. Analyse the compliance situation described.
Return ONLY valid JSON (no markdown):
{{"title":"...","type":"{body.obs_type}","location":"{body.location or 'Not specified'}","severity":"{body.severity.upper()}","ai_severity":"LOW|MEDIUM|HIGH|CRITICAL","summary":"...","findings":[{{"label":"...","value":"..."}}],"recommendations":["..."],"legal_refs":["..."],"requires_pho":true|false}}
Language: {lang}. Be specific and legally grounded. Include 3-5 findings, 3-5 recommendations."""

    # Build message — include image if present
    if body.image_b64:
        user_content = [
            {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data": body.image_b64}},
            {"type":"text","text":f"Compliance observation.\nType: {body.obs_type}\nLocation: {body.location}\nSeverity: {body.severity.upper()}\nDescription: {body.description}"}
        ]
    else:
        user_content = f"Compliance observation.\nType: {body.obs_type}\nLocation: {body.location or '—'}\nSeverity: {body.severity.upper()}\nDescription: {body.description or 'General compliance assessment requested.'}"

    raw = await call_anthropic(system=system, messages=[{"role":"user","content":user_content}])
    try:
        obs = json.loads(raw.replace("```json","").replace("```","").strip())
    except Exception:
        obs = {"title":"Observation Report","summary":raw[:500],"findings":[],"recommendations":[],"ai_severity":body.severity.upper(),"requires_pho":False}

    obs_hash = sha256(json.dumps(obs) + now_iso())
    rid = receipt_id("OBS")
    sev = obs.get("ai_severity", body.severity.upper())
    gov = "HIGH" if sev in ("HIGH","CRITICAL") else "MEDIUM"
    AUDIT_DB.insert(0, {"event": f"Observation Analysed: {obs.get('title','—')}", "module":"OBS", "ts": now_iso()[:16], "receipt": rid})
    ledger = await seal_ledger({
        "id": rid, "actor": body.actor, "app": "windi-enterprise-observations",
        "doc_name": obs.get("title","Observation"), "doc_type": "observation",
        "governance_level": gov, "hash": obs_hash,
    })
    log.info(f"[OBS] Analysed {body.obs_type} → severity {sev}")
    return {"observation": obs, "hash": obs_hash, "receipt_id": rid, "ledger": ledger, "requires_pho": obs.get("requires_pho", sev in ("HIGH","CRITICAL"))}


# ════════════════════════════════════════════════════════
#  ROUTE — LEGAL ADVISORY
# ════════════════════════════════════════════════════════
@app.post("/api/legal")
async def legal_advisory(body: LegalRequest):
    lang = {"de":"German","en":"English","pt":"Portuguese"}.get(body.language,"English")

    system = f"""You are WINDI's AI Legal Compliance Advisor. Analyse legal questions under German/EU law.
Applicable law: HGB, DSGVO/GDPR, EU AI Act, BGB, KWG, MiFID II as applicable.
Return ONLY valid JSON (no markdown):
{{"answer":"...","risk_level":"LOW|MEDIUM|HIGH","legal_refs":["..."],"action_required":true|false,"disclaimer":"Not legally binding. Consult qualified lawyer for high-impact decisions."}}
Language: {lang}. Cite specific articles. 3-5 sentences. Professional tone."""

    history = body.history or []
    msgs = history + [{"role":"user","content":body.question}]

    raw = await call_anthropic(system=system, messages=msgs)
    try:
        res = json.loads(raw.replace("```json","").replace("```","").strip())
    except Exception:
        res = {"answer": raw[:500], "risk_level":"MEDIUM","legal_refs":[],"action_required":False,"disclaimer":"Not legally binding."}

    AUDIT_DB.insert(0, {"event": f"Legal Query: {body.question[:60]}…", "module":"LEGAL", "ts": now_iso()[:16], "receipt": None})
    log.info(f"[LEGAL] Query answered · risk={res.get('risk_level','—')}")
    return {"response": res, "model": AI_MODEL}


# ════════════════════════════════════════════════════════
#  ROUTE — INVOICE SEAL
# ════════════════════════════════════════════════════════
@app.post("/api/invoice")
async def seal_invoice(body: InvoiceRequest):
    subtotal = sum(l.get("qty",1) * l.get("price",0) for l in body.lines)
    vat      = round(subtotal * 0.19, 2)
    total    = round(subtotal + vat, 2)
    payload  = {
        "number": body.invoice_number, "from": body.from_name, "to": body.to_name,
        "lines": body.lines, "subtotal": subtotal, "vat": vat, "total": total,
        "date": body.date, "due": body.due_date,
    }
    inv_hash = sha256(json.dumps(payload, sort_keys=True))
    rid = receipt_id("INV")
    AUDIT_DB.insert(0, {"event": f"Invoice Sealed: {body.invoice_number} — {body.to_name}", "module":"INVOICES", "ts": now_iso()[:16], "receipt": rid})
    ledger = await seal_ledger({
        "id": rid, "actor": body.actor, "app": "windi-enterprise-invoices",
        "doc_name": f"Invoice {body.invoice_number} — {body.to_name}",
        "doc_type": "invoice", "governance_level": "MEDIUM", "hash": inv_hash,
        "note": f"HGB §257 · Total: {total} EUR · VAT: {vat} EUR"
    })
    log.info(f"[INV] Sealed {body.invoice_number} → {rid}")
    return {"receipt_id": rid, "hash": inv_hash[:8], "total": total, "vat": vat, "subtotal": subtotal, "ledger": ledger}


# ════════════════════════════════════════════════════════
#  ROUTE — REP (Regulatory Evidence Package)
# ════════════════════════════════════════════════════════
@app.post("/api/rep")
async def generate_rep(body: REPRequest):
    rep_id   = receipt_id("REP")
    rep_hash = sha256(rep_id + json.dumps(body.decisions) + json.dumps(body.pho_receipts))
    ledger   = await seal_ledger({
        "id": rep_id, "actor": body.actor, "app": "windi-enterprise-rep",
        "doc_name": "Regulatory Evidence Package",
        "doc_type": "regulatory_report", "governance_level": "HIGH", "hash": rep_hash,
        "note": f"REP · {len(body.decisions)} decisions · {len(body.pho_receipts)} PHO receipts · EU AI Act Art.14"
    })
    AUDIT_DB.insert(0, {"event": f"REP Generated: {rep_id}", "module":"AUDIT", "ts": now_iso()[:16], "receipt": rep_id})
    log.info(f"[REP] Generated {rep_id}")
    return {
        "rep_id": rep_id, "hash": rep_hash, "ledger": ledger,
        "verify_url": f"https://www.windi-domain.com/verify-public/?id={rep_id}",
        "timestamp": now_iso(),
    }


# ════════════════════════════════════════════════════════
#  ROUTE — AUDIT LOG (read)
# ════════════════════════════════════════════════════════
@app.get("/api/audit")
async def get_audit(limit: int = 50):
    return {"events": AUDIT_DB[:limit], "total": len(AUDIT_DB)}


# ════════════════════════════════════════════════════════
#  ROUTE — CANVAS INTEGRATION §166
# ════════════════════════════════════════════════════════
class CoverRequest(BaseModel):
    title: str
    subtitle: str = "Risk Evidence Package"
    theme: str = "NOIR"  # NOIR | KLAR
    actor: str = "Human Dragon"

class PHOCertRequest(BaseModel):
    actor_name: str
    decision_summary: str
    doc_id: str

@app.post("/api/canvas/cover")
async def generate_cover(body: CoverRequest):
    """
    Generate visual cover for REP/PHO packages using W-CANVAS-001.
    §166 · I9-P: AI renders, Human approves, WINDI seals.
    """
    if not CANVAS_AVAILABLE:
        return {"error": "Canvas integration not available", "canvas_available": False}

    result = await enterprise_generate_cover(
        title=body.title,
        subtitle=body.subtitle,
        theme=body.theme,
        actor=body.actor
    )

    if result:
        AUDIT_DB.insert(0, {
            "event": f"Canvas Cover Generated: {body.title}",
            "module": "CANVAS",
            "ts": now_iso()[:16],
            "receipt": result.get("ledger_receipt")
        })
        log.info(f"[CANVAS] Cover generated: {result.get('job_id')}")
        return {
            "success": True,
            "job_id": result.get("job_id"),
            "download_url": result.get("download_url"),
            "sha256": result.get("sha256"),
            "ledger_receipt": result.get("ledger_receipt"),
            "render_ms": result.get("render_ms")
        }
    else:
        # I14: Explicit failure, no silent null
        return {"success": False, "error": "Canvas worker offline or render failed", "canvas_available": True}


@app.post("/api/canvas/pho-cert")
async def generate_pho_certificate(body: PHOCertRequest):
    """
    Generate PHO Certificate visual for EU AI Act Art.14 compliance.
    §166 · Proof of Human Oversight — visual evidence.
    """
    if not CANVAS_AVAILABLE:
        return {"error": "Canvas integration not available", "canvas_available": False}

    result = await enterprise_generate_pho_cert(
        actor_name=body.actor_name,
        decision_summary=body.decision_summary,
        doc_id=body.doc_id
    )

    if result:
        AUDIT_DB.insert(0, {
            "event": f"PHO Certificate Generated: {body.doc_id}",
            "module": "CANVAS",
            "ts": now_iso()[:16],
            "receipt": result.get("ledger_receipt")
        })
        log.info(f"[CANVAS] PHO Cert generated: {result.get('job_id')}")
        return {
            "success": True,
            "job_id": result.get("job_id"),
            "download_url": result.get("download_url"),
            "sha256": result.get("sha256"),
            "ledger_receipt": result.get("ledger_receipt"),
            "render_ms": result.get("render_ms")
        }
    else:
        return {"success": False, "error": "Canvas worker offline or render failed", "canvas_available": True}


@app.get("/api/canvas/status")
async def canvas_status():
    """Check W-CANVAS-001 availability and status."""
    if not CANVAS_AVAILABLE:
        return {"available": False, "reason": "Integration module not loaded"}

    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://127.0.0.1:8155/canvas/health")
            if r.status_code == 200:
                data = r.json()
                return {
                    "available": True,
                    "service": data.get("service"),
                    "version": data.get("version"),
                    "outputs": data.get("outputs"),
                    "invariant": data.get("invariant")
                }
    except Exception as e:
        log.warning(f"[CANVAS] Health check failed: {e}")

    return {"available": False, "reason": "Canvas worker not responding"}


# ════════════════════════════════════════════════════════
#  STARTUP
# ════════════════════════════════════════════════════════
@app.on_event("startup")
async def startup():
    log.info(f"W-Enterprise-001 v{SERVICE_VERSION} starting on :8150")
    log.info(f"AI ready: {bool(ANTHROPIC_API_KEY)} · Model: {AI_MODEL}")
    log.info(f"Ledger: {LEDGER_URL}")
    log.info(f"Static: {STATIC_DIR} (exists={STATIC_DIR.exists()})")
    log.info("VERA Agent: REGO v1.0 · /enterprise/vera/* routes active")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8150)
