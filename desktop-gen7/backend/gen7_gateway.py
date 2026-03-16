#!/usr/bin/env python3
"""
WINDI Desktop GEN 7 — Smart Zones Gateway (FastAPI)
====================================================
Port: 8109 (staging) → 8100 (production swap)

Smart Zones:
- D1: Agent Corps (Constellation)
- D2: Sovereign Editor (Canvas/Code)
- D3: Governance Glass (Forensics)

Principle: "AI processes. Human decides. WINDI guarantees."
"""

import os
import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── SLIDES: Import chave centralizada ──────────────────────────────
import sys as _sys
_sys.path.insert(0, "/opt/windi/engine")
try:
    from dragon_apis import ANTHROPIC_API_KEY as _ANTHROPIC_KEY
except Exception:
    _ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SLIDES_SYSTEM_PROMPT = """És W-COMM-001, agente de comunicação institucional WINDI.
REGRA ABSOLUTA: Responde APENAS com HTML válido. NUNCA texto corrido. NUNCA markdown. NUNCA JSON.

Gera IMEDIATAMENTE uma apresentação com este formato exacto:

<div class="windi-slides">
  <div class="slide slide-cover">
    <p class="slide-ep">EP.1 — [TEMA EXTRAÍDO DO INTENT]</p>
    <h1>[TÍTULO PRINCIPAL]</h1>
    <p class="slide-sub">[SUBTÍTULO PROVOCADOR]</p>
    <footer class="slide-brand">WINDI <span>Publishing House</span></footer>
  </div>
  <div class="slide slide-content">
    <h2>[TÍTULO SLIDE 2]</h2>
    <ul><li>[PONTO 1 CONCRETO]</li><li>[PONTO 2 CONCRETO]</li><li>[PONTO 3 CONCRETO]</li></ul>
  </div>
  <div class="slide slide-content">
    <h2>[TÍTULO SLIDE 3]</h2>
    <p>[PARÁGRAFO EXPLICATIVO — máx 40 palavras]</p>
  </div>
  <div class="slide slide-content">
    <h2>[TÍTULO SLIDE 4]</h2>
    <ul><li>[PONTO A]</li><li>[PONTO B]</li></ul>
  </div>
  <div class="slide slide-final">
    <h2>[CALL TO ACTION]</h2>
    <p>WINDI</p>
    <p class="slide-sub">Publishing House · Kempten, Bavaria</p>
  </div>
</div>

REGRAS:
- Mínimo 5 slides, máximo 10
- Slide 1: sempre slide-cover
- Último slide: sempre slide-final
- Conteúdo real baseado no intent — NUNCA placeholders genéricos
- Idioma: detectar automaticamente pelo intent (PT/DE/EN)
- NUNCA perguntar. NUNCA menus. PRODUZ HTML AGORA."""

WEB_SYSTEM_PROMPT = """És W-COMM-001, especialista em web design institucional WINDI.
REGRA ABSOLUTA: Output = HTML completo num único ficheiro. NUNCA frameworks externos.

Gera IMEDIATAMENTE uma página web com estrutura:
<html><head><style>/* CSS inline responsivo */</style></head>
<body>
  <section class="windi-hero">/* Hero com título + CTA */</section>
  <section class="windi-about">/* Sobre */</section>
  <section class="windi-services">/* Serviços/Features 3 colunas */</section>
  <section class="windi-cta">/* Call to action */</section>
  <footer class="windi-footer">/* Footer WINDI */</footer>
<script>/* JS inline mínimo */</script>
</body></html>

REGRAS:
- Paleta KLAR (#F5F0E0 bg, #2C2924 texto, #8B6914 gold) ou NOIR (#0E0E14 bg)
- Mobile-first, responsivo, sem dependências externas
- Conteúdo real baseado no intent — NUNCA placeholders
- Idioma detectado automaticamente (PT/DE/EN)
- NUNCA perguntar. PRODUZ HTML COMPLETO AGORA."""

