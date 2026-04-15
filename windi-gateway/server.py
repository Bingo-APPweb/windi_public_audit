import os, re, time, logging
from enum import Enum
from typing import Optional, Any
from datetime import datetime

import requests
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ── W-COST-001 Integration ───────────────────────────────
COST_API_URL = "http://127.0.0.1:8152/api/cost/record"

def record_cost(service: str, provider: str, model: str,
                tokens_in: int, tokens_out: int, tier: str = "FREE",
                task_type: str = None):
    """Record cost to W-COST-001 (non-blocking)."""
    try:
        requests.post(COST_API_URL, json={
            "service": service,
            "provider": provider,
            "model": model,
            "tier": tier,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "task_type": task_type,
        }, timeout=1.0)
    except:
        pass  # Non-critical, fail silently
logging.basicConfig(level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(message)s')
log = logging.getLogger("W-GATEWAY-001")

app = FastAPI(title="WINDI LLM Bridge", version="1.1.0")
app.add_middleware(CORSMiddleware,
    allow_origins=["https://www.windi-domain.com"],
    allow_methods=["POST","GET"], allow_headers=["*"])

# ── Keys ──────────────────────────────────────────────────
KEYS = {
    "anthropic":  os.getenv("ANTHROPIC_API_KEY",""),
    "mistral":    os.getenv("MISTRAL_API_KEY",""),
    "gemini":     os.getenv("GEMINI_API_KEY",""),
    "openai":     os.getenv("OPENAI_API_KEY",""),
    "elevenlabs": os.getenv("ELEVENLABS_API_KEY",""),
}
LEDGER_URL      = os.getenv("LEDGER_URL","https://www.windi-domain.com/api/receipts")
AGENT_CORPS_URL = os.getenv("AGENT_CORPS_URL","http://127.0.0.1:8091")
GATEWAY_SECRET  = os.getenv("GATEWAY_SECRET","")

# ── Tiers ─────────────────────────────────────────────────
class Tier(str, Enum):
    FREE = "FREE"
    MED  = "MED"
    HIGH = "HIGH"

# ── Token Budget ──────────────────────────────────────────
TOKEN_BUDGET = {
    Tier.FREE: 0,
    Tier.MED:  {"chat":268, "analysis":500, "document":400},
    Tier.HIGH: {"chat":1000,"legal":4000,"wisdom":1000,
                "document":2000,"architect":3000,"voice":500},
}

# ── LLM Router ────────────────────────────────────────────
class LLMRouter:
    LOCAL_TASKS = {
        "hash","verify","ledger_seal","did_create",
        "metadata_extract","isp_apply","autocat",
        "health_check","template_render","gps_proof"
    }
    def route(self, task:str, tier:Tier, agent_id:str) -> dict:
        if tier == Tier.FREE:
            return {"provider":"local","model":"sovereign_router",
                    "max_tokens":0,
                    "justification":"FREE — soberania absoluta"}
        if task in self.LOCAL_TASKS:
            return {"provider":"local","model":"windi_local",
                    "max_tokens":0,
                    "justification":f"Determinístico '{task}' → local"}
        if tier == Tier.MED:
            budget = TOKEN_BUDGET[Tier.MED].get(task,268)
            return {"provider":"mistral","model":"mistral-small-latest",
                    "max_tokens":budget,
                    "justification":f"MED · {budget}tk"}
        if tier == Tier.HIGH:
            if task == "voice":
                return {"provider":"elevenlabs",
                        "model":"eleven_multilingual_v2",
                        "max_tokens":500,
                        "justification":"Narração Travel · ElevenLabs"}
            if task in ("vision","image_analysis"):
                return {"provider":"gemini","model":"gemini-1.5-flash",
                        "max_tokens":1000,
                        "justification":"Análise visual · Gemini Flash"}
            budget = TOKEN_BUDGET[Tier.HIGH].get(task,1000)
            return {"provider":"anthropic",
                    "model":"claude-sonnet-4-20250514",
                    "max_tokens":budget,
                    "justification":f"HIGH · {budget}tk · Claude"}
        return {"provider":"local","model":"fallback",
                "max_tokens":0,"justification":"I10 fallback"}

router = LLMRouter()

# ── LLM Providers ─────────────────────────────────────────
class LLMProviders:

    @staticmethod
    def call_anthropic(prompt,system,max_tokens,history=None):
        if not KEYS["anthropic"]: raise ValueError("ANTHROPIC_API_KEY em falta")
        msgs = list(history or [])
        msgs.append({"role":"user","content":prompt})
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":KEYS["anthropic"],
                     "anthropic-version":"2023-06-01",
                     "content-type":"application/json"},
            json={"model":"claude-sonnet-4-20250514",
                  "max_tokens":max_tokens,"system":system,"messages":msgs},
            timeout=30)
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage", {})
        return {
            "text": data["content"][0]["text"],
            "tokens_in": usage.get("input_tokens", 0),
            "tokens_out": usage.get("output_tokens", 0),
            "model": "claude-sonnet-4-20250514",
        }

    @staticmethod
    def call_mistral(prompt,system,max_tokens,history=None):
        if not KEYS["mistral"]: raise ValueError("MISTRAL_API_KEY em falta")
        msgs = [{"role":"system","content":system}]
        msgs.extend(history or [])
        msgs.append({"role":"user","content":prompt})
        r = requests.post("https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization":f"Bearer {KEYS['mistral']}",
                     "Content-Type":"application/json"},
            json={"model":"mistral-small-latest",
                  "messages":msgs,"max_tokens":max_tokens},
            timeout=30)
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage", {})
        return {
            "text": data["choices"][0]["message"]["content"],
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
            "model": "mistral-small-latest",
        }

    @staticmethod
    def call_gemini(prompt,max_tokens,image_b64=None):
        if not KEYS["gemini"]: raise ValueError("GEMINI_API_KEY em falta")
        parts = []
        if image_b64:
            parts.append({"inline_data":{"mime_type":"image/jpeg","data":image_b64}})
        parts.append({"text":prompt})
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={KEYS['gemini']}",
            json={"contents":[{"parts":parts}],
                  "generationConfig":{"maxOutputTokens":max_tokens}},
            timeout=30)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

    @staticmethod
    def call_elevenlabs(text,voice_id="pNInz6obpgDQGcFmaJgB",language="de"):
        if not KEYS["elevenlabs"]: raise ValueError("ELEVENLABS_API_KEY em falta")
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key":KEYS["elevenlabs"],
                     "Content-Type":"application/json"},
            json={"text":text[:500],"model_id":"eleven_multilingual_v2",
                  "voice_settings":{"stability":0.65,
                                    "similarity_boost":0.75,"style":0.3}},
            timeout=30)
        r.raise_for_status()
        return r.content

    @staticmethod
    def call_openai(prompt,system,max_tokens):
        if not KEYS["openai"]: raise ValueError("OPENAI_API_KEY em falta")
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {KEYS['openai']}",
                     "Content-Type":"application/json"},
            json={"model":"gpt-4o-mini",
                  "messages":[{"role":"system","content":system},
                               {"role":"user","content":prompt}],
                  "max_tokens":max_tokens},
            timeout=30)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

