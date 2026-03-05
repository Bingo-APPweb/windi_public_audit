"""
DRAGON HUB v1.0 — WINDI Surgical Bridge
========================================
Vive dentro do :8108. Não muda nginx, porta, nem React.
Liga o Dragon monolith ao Constitutional Agent Corps (:8091).

Arquitectura:
  React → :8108/dragon → dragon_hub.handle() → :8091 blueprints

Invariantes:
  - Gate Controller (dragon_apis.py) é preservado intacto
  - Fallback guardian garante continuidade mesmo se :8091 cair
  - History gerida pelo Hub, não pelo React
  - C6: IA prepara. Humano aprova. Sistema garante.
"""

from __future__ import annotations

import time
import asyncio
from typing import Any, Callable, Dict, List, Optional

import httpx

# ─── CONFIG ──────────────────────────────────────────────────────────────────

SANDBOX_BASE = "http://localhost:8091"

# Endpoints reais confirmados por grep nos blueprints
# NOTE: Intents que precisam de AI generation (communique, journalist)
#       devem ir para "guardian" (Dragon LLM), não para :8091
AGENT_ROUTES = {
    # Data storage endpoints (no LLM required)
    "legal":              "/legal/cases",
    "evidence":           "/legal/evidence/commit",
    "accounting_stats":   "/accounting/stats",           # GET - queries
    "accounting_validate": "/accounting/invoice/validate",  # POST - with file/xml
    "audit_status":       "/audit/status",               # GET - queries
    "audit_chain":        "/audit/chain",                # POST - with document_id
    "notary":             "/notary/act/certify",
    "compliance":         "/compliance/invariants/check",
}

# Intents que DEVEM ir para guardian (Dragon LLM)
# Porque Agent Corps não tem LLM próprio
GUARDIAN_INTENTS = {"communique", "journalist", "report"}

HISTORY_SLICE       = 20     # msgs enviadas ao agent por request
MAX_SESSION_MSGS    = 200    # hard cap por sessão
SESSION_TTL_SECONDS = 21600  # 6 horas


# ─── SESSION STORE ────────────────────────────────────────────────────────────