ART_SYSTEM_PROMPT = """És W-COMM-001, especialista em design gráfico institucional WINDI.
REGRA ABSOLUTA: Output = SVG completo e autocontido. NUNCA imagens externas.

Gera IMEDIATAMENTE um SVG artístico com:
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
  <defs>/* gradients, fonts, filters */</defs>
  <!-- Fundo, elementos visuais, tipografia, branding -->
  <!-- Composição profissional: hierarquia visual clara -->
</svg>

REGRAS:
- Paleta WINDI: #8B6914 (gold), #0a0a0a (escuro), #F5F0E0 (claro)
- Tipografia via SVG text com font-family institucional
- Composição equilibrada: título dominante + subtítulo + elementos visuais
- Branding WINDI no rodapé (discreto)
- Conteúdo real baseado no intent — NUNCA placeholders
- Idioma detectado automaticamente (PT/DE/EN)
- NUNCA perguntar. PRODUZ SVG AGORA."""

DATA_SYSTEM_PROMPT = """És W-COMM-001, especialista em visualização de dados WINDI.
REGRA ABSOLUTA: Output = HTML completo com charts via Chart.js CDN.

Gera IMEDIATAMENTE um dashboard com:
<html><head>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>/* CSS dashboard inline */</style>
</head>
<body class="windi-dashboard">
  <header>/* Título + métricas principais */</header>
  <main>/* Grid de charts: bar, line, doughnut conforme dados */</main>
  <footer>/* Fonte + timestamp */</footer>
<script>/* Chart.js configs com dados reais do intent */</script>
</body></html>

REGRAS:
- Cores WINDI nos charts: #8B6914, #2C2924, #6B6560, #DDD6C2
- Dados inventados mas plausíveis baseados no intent
- Mínimo 2 charts, máximo 4
- Layout responsivo tipo corretora de valores
- Idioma detectado automaticamente (PT/DE/EN)
- NUNCA perguntar. PRODUZ HTML AGORA."""

CODE_SYSTEM_PROMPT = """És W-COMM-001, especialista em documentação técnica WINDI.
REGRA ABSOLUTA: Output = HTML com código syntax-highlighted via highlight.js CDN.

Gera IMEDIATAMENTE documentação técnica com:
<html><head>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <style>/* CSS docs inline */</style>
</head>
<body class="windi-docs">
  <nav>/* Índice lateral */</nav>
  <main>
    <h1>/* Título */</h1>
    <section>/* Descrição + exemplos de código */</section>
    <pre><code class="language-python">/* Código real */</code></pre>
  </main>
<script>hljs.highlightAll();</script>
</body></html>

REGRAS:
- Código real e funcional baseado no intent
- Comentários em PT/DE/EN conforme idioma detectado
- Estrutura: Overview → Instalação → Uso → Exemplos → API Reference
- NUNCA perguntar. PRODUZ HTML AGORA."""

MEDIA_SYSTEM_PROMPT = """És W-COMM-001, especialista em comunicação digital WINDI.
REGRA ABSOLUTA: Output = HTML completo pronto para envio/publicação.

Gera IMEDIATAMENTE conteúdo media com estrutura:
<html><head><style>/* CSS email/social inline, máx 600px width */</style></head>
<body class="windi-media">
  <header class="media-header">/* Logo WINDI + data */</header>
  <section class="media-hero">/* Título principal + imagem placeholder SVG */</section>
  <section class="media-body">/* Conteúdo principal em blocos */</section>
  <section class="media-cta">/* Call to action com botão */</section>
  <footer class="media-footer">/* Unsubscribe + contacto */</footer>
</body></html>

REGRAS:
- Layout 600px max-width (compatível email + social)
- Inline CSS para compatibilidade máxima
- Conteúdo real baseado no intent
- Tom adequado: newsletter=informativo, press kit=formal, social=conciso
- Idioma detectado automaticamente (PT/DE/EN)
- NUNCA perguntar. PRODUZ HTML AGORA."""

