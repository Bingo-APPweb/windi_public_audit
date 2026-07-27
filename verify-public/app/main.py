import os
import hashlib
import logging
import time
import sys
import threading
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
import re
import sqlite3
from pydantic import BaseModel
from fastapi import Request
from fastapi.templating import Jinja2Templates

sys.path.insert(0, os.path.dirname(__file__))
from verify_engine import VerifyEngine, extract_jmpg_proof

# Import Dragonprint for /verify-public/dragonprint endpoint (G4)
try:
    sys.path.insert(0, "/opt/windi/dragonprint")
    from dragonprint import (
        decode_dragonprint,
        verify_signature_safe,
        compute_signature_projection,
        SIGN_DOMAIN_PREFIX,
    )
    DRAGONPRINT_AVAILABLE = True
except ImportError:
    DRAGONPRINT_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# W-CACHE-001 Integration — Verifiable Cache Layer
# Replaces simple dict cache with temporal + proof-aware cache
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from wcache_integration import cache_get, cache_set, wcache_health
    WCACHE_ENABLED = True
    logging.getLogger("windi.verify").info("[WCACHE] W-CACHE-001 integration ENABLED")
except ImportError:
    WCACHE_ENABLED = False
    logging.getLogger("windi.verify").warning("[WCACHE] W-CACHE-001 not available, using fallback")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [VERIFY] %(levelname)s %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler("/opt/windi/logs/verify-public.log")])
log = logging.getLogger("windi.verify")

PORT          = int(os.getenv("VERIFY_PORT", 8114))
LEDGER_URL    = os.getenv("LEDGER_URL", "http://localhost:8101")
AGENTS_URL    = os.getenv("AGENTS_URL", "http://localhost:8091")
MAX_FILE_SIZE = 10 * 1024 * 1024
CACHE_TTL     = 60
_cache: dict  = {}

# Fallback cache functions (used if W-CACHE-001 not available)
if not WCACHE_ENABLED:
    def cache_get(key):
        e = _cache.get(key)
        if e and time.time() < e[1]:
            return e[0]
        return None

    def cache_set(key, value):
        _cache[key] = (value, time.time() + CACHE_TTL)
        if len(_cache) > 1000:
            now = time.time()
            for k in [k for k, v in list(_cache.items()) if now >= v[1]]:
                del _cache[k]

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# ═══════════════════════════════════════════════════════════════════════════════
# W-PROV-002 — Propagation Event Hook
# Emits propagation events to Propagation Index after successful verification
# NEVER blocks verification — timeout=0.5, silent failure
# ═══════════════════════════════════════════════════════════════════════════════

PROPAGATION_API = os.getenv("PROPAGATION_API", "http://localhost:8091/propagation/event")

def extract_domain(url: str) -> str:
    """Extract domain from URL or referer."""
    if not url or url == "-":
        return "direct"
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or "direct"
    except:
        return "direct"

def emit_propagation_event(receipt_id: str, request: Request, verified: bool = True):
    """
    Emit propagation event to W-PROV-002 after successful verification.
    NEVER blocks verification — uses timeout=0.5 and silent try/except.
    C-PROV-002: Fingerprints are anonymous — no personal data.
    """
    if not verified or not receipt_id:
        return

    try:
        import requests as req_lib

        # Anonymous fingerprint — NEVER store full IP (C-PROV-002)
        raw_ip = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", "unknown"))
        if "," in raw_ip:
            raw_ip = raw_ip.split(",")[0].strip()
        client_fp = hashlib.sha256(raw_ip.encode()).hexdigest()[:8]

        # Extract origin domain from Referer
        referer = request.headers.get("Referer", "direct")
        origin_domain = extract_domain(referer)

        # Country hint from header (if available via Cloudflare/nginx)
        country_hint = request.headers.get("CF-IPCountry", request.headers.get("X-Country", ""))

        payload = {
            "ledger_anchor": receipt_id,
            "event_type": "VERIFICATION",
            "source_type": "web",
            "origin_domain": origin_domain,
            "country_hint": country_hint,
            "verify_node": "verify-public-8114",
            "client_fp": client_fp,
            "timestamp": int(time.time())
        }

        req_lib.post(PROPAGATION_API, json=payload, timeout=0.5)
        log.debug(f"[PROV] Event emitted: {receipt_id} from {origin_domain}")

    except Exception as e:
        # Silent failure — verification NEVER depends on W-PROV-002
        log.debug(f"[PROV] Event emission failed (non-blocking): {e}")
        pass