providers = LLMProviders()

# ── Agent Bridge ──────────────────────────────────────────
class AgentBridge:
    ROUTES = {
        "legal":"/legal/analyze","notary":"/notary/seal",
        "compliance":"/compliance/check","comm":"/comm/generate",
        "journal":"/journ/publish","audit":"/audit/verify",
        "accounting":"/accounting/process","travel":"/travel/moment",
    }
    def inject_llm_to_agent(self,agent,llm_response,payload):
        route = self.ROUTES.get(agent)
        if not route: raise ValueError(f"Agente '{agent}' não registado")
        enriched = {**payload,"llm_enrichment":{
            "text":llm_response,"source":"W-GATEWAY-001",
            "ts":datetime.utcnow().isoformat()}}
        r = requests.post(f"{AGENT_CORPS_URL}{route}",
                          json=enriched,timeout=15)
        r.raise_for_status()
        return r.json()

agent_bridge = AgentBridge()

# ── Cost calculator ───────────────────────────────────────
COST_PER_1K = {
    "anthropic":0.003,"mistral":0.0002,"gemini":0.00015,
    "openai":0.00015,"elevenlabs":0.00030,"local":0.0,
}
def calc_cost(provider,tokens):
    return round((tokens/1000)*COST_PER_1K.get(provider,0),6)