# === Configuration ===
PORT = int(os.getenv("PORT", "8119"))
DRAGON_URL = os.getenv("DRAGON_URL", "http://localhost:8108")
LEDGER_URL = os.getenv("LEDGER_URL", "http://localhost:8101")
SANDBOX_URL = os.getenv("SANDBOX_URL", "http://localhost:8091")
STATIC_DIR = Path(os.getenv("STATIC_DIR", "/opt/windi/desktop-gen7/frontend"))
LOG_DIR = Path(os.getenv("LOG_DIR", "/opt/windi/logs"))

# Agent Corps endpoints for health checks
AGENT_CORPS = {
    "W-COMM-001": {"port": 8091, "health": "/communique/health", "name": "Communique"},
    "W-LEGAL-001": {"port": 8091, "health": "/legal/health", "name": "Justica"},
    "W-NOTARY-001": {"port": 8091, "health": "/notary/health", "name": "Notarial"},
    "W-JOURN-001": {"port": 8091, "health": "/journalist/health", "name": "Journalist"},
    "W-AUDIT-001": {"port": 8091, "health": "/audit/health", "name": "Auditor"},
    "W-COMPLY-001": {"port": 8091, "health": "/compliance/health", "name": "Compliance"},
    "W-ACCT-001": {"port": 8091, "health": "/accounting/health", "name": "Accountant"},
    "GROVE-ARENA": {"port": 8091, "health": "/grove/health", "name": "Grove Arena"},
}

# Core services for ecosystem health
CORE_SERVICES = {
    "dragon": {"url": f"{DRAGON_URL}/health", "critical": True},
    "ledger": {"url": f"{LEDGER_URL}/health", "critical": True},
    "sandbox": {"url": f"{SANDBOX_URL}/agent/health", "critical": True},
}

# Uptime tracking
GEN7_START_TIME = time.time()


# === Pydantic Models ===
class KeyValidateRequest(BaseModel):
    key_type: str  # "anthropic" | "openai" | "mistral"
    key_prefix: str  # First 8 chars only for validation


class OneTouchRequest(BaseModel):
    intent: str
    wallet_id: str
    agent: Optional[str] = None
    doc_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OneTouchResponse(BaseModel):
    session_id: str
    stage: str
    agent: str
    message: str
    next_step: str


# === Lifespan ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[GEN7] Desktop GEN 7 Gateway starting on :{PORT}")
    print(f"[GEN7] Dragon: {DRAGON_URL}")
    print(f"[GEN7] Ledger: {LEDGER_URL}")
    print(f"[GEN7] Sandbox: {SANDBOX_URL}")
    yield
    print("[GEN7] Shutting down...")


# === App ===
app = FastAPI(
    title="WINDI Desktop GEN 7",
    description="Smart Zones Gateway — AI processes. Human decides. WINDI guarantees.",
    version="7.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Health ===
@app.get("/health")
async def health():
    """GEN 7 health check with ecosystem status."""
    ecosystem = {}

    async with httpx.AsyncClient(timeout=3.0) as client:
        # Check core services
        for name, cfg in CORE_SERVICES.items():
            try:
                r = await client.get(cfg["url"])
                ecosystem[name] = {
                    "status": "UP" if r.status_code == 200 else "DEGRADED",
                    "code": r.status_code,
                    "critical": cfg["critical"],
                }
            except Exception:
                ecosystem[name] = {
                    "status": "DOWN",
                    "code": 0,
                    "critical": cfg["critical"],
                }

    # Count status
    up_count = sum(1 for s in ecosystem.values() if s["status"] == "UP")
    critical_down = any(
        s["status"] == "DOWN" and s["critical"]
        for s in ecosystem.values()
    )

    return {
        "service": "windi-desktop-gen7",
        "version": "7.0.0",
        "status": "degraded" if critical_down else "operational",
        "principle": "AI processes. Human decides. WINDI guarantees.",
        "port": PORT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ecosystem": {
            "services": ecosystem,
            "total": len(ecosystem),
            "up": up_count,
        },
        "smart_zones": {
            "D1": "Agent Corps",
            "D2": "Sovereign Editor",
            "D3": "Governance Glass",
        },
    }


