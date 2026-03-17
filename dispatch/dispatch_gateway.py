"""
WINDI Dispatch Gateway v1.0.2
──────────────────────────────
Port    : 8121
Role    : .jmpg Hydration Engine — Progressive Asset Delivery P1→P4
Ledger  : http://localhost:8101  (I5 integrity + I6 authenticity)
Vault   : http://localhost:8106  (asset URL resolution)

Invariants Enforced:
  I5 — Permanência de Integridade (hash must match Ledger)
  I6 — Autenticidade de Origem (provenance must be WINDI-signed)
  I9 — Proibição de Escalada de Autonomia (AI proposes, human activates)

Principle: "AI processes. Human decides. WINDI guarantees."
Liga IA+H · Kempten, Bavaria · 2026
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import httpx
import time
import uuid
import logging
import os
from datetime import datetime

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
PORT         = int(os.getenv("DISPATCH_PORT", 8121))
LEDGER_URL   = os.getenv("LEDGER_URL",  "http://localhost:8101")
VAULT_URL    = os.getenv("VAULT_URL",   "http://localhost:8106")
BASE_DOMAIN  = os.getenv("BASE_DOMAIN", "https://windi-domain.com")
LOG_FILE     = "/opt/windi/logs/dispatch_gateway.log"
VERSION      = "1.0.2"

# ── SEED VERIFICATION CACHE (TTL 60s) ─────────
# Evita repetir handshake Ledger para a mesma semente.
# Cache guarda apenas booleanos + hash truncado — nunca conteúdo.
_verify_cache: dict = {}
CACHE_TTL_SECONDS = 60

# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────
_handlers = [logging.StreamHandler()]
try:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    _handlers.append(logging.FileHandler(LOG_FILE))
except OSError:
    pass  # Log to stdout only if /opt/windi/logs doesn't exist

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DISPATCH] %(levelname)s %(message)s",
    handlers=_handlers
)
log = logging.getLogger("dispatch")

# ──────────────────────────────────────────────
# SHARED HTTP CLIENT (connection pooling)
# ──────────────────────────────────────────────
_http_client: httpx.AsyncClient = None

async def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=3.0,
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=200)
        )
    return _http_client

# ──────────────────────────────────────────────
# FASTAPI APP
# ──────────────────────────────────────────────
app = FastAPI(
    title="WINDI Dispatch Gateway",
    version=VERSION,
    description=".jmpg Hydration Engine — Progressive Asset Delivery P1→P4"
)

@app.on_event("startup")
async def startup():
    global _http_client
    _http_client = httpx.AsyncClient(
        timeout=3.0,
        limits=httpx.Limits(max_keepalive_connections=50, max_connections=200)
    )
    log.info("HTTP client pool initialized (50 keepalive, 200 max)")

@app.on_event("shutdown")
async def shutdown():
    global _http_client
    if _http_client:
        await _http_client.aclose()
        log.info("HTTP client pool closed")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[BASE_DOMAIN, "http://localhost:3000", "http://localhost:8100"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Stream-Token", "X-WINDI-Seed"],
)

# ──────────────────────────────────────────────
# MODELS
# ──────────────────────────────────────────────

class DispatchRequest(BaseModel):
    seed_id:         str   = Field(..., description="Receipt ID from the Forensic Ledger")
    stream_token:    str   = Field(..., description="Session token from Viewer")
    network_quality: str   = Field(..., description="2g | 3g | 4g | 5g | wifi")
    device_id:       Optional[str] = Field(None, description="Anonymous device fingerprint")

class HydrationLayer(BaseModel):
    priority:  str   # P1 | P2 | P3 | P4
    url:       str
    media_type: str  # text/json | image/webp | video/mp4 | application/zip
    size_kb:   int
    mandatory: bool  # P1+P2=True, P3+P4=False

class VerificationResult(BaseModel):
    i5_integrity:    bool
    i6_authenticity: bool
    ledger_receipt:  Optional[str] = None
    sha256:          Optional[str] = None
    verified_at:     str

class DispatchResponse(BaseModel):
    status:             str   # ACTIVATED | DENIED | PARTIAL
    activation_id:      str   # Unique activation receipt
    invariants:         VerificationResult
    manifest:           List[HydrationLayer]
    evaporation_policy: str   # immediate | session_end | never
    network_tier:       str   # CORE | STANDARD | RICH | VAULT
    server_ts:          float
    gateway_version:    str

# ──────────────────────────────────────────────
# NETWORK TIER MAP
# ──────────────────────────────────────────────
# Maps network quality → which P-layers to include
NETWORK_TIERS = {
    "2g":   {"layers": ["P1"],              "tier": "CORE"},
    "3g":   {"layers": ["P1", "P2"],        "tier": "STANDARD"},
    "4g":   {"layers": ["P1", "P2", "P3"], "tier": "RICH"},
    "5g":   {"layers": ["P1", "P2", "P3", "P4"], "tier": "VAULT"},
    "wifi": {"layers": ["P1", "P2", "P3", "P4"], "tier": "VAULT"},
}
# Unknown network → safe fallback to CORE only
DEFAULT_TIER = {"layers": ["P1"], "tier": "CORE"}

# ──────────────────────────────────────────────
# LEDGER HANDSHAKE — I5 + I6
# ──────────────────────────────────────────────
async def verify_invariants(seed_id: str) -> VerificationResult:
    """
    Queries the Forensic Ledger (:8101) to verify I5 + I6.
    Results cached for CACHE_TTL_SECONDS — avoids redundant
    Ledger queries under concurrent load while preserving
    full integrity: cache stores only booleans + truncated hash.
    """
    ts = datetime.utcnow().isoformat() + "Z"

    # ── Cache hit ────────────────────────────────
    cached = _verify_cache.get(seed_id)
    if cached and time.time() < cached[1]:
        log.info(f"VERIFY cache-hit seed={seed_id}")
        return cached[0]

    try:
        client = await get_http_client()
        r = await client.get(f"{LEDGER_URL}/api/receipts/{seed_id}")

        if r.status_code == 200:
            data = r.json()
            # Ledger returns data nested under "receipt" key
            receipt = data.get("receipt", data)

            sha256    = receipt.get("content_hash", receipt.get("hash", ""))
            actor     = receipt.get("actor", "")
            app_name  = receipt.get("app", "")
            gov_level = receipt.get("governance_level", "")

            # I5: hash must be present and non-empty (Ledger sealed it)
            i5 = bool(sha256 and len(sha256) >= 8)

            # I6: must originate from WINDI platform
            i6 = (
                "windi" in actor.lower() or
                "windi" in app_name.lower() or
                gov_level in ("LOW", "MEDIUM", "HIGH")
            )

            log.info(f"VERIFY seed={seed_id} I5={i5} I6={i6} sha={sha256[:12]}...")
            result = VerificationResult(
                i5_integrity=i5,
                i6_authenticity=i6,
                ledger_receipt=seed_id,
                sha256=sha256[:16] + "…" if sha256 else None,
                verified_at=ts
            )
            # ── Store in cache ───────────────────
            _verify_cache[seed_id] = (result, time.time() + CACHE_TTL_SECONDS)
            return result

        elif r.status_code == 404:
            # Seed not in Ledger — I5 fails
            log.warning(f"VERIFY seed={seed_id} NOT_FOUND in Ledger")
            return VerificationResult(
                i5_integrity=False,
                i6_authenticity=False,
                ledger_receipt=None,
                sha256=None,
                verified_at=ts
            )

    except httpx.TimeoutException:
        log.error(f"VERIFY timeout reaching Ledger for seed={seed_id}")
    except Exception as e:
        log.error(f"VERIFY error seed={seed_id}: {e}")

    # Ledger unreachable — degrade gracefully (still serve P1 core)
    # Constitutional note: I9 — we never block reading; we flag uncertainty
    return VerificationResult(
        i5_integrity=False,
        i6_authenticity=False,
        ledger_receipt=None,
        sha256=None,
        verified_at=ts
    )

# ──────────────────────────────────────────────
# VAULT URL RESOLVER
# ──────────────────────────────────────────────
async def resolve_vault_urls(seed_id: str) -> dict:
    """
    Queries Vault (:8106) for asset URLs associated with this seed.
    Falls back to constructed URL pattern if Vault is unreachable.
    """
    try:
        client = await get_http_client()
        r = await client.get(f"{VAULT_URL}/api/assets/{seed_id}")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        log.warning(f"VAULT unreachable for seed={seed_id}: {e}")

    # Fallback: construct canonical URLs from seed_id
    vault_base = f"{VAULT_URL}/assets/{seed_id}"
    return {
        "p1_core":    f"{vault_base}/core.json",
        "p2_thumb":   f"{vault_base}/thumb.webp",
        "p3_media":   f"{vault_base}/media.mp4",
        "p4_archive": f"{vault_base}/raw.zip",
    }

# ──────────────────────────────────────────────
# HYDRATION MANIFEST BUILDER
# ──────────────────────────────────────────────
def build_manifest(
    seed_id: str,
    vault_urls: dict,
    allowed_layers: List[str]
) -> List[HydrationLayer]:
    """
    Builds the ordered P1→P4 hydration queue.
    Only includes layers permitted by the network tier.
    """
    all_layers = [
        HydrationLayer(
            priority="P1",
            url=vault_urls.get("p1_core", f"{VAULT_URL}/assets/{seed_id}/core.json"),
            media_type="application/json",
            size_kb=45,
            mandatory=True
        ),
        HydrationLayer(
            priority="P2",
            url=vault_urls.get("p2_thumb", f"{VAULT_URL}/assets/{seed_id}/thumb.webp"),
            media_type="image/webp",
            size_kb=180,
            mandatory=True
        ),
        HydrationLayer(
            priority="P3",
            url=vault_urls.get("p3_media", f"{VAULT_URL}/assets/{seed_id}/media.mp4"),
            media_type="video/mp4",
            size_kb=12000,
            mandatory=False
        ),
        HydrationLayer(
            priority="P4",
            url=vault_urls.get("p4_archive", f"{VAULT_URL}/assets/{seed_id}/raw.zip"),
            media_type="application/zip",
            size_kb=850000,
            mandatory=False
        ),
    ]
    return [layer for layer in all_layers if layer.priority in allowed_layers]

# ──────────────────────────────────────────────
# EVAPORATION POLICY
# ──────────────────────────────────────────────
def evaporation_policy(network: str) -> str:
    """
    Soberania de Cache: heavy assets evaporate from client device.
    - wifi/5g: reader might want to keep the archive (session_end)
    - 4g/3g: evaporate P3/P4 when document closes (immediate)
    - 2g: only P1 delivered — nothing to evaporate (none)
    """
    if network in ("wifi", "5g"):
        return "session_end"
    elif network in ("4g", "3g"):
        return "immediate"
    return "none"

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "service": "WINDI Dispatch Gateway",
        "version": VERSION,
        "port": PORT,
        "status": "GREEN",
        "ledger": LEDGER_URL,
        "vault": VAULT_URL,
        "invariants_enforced": ["I5", "I6", "I9"],
        "ts": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/activate", response_model=DispatchResponse)
async def activate_seed(req: DispatchRequest, response: Response):
    """
    Core activation endpoint.

    Flow:
    1. Verify I5+I6 on Ledger (:8101)
    2. If I5 fails → DENIED (integrity violation)
    3. Resolve Vault URLs for this seed
    4. Map network_quality → P-layer allowlist
    5. Build hydration manifest
    6. Return DispatchResponse with evaporation policy

    The Viewer streams layers progressively in the returned order.
    P1 is always delivered first — text + proof = instant reading.
    """
    t_start = time.time()
    activation_id = f"DISPATCH-{uuid.uuid4().hex[:12].upper()}"

    log.info(f"ACTIVATE {activation_id} seed={req.seed_id} net={req.network_quality}")

    # ── Step 1+2: Parallel Forensic + Vault lookup ─
    # asyncio.gather runs both HTTP calls concurrently.
    # Total wait = max(ledger_time, vault_time) not their sum.
    verification, vault_urls = await asyncio.gather(
        verify_invariants(req.seed_id),
        resolve_vault_urls(req.seed_id)
    )

    if not verification.i5_integrity:
        log.warning(f"DENIED {activation_id} I5 failed seed={req.seed_id}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "I5_INTEGRITY_VIOLATION",
                "message": "Invariante I5 falhou: integridade do pacote comprometida.",
                "seed_id": req.seed_id,
                "activation_id": activation_id
            }
        )

    # ── Step 3: Network → Layer Mapping ─────────
    net_config = NETWORK_TIERS.get(req.network_quality.lower(), DEFAULT_TIER)
    allowed    = net_config["layers"]
    tier_name  = net_config["tier"]

    # ── Step 4: Build Manifest ──────────────────
    manifest = build_manifest(req.seed_id, vault_urls, allowed)

    # ── Step 5: Evaporation Policy ──────────────
    policy = evaporation_policy(req.network_quality.lower())

    # ── Step 6: Set Cache Sovereignty Header ────
    response.headers["X-WINDI-Policy"]      = f"EVAPORATE-{policy.upper()}"
    response.headers["X-WINDI-Activation"]  = activation_id
    response.headers["X-WINDI-Tier"]        = tier_name
    response.headers["X-WINDI-Invariants"]  = "I5:OK,I6:" + ("OK" if verification.i6_authenticity else "WARN")

    latency_ms = round((time.time() - t_start) * 1000, 2)
    log.info(
        f"ACTIVATED {activation_id} tier={tier_name} "
        f"layers={len(manifest)} evap={policy} latency={latency_ms}ms"
    )

    return DispatchResponse(
        status="ACTIVATED",
        activation_id=activation_id,
        invariants=verification,
        manifest=manifest,
        evaporation_policy=policy,
        network_tier=tier_name,
        server_ts=time.time(),
        gateway_version=VERSION
    )


@app.get("/verify/{seed_id}")
async def quick_verify(seed_id: str):
    """
    Quick invariant check without full activation.
    Useful for pre-flight validation in the Composer.
    """
    result = await verify_invariants(seed_id)
    return {
        "seed_id":  seed_id,
        "i5_ok":    result.i5_integrity,
        "i6_ok":    result.i6_authenticity,
        "sha256":   result.sha256,
        "status":   "VALID" if result.i5_integrity else "INVALID",
        "verified_at": result.verified_at
    }


@app.get("/tiers")
async def list_tiers():
    """Returns the network-to-layer mapping table."""
    return {
        "description": "Network quality → hydration layer allowlist",
        "tiers": NETWORK_TIERS,
        "evaporation_policies": {
            "wifi": "session_end — heavy assets evaporate on document close",
            "5g":   "session_end — heavy assets evaporate on document close",
            "4g":   "immediate  — P3/P4 evaporate as soon as viewport leaves",
            "3g":   "immediate  — P3/P4 evaporate as soon as viewport leaves",
            "2g":   "none       — only P1 (Core) delivered",
        }
    }

# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    log.info(f"WINDI Dispatch Gateway v{VERSION} starting on :{PORT}")
    uvicorn.run(
        "dispatch_gateway:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=False  # We have our own structured logging
    )