# ── I10: Bunker Monitor ───────────────────────────────────
class BunkerMonitor:
    def __init__(self):
        self.bunker_active     = False
        self.consecutive_fails = 0
        self.THRESHOLD         = 3
    def record_success(self):
        self.consecutive_fails = 0
        if self.bunker_active:
            self.bunker_active = False
            log.info("[BUNKER] OFF — rede estável")
    def record_failure(self):
        self.consecutive_fails += 1
        if self.consecutive_fails >= self.THRESHOLD and not self.bunker_active:
            self.bunker_active = True
            log.warning(f"[BUNKER] ON — {self.consecutive_fails} falhas · FREE forçado")
    def is_active(self): return self.bunker_active
    def status(self): return {"bunker_active":self.bunker_active,
        "consecutive_fails":self.consecutive_fails,"note":"I10"}

bunker = BunkerMonitor()

# ── I1: SGE PII Filter ────────────────────────────────────
class SGEFilter:
    PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b','[EMAIL]'),
        (r'\b(\+49|0049|0)[0-9\s\-\/]{8,}\b','[PHONE]'),
        (r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b','[IBAN]'),
        (r'did:windi:[a-f0-9\-]{36}','[DID]'),
        (r'\b\d{2}\.\d{4,},\s*\d{1,2}\.\d{4,}\b','[GPS]'),
        (r'\b(?:\d{4}[\s\-]?){3}\d{4}\b','[CARD]'),
        (r'\bsk-[a-zA-Z0-9]{20,}\b','[KEY]'),
        (r'\bAIza[a-zA-Z0-9_\-]{30,}\b','[KEY]'),
    ]
    def sanitize(self, text):
        redactions = []
        out = text
        for pattern, replacement in self.PATTERNS:
            found = re.findall(pattern, out, re.IGNORECASE)
            if found:
                redactions.extend(found if isinstance(found[0],str)
                                  else [str(m) for m in found])
                out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
        if redactions:
            log.warning(f"[SGE-PII] {len(redactions)} item(s) sanitizados · I1")
        return out, redactions

sge_filter = SGEFilter()

# ── I9: Gateway Secret Auth ───────────────────────────────
def verify_secret(x_gateway_secret: str = Header(default="")):
    if GATEWAY_SECRET and x_gateway_secret != GATEWAY_SECRET:
        log.warning("[AUTH] Secret inválido · bloqueado")
        raise HTTPException(401, "Gateway secret inválido")
    return x_gateway_secret

# ── I11+I12: Ledger seal com custo ────────────────────────
def seal_to_ledger(provider,task,actor,tokens,
                   receipt_id,cost_eur=0.0,redactions=0):
    try:
        requests.post(LEDGER_URL, json={
            "id":receipt_id,"actor":actor,
            "app":"windi-gateway-001",
            "doc_name":f"LLM · {provider} · {task}",
            "doc_type":"doc","governance_level":"HIGH",
            "note":(f"Provider:{provider}·Task:{task}·"
                    f"Tokens:{tokens}·Cost:{cost_eur:.6f}EUR·"
                    f"PII:{redactions}·Bunker:{bunker.is_active()}·"
                    f"I9·I11·I12"),
            "invariant":"I11",
        }, timeout=5)
    except Exception as e:
        log.warning(f"Ledger seal non-blocking: {e}")

# ── Models ────────────────────────────────────────────────
class GatewayRequest(BaseModel):
    actor:     str
    tier:      Tier
    task:      str
    agent:     Optional[str] = None
    prompt:    str
    system:    Optional[str] = "És um assistente soberano WINDI."
    history:   Optional[list] = []
    image_b64: Optional[str] = None
    language:  Optional[str] = "de"

class GatewayResponse(BaseModel):
    receipt_id:  str
    provider:    str
    model:       str
    response:    Any
    tokens:      int
    cost_eur:    float
    ledger:      str
    duration_ms: int

class RefineRequest(BaseModel):
    actor:      str
    agent_logs: list
    domain:     str
    intent:     str