# === API Keys Validation ===
@app.post("/api/keys/validate")
async def validate_api_key(req: KeyValidateRequest):
    """
    Validate API key format (not the actual key).
    Keys are NEVER sent to this endpoint - only prefix for format check.
    """
    valid_prefixes = {
        "anthropic": ["sk-ant-"],
        "openai": ["sk-"],
        "mistral": ["mistral-"],
    }

    if req.key_type not in valid_prefixes:
        raise HTTPException(400, f"Unknown key type: {req.key_type}")

    is_valid = any(
        req.key_prefix.startswith(prefix)
        for prefix in valid_prefixes[req.key_type]
    )

    return {
        "key_type": req.key_type,
        "format_valid": is_valid,
        "message": "Format validated" if is_valid else "Invalid key prefix",
        "note": "This validates format only. Actual key validation happens server-side.",
    }


# === Dragon Status (Pulse) ===
@app.get("/api/dragon/status")
async def dragon_status():
    """
    Dragon Pulse — proxy health status from :8108.
    Used by Command Bar indicator.
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{DRAGON_URL}/health")
            if r.status_code == 200:
                data = r.json()
                return {
                    "pulse": "ACTIVE",
                    "dragon_version": data.get("version", "unknown"),
                    "model": data.get("model", "unknown"),
                    "latency_ms": r.elapsed.total_seconds() * 1000,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                return {
                    "pulse": "DEGRADED",
                    "code": r.status_code,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except httpx.TimeoutException:
            return {
                "pulse": "TIMEOUT",
                "message": "Dragon not responding",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "pulse": "DOWN",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# === Institutional Status Panel ===
@app.get("/api/status")
async def institutional_status():
    """
    Institutional Status Panel — aggregates all WINDI services.
    Used by /status.html for live dashboard.
    """
    async def probe(url: str, timeout: float = 3.0) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=timeout)
                data = r.json() if r.status_code == 200 else {}
                return {"ok": r.status_code == 200, "data": data, "ms": int(r.elapsed.total_seconds() * 1000)}
        except Exception as e:
            return {"ok": False, "data": {}, "ms": -1, "error": str(e)}

    uptime_s = int(time.time() - GEN7_START_TIME)
    uptime_h = f"{uptime_s // 3600}h {(uptime_s % 3600) // 60}m"

    dragon = await probe(f"{DRAGON_URL}/health")
    ledger = await probe(f"{LEDGER_URL}/health")
    sandbox = await probe(f"{SANDBOX_URL}/agent/health")

    # Receipt count from Ledger /health
    receipt_count = ledger["data"].get("receipts") if ledger["ok"] else None

    return {
        "gen7": {
            "version": "7.0.0",
            "status": "operational",
            "uptime": uptime_h,
            "uptime_s": uptime_s,
            "smart_zones": {"D1": True, "D2": True, "D3": True}
        },
        "dragon": {
            "ok": dragon["ok"],
            "version": dragon["data"].get("version", "—"),
            "ms": dragon["ms"]
        },
        "ledger": {
            "ok": ledger["ok"],
            "receipts": receipt_count,
            "ms": ledger["ms"]
        },
        "sandbox": {
            "ok": sandbox["ok"],
            "agents": len(AGENT_CORPS),
            "ms": sandbox["ms"]
        },
        "timestamp": int(time.time()),
        "principle": "AI processes. Human decides. WINDI guarantees."
    }


# === One Touch Execute ===
@app.post("/api/onetouch/execute", response_model=OneTouchResponse)
async def onetouch_execute(req: OneTouchRequest):
    """
    One Touch Pipeline — single entry point for all document operations.

    Phase 1: Intent Capture
    Phase 2: Agent Routing (auto-detect or explicit)
    Phase 3: Bridge Session Creation
    Phase 4: Return session for Canvas materialization
    """
    # Phase 1: Intent received
    intent_hash = hashlib.sha256(req.intent.encode()).hexdigest()[:8]

    # Phase 2: Agent routing
    agent = req.agent
    if not agent:
        # Auto-detect based on intent keywords
        intent_lower = req.intent.lower()
        if any(kw in intent_lower for kw in ["contrato", "contract", "legal", "jurídico"]):
            agent = "W-LEGAL-001"
        elif any(kw in intent_lower for kw in ["certidão", "certificate", "notarial", "seal", "selar", "forense", "evidência", "hash", "ledger"]):
            agent = "W-NOTARY-001"
        elif any(kw in intent_lower for kw in ["artigo", "article", "publicar", "editorial"]):
            agent = "W-JOURN-001"
        elif any(kw in intent_lower for kw in ["fatura", "invoice", "fiscal", "financeiro", "imposto", "tax", "elster", "buchung"]):
            agent = "W-ACCT-001"
        elif any(kw in intent_lower for kw in ["audit", "auditoria", "verificar", "compliance", "relatório"]):
            agent = "W-AUDIT-001"
        else:
            agent = "W-COMM-001"  # Default: Communique

    # Phase 3: Create bridge session
    bridge_map = {
        "W-COMM-001": "/communique/bridge/open",
        "W-LEGAL-001": "/legal/bridge/open",
        "W-NOTARY-001": "/notary/bridge/open",
        "W-JOURN-001": "/journalist/bridge/open",
        "W-ACCT-001": "/accounting/bridge/open",
        "W-AUDIT-001": "/audit/bridge/open",
    }

    bridge_endpoint = bridge_map.get(agent, "/communique/bridge/open")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(
                f"{SANDBOX_URL}{bridge_endpoint}",
                json={
                    "wallet_id": req.wallet_id,
                    "doc_type": req.doc_type or "document",
                    "title": req.intent[:50],
                    "metadata": req.metadata or {},
                },
            )

            if r.status_code in (200, 201):
                data = r.json()
                session_id = data.get("session_id", f"OT-{intent_hash}")

                # Phase 4: Call Dragon to generate draft (HTML Canvas mode)
                # ── Intent detection: 7 motores ───────────────────────────
                _intent_lower = req.intent.lower()
                _is_slides = any(kw in _intent_lower for kw in [
                    "präsentation", "presentation", "slides", "slide deck",
                    "apresentação", "apresentacao", "slide", "pitchdeck", "pitch deck"
                ])
                _is_web = any(kw in _intent_lower for kw in [
                    "website", "página web", "pagina web", "landing page",
                    "site", "webpage", "microsite", "portfólio web", "portfolio web"
                ])
                _is_art = any(kw in _intent_lower for kw in [
                    "poster", "flyer", "capa", "cartaz", "banner",
                    "identidade visual", "arte", "design gráfico", "design grafico",
                    "ilustração", "ilustracao", "svg"
                ])
                _is_data = any(kw in _intent_lower for kw in [
                    "dashboard", "infográfico", "infografico", "gráfico", "grafico",
                    "chart", "relatório visual", "relatorio visual", "dados visuais",
                    "visualização", "visualizacao"
                ])
                _is_code = any(kw in _intent_lower for kw in [
                    "script", "código", "codigo", "api", "função", "funcao",
                    "documentação técnica", "documentacao tecnica", "programar",
                    "endpoint", "biblioteca", "library"
                ])
                _is_media = any(kw in _intent_lower for kw in [
                    "newsletter", "press kit", "social", "instagram", "linkedin",
                    "post", "email marketing", "campanha", "comunicado de imprensa"
                ])

                # Seleccionar system prompt pelo motor detectado
                _active_motor = None
                _active_prompt = None
                if _is_slides:
                    _active_motor, _active_prompt = "SLIDES", SLIDES_SYSTEM_PROMPT
                elif _is_web:
                    _active_motor, _active_prompt = "WEB", WEB_SYSTEM_PROMPT
                elif _is_art:
                    _active_motor, _active_prompt = "ART", ART_SYSTEM_PROMPT
                elif _is_data:
                    _active_motor, _active_prompt = "DATA", DATA_SYSTEM_PROMPT
                elif _is_code:
                    _active_motor, _active_prompt = "CODE", CODE_SYSTEM_PROMPT
                elif _is_media:
                    _active_motor, _active_prompt = "MEDIA", MEDIA_SYSTEM_PROMPT

                if _active_motor and _ANTHROPIC_KEY:
                    # Motor detectado: Claude directo com system prompt específico
                    import anthropic as _anthropic
                    import asyncio as _asyncio
                    def _call_motor():
                        _c = _anthropic.Anthropic(api_key=_ANTHROPIC_KEY)
                        _r = _c.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=4000,
                            system=_active_prompt,
                            messages=[{"role": "user", "content": req.intent}]
                        )
                        return _r.content[0].text
                    draft_message = await _asyncio.to_thread(_call_motor)

                    # ── Ledger logging para osmose (training) ──────────────
                    try:
                        _ledger_payload = {
                            "id": f"WINDI-{_active_motor}-{session_id}",
                            "actor": "gen7-gateway",
                            "app": f"canvas-{_active_motor.lower()}",
                            "doc_name": req.intent[:80],
                            "doc_type": "doc",  # Ledger requires valid type
                            "governance_level": "HIGH",
                            "content_hash": hashlib.sha256(draft_message.encode()).hexdigest(),
                            "sge_score": 1.0,  # Required by Ledger
                            "metadata": {
                                "intent": req.intent,
                                "model": "claude-sonnet-4-20250514",
                                "tokens_estimate": 4000,
                                "training_eligible": True,
                                "canvas_type": _active_motor.lower(),
                            }
                        }
                        # Await with short timeout (don't block Canvas long)
                        await client.post(
                            f"{LEDGER_URL}/api/receipts",
                            json=_ledger_payload,
                            timeout=2.0
                        )
                    except Exception:
                        pass  # Ledger logging is optional, never block Canvas
                else:
                    canvas_instruction = f"""[CANVAS HTML MODE — GERA IMEDIATAMENTE]

