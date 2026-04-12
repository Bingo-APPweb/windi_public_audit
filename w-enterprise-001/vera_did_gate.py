# ═══════════════════════════════════════════════════════════════════════════
#  vera_did_gate.py — DID Gate · As Três Leis da Semente
#  EVANGELHO WINDI: ALMA → DID → CÉREBRO → LEDGER → MUNDO
#  REGO v1.2 · Liga IA+H · Human Dragon · 12 Abril 2026
#
#  "WINDI é para todos. Só funciona com DID."
#  "Um cérebro não funciona sem Alma. A Alma entra pelo DID."
#
#  AS TRÊS LEIS:
#    Lei I   — Existência antes de Acção (sem DID → WalletBanner mode)
#    Lei II  — Toda Acção gera Rastro DID (receipt obrigatório)
#    Lei III — Sistema lê Histórico do DID (contexto ao regressar)
#
#  Endpoints validados:
#    :8096 — W-SESSION-001 (DID validation)
#    :8101 — Forensic Ledger (history + seal)
# ═══════════════════════════════════════════════════════════════════════════

import logging
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from functools import wraps

import httpx
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

log = logging.getLogger("vera.did_gate")

# ─── CONFIG ───────────────────────────────────────────────────────────────
SESSION_SERVICE_URL = "http://localhost:8096"
LEDGER_URL = "http://localhost:8101"
DID_CACHE_TTL_SECONDS = 300  # 5 min cache

# In-memory cache for DID validation (production: use Redis)
_did_cache: Dict[str, Dict[str, Any]] = {}


# ═══════════════════════════════════════════════════════════════════════════
#  MODELS
# ═══════════════════════════════════════════════════════════════════════════

class DIDValidation(BaseModel):
    """Result of DID validation against W-SESSION-001"""
    valid: bool
    did: str
    active: bool
    tier: Optional[str] = None
    created_at: Optional[str] = None
    last_seen: Optional[str] = None
    error: Optional[str] = None

class DIDHistory(BaseModel):
    """Officer's action history from Ledger"""
    did: str
    total_actions: int
    last_action: Optional[str] = None
    modules_used: List[str]
    receipts: List[Dict[str, Any]]

class WalletBanner(BaseModel):
    """Lei I: Response when no DID present"""
    mode: str = "wallet_banner"
    message_pt: str
    message_de: str
    message_en: str
    create_did_url: str
    what_is_did: Dict[str, str]
    what_is_vera: Dict[str, str]
    adoption_preview: List[str]


# ═══════════════════════════════════════════════════════════════════════════
#  LEI I — EXISTÊNCIA ANTES DE ACÇÃO
#  Sem DID = WalletBanner mode. Zero acções.
# ═══════════════════════════════════════════════════════════════════════════