class SessionStore:
    """
    In-memory. Substitui por SQLite/Redis sem tocar no router.
    Thread-safe via asyncio.Lock.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._sessions: Dict[str, Dict[str, Any]] = {}

    async def get(self, session_id: str, n: int = HISTORY_SLICE) -> List[Dict]:
        async with self._lock:
            self._gc()
            bucket = self._sessions.get(session_id)
            if not bucket:
                return []
            return list(bucket["msgs"])[-n:]

    async def append(self, session_id: str, role: str, content: str) -> None:
        now = int(time.time())
        async with self._lock:
            self._gc()
            if session_id not in self._sessions:
                self._sessions[session_id] = {"ts": now, "msgs": []}
            b = self._sessions[session_id]
            b["ts"] = now
            b["msgs"].append({"role": role, "content": str(content)[:4000]})
            if len(b["msgs"]) > MAX_SESSION_MSGS:
                b["msgs"] = b["msgs"][-MAX_SESSION_MSGS:]

    async def clear(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)

    def _gc(self) -> None:
        now = int(time.time())
        dead = [
            sid for sid, b in self._sessions.items()
            if (now - b["ts"]) > SESSION_TTL_SECONDS
        ]
        for sid in dead:
            del self._sessions[sid]


# ─── INTENT RESOLVER ─────────────────────────────────────────────────────────

def resolve_intent(message: str, explicit: Optional[str] = None) -> str:
    """
    Classifica a intenção do utilizador.
    Trilingual: PT / DE / EN.
    """
    if explicit:
        return explicit

    m = (message or "").lower()

    # Communiqué / Publishing
    if any(k in m for k in [
        "communique", "comunicado", "communiqué",
        "press release", "pressemitteilung",
        "relatório", "report", "briefing", "publish", "publicar"
    ]):
        return "communique"

    # Legal
    if any(k in m for k in [
        "legal", "contrato", "vertrag", "contract",
        "evidência", "evidence", "beweis",
        "jurídico", "processo", "klage", "lawsuit"
    ]):
        return "legal"

    # Evidence commit (subset of legal but direct)
    if any(k in m for k in [
        "evidence commit", "commit evidence", "evidência commit"
    ]):
        return "evidence"

    # Accounting
    if any(k in m for k in [
        "invoice", "fatura", "rechnung", "recibo",
        "accounting", "contabilidade", "buchhaltung",
        "datev", "xrechnung", "zugferd", "elster"
    ]):
        return "accounting"

    # Audit / Verify
    if any(k in m for k in [
        "verify", "audit", "ledger", "hash", "qr",
        "wcaf", "proof", "merkle", "verificar", "prüfen"
    ]):
        return "audit"

    # Journalism
    if any(k in m for k in [
        "journalist", "jornalista", "article", "artigo",
        "news", "notícia", "nachricht"
    ]):
        return "journalist"

    # Notary
    if any(k in m for k in [
        "notary", "notarial", "notário", "certify",
        "certificate", "certificado", "zertifikat"
    ]):
        return "notary"

    # Compliance
    if any(k in m for k in [
        "compliance", "conform", "gdpr", "dsgvo",
        "eu ai act", "bafin", "regulament"
    ]):
        return "compliance"

    return "guardian"


# ─── SANDBOX CALLER ──────────────────────────────────────────────────────────

async def call_sandbox(
    endpoint: str,
    payload: Dict[str, Any],
    timeout: float = 30.0,
    method: str = "POST"
) -> Dict[str, Any]:
    url = f"{SANDBOX_BASE}{endpoint}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        if method == "GET":
            r = await client.get(url, params=payload)
        else:
            r = await client.post(url, json=payload)
        r.raise_for_status()
        return r.json()


# ─── PAYLOAD BUILDERS ────────────────────────────────────────────────────────

def build_communique_payload(payload: Dict, history: List) -> Dict:
    """
    W-COMM-001 espera: prompt, doc_type, session_id
    Mapeamos 'message' → 'prompt' (contrato real do blueprint).
    """
    return {
        "prompt":     payload.get("message") or payload.get("prompt", ""),
        "doc_type":   payload.get("doc_type", "press_release"),
        "session_id": payload.get("session_id", "hub"),
        "history":    history,
        "meta":       payload.get("meta", {}),
        "isp":        payload.get("isp"),
        "locale":     payload.get("locale", "de"),
    }

def build_legal_payload(payload: Dict, history: List) -> Dict:
    return {
        "title":      payload.get("message", "")[:200],
        "description": payload.get("message", ""),
        "jurisdiction": payload.get("jurisdiction", "DE"),
        "session_id": payload.get("session_id", "hub"),
        "history":    history,
    }

def build_accounting_payload(payload: Dict, history: List) -> Dict:
    return {
        "description": payload.get("message", ""),
        "session_id":  payload.get("session_id", "hub"),
        "history":     history,
        **{k: v for k, v in payload.items()
           if k not in ("message", "session_id", "intent", "history")},
    }


# ─── DRAGON HUB ──────────────────────────────────────────────────────────────

class DragonHub:
    """
    Entry point único.
    Uso no monolith :8108:

        from dragon_hub import hub

        @app.route("/dragon", methods=["POST"])
        async def dragon():
            data = request.get_json()
            result = await hub.handle(data, guardian_fallback=_old_guardian)
            return jsonify(result)
    """

    def __init__(self):
        self.sessions = SessionStore()

    def _session_id(self, payload: Dict) -> str:
        return (
            payload.get("session_id")
            or payload.get("wallet_id")
            or payload.get("did")
            or "anon"
        )

    async def handle(
        self,
        payload: Dict[str, Any],
        *,
        guardian_fallback: Callable,
    ) -> Dict[str, Any]:
        """
        Contrato de entrada (mínimo):
          message:    str
          session_id: str  (wallet_id / did / qualquer id estável)
          intent:     str  (opcional — Hub classifica se ausente)
          doc_type:   str  (opcional — para communique)
          meta:       dict (opcional — tier, isp, locale)
        """
        message    = payload.get("message", "") or ""
        session_id = self._session_id(payload)
        intent     = resolve_intent(message, payload.get("intent"))

        # Histórico real — não do React
        history = await self.sessions.get(session_id)

        # Registar mensagem do utilizador
        await self.sessions.append(session_id, "user", message)

        try:
            result = await self._dispatch(intent, payload, history)
        except httpx.HTTPStatusError as e:
            # Agent retornou erro HTTP — fallback gracioso
            result = await guardian_fallback(payload, history)
            result["hub_warning"] = f"agent_http_error: {e.response.status_code}"
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            # :8091 indisponível — sistema continua
            result = await guardian_fallback(payload, history)
            result["hub_warning"] = f"sandbox_unreachable: {type(e).__name__}"

        # Registar resposta
        reply_text = result.get("message") or result.get("response") or ""
        await self.sessions.append(session_id, "assistant", str(reply_text))

        return result

    async def _dispatch(
        self,
        intent: str,
        payload: Dict,
        history: List,
    ) -> Dict[str, Any]:

        # Intents que precisam de LLM vão para guardian
        if intent in GUARDIAN_INTENTS:
            raise ValueError(f"intent '{intent}' requires LLM → routes to guardian")

        if intent in ("legal", "evidence"):
            endpoint = AGENT_ROUTES[intent]
            res = await call_sandbox(
                endpoint,
                build_legal_payload(payload, history),
            )
            return {**res, "agent": "W-LEGAL-001", "intent": intent}

        if intent == "accounting":
            # Se tem dados de factura real → validar
            if payload.get("xml") or payload.get("amount") or payload.get("file"):
                res = await call_sandbox(
                    AGENT_ROUTES["accounting_validate"],
                    build_accounting_payload(payload, history),
                )
            else:
                # Query de chat → buscar stats (GET)
                res = await call_sandbox(
                    AGENT_ROUTES["accounting_stats"],
                    {"session_id": payload.get("session_id", "hub")},
                    method="GET"
                )
            return {**res, "agent": "W-ACCT-001", "intent": intent}

        if intent == "audit":
            # Se tem document_id → audit chain completo
            if payload.get("document_id"):
                res = await call_sandbox(
                    AGENT_ROUTES["audit_chain"],
                    {"document_id": payload.get("document_id")},
                )
            else:
                # Query de chat → buscar status (GET)
                res = await call_sandbox(
                    AGENT_ROUTES["audit_status"],
                    {},
                    method="GET"
                )
            return {**res, "agent": "W-AUDIT-001", "intent": intent}

        if intent == "notary":
            res = await call_sandbox(
                AGENT_ROUTES["notary"],
                {**payload, "history": history},
            )
            return {**res, "agent": "W-NOTARY-001", "intent": intent}

        if intent == "compliance":
            res = await call_sandbox(
                AGENT_ROUTES["compliance"],
                {**payload, "history": history},
            )
            return {**res, "agent": "W-COMPLY-001", "intent": intent}

        # Guardian — chat local, sem :8091
        raise ValueError(f"intent '{intent}' routes to guardian (not sandbox)")


# Instância global — importar e usar directamente
hub = DragonHub()