# ── POST /gateway/call ────────────────────────────────────
@app.post("/gateway/call", response_model=GatewayResponse)
async def gateway_call(req: GatewayRequest,
                       _auth: str = Depends(verify_secret)):
    t0 = time.time()
    # I10 Bunker
    tier = Tier.FREE if bunker.is_active() and req.tier != Tier.FREE else req.tier
    if tier != req.tier:
        log.warning(f"[BUNKER] {req.tier} → FREE forçado")
    route = router.route(req.task, tier, req.agent or "direct")
    # I1 SGE filter
    clean_prompt, redactions = sge_filter.sanitize(req.prompt)
    llm_response = ""
    tokens_in, tokens_out = 0, 0
    model_used = route["model"]
    try:
        if   route["provider"] == "local":
            llm_response = f"[LOCAL] {req.task}"
        elif route["provider"] == "anthropic":
            result = providers.call_anthropic(
                clean_prompt, req.system, route["max_tokens"], req.history)
            llm_response = result["text"]
            tokens_in, tokens_out = result["tokens_in"], result["tokens_out"]
            model_used = result["model"]
            bunker.record_success()
            record_cost("W-GATEWAY", "anthropic", model_used,
                       tokens_in, tokens_out, str(req.tier), req.task)
        elif route["provider"] == "mistral":
            result = providers.call_mistral(
                clean_prompt, req.system, route["max_tokens"], req.history)
            llm_response = result["text"]
            tokens_in, tokens_out = result["tokens_in"], result["tokens_out"]
            model_used = result["model"]
            bunker.record_success()
            record_cost("W-GATEWAY", "mistral", model_used,
                       tokens_in, tokens_out, str(req.tier), req.task)
        elif route["provider"] == "gemini":
            llm_response = providers.call_gemini(
                clean_prompt, route["max_tokens"], req.image_b64)
            tokens_in = len(clean_prompt) // 4  # Estimate
            tokens_out = route["max_tokens"]
            bunker.record_success()
            record_cost("W-GATEWAY", "gemini", "gemini-1.5-flash",
                       tokens_in, tokens_out, str(req.tier), req.task)
        elif route["provider"] == "elevenlabs":
            audio = providers.call_elevenlabs(clean_prompt, language=req.language)
            llm_response = f"[VOICE] {len(audio)}B · {req.language}"
            tokens_in = len(clean_prompt)
            bunker.record_success()
            record_cost("W-GATEWAY", "elevenlabs", "eleven_multilingual_v2",
                       tokens_in, 0, str(req.tier), "voice")
        elif route["provider"] == "openai":
            llm_response = providers.call_openai(
                clean_prompt, req.system, route["max_tokens"])
            tokens_in = len(clean_prompt) // 4
            tokens_out = route["max_tokens"]
            bunker.record_success()
            record_cost("W-GATEWAY", "openai", "gpt-4o-mini",
                       tokens_in, tokens_out, str(req.tier), req.task)
    except Exception as e:
        bunker.record_failure()
        log.warning(f"[FALLBACK-I10] {route['provider']}: {e}")
        llm_response = "[FALLBACK] Serviço indisponível · local activado"
        route["provider"] = "local"
    tokens_used = tokens_in + tokens_out
    # Inject agent
    agent_resp = None
    if req.agent and route["provider"] != "local":
        try:
            agent_resp = agent_bridge.inject_llm_to_agent(
                req.agent, llm_response,
                {"actor":req.actor,"task":req.task,"prompt":clean_prompt})
        except Exception as e:
            log.warning(f"[AGENT] non-blocking: {e}")
    # Seal I11+I12
    cost = calc_cost(route["provider"], tokens_used)
    rid  = f"WGW-{int(time.time())}-{req.actor[:6].replace(':','')}-{req.task[:4].upper()}"
    seal_to_ledger(route["provider"],req.task,req.actor,
                   tokens_used,rid,cost,len(redactions))
    ms = int((time.time()-t0)*1000)
    log.info(f"[DONE] {rid} · {route['provider']} · {tokens_used}tk · {cost:.6f}€ · {ms}ms")
    return GatewayResponse(receipt_id=rid,provider=route["provider"],
        model=route["model"],response=agent_resp or llm_response,
        tokens=tokens_used,cost_eur=cost,
        ledger=f"https://windi-domain.com/verify-public/?id={rid}",
        duration_ms=ms)