app = FastAPI(title="WINDI Verify Public Agent", version="1.0.2", docs_url="/verify-public/docs", redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET","POST"], allow_headers=["*"])
engine = VerifyEngine(ledger_url=LEDGER_URL, agents_url=AGENTS_URL, timeout=5.0)

WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")
if os.path.isdir(WEB_DIR):
    app.mount("/verify-public/static", StaticFiles(directory=WEB_DIR), name="static")

DOCS_DIR = os.path.join(WEB_DIR, "docs")
if os.path.isdir(DOCS_DIR):
    app.mount("/verify-public/docs", StaticFiles(directory=DOCS_DIR), name="docs")

# VPR static pages (e.g., /verify-public/vpr/anna-weber/)
VPR_DIR = os.path.join(WEB_DIR, "vpr")
if os.path.isdir(VPR_DIR):
    app.mount("/verify-public/vpr", StaticFiles(directory=VPR_DIR, html=True), name="vpr")

# ═══════════════════════════════════════════════════════════════════════════════
# VPR — Verified Professional Record (v2.0)
# WINDI-VPR-SPEC-v2.0 · 2026-03-10
# ═══════════════════════════════════════════════════════════════════════════════

WALLET_DB = "/opt/windi/data/wallet.db"
LEDGER_DB = "/opt/windi/data/forensic_ledger.sqlite3"
VERIFY_METRICS_DB = "/opt/windi/data/verify_metrics.sqlite3"
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
os.makedirs(TEMPLATES_DIR, exist_ok=True)
_metrics_lock = threading.Lock()

# Jinja2 templates para VPR
vpr_templates = Jinja2Templates(directory=TEMPLATES_DIR) if os.path.isdir(TEMPLATES_DIR) else None

def wallet_conn():
    """Connection to wallet.db."""
    c = sqlite3.connect(f"file:{WALLET_DB}?mode=ro&immutable=1", uri=True, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def ledger_conn():
    """Connection to forensic_ledger.sqlite3."""
    c = sqlite3.connect(f"file:{LEDGER_DB}?mode=ro&immutable=1", uri=True, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFY Distribution Metrics — Download Tracking (Future: VERIFY Free Distribution)
# Schema: verify_artifact_downloads (aggregate) + verify_artifact_download_events (log)
# ═══════════════════════════════════════════════════════════════════════════════

def metrics_conn():
    """Connection to verify_metrics.sqlite3 (read-write)."""
    c = sqlite3.connect(VERIFY_METRICS_DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_metrics_db():
    """Initialize metrics database schema on startup."""
    os.makedirs(os.path.dirname(VERIFY_METRICS_DB), exist_ok=True)
    with _metrics_lock:
        db = metrics_conn()
        try:
            db.execute("""
                CREATE TABLE IF NOT EXISTS verify_artifact_downloads (
                    artifact_id TEXT PRIMARY KEY,
                    download_count INTEGER NOT NULL DEFAULT 0,
                    last_download_at TEXT
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS verify_artifact_download_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artifact_id TEXT NOT NULL,
                    downloaded_at TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'verify-public',
                    referer_domain TEXT DEFAULT 'direct',
                    client_fp TEXT,
                    user_agent TEXT
                )
            """)
            db.commit()
        finally:
            db.close()


init_metrics_db()  # Initialize download metrics on startup


def _client_fp(request: Request) -> str:
    """Generate anonymous client fingerprint from IP (C-PROV-002 compliant)."""
    raw_ip = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", "unknown"))
    if "," in raw_ip:
        raw_ip = raw_ip.split(",")[0].strip()
    return hashlib.sha256(raw_ip.encode()).hexdigest()[:16]


def track_artifact_download(artifact_id: str, request: Request, source: str = "verify-public") -> int:
    """Track artifact download event. Returns updated count."""
    ts = now_iso()
    referer_domain = extract_domain(request.headers.get("Referer", "direct"))
    client_fp = _client_fp(request)
    user_agent = request.headers.get("User-Agent", "")[:240]
    with _metrics_lock:
        db = metrics_conn()
        try:
            db.execute("""
                INSERT INTO verify_artifact_downloads (artifact_id, download_count, last_download_at)
                VALUES (?, 1, ?)
                ON CONFLICT(artifact_id) DO UPDATE SET
                    download_count = download_count + 1,
                    last_download_at = excluded.last_download_at
            """, (artifact_id, ts))
            db.execute("""
                INSERT INTO verify_artifact_download_events (
                    artifact_id, downloaded_at, source, referer_domain, client_fp, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (artifact_id, ts, source, referer_domain, client_fp, user_agent))
            row = db.execute("""
                SELECT download_count
                FROM verify_artifact_downloads
                WHERE artifact_id = ?
            """, (artifact_id,)).fetchone()
            db.commit()
            return int(row["download_count"]) if row else 0
        finally:
            db.close()


def get_artifact_download_stats(artifact_id: str) -> dict:
    """Get download statistics for an artifact."""
    db = metrics_conn()
    try:
        row = db.execute("""
            SELECT download_count, last_download_at
            FROM verify_artifact_downloads
            WHERE artifact_id = ?
        """, (artifact_id,)).fetchone()
        if not row:
            return {
                "artifact_id": artifact_id,
                "download_count": 0,
                "last_download_at": None
            }
        return {
            "artifact_id": artifact_id,
            "download_count": int(row["download_count"]),
            "last_download_at": row["last_download_at"]
        }
    finally:
        db.close()


class JmpgProof(BaseModel):
    issuer_did: Optional[str] = None
    issuer_actor: Optional[str] = None
    timestamp: Optional[str] = None  # ISO 8601 format
    capabilities: list = []
    verify_url: Optional[str] = None
    governance_level: Optional[str] = None
    content_hash: Optional[str] = None

class VerifyResult(BaseModel):
    status: str
    document_id: Optional[str] = None
    hash: Optional[str] = None
    integrity: str
    signature: str
    ledger_anchor: bool
    timestamp: Optional[str] = None
    checked_at: str
    message: str
    proof_limits: Optional[str] = None
    cached: bool = False
    jmpg_proof: Optional[JmpgProof] = None  # .jmpg sovereign proof metadata

@app.get("/health")
@app.get("/verify-public/health")
async def health():
    wcache_status = wcache_health() if WCACHE_ENABLED else {"wcache": "disabled"}
    return {
        "service": "windi-verify-public",
        "version": "1.0.2",
        "status": "operational",
        "wcache_enabled": WCACHE_ENABLED,
        "wcache_status": wcache_status.get("wcache", "unknown"),
        "fallback_cache_entries": len(_cache),
        "port": PORT,
        "timestamp": now_iso()
    }

@app.get("/verify-public/")
async def ui_root():
    index = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return JSONResponse({"service":"WINDI Verify Public","version":"1.0.1"})

@app.get("/verify-public/document/{document_id}", response_model=VerifyResult)
async def verify_by_id(document_id: str, request: Request):
    c = cache_get(f"doc:{document_id}")
    if c: return {**c, "cached": True}
    r = await engine.verify_document_id(document_id)
    cache_set(f"doc:{document_id}", r)
    # W-PROV-002: Emit propagation event (non-blocking)
    emit_propagation_event(document_id, request, r.get("status") == "verified")
    return r

@app.get("/verify-public/hash/{sha256_hash}", response_model=VerifyResult)
async def verify_by_hash(sha256_hash: str, request: Request):
    c = cache_get(f"hash:{sha256_hash}")
    if c: return {**c, "cached": True}
    r = await engine.verify_hash(sha256_hash)
    cache_set(f"hash:{sha256_hash}", r)
    # W-PROV-002: Emit propagation event (non-blocking)
    emit_propagation_event(r.get("document_id") or sha256_hash[:16], request, r.get("status") == "verified")
    return r

@app.get("/verify-public/qr/{qr_data:path}", response_model=VerifyResult)
async def verify_by_qr(qr_data: str, request: Request):
    c = cache_get(f"qr:{qr_data}")
    if c: return {**c, "cached": True}
    r = await engine.verify_qr(qr_data)
    cache_set(f"qr:{qr_data}", r)
    # W-PROV-002: Emit propagation event (non-blocking)
    emit_propagation_event(r.get("document_id"), request, r.get("status") == "verified")
    return r

@app.post("/verify-public/file", response_model=VerifyResult)
async def verify_file(file: UploadFile = File(...), request: Request = None):
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 10MB.")

    # ═══ JMPG Detection — Extract embedded proof ═══
    proof = extract_jmpg_proof(content)
    if proof and proof.get('ledger_anchor'):
        ledger_anchor = proof['ledger_anchor']
        log.info(f"[VERIFY] .jmpg detected — verifying anchor: {ledger_anchor}")
        c = cache_get(f"jmpg:{ledger_anchor}")
        if c: return {**c, "cached": True}
        r = await engine.verify_document_id(ledger_anchor)
        # Enrich response with proof metadata from .jmpg bundle
        r["jmpg_proof"] = {
            "issuer_did": proof.get('issuer_did'),
            "issuer_actor": proof.get('issuer_actor'),
            "timestamp": proof.get('timestamp'),
            "capabilities": proof.get('capabilities', []),
            "verify_url": proof.get('verify_url'),
            "governance_level": proof.get('governance_level'),
            "content_hash": proof.get('content_hash')
        }
        cache_set(f"jmpg:{ledger_anchor}", r)
        # W-PROV-002: Emit propagation event for .jmpg (non-blocking)
        if request:
            emit_propagation_event(ledger_anchor, request, r.get("status") == "verified")
        return r

    # ═══ Standard file — verify by SHA-256 hash ═══
    sha256 = hashlib.sha256(content).hexdigest()
    c = cache_get(f"hash:{sha256}")
    if c: return {**c, "cached": True}
    r = await engine.verify_hash(sha256)
    cache_set(f"hash:{sha256}", r)
    # W-PROV-002: Emit propagation event (non-blocking)
    if request:
        emit_propagation_event(r.get("document_id") or sha256[:16], request, r.get("status") == "verified")
    return r

@app.get("/verify-public/timeline/{document_id}")
async def verify_timeline(document_id: str):
    return await engine.get_timeline(document_id)


# ═══════════════════════════════════════════════════════════════════════════════
# DRAGONPRINT VERIFICATION — G4 Endpoint
# 8-phase verification of Dragonprint payloads
# ═══════════════════════════════════════════════════════════════════════════════

MANDATORY_VERIFY_PROOF_LIMITS = [
    "WINDI proves existence, integrity, and recorded path.",
    "WINDI does not prove the truthfulness of the content.",
    "Not found means no WINDI record was located; it does not prove falsity.",
]

class DragonprintPayload(BaseModel):
    """Dragonprint payload for POST verification."""
    standard: str
    state: str
    pattern_id: str
    source: dict
    copy: dict
    encoding: dict
    crypto: dict
    verification: dict
    proof_limits: list


@app.post("/verify-public/dragonprint")
async def verify_dragonprint_endpoint(payload: dict, request: Request):
    """
    G4 VERIFY: Dragonprint payload verification.

    8 phases:
    1. Structure (decode_dragonprint)
    2. Payload hash
    3. Signature (if issued)
    4. Ledger anchor
    5. Content hash (if file provided)
    6. Carrier integrity
    7. Confidence
    8. proof_limits MANDATORY (G6)
    """
    if not DRAGONPRINT_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Dragonprint verification not available",
                "proof_limits": MANDATORY_VERIFY_PROOF_LIMITS
            }
        )

    result = {
        "status": "unknown",
        "phases": {},
        "errors": [],
        "warnings": [],
        "checked_at": now_iso(),
        "proof_limits": MANDATORY_VERIFY_PROOF_LIMITS  # G6: Always present
    }

    # ─── Phase 1: Structure validation ───
    try:
        decode_result = decode_dragonprint(payload)
        result["phases"]["structure"] = decode_result.structure
        result["phases"]["state_support"] = decode_result.state_support
        result["phases"]["payload_hash"] = decode_result.payload_hash
        result["errors"].extend(decode_result.errors)
        result["warnings"].extend(decode_result.warnings)

        if decode_result.structure != "valid":
            result["status"] = "invalid_structure"
            return result
    except Exception as e:
        result["status"] = "decode_error"
        result["errors"].append(f"Decode failed: {e}")
        return result

    # ─── Phase 2: Payload hash verification ───
    if decode_result.payload_hash == "matching":
        result["phases"]["payload_hash_valid"] = True
    elif decode_result.payload_hash == "incomplete":
        result["phases"]["payload_hash_valid"] = None
        result["warnings"].append("Payload hash incomplete (candidate without hash)")
    else:
        result["phases"]["payload_hash_valid"] = False
        result["status"] = "payload_hash_mismatch"
        return result

    # ─── Phase 3: Signature verification (if issued) ───
    state = payload.get("state")
    if state == "issued":
        crypto = payload.get("crypto", {})
        signature_hex = crypto.get("signature")
        key_id = crypto.get("key_id")

        if signature_hex and key_id:
            # Build the message that was signed
            try:
                # Reconstruct payload at signing time (signature=null)
                import copy
                sign_payload = copy.deepcopy(payload)
                sign_payload["crypto"]["signature"] = None
                projection = compute_signature_projection(sign_payload)

                # For now, we mark signature as "not_verified" since we don't have
                # the public key in the payload (would need key registry lookup)
                result["phases"]["signature"] = "present_not_verified"
                result["warnings"].append(
                    "Signature present but public key lookup not implemented yet. "
                    "Use offline verification with known public key."
                )
            except Exception as e:
                result["phases"]["signature"] = "error"
                result["errors"].append(f"Signature verification error: {e}")
        else:
            result["phases"]["signature"] = "missing"
            result["errors"].append("Issued state requires signature")
            result["status"] = "missing_signature"
            return result
    else:
        result["phases"]["signature"] = "not_applicable"

    # ─── Phase 4: Ledger anchor lookup ───
    receipt_id = payload.get("source", {}).get("receipt_id")
    if receipt_id:
        try:
            ledger_result = await engine.verify_document_id(receipt_id)
            if ledger_result.get("status") == "verified":
                result["phases"]["ledger_anchor"] = "verified"
            elif ledger_result.get("status") == "not_found":
                result["phases"]["ledger_anchor"] = "not_found"
                result["warnings"].append("Receipt not found in Ledger")
            else:
                result["phases"]["ledger_anchor"] = ledger_result.get("status", "unknown")
        except Exception as e:
            result["phases"]["ledger_anchor"] = "lookup_error"
            result["warnings"].append(f"Ledger lookup failed: {e}")
    else:
        result["phases"]["ledger_anchor"] = "missing_receipt_id"
        result["warnings"].append("No receipt_id in payload")

    # ─── Phase 5: Content hash (if expected file hash provided) ───
    content_sha256 = payload.get("source", {}).get("content_sha256")
    if content_sha256:
        result["phases"]["content_hash"] = "present"
        result["content_sha256"] = content_sha256
    else:
        result["phases"]["content_hash"] = "missing"

    # ─── Phase 6: Carrier integrity ───
    carriers = payload.get("encoding", {}).get("carriers", [])
    if carriers:
        result["phases"]["carriers"] = f"{len(carriers)} carriers defined"
    else:
        result["phases"]["carriers"] = "none"

    # ─── Phase 7: Confidence calculation ───
    phases = result["phases"]
    confidence_points = 0
    max_points = 5

    if phases.get("structure") == "valid":
        confidence_points += 1
    if phases.get("payload_hash_valid") is True:
        confidence_points += 1
    if phases.get("ledger_anchor") == "verified":
        confidence_points += 2
    if phases.get("signature") in ("verified", "present_not_verified"):
        confidence_points += 1

    confidence = confidence_points / max_points
    result["confidence"] = confidence
    result["confidence_label"] = (
        "HIGH" if confidence >= 0.8 else
        "MEDIUM" if confidence >= 0.6 else
        "LOW"
    )

    # ─── Final status ───
    if result["errors"]:
        result["status"] = "invalid"
    elif confidence >= 0.8:
        result["status"] = "verified"
    elif confidence >= 0.4:
        result["status"] = "partial"
    else:
        result["status"] = "unverified"

    # W-PROV-002: Emit propagation event (non-blocking)
    if receipt_id and result["status"] == "verified":
        emit_propagation_event(receipt_id, request, True)

    log.info(f"[DRAGONPRINT] Verified: state={state} status={result['status']} confidence={confidence:.2f}")

    return result


@app.get("/verify-public/dragonprint/health")
async def dragonprint_health():
    """Health check for Dragonprint verification endpoint."""
    return {
        "service": "dragonprint-verify",
        "available": DRAGONPRINT_AVAILABLE,
        "timestamp": now_iso()
    }


async def get_document_metadata(doc_id: str) -> dict:
    """Fetch document metadata from Ledger for OG tags."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            # Try Ledger receipt endpoint
            r = await client.get(f"{LEDGER_URL}/api/receipts/{doc_id}")
            if r.status_code == 200:
                data = r.json()
                return {
                    "title": data.get("doc_title") or data.get("title") or doc_id,
                    "doc_type": data.get("doc_type", "Document"),
                    "created_at": data.get("created_at", data.get("ts", "")),
                    "issuer": data.get("issuer") or data.get("actor") or "WINDI",
                    "status": "verified"
                }
    except Exception as e:
        log.warning(f"[OG] Failed to fetch metadata for {doc_id}: {e}")
    return {"title": doc_id, "doc_type": "Document", "created_at": "", "issuer": "WINDI", "status": "pending"}


async def fetch_wick_artifact(artifact_id: str) -> dict:
    """Fetch artifact from Constitutional Agent WICK."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(f"http://localhost:8091/wick/artifact/{artifact_id}")
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_id}")
        r.raise_for_status()
        return r.json().get("artifact", {})


def inject_og_tags(html: str, doc_id: str, meta: dict) -> str:
    """Inject dynamic OG tags into HTML for social sharing."""
    title = f"✓ {meta['title']} — WINDI Verified"
    description = f"Document {doc_id} authenticated by WINDI Forensic Ledger. Type: {meta['doc_type']}. Issuer: {meta['issuer']}. Integrity confirmed."
    url = f"https://windi-domain.com/verify-public/{doc_id}"

    # Replace OG tags
    html = re.sub(
        r'<meta property="og:title" content="[^"]*"/>',
        f'<meta property="og:title" content="{title}"/>',
        html
    )
    html = re.sub(
        r'<meta property="og:description" content="[^"]*"/>',
        f'<meta property="og:description" content="{description}"/>',
        html
    )
    html = re.sub(
        r'<meta property="og:url" content="[^"]*"/>',
        f'<meta property="og:url" content="{url}"/>',
        html
    )
    # Twitter cards
    html = re.sub(
        r'<meta name="twitter:title" content="[^"]*"/>',
        f'<meta name="twitter:title" content="{title}"/>',
        html
    )
    html = re.sub(
        r'<meta name="twitter:description" content="[^"]*"/>',
        f'<meta name="twitter:description" content="{description}"/>',
        html
    )
    # Page title
    html = re.sub(
        r'<title>[^<]*</title>',
        f'<title>{title}</title>',
        html
    )
    return html


# ═══════════════════════════════════════════════════════════════════════════════
# S3-2: WICK VIEW — HTML render with OG tags + embedded Verify
# URL: windi-domain.com/wick/{artifact_id}
# Decisão Human Dragon 2026-03-08: Privado por defeito
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/wick/view/{artifact_id}")
async def wick_artifact_view(artifact_id: str):
    """S3-2: HTML view for WICK artifacts with OG tags.
    URL: windi-domain.com/wick/view/{artifact_id}
    """
    # 1. Fetch artifact from Constitutional Agent
    try:
        artifact = await fetch_wick_artifact(artifact_id)
    except HTTPException as e:
        if e.status_code == 404:
            return HTMLResponse(
                "<html><body style='font-family:system-ui;text-align:center;padding:60px;'>"
                "<h1>🔍 Artifact not found</h1>"
                f"<p>ID: <code>{artifact_id}</code></p>"
                "<a href='/verify-public/'>Go to Verify</a>"
                "</body></html>",
                status_code=404
            )
        log.error(f"[WICK] Failed to fetch artifact {artifact_id}: {e.detail}")
        return HTMLResponse(
            "<html><body style='font-family:system-ui;text-align:center;padding:60px;'>"
            "<h1>⚠️ Service unavailable</h1>"
            "<p>Please try again later.</p>"
            "</body></html>",
            status_code=503
        )
    except Exception as e:
        log.error(f"[WICK] Failed to fetch artifact {artifact_id}: {e}")
        return HTMLResponse(
            "<html><body style='font-family:system-ui;text-align:center;padding:60px;'>"
            "<h1>⚠️ Service unavailable</h1>"
            "<p>Please try again later.</p>"
            "</body></html>",
            status_code=503
        )

    # 2. Check visibility (private = 403, GDPR compliant)
    visibility = artifact.get("visibility", "private")
    if visibility == "private":
        return HTMLResponse(
            "<html><body style='font-family:system-ui;text-align:center;padding:60px;'>"
            "<h1>🔒 Private Artifact</h1>"
            "<p>This artifact is private. Only the owner can view it.</p>"
            "<p style='color:#666;font-size:14px;'>I12 — Web of Proofs · Privacy by Default</p>"
            "</body></html>",
            status_code=403
        )

    # 3. Build HTML with OG tags
    title = artifact.get("title", artifact_id)
    author = artifact.get("author_name", "WINDI")
    artifact_type = artifact.get("type", "document")
    created_at = artifact.get("created_at", "")[:10] if artifact.get("created_at") else ""
    page_url = artifact.get("page_url", "")
    verify_url = f"https://windi-domain.com/verify-public/?id={artifact_id}"
    wick_url = f"https://windi-domain.com/wick/{artifact_id}"
    download_url = f"/verify-public/artifact/{artifact_id}/download"

    # Escape HTML in title/author
    import html as html_escape
    title_safe = html_escape.escape(title)
    author_safe = html_escape.escape(author)

    html = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>✓ {title_safe} — WINDI</title>

    <!-- OG Tags for Social Sharing -->
    <meta property="og:title" content="✓ {title_safe} — WINDI Verified"/>
    <meta property="og:description" content="Document by {author_safe}. Verified on WINDI Forensic Ledger. Type: {artifact_type}."/>
    <meta property="og:url" content="{wick_url}"/>
    <meta property="og:type" content="article"/>
    <meta property="og:image" content="https://windi-domain.com/verify-public/og-preview.png"/>

    <!-- Twitter Cards -->
    <meta name="twitter:card" content="summary"/>
    <meta name="twitter:title" content="✓ {title_safe} — WINDI Verified"/>
    <meta name="twitter:description" content="Document by {author_safe}. Verified on WINDI."/>

    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family: 'Bricolage Grotesque', system-ui, sans-serif; background: #FFFDF5; color: #1a1a1a; min-height: 100vh; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
        header {{ border-bottom: 3px solid #C9A84C; padding-bottom: 20px; margin-bottom: 30px; }}
        .badge {{ display: inline-block; background: #C9A84C; color: #fff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 12px; }}
        h1 {{ font-size: 28px; font-weight: 800; margin-bottom: 8px; }}
        .meta {{ color: #666; font-size: 14px; }}
        .meta span {{ margin-right: 16px; }}
        .card {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 12px; padding: 24px; margin-bottom: 20px; }}
        .card h2 {{ font-size: 16px; font-weight: 700; margin-bottom: 12px; color: #C9A84C; }}
        .info-grid {{ display: grid; grid-template-columns: 120px 1fr; gap: 8px; font-size: 14px; }}
        .info-grid dt {{ color: #666; }}
        .info-grid dd {{ font-family: 'JetBrains Mono', monospace; word-break: break-all; }}
        .actions {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 30px; }}
        .btn {{ display: inline-flex; align-items: center; gap: 8px; padding: 14px 24px; border-radius: 10px; font-size: 14px; font-weight: 700; text-decoration: none; transition: transform 0.2s; }}
        .btn:hover {{ transform: translateY(-2px); }}
        .btn-primary {{ background: #C9A84C; color: #fff; }}
        .btn-secondary {{ background: #fff; color: #1a1a1a; border: 2px solid #e0e0e0; }}
        footer {{ margin-top: 60px; padding-top: 20px; border-top: 1px solid #e0e0e0; text-align: center; color: #999; font-size: 12px; }}
        .dragon {{ font-size: 24px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <span class="badge">🛡️ WICK Evidence Graph</span>
            <h1>{title_safe}</h1>
            <p class="meta">
                <span>👤 {author_safe}</span>
                <span>📄 {artifact_type}</span>
                {f'<span>📅 {created_at}</span>' if created_at else ''}
                <span>🔓 {visibility}</span>
            </p>
        </header>

        <div class="card">
            <h2>📋 Artifact Details</h2>
            <dl class="info-grid">
                <dt>ID:</dt>
                <dd>{artifact_id}</dd>
                <dt>Type:</dt>
                <dd>{artifact_type}</dd>
                <dt>Visibility:</dt>
                <dd>{visibility}</dd>
                <dt>Ledger Receipt:</dt>
                <dd>{artifact.get("ledger_receipt_id", "—")}</dd>
            </dl>
        </div>

        {f'<div class="card"><h2>🔗 Original Page</h2><p><a href="{page_url}" style="color:#C9A84C;">{page_url}</a></p></div>' if page_url else ''}

        <div class="actions">
            <a href="{verify_url}" class="btn btn-primary">🛡️ Verify on Ledger</a>
            {f'<a href="{download_url}" class="btn btn-secondary">⬇️ Download</a>' if page_url else ''}
            {f'<a href="{page_url}" class="btn btn-secondary">📄 View Original</a>' if page_url else ''}
            <a href="/wick/feed" class="btn btn-secondary">📡 WICK Feed</a>
        </div>

        <footer>
            <p class="dragon">🐉</p>
            <p style="margin-top:8px;">AI processes. Human decides. WINDI guarantees.</p>
            <p style="margin-top:4px;">I12 — Web of Proofs · windi-domain.com</p>
        </footer>
    </div>
</body>
</html>'''

    return HTMLResponse(content=html, status_code=200)


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFY Distribution Metrics — Download Endpoints
# Future: VERIFY Free Distribution tracking
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/verify-public/artifact/{artifact_id}/download")
async def download_artifact(artifact_id: str, request: Request):
    """
    Download/click counter for VERIFY artifacts.
    Increments counter and redirects to canonical public URL.
    Future: Will serve actual files for VERIFY distribution.
    """
    artifact = await fetch_wick_artifact(artifact_id)
    visibility = artifact.get("visibility", "private")
    if visibility == "private":
        raise HTTPException(status_code=403, detail="Private artifact")

    target_url = artifact.get("page_url")
    if not target_url:
        raise HTTPException(status_code=404, detail="Artifact has no public URL")

    count = track_artifact_download(artifact_id, request, source="verify-artifact-download")
    log.info(f"[VERIFY-DL] artifact={artifact_id} count={count}")
    return RedirectResponse(url=target_url, status_code=307)


@app.get("/verify-public/artifact/{artifact_id}/downloads")
async def artifact_download_stats(artifact_id: str):
    """Get download statistics for an artifact."""
    return {
        "status": "ok",
        **get_artifact_download_stats(artifact_id)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# WINDI FIELD — Forensic Capture Endpoint
# 3 Gates: DID + GPS + Native Camera
# Server timestamp = AUTHORITATIVE (not browser)
# ═══════════════════════════════════════════════════════════════════════════════

class FieldSealRequest(BaseModel):
    hash: str
    did: str
    gps: dict
    fileType: Optional[str] = None
    fileSize: Optional[int] = None
    clientTimestamp: Optional[str] = None
    mode: str = "FIELD"

@app.post("/field/seal")
async def field_seal(data: FieldSealRequest):
    """
    WINDI FIELD — Forensic seal with server-authoritative timestamp.

    Required: hash, did, gps, mode=FIELD
    Returns: receipt_id, server_timestamp (AUTHORITATIVE), verify_url
    """
    # Server timestamp — AUTHORITATIVE, not client
    server_timestamp = now_iso()

    # Validate required fields
    if not data.hash or len(data.hash) != 64:
        raise HTTPException(status_code=400, detail="FIELD_MISSING: valid SHA-256 hash required")
    if not data.did:
        raise HTTPException(status_code=400, detail="FIELD_MISSING: DID required for forensic capture")
    if not data.gps or 'lat' not in data.gps or 'lng' not in data.gps:
        raise HTTPException(status_code=400, detail="FIELD_MISSING: GPS coordinates required")

    # GPS precision check (±100m)
    gps_accuracy = data.gps.get('accuracy', 999)
    if gps_accuracy > 100:
        raise HTTPException(status_code=400, detail=f"GPS_IMPRECISE: accuracy {gps_accuracy}m exceeds 100m limit")

    # Generate FIELD receipt ID
    receipt_id = f"WINDI-FIELD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{data.hash[:8].upper()}"

    # Build receipt for Ledger
    receipt = {
        "id": receipt_id,
        "actor": data.did,
        "app": "windi-field",
        "doc_name": f"WINDI FIELD Capture — {server_timestamp}",
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content_hash": f"sha256:{data.hash}",
        "sge_score": 95,
        "metadata": {
            "mode": "FIELD",
            "forensic_grade": True,
            "gps": {
                "lat": data.gps.get('lat'),
                "lng": data.gps.get('lng'),
                "accuracy_meters": gps_accuracy,
                "locked_at": data.gps.get('lockedAt')
            },
            "file_type": data.fileType,
            "file_size_bytes": data.fileSize,
            "server_timestamp": server_timestamp,
            "client_timestamp": data.clientTimestamp,
            "chain_of_custody": {
                "captured_by": data.did,
                "captured_at": server_timestamp,
                "location": f"{data.gps.get('lat', 0):.4f}, {data.gps.get('lng', 0):.4f}",
                "device_mode": "native_camera_only",
                "gallery_upload": False
            }
        },
        "tags": ["field", "forensic", "native-capture", "gps-locked", "did-bound"]
    }

    # Seal to Ledger
    try:
        import requests as req_lib
        response = req_lib.post(
            f"{LEDGER_URL}/api/receipts",
            json=receipt,
            timeout=5
        )

        if response.status_code in (200, 201):
            log.info(f"[FIELD] Sealed: {receipt_id} | DID: {data.did[:16]}... | GPS: {data.gps.get('lat'):.4f},{data.gps.get('lng'):.4f}")
            return {
                "status": "FIELD_SEALED",
                "receipt_id": receipt_id,
                "server_timestamp": server_timestamp,
                "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}",
                "forensic_grade": True,
                "gps_locked": True,
                "did_bound": True
            }
        else:
            log.warning(f"[FIELD] Ledger error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=503, detail="LEDGER_UNAVAILABLE")

    except Exception as e:
        log.error(f"[FIELD] Seal error: {e}")
        raise HTTPException(status_code=503, detail=f"LEDGER_ERROR: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# ONE TOUCH BRIDGE v1.1 — Mobile-First UI
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/verify-public/one-touch-bridge.html")
async def one_touch_bridge():
    """One Touch Bridge v1.1 — mobile-first UI for W-PAGE-001."""
    bridge_file = "/opt/windi/verify-public/one-touch-bridge.html"
    if os.path.exists(bridge_file):
        return FileResponse(bridge_file, media_type="text/html")
    return HTMLResponse("<h1>One Touch Bridge not found</h1>", status_code=404)


@app.get("/verify-public/{doc_id}")
async def verify_direct_url(doc_id: str):
    """URL limpa: /verify-public/VR-BABEL-0001 — serve UI com OG tags dinâmicas."""
    index = os.path.join(WEB_DIR, "index.html")
    if not os.path.exists(index):
        return JSONResponse({"id": doc_id})

    # Skip SSR for static assets
    if doc_id in ["favicon.ico", "og-preview.png", "static"] or "." in doc_id:
        return FileResponse(index)

    # Fetch document metadata for OG tags
    meta = await get_document_metadata(doc_id)

    # Read and inject OG tags
    with open(index, "r", encoding="utf-8") as f:
        html = f.read()

    html = inject_og_tags(html, doc_id, meta)

    return HTMLResponse(content=html, status_code=200)


# ═══════════════════════════════════════════════════════════════════════════════
# VPR ENDPOINTS — Verified Professional Record
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/did/{did_short}")
async def get_did_profile(did_short: str):
    """
    VPR Profile + Governance Score.
    did_short = fingerprint[:8] da tabela wallet_human.
    """
    # Resolver fingerprint[:8] → human_id
    wdb = wallet_conn()
    try:
        row = wdb.execute("""
            SELECT human_id, display_name, email, pubkey_ed25519,
                   fingerprint, created_at
            FROM wallet_human
            WHERE fingerprint LIKE ? AND status = 'active'
            LIMIT 1
        """, (did_short + "%",)).fetchone()
    finally:
        wdb.close()

    if not row:
        raise HTTPException(404, "DID not found")

    profile = dict(row)
    human_id = profile["human_id"]

    # Buscar wallet_context para role e governance_level
    wdb = wallet_conn()
    try:
        ctx = wdb.execute("""
            SELECT wallet_id, governance_level, role
            FROM wallet_context
            WHERE human_id = ? AND state = 'active'
            ORDER BY created_at DESC LIMIT 1
        """, (human_id,)).fetchone()

        # Buscar todos os aliases deste human
        aliases = [r["alias"] for r in wdb.execute(
            "SELECT alias FROM actor_alias WHERE human_id = ?",
            (human_id,)
        ).fetchall()]
    finally:
        wdb.close()

    # Adicionar wallet_id como alias também
    if ctx:
        aliases.append(ctx["wallet_id"])
    aliases.append(human_id)
    aliases = list(set(aliases))

    # Calcular governance com todos os aliases
    placeholders = ",".join("?" * len(aliases))
    ldb = ledger_conn()
    try:
        receipts_rows = ldb.execute(f"""
            SELECT governance_level, jurisdiction, isp_context
            FROM receipts
            WHERE actor IN ({placeholders})
        """, aliases).fetchall()
    finally:
        ldb.close()

    total = len(receipts_rows)
    jurisdictions = set()
    for r in receipts_rows:
        raw = r["jurisdiction"] or r["isp_context"] or ""
        for j in raw.split(","):
            j = j.strip()
            if j and len(j) <= 5:
                jurisdictions.add(j.upper())

    violations = 0  # tabela futura

    score = "HIGH"   if (total >= 5 and violations == 0) else \
            "MEDIUM" if (total >= 2) else "LOW"

    return {
        "did":       f"did:windi:{profile['fingerprint']}",
        "did_short": did_short,
        "profile": {
            "name":      profile["display_name"],
            "role":      ctx["role"] if ctx else "",
            "network":   "Grove Network",
            "registered": profile["created_at"],
            "crypto_method": "Ed25519"
        },
        "governance": {
            "score":         score,
            "documents":     total,
            "jurisdictions": sorted(list(jurisdictions)),
            "violations":    violations
        },
        "generated_at": now_iso(),
        "ledger_node":  "windi-domain.com:8101"
    }


@app.get("/api/receipts/by-did/{did_short}")
async def get_receipts_by_did(did_short: str, limit: int = 10):
    """Receipts públicos de um profissional (últimos N)."""
    wdb = wallet_conn()
    try:
        row = wdb.execute(
            "SELECT human_id FROM wallet_human WHERE fingerprint LIKE ? LIMIT 1",
            (did_short + "%",)
        ).fetchone()
    finally:
        wdb.close()

    if not row:
        raise HTTPException(404, "DID not found")

    human_id = row["human_id"]

    wdb = wallet_conn()
    try:
        aliases = [r["alias"] for r in wdb.execute(
            "SELECT alias FROM actor_alias WHERE human_id = ?", (human_id,)
        ).fetchall()]
        ctx = wdb.execute(
            "SELECT wallet_id FROM wallet_context WHERE human_id = ? LIMIT 1",
            (human_id,)
        ).fetchone()
    finally:
        wdb.close()

    if ctx:
        aliases.append(ctx["wallet_id"])
    aliases.append(human_id)
    aliases = list(set(aliases))

    placeholders = ",".join("?" * len(aliases))
    ldb = ledger_conn()
    try:
        rows = ldb.execute(f"""
            SELECT id, doc_name, doc_type, governance_level,
                   vpr_title, jurisdiction, declaration,
                   content_hash, created_at
            FROM receipts
            WHERE actor IN ({placeholders})
            ORDER BY created_at DESC
            LIMIT ?
        """, aliases + [limit]).fetchall()
    finally:
        ldb.close()

    def _format_ts(ts):
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        return str(ts)[:10] if ts else "—"

    return [
        {
            "receipt_id":       r["id"],
            "title":            r["vpr_title"] or r["doc_name"],
            "doc_type":         r["doc_type"],
            "governance_level": r["governance_level"],
            "jurisdiction":     [j.strip() for j in (r["jurisdiction"] or "").split(",") if j.strip()],
            "declaration":      r["declaration"] or "operator",
            "sealed_at":        _format_ts(r["created_at"]),
            "hash":             r["content_hash"]
        }
        for r in rows
    ]


@app.get("/api/did/by-wallet/{wallet_id}")
async def did_by_wallet(wallet_id: str):
    """Resolve wallet_id → did_short (para o tile do Palette)."""
    wdb = wallet_conn()
    try:
        row = wdb.execute("""
            SELECT wh.fingerprint
            FROM wallet_context wc
            JOIN wallet_human wh ON wc.human_id = wh.human_id
            WHERE wc.wallet_id = ? AND wc.state = 'active'
            LIMIT 1
        """, (wallet_id,)).fetchone()
    finally:
        wdb.close()

    if not row:
        raise HTTPException(404, "Wallet not found")

    return {"did_short": row["fingerprint"][:8]}


@app.get("/vpr/{did_short}", response_class=HTMLResponse)
@app.get("/verify-public/vpr/{did_short}", response_class=HTMLResponse)
async def vpr_page(request: Request, did_short: str):
    """
    Verified Professional Record — página pública dinâmica.
    URL: /vpr/{fingerprint[:8]} ou /verify-public/vpr/{fingerprint[:8]}
    """
    try:
        profile_data  = await get_did_profile(did_short)
        receipts_data = await get_receipts_by_did(did_short, limit=5)
    except HTTPException as e:
        if e.status_code == 404:
            return HTMLResponse(
                f"<html><body style='font-family:system-ui;padding:40px;text-align:center;'>"
                f"<h1>🔍 Record not found</h1>"
                f"<p>DID: <code>{did_short}</code></p>"
                f"<p>No verified professional record exists for this identifier.</p>"
                f"<p style='color:#666;margin-top:20px;'>I11 — Permanência de Evidência Criptográfica</p>"
                f"</body></html>",
                status_code=404
            )
        return HTMLResponse("Ledger unavailable", status_code=503)

    # Se não tem receipts, retorna 404 (I11)
    if profile_data["governance"]["documents"] == 0:
        return HTMLResponse(
            f"<html><body style='font-family:system-ui;padding:40px;text-align:center;'>"
            f"<h1>🔍 No verified work</h1>"
            f"<p>This professional has no documents on the Forensic Ledger yet.</p>"
            f"<p style='color:#666;'>VPR requires at least one sealed document.</p>"
            f"</body></html>",
            status_code=404
        )

    # Usar template se existir, senão inline HTML
    if vpr_templates:
        try:
            return vpr_templates.TemplateResponse("vpr.html", {
                "request":      request,
                "profile":      profile_data["profile"],
                "did":          profile_data["did"],
                "did_short":    did_short,
                "governance":   profile_data["governance"],
                "receipts":     receipts_data,
                "generated_at": profile_data["generated_at"],
                "ledger_node":  profile_data["ledger_node"],
                "record_id":    did_short.upper(),
                "verify_base":  "https://windi-domain.com/verify-public"
            })
        except Exception as e:
            log.warning(f"[VPR] Template error: {e}, falling back to inline HTML")

    # Fallback: Inline HTML (estilo KLAR)
    p = profile_data["profile"]
    g = profile_data["governance"]
    score_color = {"HIGH": "#2d5a27", "MEDIUM": "#b8860b", "LOW": "#8b0000"}.get(g["score"], "#666")

    receipts_html = ""
    for r in receipts_data[:3]:
        decl = "✓ Operator + Client" if r["declaration"] == "operator_confirmed" else "○ Operator declared"
        receipts_html += f'''
        <div style="background:#f9f9f7;border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-weight:700;font-size:14px;">{r["title"]}</div>
                    <div style="font-size:11px;color:#666;margin-top:4px;">
                        {r["receipt_id"]} · {r["doc_type"]} · {r["governance_level"]}
                    </div>
                </div>
                <a href="https://windi-domain.com/verify-public/?id={r["receipt_id"]}"
                   style="background:#C9A84C;color:#fff;padding:6px 12px;border-radius:6px;text-decoration:none;font-size:11px;font-weight:600;">
                    Verify
                </a>
            </div>
            <div style="font-size:10px;color:#888;margin-top:8px;">{decl}</div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VPR-{did_short.upper()} — {p["name"]} — WINDI</title>
    <meta property="og:title" content="✓ {p["name"]} — WINDI Verified Professional"/>
    <meta property="og:description" content="{g["documents"]} documents verified. Governance: {g["score"]}. Member of Grove Network."/>
    <meta property="og:url" content="https://windi-domain.com/verify-public/vpr/{did_short}"/>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family: 'Bricolage Grotesque', system-ui, sans-serif; background: #FFFDF5; color: #1a1a1a; min-height:100vh; }}
        .crown {{ background:#1a1a1a; color:#C9A84C; text-align:center; padding:12px; font-size:11px; font-weight:700; letter-spacing:2px; border-bottom:3px solid #C9A84C; }}
        .container {{ max-width:700px; margin:0 auto; padding:40px 20px; }}
        .header {{ text-align:center; margin-bottom:30px; }}
        .record-id {{ background:#C9A84C; color:#fff; padding:4px 14px; border-radius:20px; font-size:11px; font-weight:700; display:inline-block; }}
        h1 {{ font-size:28px; font-weight:800; margin:16px 0 4px; }}
        .role {{ color:#666; font-size:14px; }}
        .did {{ font-family:'JetBrains Mono',monospace; font-size:10px; color:#888; margin-top:12px; word-break:break-all; }}
        .governance {{ display:flex; gap:20px; justify-content:center; margin:30px 0; flex-wrap:wrap; }}
        .gov-card {{ background:#fff; border:1px solid #e0e0e0; border-radius:10px; padding:20px 30px; text-align:center; }}
        .gov-score {{ font-size:24px; font-weight:800; color:{score_color}; }}
        .gov-label {{ font-size:10px; color:#888; margin-top:4px; text-transform:uppercase; letter-spacing:1px; }}
        .section {{ margin-top:30px; }}
        .section-title {{ font-size:12px; font-weight:700; color:#C9A84C; text-transform:uppercase; letter-spacing:1px; margin-bottom:16px; border-bottom:1px solid #e0e0e0; padding-bottom:8px; }}
        .footer {{ margin-top:40px; padding-top:20px; border-top:3px solid #C9A84C; text-align:center; }}
        .footer p {{ font-size:10px; color:#888; margin:4px 0; }}
        .disclaimer {{ background:#f5f5f0; border:1px solid #e0e0e0; border-radius:8px; padding:12px; font-size:10px; color:#666; margin-top:20px; text-align:center; }}
    </style>
</head>
<body>
    <div class="crown">WINDI VERIFIED PROFESSIONAL RECORD</div>
    <div class="container">
        <div class="header">
            <span class="record-id">VPR-{did_short.upper()}</span>
            <h1>{p["name"]}</h1>
            <div class="role">{p["role"]} · {p["network"]}</div>
            <div class="did">{profile_data["did"]}</div>
            <div style="font-size:10px;color:#888;margin-top:4px;">Ed25519 · Registered {p["registered"][:10] if p["registered"] else "—"}</div>
        </div>

        <div class="governance">
            <div class="gov-card">
                <div class="gov-score">{g["score"]}</div>
                <div class="gov-label">Governance</div>
            </div>
            <div class="gov-card">
                <div class="gov-score">{g["documents"]}</div>
                <div class="gov-label">Documents</div>
            </div>
            <div class="gov-card">
                <div class="gov-score">{g["violations"]}</div>
                <div class="gov-label">Violations</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Recent Verified Work</div>
            {receipts_html if receipts_html else '<p style="color:#888;font-size:12px;">No recent documents.</p>'}
        </div>

        <div class="disclaimer">
            <strong>WINDI certifies existence, integrity, and authorship.</strong><br>
            It does not certify quality, competence, or outcome.<br>
            Declaration model: Operator-declared · Client-confirmable (Modelo B)
        </div>

        <div class="footer">
            <p style="font-size:18px;">🐉</p>
            <p>AI processes. Human decides. WINDI guarantees.</p>
            <p>Generated {profile_data["generated_at"]} · {profile_data["ledger_node"]}</p>
        </div>
    </div>
</body>
</html>'''

    return HTMLResponse(content=html, status_code=200)


if __name__ == "__main__":
    import uvicorn
    log.info(f"WINDI Verify Public Agent v1.0.1 — port {PORT}")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