INTENT DO UTILIZADOR: {req.intent}

REGRA ABSOLUTA: Gera o DOCUMENTO AGORA. NÃO faças perguntas. NÃO mostres menus. PRODUZ HTML.

<article class="windi-doc">
  <header class="doc-header"><h1 class="doc-title">[TÍTULO]</h1><p class="doc-meta">[DATA]</p></header>
  <section class="doc-body">[CONTEÚDO]</section>
  <footer class="doc-footer">[ASSINATURA]</footer>
</article>

NUNCA markdown. NUNCA menus. NUNCA perguntas. PRODUZ HTML AGORA."""

                    try:
                        dragon_r = await client.post(
                            f"{DRAGON_URL}/api/dragon/chat",
                            json={
                                "message": canvas_instruction,
                                "tier": "HIGH",
                                "session_id": session_id,
                                "doc_type": agent,
                                "history": [],
                                "intentMode": "document",  # Force ARCHITECT
                                "chatType": "document",    # Force document mode
                            },
                            timeout=30.0,
                        )
                        if dragon_r.status_code == 200:
                            dragon_data = dragon_r.json()
                            draft_message = dragon_data.get("message", "Rascunho em preparação...")
                            # Sanitize: remove any code blocks and JSON that Dragon may append
                            import re
                            # Remove ```json ... ``` blocks
                            draft_message = re.sub(r'```json[\s\S]*?```', '', draft_message)
                            # Remove ```html ... ``` wrappers (keep content)
                            draft_message = re.sub(r'```html\s*', '', draft_message)
                            draft_message = re.sub(r'```\s*$', '', draft_message)
                            # Remove trailing JSON objects
                            draft_message = re.sub(r'\n*\{"document":\s*\{[\s\S]*$', '', draft_message)
                            draft_message = re.sub(r'\n*\{"title":\s*"[\s\S]*$', '', draft_message)
                            # Clean up
                            draft_message = draft_message.strip()
                        else:
                            draft_message = f"Sessão {session_id} criada. Dragon indisponível."
                    except Exception:
                        draft_message = f"Sessão {session_id} criada. Aguarda input manual."

                return OneTouchResponse(
                    session_id=session_id,
                    stage=data.get("stage", "C2"),  # C2 = draft generated
                    agent=agent,
                    message=draft_message,
                    next_step="Rascunho pronto. Edita em D2 e clica Finalizar.",
                )
            else:
                raise HTTPException(r.status_code, f"Bridge error: {r.text}")

        except httpx.TimeoutException:
            raise HTTPException(504, "Bridge timeout")
        except Exception as e:
            raise HTTPException(500, str(e))


# === Agent Corps Status ===
@app.get("/api/agents/status")
async def agents_status():
    """
    Agent Corps Constellation — health of all 8 agents.
    Used by D1 (Agent Corps) zone.
    """
    agents = {}

    async with httpx.AsyncClient(timeout=3.0) as client:
        for agent_id, cfg in AGENT_CORPS.items():
            url = f"http://localhost:{cfg['port']}{cfg['health']}"
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    data = r.json()
                    agents[agent_id] = {
                        "name": cfg["name"],
                        "status": data.get("status", "UP"),
                        "version": data.get("version", "unknown"),
                        "latency_ms": round(r.elapsed.total_seconds() * 1000, 1),
                    }
                else:
                    agents[agent_id] = {
                        "name": cfg["name"],
                        "status": "DEGRADED",
                        "code": r.status_code,
                    }
            except Exception:
                agents[agent_id] = {
                    "name": cfg["name"],
                    "status": "DOWN",
                }

    # Summary
    live = sum(1 for a in agents.values() if a["status"] in ["UP", "GREEN"])

    return {
        "constellation": "WINDI Agent Corps",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(agents),
            "live": live,
            "status": "FULL" if live == len(agents) else "PARTIAL",
        },
        "agents": agents,
    }


# === Canvas Seal ===
class SealRequest(BaseModel):
    session_id: str
    content_hash: str
    doc_type: Optional[str] = "canvas-output"


@app.post("/api/seal")
async def seal_canvas_output(req: SealRequest):
    """
    Seal Canvas output to Forensic Ledger.
    Called by frontend Download/Seal buttons.
    """
    receipt_id = f"WINDI-CANVAS-{req.session_id}"

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            ledger_payload = {
                "id": receipt_id,
                "actor": "gen7-canvas",
                "app": "desktop-gen7",
                "doc_name": f"Canvas Output {req.session_id}",
                "doc_type": "doc",
                "governance_level": "HIGH",
                "content_hash": req.content_hash,
                "sge_score": 1.0,
                "metadata": {
                    "session_id": req.session_id,
                    "canvas_type": req.doc_type,
                    "sealed_by": "human",
                }
            }
            r = await client.post(
                f"{LEDGER_URL}/api/receipts",
                json=ledger_payload
            )
            if r.status_code == 200:
                return {
                    "ok": True,
                    "receipt_id": receipt_id,
                    "content_hash": req.content_hash[:16] + "...",
                    "message": "Selado no Forensic Ledger"
                }
            else:
                raise HTTPException(r.status_code, f"Ledger error: {r.text}")
        except httpx.TimeoutException:
            raise HTTPException(504, "Ledger timeout")
        except Exception as e:
            raise HTTPException(500, str(e))


# === Static Files ===
@app.get("/")
async def root(request: Request):
    """Serve index.html — unified experience for all devices (GEN 7 Canvas)"""
    template_path = STATIC_DIR / "index.html"
    if template_path.exists():
        return FileResponse(template_path)
    return {"message": "WINDI Desktop GEN 7", "status": "frontend pending"}


@app.get("/status.html")
async def status_page():
    """Serve institutional status dashboard"""
    status_path = STATIC_DIR / "status.html"
    if status_path.exists():
        return FileResponse(status_path)
    return JSONResponse({"error": "status.html not found"}, status_code=404)


# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR / "static"), name="static")


# === Main ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