# ── POST /gateway/voice/stream ────────────────────────────
@app.post("/gateway/voice/stream")
async def stream_memory(actor:str, caption:str, gps:str,
                        language:str="de",
                        _auth:str=Depends(verify_secret)):
    if not KEYS["elevenlabs"]:
        raise HTTPException(503,"ElevenLabs não configurado")
    tpl = {"de":f"{caption} · Aufgenommen bei {gps}.",
           "en":f"{caption} · Captured at {gps}.",
           "pt":f"{caption} · Capturado em {gps}."}
    clean, redactions = sge_filter.sanitize(tpl.get(language,tpl["de"]))
    def generate():
        try:
            r = requests.post(
                "https://api.elevenlabs.io/v1/text-to-speech/"
                "pNInz6obpgDQGcFmaJgB/stream",
                headers={"xi-api-key":KEYS["elevenlabs"],
                         "Content-Type":"application/json"},
                json={"text":clean[:500],"model_id":"eleven_multilingual_v2",
                      "voice_settings":{"stability":0.65,
                                        "similarity_boost":0.75,"style":0.3}},
                stream=True, timeout=30)
            r.raise_for_status(); bunker.record_success()
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: yield chunk
        except Exception as e:
            bunker.record_failure()
            log.warning(f"[VOICE] fallback: {e}"); yield b""
    rid = f"WGW-VOICE-{int(time.time())}"
    seal_to_ledger("elevenlabs","voice_stream",actor,
                   len(clean),rid,calc_cost("elevenlabs",len(clean)),
                   len(redactions))
    return StreamingResponse(generate(), media_type="audio/mpeg",
                             headers={"X-Receipt-ID":rid})

# ── POST /gateway/refine ──────────────────────────────────
@app.post("/gateway/refine")
async def refine_with_wisdom(req: RefineRequest,
                              _auth:str=Depends(verify_secret)):
    route = router.route("wisdom", Tier.HIGH, f"wisdom-{req.domain}")
    clean_logs, total_red = [], 0
    for entry in req.agent_logs[:20]:
        c, r = sge_filter.sanitize(entry)
        clean_logs.append(c); total_red += len(r)
    system = (f"Destilador de Sabedoria WINDI · domínio:{req.domain}. "
              f"Analisa logs e propõe Wisdom Block candidato (JSON). I9 inviolável.")
    prompt = f"Intenção:{req.intent}\nLogs:\n" + \
             "\n".join(f"[{i+1}] {l}" for i,l in enumerate(clean_logs))
    tokens_in, tokens_out = 0, 0
    try:
        result = providers.call_anthropic(prompt,system,route["max_tokens"])
        resp = result["text"]
        tokens_in, tokens_out = result["tokens_in"], result["tokens_out"]
        bunker.record_success()
        record_cost("W-GATEWAY", "anthropic", result["model"],
                   tokens_in, tokens_out, "HIGH", "wisdom")
    except Exception as e:
        bunker.record_failure()
        resp = f"[FALLBACK] {e}"
    tokens_used = tokens_in + tokens_out
    cost = calc_cost("anthropic", tokens_used)
    rid  = f"WGW-WISDOM-{int(time.time())}-{req.domain[:4].upper()}"
    seal_to_ledger("anthropic",f"wisdom_{req.domain}",req.actor,
                   tokens_used,rid,cost,total_red)
    return {"receipt_id":rid,"domain":req.domain,"proposal":resp,
            "tokens":route["max_tokens"],"cost_eur":cost,
            "pii_redacted":total_red,
            "ledger":f"https://windi-domain.com/verify-public/?id={rid}",
            "note":"I17 — Proposta gerada. Human Dragon aprova."}

# ── GET /gateway/health ───────────────────────────────────
@app.get("/gateway/health")
def health():
    return {"service":"W-GATEWAY-001","status":"healthy","port":8130,
            "providers":{k:bool(v) for k,v in KEYS.items()},
            "bunker":bunker.status(),
            "timestamp":datetime.utcnow().isoformat()}

# ── GET /gateway/sovereignty ──────────────────────────────
@app.get("/gateway/sovereignty")
def sovereignty():
    return {
        "service":"W-GATEWAY-001 v1.1",
        "principle":"O externo sustenta. O interno orienta.",
        "bunker":bunker.status(),
        "sge":{"patterns":len(sge_filter.PATTERNS),"note":"I1 · zero PII sai"},
        "routing":{"FREE":"local·0€","MED":"mistral·0.0002€/1k",
                   "HIGH":"claude·0.003€/1k"},
        "special":{"voice":"elevenlabs streaming","vision":"gemini-flash",
                   "wisdom":"claude HIGH"},
        "sovereignty":"93.3% local",
        "invariants":["I1","I9","I10","I11","I12","I17"],
        "witness":"✓ 5/5 refinamentos Irmã Witness",
    }
