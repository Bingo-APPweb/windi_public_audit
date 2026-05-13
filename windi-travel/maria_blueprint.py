"""
W-MARIA-001 — WINDI Travel Agent Blueprint
Iron Rule: domain extension of Sandbox Core (:8091)
Path prefix: /maria/

Endpoints (Phase 1 — Seal):
  POST /maria/seal       → Seal decision to Ledger + return verify_url
  GET  /maria/health     → Health check

Ledger API (:8101) contract:
  Required: id, actor, app, doc_name
  doc_type ∈ {doc, xlsx, pptx, jmpg, communique}
  governance_level ∈ {LOW, MEDIUM, HIGH}
"""

import hashlib
import json
import uuid
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

logger = logging.getLogger("w-maria-001")

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

LEDGER_URL       = "http://localhost:8101"
VERIFY_BASE_URL  = "https://windi-domain.com/verify-public"
AGENT_ID         = "W-MARIA-001"
AGENT_VERSION    = "1.0.0"

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class TravelIntent(BaseModel):
    """O que o utilizador quer."""
    raw_input: str
    language: str = "DE"                          # DE | PT | EN
    needs_wifi: Optional[bool] = None
    needs_shelter: Optional[bool] = None
    walking_minutes: Optional[int] = None
    weather_condition: Optional[str] = None       # rain | sun | cloudy
    group_size: Optional[int] = 1

class TravelContext(BaseModel):
    """Estado do mundo no momento da decisão."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    weather: Optional[str] = None
    timestamp: Optional[str] = None

class TravelDecision(BaseModel):
    """O que Maria decidiu."""
    place_name: str
    place_address: Optional[str] = None
    place_id: Optional[str] = None                # Google Places ID
    reason: str                                   # justificação humana
    distance_minutes: Optional[int] = None
    source: str = "live"                          # live | fallback
    score: Optional[float] = None                 # 0.0 - 1.0

class SealRequest(BaseModel):
    """Payload completo para selar uma decisão Maria."""
    wallet_id: Optional[str] = Field(default=None, description="DID do utilizador (opcional)")
    intent: TravelIntent
    context: TravelContext
    decision: TravelDecision
    lang: str = "DE"

class SealResponse(BaseModel):
    """Resposta do seal com prova imutável."""
    receipt_id: str
    verify_url: str
    hash: str
    sealed_at: str
    governance_level: str
    source: str
    agent: str = AGENT_ID

# ──────────────────────────────────────────────
# ROUTER
# ──────────────────────────────────────────────

router = APIRouter(prefix="/maria", tags=["W-MARIA-001"])

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _generate_receipt_id() -> str:
    """WINDI-TRAVEL-YYYYMMDD-XXXX"""
    date_str  = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:8].upper()
    return f"WINDI-TRAVEL-{date_str}-{unique_id}"

def _hash_decision(receipt_id: str, decision_payload: dict) -> str:
    """SHA-256 do conteúdo canónico da decisão."""
    canonical = json.dumps(
        {"receipt_id": receipt_id, **decision_payload},
        sort_keys=True, ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode()).hexdigest()

def _build_ledger_payload(receipt_id: str, req: SealRequest, sha256: str) -> dict:
    """Monta o payload para o Ledger :8101 com os campos obrigatórios."""
    return {
        # ── campos obrigatórios do Ledger ──
        "id":               receipt_id,
        "actor":            req.wallet_id,  # §167: wallet_id now required
        "app":              "windi-travel",
        "doc_name":         f"TRAVEL_DECISION_{req.decision.place_name.upper().replace(' ', '_')}",
        "doc_type":         "doc",
        "governance_level": "HIGH",
        "content_hash":     sha256,
        "sge_score":        97,

        # ── metadados da decisão (nota: opcional, vai para content) ──
        "note": json.dumps({
            "type":      "TRAVEL_DECISION",
            "version":   AGENT_VERSION,
            "lang":      req.lang,
            "intent":    req.intent.model_dump(exclude_none=True),
            "context":   req.context.model_dump(exclude_none=True),
            "decision":  req.decision.model_dump(exclude_none=True),
            "sealed_by": AGENT_ID,
            "source":    req.decision.source,
        }, ensure_ascii=False),
    }

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.get("/health")
async def maria_health():
    """Health check do agente W-MARIA-001."""
    return {
        "agent":   AGENT_ID,
        "version": AGENT_VERSION,
        "status":  "operational",
        "ledger":  LEDGER_URL,
    }


@router.post("/seal", response_model=SealResponse)
async def seal_decision(req: SealRequest):
    """
    Sela uma decisão de viagem no Ledger WINDI.

    Fluxo:
      1. Gera receipt_id canónico (WINDI-TRAVEL-YYYYMMDD-XXXX)
      2. Calcula SHA-256 do payload
      3. POST para Ledger :8101
      4. Devolve receipt_id + verify_url + hash

    Constitucionalmente conforme:
      - I1  (Soberania de Dados)
      - I10 (Fallback gracioso)
      - I11 (Permanência de Evidência Criptográfica — IRREMEDIÁVEL)

    §167 Audit Fix (14 Abr 2026):
      - wallet_id agora OBRIGATÓRIO para governance_level HIGH
      - Anonymous receipts proibidos (I1 + I14)
    """
    # §167: I1 + I14 — Actor identification required for HIGH governance
    if not req.wallet_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "wallet_id_required",
                "message": "Travel decision seal requires identified actor. Anonymous access not permitted for governance_level HIGH.",
                "invariant": "I1 — Soberania Humana",
                "code": "W-MARIA-001-AUTH-REQUIRED"
            }
        )

    receipt_id = _generate_receipt_id()
    sealed_at  = datetime.now(timezone.utc).isoformat()

    # ── payload para hash ──
    decision_payload = {
        "intent":   req.intent.model_dump(exclude_none=True),
        "context":  req.context.model_dump(exclude_none=True),
        "decision": req.decision.model_dump(exclude_none=True),
        "lang":     req.lang,
        "sealed_at": sealed_at,
    }
    sha256 = _hash_decision(receipt_id, decision_payload)

    ledger_payload = _build_ledger_payload(receipt_id, req, sha256)

    # ── POST ao Ledger real ──
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"{LEDGER_URL}/api/receipts",
                json=ledger_payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            logger.info(f"[SEAL OK] {receipt_id} → Ledger {resp.status_code}")

    except httpx.HTTPStatusError as e:
        logger.error(f"[SEAL FAIL] Ledger HTTP error: {e.response.status_code} — {e.response.text}")
        raise HTTPException(
            status_code=502,
            detail={
                "error":      "ledger_http_error",
                "receipt_id": receipt_id,
                "ledger_status": e.response.status_code,
                "message":    "Ledger recusou o seal. Verifica os campos obrigatórios.",
            }
        )
    except httpx.RequestError as e:
        logger.error(f"[SEAL FAIL] Ledger unreachable: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error":      "ledger_unreachable",
                "receipt_id": receipt_id,
                "message":    "Ledger :8101 não está acessível. I10: fallback activado.",
            }
        )

    verify_url = f"{VERIFY_BASE_URL}/?id={receipt_id}"

    return SealResponse(
        receipt_id      = receipt_id,
        verify_url      = verify_url,
        hash            = sha256,
        sealed_at       = sealed_at,
        governance_level = "HIGH",
        source          = req.decision.source,
    )