def get_wallet_banner(lang: str = "en") -> WalletBanner:
    """
    Lei I: Returns the WalletBanner response for users without DID.
    VERA explains what it is and how to create identity. Nothing more.
    """
    return WalletBanner(
        mode="wallet_banner",
        message_pt="Bem-vindo ao W-Enterprise. Para usar VERA, precisas de uma identidade digital (DID). Cria a tua carteira para começar.",
        message_de="Willkommen bei W-Enterprise. Um VERA zu nutzen, benötigst du eine digitale Identität (DID). Erstelle deine Wallet, um zu beginnen.",
        message_en="Welcome to W-Enterprise. To use VERA, you need a digital identity (DID). Create your wallet to begin.",
        create_did_url="https://windi-domain.com/wallet/create",
        what_is_did={
            "pt": "O DID (Decentralized Identifier) é a tua identidade soberana no ecossistema WINDI. Não pertence a nenhuma empresa — pertence a ti. Com ele, todas as tuas acções são rastreáveis e verificáveis, mas só tu controlas o acesso.",
            "de": "Die DID (Decentralized Identifier) ist deine souveräne Identität im WINDI-Ökosystem. Sie gehört keinem Unternehmen — sie gehört dir. Damit sind alle deine Aktionen nachvollziehbar und überprüfbar, aber nur du kontrollierst den Zugang.",
            "en": "The DID (Decentralized Identifier) is your sovereign identity in the WINDI ecosystem. It doesn't belong to any company — it belongs to you. With it, all your actions are traceable and verifiable, but only you control access.",
        },
        what_is_vera={
            "pt": "VERA é a tua secretária de compliance constitucional. Guia-te pelos 8 módulos do W-Enterprise, responde às tuas perguntas com âncoras legais específicas (EU AI Act, GDPR, DORA), e garante que cada decisão AI passa por supervisão humana (PHO).",
            "de": "VERA ist deine konstitutionelle Compliance-Sekretärin. Sie führt dich durch die 8 Module des W-Enterprise, beantwortet deine Fragen mit spezifischen rechtlichen Ankern (EU AI Act, DSGVO, DORA) und stellt sicher, dass jede KI-Entscheidung menschliche Aufsicht (PHO) durchläuft.",
            "en": "VERA is your constitutional compliance secretary. She guides you through the 8 W-Enterprise modules, answers your questions with specific legal anchors (EU AI Act, GDPR, DORA), and ensures every AI decision goes through human oversight (PHO).",
        },
        adoption_preview=[
            "PHO — Proof of Human Oversight",
            "ObsEngine — Observation Engine",
            "1LOD — First Line of Defence",
            "2LOD — Second Line of Defence",
            "DocGen — Document Generator",
            "LegalAdvisory — AI Legal Counsel",
            "InvoiceGen — XRechnung Ready",
            "REP — Reporting Engine",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
#  DID VALIDATION — Verifica DID activo em :8096
# ═══════════════════════════════════════════════════════════════════════════

async def verify_did(did: str) -> DIDValidation:
    """
    Validates DID against W-SESSION-001 (:8096).
    Returns validation result with session details.

    Evangelho: "A Alma entra pelo DID" — sem validação, sem entrada.
    """
    if not did or len(did) < 10:
        return DIDValidation(
            valid=False,
            did=did or "",
            active=False,
            error="DID inválido ou ausente [Lei I]"
        )

    # Check cache first
    cache_key = f"did:{did}"
    now = datetime.now(timezone.utc)

    if cache_key in _did_cache:
        cached = _did_cache[cache_key]
        cache_age = (now - cached["cached_at"]).total_seconds()
        if cache_age < DID_CACHE_TTL_SECONDS:
            log.debug(f"DID cache hit: {did[:20]}...")
            return DIDValidation(**cached["validation"])

    # Call W-SESSION-001
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Try the session validation endpoint
            r = await client.get(f"{SESSION_SERVICE_URL}/session/validate/{did}")

            if r.status_code == 200:
                data = r.json()
                validation = DIDValidation(
                    valid=True,
                    did=did,
                    active=data.get("active", True),
                    tier=data.get("tier", "SEED"),
                    created_at=data.get("created_at"),
                    last_seen=data.get("last_seen"),
                )
            elif r.status_code == 404:
                # DID not in session DB but format is valid → graceful pass
                # Evangelho: Every soul with a DID deserves entry
                if did.startswith("did:windi:") and len(did) > 15:
                    log.info(f"DID format valid but not in DB — graceful pass: {did[:25]}...")
                    validation = DIDValidation(
                        valid=True,
                        did=did,
                        active=True,
                        tier="SEED",
                        error="DID válido · Modo local [Lei I graceful]"
                    )
                else:
                    validation = DIDValidation(
                        valid=False,
                        did=did,
                        active=False,
                        error="DID não encontrado em W-SESSION-001"
                    )
            else:
                # Session service might be down, allow graceful degradation
                log.warning(f"W-SESSION-001 returned {r.status_code} for DID validation")
                validation = DIDValidation(
                    valid=True,  # Graceful: assume valid if service unavailable
                    did=did,
                    active=True,
                    error=f"W-SESSION-001 status {r.status_code} — graceful pass"
                )
    except httpx.ConnectError:
        # Service unavailable — graceful degradation
        log.warning("W-SESSION-001 unavailable — graceful DID pass")
        validation = DIDValidation(
            valid=True,
            did=did,
            active=True,
            error="W-SESSION-001 offline — graceful pass [I14 declared]"
        )
    except Exception as e:
        log.error(f"DID validation error: {e}")
        validation = DIDValidation(
            valid=False,
            did=did,
            active=False,
            error=f"Validation error: {str(e)}"
        )

    # Cache result
    _did_cache[cache_key] = {
        "validation": validation.model_dump(),
        "cached_at": now,
    }

    return validation


# ═══════════════════════════════════════════════════════════════════════════
#  LEI II — TODA ACÇÃO GERA RASTRO DID
#  Instrução + DID + timestamp → receipt obrigatório
# ═══════════════════════════════════════════════════════════════════════════

async def bind_action_to_did(
    did: str,
    action: str,
    module: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Lei II: Every VERA action creates a DID-bound trace in the Ledger.
    The officer has a verifiable lifeline within W-Enterprise.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Build action record
    action_content = f"{did}:{action}:{module}:{timestamp}"
    action_hash = hashlib.sha256(action_content.encode()).hexdigest()[:16].upper()
    receipt_id = f"VERA-ACTION-{action_hash}"

    payload = {
        "id": receipt_id,
        "actor": did,
        "app": "VERA",
        "doc_name": f"VERA Action: {action}",
        "doc_type": "doc",
        "content_hash": f"sha256:{action_hash}",
        "governance_level": "LOW",
        "sge_score": 0.0,
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(f"{LEDGER_URL}/api/receipts", json=payload)
            if r.status_code == 200:
                result = r.json()
                log.info(f"Lei II: Action bound to DID {did[:20]}... → {receipt_id}")
                return {
                    "bound": True,
                    "receipt_id": receipt_id,
                    "action_hash": action_hash,
                    "ledger_response": result,
                }
            else:
                log.warning(f"Ledger seal failed for action: {r.status_code}")
                return {
                    "bound": False,
                    "receipt_id": receipt_id,
                    "action_hash": action_hash,
                    "error": f"Ledger status {r.status_code}",
                }
    except Exception as e:
        log.error(f"Lei II binding error: {e}")
        return {
            "bound": False,
            "receipt_id": receipt_id,
            "action_hash": action_hash,
            "error": str(e),
        }


# ═══════════════════════════════════════════════════════════════════════════
#  LEI III — SISTEMA LÊ HISTÓRICO DO DID
#  DID retorna → Ledger query → VERA adapta contexto
# ═══════════════════════════════════════════════════════════════════════════

async def read_did_history(did: str, limit: int = 50) -> DIDHistory:
    """
    Lei III: When officer returns, VERA reads their Ledger history.
    What have they done? Which modules used? Instruction starts exactly
    from the right point.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Query Ledger for receipts by this DID
            r = await client.get(
                f"{LEDGER_URL}/api/receipts",
                params={"actor": did, "limit": limit}
            )

            if r.status_code == 200:
                data = r.json()
                receipts = data.get("receipts", [])

                # Extract modules used
                modules_used = set()
                for receipt in receipts:
                    doc_name = receipt.get("doc_name", "")
                    if "PHO" in doc_name or "pho" in doc_name.lower():
                        modules_used.add("pho")
                    if "1LOD" in doc_name or "lod1" in doc_name.lower():
                        modules_used.add("lod1")
                    if "2LOD" in doc_name or "lod2" in doc_name.lower():
                        modules_used.add("lod2")
                    if "DocGen" in doc_name or "document" in doc_name.lower():
                        modules_used.add("doc_gen")
                    if "Legal" in doc_name:
                        modules_used.add("legal_advisory")
                    if "Invoice" in doc_name:
                        modules_used.add("invoice_gen")
                    if "Routing" in doc_name:
                        modules_used.add("routing")
                    if "Instructor" in doc_name:
                        modules_used.add("instructor")

                last_action = receipts[0].get("created_at") if receipts else None

                return DIDHistory(
                    did=did,
                    total_actions=len(receipts),
                    last_action=last_action,
                    modules_used=list(modules_used),
                    receipts=receipts[:10],  # Last 10 for context
                )
            else:
                return DIDHistory(
                    did=did,
                    total_actions=0,
                    modules_used=[],
                    receipts=[],
                )
    except Exception as e:
        log.error(f"Lei III history read error: {e}")
        return DIDHistory(
            did=did,
            total_actions=0,
            modules_used=[],
            receipts=[],
        )


async def restore_did_context(did: str) -> Dict[str, Any]:
    """
    Lei III: Full context restoration for returning officer.
    Combines validation + history for complete situational awareness.
    """
    validation = await verify_did(did)

    if not validation.valid:
        return {
            "restored": False,
            "reason": validation.error,
            "wallet_banner": get_wallet_banner().model_dump(),
        }

    history = await read_did_history(did)

    # Build context summary
    context = {
        "restored": True,
        "did": did,
        "validation": validation.model_dump(),
        "history": history.model_dump(),
        "vera_greeting": _build_greeting(history),
        "recommended_next": _recommend_next_module(history.modules_used),
    }

    log.info(f"Lei III: Context restored for {did[:20]}... ({history.total_actions} actions)")
    return context


def _build_greeting(history: DIDHistory) -> Dict[str, str]:
    """Build personalized greeting based on history."""
    if history.total_actions == 0:
        return {
            "pt": "Bem-vindo ao W-Enterprise. É a tua primeira vez aqui. Vou guiar-te pelo sistema.",
            "de": "Willkommen bei W-Enterprise. Es ist dein erstes Mal hier. Ich werde dich durch das System führen.",
            "en": "Welcome to W-Enterprise. This is your first time here. I'll guide you through the system.",
        }
    elif history.total_actions < 10:
        return {
            "pt": f"Bem-vindo de volta. Tens {history.total_actions} acções registadas. Vamos continuar onde paraste.",
            "de": f"Willkommen zurück. Du hast {history.total_actions} Aktionen registriert. Lass uns weitermachen, wo du aufgehört hast.",
            "en": f"Welcome back. You have {history.total_actions} actions registered. Let's continue where you left off.",
        }
    else:
        return {
            "pt": f"Bem-vindo, officer experiente. {history.total_actions} acções no teu histórico. Como posso ajudar hoje?",
            "de": f"Willkommen, erfahrener Officer. {history.total_actions} Aktionen in deiner Historie. Wie kann ich heute helfen?",
            "en": f"Welcome, experienced officer. {history.total_actions} actions in your history. How can I help today?",
        }


def _recommend_next_module(modules_used: List[str]) -> Dict[str, Any]:
    """Recommend next module based on adoption sequence."""
    adoption_order = ["pho", "obs_engine", "lod1", "lod2", "doc_gen", "legal_advisory", "invoice_gen", "rep"]

    for module in adoption_order:
        if module not in modules_used:
            return {
                "module_id": module,
                "reason": {
                    "pt": f"Recomendo começares pelo {module} — segue a sequência de adopção.",
                    "de": f"Ich empfehle, mit {module} zu beginnen — folgt der Adoptionssequenz.",
                    "en": f"I recommend starting with {module} — follows the adoption sequence.",
                },
            }

    return {
        "module_id": None,
        "reason": {
            "pt": "Já usaste todos os módulos. Estás pronto para operações avançadas.",
            "de": "Du hast alle Module verwendet. Du bist bereit für fortgeschrittene Operationen.",
            "en": "You've used all modules. You're ready for advanced operations.",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
#  DID GATE — FastAPI Dependency
#  Aplica as Três Leis a todos os endpoints
# ═══════════════════════════════════════════════════════════════════════════

class DIDGateResult(BaseModel):
    """Result of DID gate check"""
    passed: bool
    did: Optional[str] = None
    validation: Optional[DIDValidation] = None
    context: Optional[Dict[str, Any]] = None
    wallet_banner: Optional[WalletBanner] = None


async def did_gate(
    request: Request,
    require_history: bool = False,
) -> DIDGateResult:
    """
    FastAPI dependency that enforces DID as gate, not parameter.

    Usage in router:
        @router.post("/endpoint")
        async def endpoint(gate: DIDGateResult = Depends(did_gate)):
            if not gate.passed:
                return JSONResponse(gate.wallet_banner.model_dump(), status_code=401)
            # Continue with gate.did and gate.context

    Evangelho: "Esta ligação passa pela semente DID ou contorna-a?"
    Se contorna → não fazemos. Se passa → fazemos com precisão cirúrgica.
    """
    # Try to extract DID from multiple sources
    did = None

    # 1. Check Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("DID "):
        did = auth_header[4:].strip()

    # 2. Check X-Officer-DID header
    if not did:
        did = request.headers.get("X-Officer-DID", "")

    # 3. Check query parameter
    if not did:
        did = request.query_params.get("officer_did", "")

    # 4. For POST requests, check body (if JSON)
    if not did and request.method == "POST":
        try:
            body = await request.json()
            did = body.get("officer_did", "")
        except:
            pass

    # No DID found → Lei I: WalletBanner mode
    if not did:
        log.info("DID Gate: No DID provided — returning WalletBanner [Lei I]")
        return DIDGateResult(
            passed=False,
            wallet_banner=get_wallet_banner(),
        )

    # Validate DID
    validation = await verify_did(did)

    if not validation.valid or not validation.active:
        log.warning(f"DID Gate: Invalid/inactive DID {did[:20]}... — {validation.error}")
        return DIDGateResult(
            passed=False,
            did=did,
            validation=validation,
            wallet_banner=get_wallet_banner(),
        )

    # DID valid — optionally restore context
    context = None
    if require_history:
        context = await restore_did_context(did)

    log.info(f"DID Gate: PASSED for {did[:20]}...")
    return DIDGateResult(
        passed=True,
        did=did,
        validation=validation,
        context=context,
    )


def require_did(require_history: bool = False):
    """
    Decorator for endpoint functions that require DID.
    Automatically returns WalletBanner if DID not valid.

    Usage:
        @router.post("/endpoint")
        @require_did(require_history=True)
        async def endpoint(request: Request):
            gate = request.state.did_gate
            # gate.did is guaranteed valid here
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            gate = await did_gate(request, require_history=require_history)

            if not gate.passed:
                return JSONResponse(
                    content={
                        "status": "did_required",
                        "law": "Lei I — Existência antes de Acção",
                        "message": "DID obrigatório para esta operação",
                        "wallet_banner": gate.wallet_banner.model_dump() if gate.wallet_banner else None,
                    },
                    status_code=401,
                )

            # Store gate result in request state for access in endpoint
            request.state.did_gate = gate
            return await func(request, *args, **kwargs)

        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════
#  FASTAPI ROUTER — DID Gate Management Endpoints
# ═══════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter

def create_did_gate_router() -> APIRouter:
    router = APIRouter(prefix="/vera/did", tags=["DID-Gate"])

    @router.get("/validate/{did}")
    async def validate_did_endpoint(did: str):
        """Validate a DID against W-SESSION-001."""
        validation = await verify_did(did)
        return {
            "status": "success" if validation.valid else "invalid",
            "validation": validation.model_dump(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/history/{did}")
    async def get_did_history(did: str, limit: int = 50):
        """Get action history for a DID from Ledger."""
        # First validate DID
        validation = await verify_did(did)
        if not validation.valid:
            return JSONResponse(
                content={
                    "status": "invalid_did",
                    "error": validation.error,
                    "wallet_banner": get_wallet_banner().model_dump(),
                },
                status_code=401,
            )

        history = await read_did_history(did, limit)
        return {
            "status": "success",
            "history": history.model_dump(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/context/{did}")
    async def restore_context(did: str):
        """Lei III: Full context restoration for returning officer."""
        context = await restore_did_context(did)

        if not context.get("restored"):
            return JSONResponse(
                content=context,
                status_code=401,
            )

        return {
            "status": "success",
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/wallet-banner")
    async def get_wallet_banner_endpoint(lang: str = "en"):
        """Get the WalletBanner for unauthenticated users."""
        banner = get_wallet_banner(lang)
        return {
            "status": "wallet_banner",
            "law": "Lei I — Existência antes de Acção",
            "banner": banner.model_dump(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/health")
    async def did_gate_health():
        """DID Gate health check."""
        # Check W-SESSION-001 connectivity
        session_ok = False
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{SESSION_SERVICE_URL}/health")
                session_ok = r.status_code == 200
        except:
            pass

        # Check Ledger connectivity
        ledger_ok = False
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{LEDGER_URL}/health")
                ledger_ok = r.status_code == 200
        except:
            pass

        return {
            "status": "operational" if (session_ok or ledger_ok) else "degraded",
            "component": "VERA DID Gate",
            "evangelho": "ALMA → DID → CÉREBRO → LEDGER → MUNDO",
            "laws": {
                "lei_i": "Existência antes de Acção",
                "lei_ii": "Toda Acção gera Rastro DID",
                "lei_iii": "Sistema lê Histórico do DID",
            },
            "dependencies": {
                "w_session_001": "operational" if session_ok else "unavailable",
                "forensic_ledger": "operational" if ledger_ok else "unavailable",
            },
            "cache_entries": len(_did_cache),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return router
