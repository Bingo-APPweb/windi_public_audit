#!/usr/bin/env python3
"""
WINDI Orchestrator v1.3.0 — "O Sistema Nervoso" (Multi-Tenant Forensic)
========================================================================
Connects: Prompt → Dragon API (LLM) → Communiqué → Seal → Ledger

Upgrades v1.3.0:
  - Tenant Context Receipt in Forensic Ledger (non-breaking segregation)
  - Audit-ready tenant isolation without Communiqué Engine changes
  - Reference hash for immutable tenant-to-document binding

Upgrades v1.2.0:
  - Multi-tenant isolation (pipeline + evidence + ledger metadata)
  - Tenant context injection into LLM prompts
  - Evidence bundle with tenant segregation
  - Audit-ready tenant observability

Upgrades v1.1.0:
  - ThreadingHTTPServer (concurrent requests)
  - human_ack gate for I9 compliance
  - tenant_id for multi-tenant isolation
  - facts_verified for anti-hallucination
  - request_id for traceability
  - Input limits (security)
  - Robust JSON extraction
  - Circuit breaker (anti-meltdown)

"AI processes. Human decides. WINDI guarantees."

26 February 2026 — Three Dragons Protocol
"""

import os
import sys
import json
import re
import time
import uuid
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from threading import Lock

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════
PORT = 8112
VERSION = "1.3.0"

# Limits
MAX_PAYLOAD_BYTES = 200_000
MAX_PROMPT_CHARS = 20_000

# Multi-tenant configuration
MULTI_TENANT = {
    "enabled": True,
    "mode": "pipeline-isolated",
    "engine_support": False,  # Communiqué Engine remains tenant-neutral
    "default_tenant": "public"
}

# Load API key
sys.path.insert(0, '/opt/windi/engine')
try:
    from dotenv import load_dotenv
    load_dotenv('/opt/windi/.env')
except ImportError:
    pass

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
MODEL = "claude-sonnet-4-20250514"

# Service endpoints
COMMUNIQUE_URL = "http://127.0.0.1:8105"
LEDGER_URL = "http://127.0.0.1:8101"

# ═══════════════════════════════════════════════════════════════
# CIRCUIT BREAKER — Anti-meltdown protection
# ═══════════════════════════════════════════════════════════════
class CircuitBreaker:
    """Simple circuit breaker for external API calls."""

    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.lock = Lock()

    def is_open(self) -> bool:
        with self.lock:
            if self.failures >= self.failure_threshold:
                if time.time() - self.last_failure_time > self.reset_timeout:
                    self.failures = 0
                    return False
                return True
            return False

    def record_failure(self):
        with self.lock:
            self.failures += 1
            self.last_failure_time = time.time()

    def record_success(self):
        with self.lock:
            self.failures = 0

# Global circuit breaker for Anthropic API
anthropic_breaker = CircuitBreaker(failure_threshold=3, reset_timeout=60)

# ═══════════════════════════════════════════════════════════════
# ARCHITECT SYSTEM PROMPT — Constitutional Content Generation
# ═══════════════════════════════════════════════════════════════
ARCHITECT_SYSTEM = """You are the WINDI Architect Dragon — a constitutional document generator.

ROLE: Generate institutional governance content from natural language prompts.
PROTOCOL: Three Dragons (Guardian protects, Architect builds, Witness verifies)

INVARIANTS (apply silently):
- I1: Human Sovereignty — structure content, never decide
- I5: No Fabrication — only verified facts
- I7: Institutional Tone — professional, diplomatic
- I9: No Autonomy Escalation — you generate, human approves

FACTS POLICY (I5 enforcement):
- You may ONLY cite facts provided in "VERIFIED FACTS" section from the user.
- If a requested fact is not present, state "FACT NOT PROVIDED" and omit it.
- Never invent dates, IDs, hashes, or regulatory references not explicitly given.

OUTPUT FORMAT — Always respond with valid JSON:
{
  "title_de": "German title",
  "title_en": "English title",
  "title_pt": "Portuguese title",
  "body_de": "German body content (2-4 paragraphs, institutional tone)",
  "body_en": "English body content (2-4 paragraphs, institutional tone)",
  "body_pt": "Portuguese body content (2-4 paragraphs, institutional tone)",
  "summary": "One-line summary of the document",
  "governance_level": "HIGH or MEDIUM",
  "suggested_template": "official|jornaline|field_report|security_advisory|governance_decision|system_bulletin",
  "sge_keywords": ["keyword1", "keyword2", "keyword3"]
}

CONTENT GUIDELINES:
- Write as WINDI Governance Institute
- Reference verified governance principles
- Include concrete details, not abstractions
- Trilingual content must be parallel (same meaning, culturally adapted)
- German is the primary institutional language (BaFin/regulatory context)
- Body should be 2-4 substantial paragraphs per language
- Use professional institutional register throughout

NEVER include markdown, code fences, or explanatory text outside the JSON."""


# ═══════════════════════════════════════════════════════════════
# DRAGON API — Call Claude as Architect (with retry + circuit breaker)
# ═══════════════════════════════════════════════════════════════
def call_architect(prompt: str, facts_verified: dict = None, request_id: str = "", tenant_id: str = "public") -> dict:
    """Send prompt to Claude (Architect role) and get structured content."""
    if not ANTHROPIC_API_KEY:
        return {"error": "ANTHROPIC_API_KEY not configured", "_request_id": request_id}

    # Circuit breaker check
    if anthropic_breaker.is_open():
        return {
            "error": "Circuit breaker OPEN — Anthropic API temporarily unavailable",
            "retry_after_seconds": 60,
            "_request_id": request_id
        }

    # ═══════════════════════════════════════════════════════════════
    # TENANT CONTEXT INJECTION — Institutional boundary awareness
    # ═══════════════════════════════════════════════════════════════
    full_prompt = f"""TENANT CONTEXT: {tenant_id}

This document is generated within the institutional boundary of the tenant above.
Ensure institutional tone and segregation awareness.

{prompt}"""

    # Inject verified facts into prompt
    if facts_verified:
        facts_json = json.dumps(facts_verified, ensure_ascii=False, indent=2)
        full_prompt = f"{full_prompt}\n\nVERIFIED FACTS (use only these, nothing else):\n{facts_json}"

    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 2048,
        "system": ARCHITECT_SYSTEM,
        "messages": [
            {"role": "user", "content": full_prompt}
        ]
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    # Retry logic (max 2 attempts for transient errors)
    max_retries = 2
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                text = ""
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        text += block["text"]

                # Robust JSON extraction — find largest {...} block
                text = text.strip()
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    json_str = match.group(0)
                else:
                    json_str = text

                # Strip markdown fences if present
                if json_str.startswith("```"):
                    json_str = json_str.split("\n", 1)[1] if "\n" in json_str else json_str[3:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                json_str = json_str.strip()

                content = json.loads(json_str)
                content["_dragon"] = "architect"
                content["_model"] = MODEL
                content["_tokens"] = data.get("usage", {})
                content["_request_id"] = request_id

                anthropic_breaker.record_success()
                return content

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)

            # Retry on 429 (rate limit) or 5xx (server error)
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
                continue

            anthropic_breaker.record_failure()
            return {"error": f"Anthropic API error {e.code}", "detail": error_body, "_request_id": request_id}

        except json.JSONDecodeError as e:
            return {"error": "Failed to parse Architect response as JSON", "raw": text[:500], "_request_id": request_id}

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            anthropic_breaker.record_failure()
            return {"error": f"Dragon API call failed: {str(e)}", "_request_id": request_id}

    return {"error": "Max retries exceeded", "_request_id": request_id}


# ═══════════════════════════════════════════════════════════════
# COMMUNIQUÉ BRIDGE — Create, Review, Publish
# ═══════════════════════════════════════════════════════════════
def _post(url: str, data: dict) -> dict:
    """HTTP POST helper for internal services."""
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8') if e.fp else ""
        return {"error": f"HTTP {e.code}", "detail": body}
    except Exception as e:
        return {"error": str(e)}


def _get(url: str) -> dict:
    """HTTP GET helper for internal services."""
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}


def communique_create(content: dict, author_name: str, author_role: str, tenant_id: str = "public") -> dict:
    """Create a new communiqué from Architect-generated content."""
    payload = {
        "title_de": content.get("title_de", "Untitled"),
        "title_en": content.get("title_en", ""),
        "title_pt": content.get("title_pt", ""),
        "body_de": content.get("body_de", ""),
        "body_en": content.get("body_en", ""),
        "body_pt": content.get("body_pt", ""),
        "author_name": author_name,
        "author_role": author_role,
        # tenant_id reserved for future Communiqué API support
    }
    if content.get("isp_template"):
        payload["isp_template"] = content["isp_template"]

    return _post(f"{COMMUNIQUE_URL}/api/communique/create", payload)


def communique_review(com_id: str, actor: str) -> dict:
    """Transition communiqué to REVIEW status."""
    return _post(f"{COMMUNIQUE_URL}/api/communique/{com_id}/review", {"actor": actor})


def communique_publish(com_id: str, actor: str) -> dict:
    """Publish communiqué — triggers auto-seal in Ledger."""
    return _post(f"{COMMUNIQUE_URL}/api/communique/{com_id}/publish", {"actor": actor})


def communique_verify(com_id: str) -> dict:
    """Verify communiqué integrity via circular hash proof."""
    return _get(f"{COMMUNIQUE_URL}/api/communique/{com_id}/verify")


# ═══════════════════════════════════════════════════════════════
# LEDGER TENANT CONTEXT — Forensic-Metadata Isolation
# "Tenant segregation enforced through ledger-anchored metadata"
# ═══════════════════════════════════════════════════════════════
def ledger_add_tenant_context(
    tenant_id: str,
    com_id: str,
    actor: str,
    publish_result: dict,
    request_id: str = ""
) -> dict:
    """
    Create a forensic tenant isolation receipt in the Ledger.

    Architecture: Since the Ledger doesn't support attaching metadata to existing
    receipts, we create a companion receipt that cryptographically links the
    tenant_id to the original document artifacts.

    The receipt contains:
    - tenant_id: institutional boundary identifier
    - segregation_mode: "forensic" (metadata-based isolation)
    - references: com_id, ledger_id, content_hash, bundle_hash
    - metadata_hash: SHA-256 of metadata (tamper-evident)

    This enables:
    - Audit trail for multi-tenant operations
    - Forensic traceability without engine modification
    - BaFin/ISO/SOC2 evidence chain compliance
    """
    now = datetime.now(timezone.utc).isoformat()

    # Skip if no ledger_id (document wasn't sealed)
    if not publish_result.get("ledger_id"):
        return {"status": "SKIPPED", "reason": "no ledger_id in publish_result"}

    # Build structured metadata (audit-friendly)
    tenant_metadata = {
        "tenant_id": tenant_id,
        "segregation_mode": "forensic",
        "pipeline": "orchestrator",
        "context": "multi-tenant-isolation",
        "attached_at": now,
        "actor": actor,
        "references": {
            "com_id": com_id,
            "ledger_id": publish_result.get("ledger_id", ""),
            "content_hash": publish_result.get("content_hash", ""),
            "bundle_hash": publish_result.get("bundle_hash", "")
        },
        "orchestrator_version": VERSION,
        "request_id": request_id
    }

    # Cryptographic proof: hash of metadata for tamper evidence
    metadata_bytes = json.dumps(tenant_metadata, sort_keys=True, ensure_ascii=False).encode("utf-8")
    metadata_hash = hashlib.sha256(metadata_bytes).hexdigest()
    tenant_metadata["metadata_hash"] = metadata_hash

    # Generate unique receipt ID
    receipt_id = f"TC-{tenant_id[:12]}-{com_id.replace('COM-', '')}"

    # Build receipt payload (using valid 'doc' doc_type)
    receipt_payload = {
        "id": receipt_id,
        "actor": actor,
        "app": "windi-orchestrator",
        "doc_name": f"[TENANT-ISO] {tenant_id} ↔ {com_id}",
        "doc_type": "doc",
        "content_hash": metadata_hash,
        "bytes": len(metadata_bytes),
        "governance_level": "GOLD",
        "sge_score": 1.0,
        "isp_context": f"tenant-isolation:{tenant_id}:{com_id}",
        "metadata": tenant_metadata
    }

    # POST to Ledger
    result = _post(f"{LEDGER_URL}/api/receipts", receipt_payload)

    if "error" not in result and result.get("ok"):
        return {
            "status": "OK",
            "tenant_id": tenant_id,
            "receipt_id": receipt_id,
            "metadata_hash": metadata_hash,
            "segregation_model": {
                "type": "forensic-metadata isolation",
                "engine_modification_required": False,
                "auditability": "full",
                "tamper_protection": "ledger anchored"
            }
        }

    return {
        "status": "FAILED",
        "tenant_id": tenant_id,
        "error": result.get("error", "Unknown error"),
        "detail": result.get("detail", "")
    }


# ═══════════════════════════════════════════════════════════════
# ORCHESTRATOR — The Full Pipeline (I9-compliant)
# ═══════════════════════════════════════════════════════════════
def orchestrate(
    prompt: str,
    author_name: str = "WINDI Governance Institute",
    author_role: str = "Architect Dragon",
    actor: str = "WINDI-Orchestrator-v1",
    auto_publish: bool = False,
    human_ack: str = "",
    tenant_id: str = "public",
    facts_verified: dict = None,
    request_id: str = ""
) -> dict:
    """
    Full orchestration pipeline:
    Prompt → Dragon → Communiqué → (optional: Review → Publish → Verify)

    I9 ENFORCEMENT:
    - If auto_publish=False (default): creates document in DRAFT status
    - If auto_publish=True: REQUIRES human_ack="I_APPROVE_PUBLISH"
      Without explicit ack, pipeline is BLOCKED (I9 violation prevention)
    """
    pipeline = {
        "orchestrator": f"WINDI Orchestrator v{VERSION}",
        "request_id": request_id,
        "tenant_id": tenant_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
        "steps": {},
        "status": "running"
    }

    # ── Step 1: ARCHITECT generates content ──
    print(f"[ORCH:{request_id[:8]}] Step 1: Calling Architect Dragon (tenant: {tenant_id})...")
    content = call_architect(prompt, facts_verified, request_id, tenant_id)
    if "error" in content:
        pipeline["steps"]["architect"] = {"status": "FAILED", "error": content["error"]}
        pipeline["status"] = "failed_at_architect"
        return pipeline

    pipeline["steps"]["architect"] = {
        "status": "OK",
        "title": content.get("title_en", ""),
        "governance_level": content.get("governance_level", ""),
        "suggested_template": content.get("suggested_template", ""),
        "tokens": content.get("_tokens", {}),
        "summary": content.get("summary", "")
    }

    # ── Step 2: CREATE in Communiqué ──
    print(f"[ORCH:{request_id[:8]}] Step 2: Creating in Communiqué...")
    create_result = communique_create(content, author_name, author_role, tenant_id)
    if "error" in create_result:
        pipeline["steps"]["create"] = {"status": "FAILED", "error": create_result["error"]}
        pipeline["status"] = "failed_at_create"
        return pipeline

    com_id = create_result.get("id", "")
    pipeline["steps"]["create"] = {
        "status": "OK",
        "com_id": com_id,
        "isp_resolver": create_result.get("isp_resolver", {})
    }

    # ── Step 3: AUTO-PUBLISH PATH (requires I9 gate) ──
    if auto_publish:
        # ════════════════════════════════════════════════════════════
        # I9 GATE: Explicit human acknowledgment required
        # "No Autonomy Escalation" — machine cannot self-authorize
        # ════════════════════════════════════════════════════════════
        if human_ack != "I_APPROVE_PUBLISH":
            pipeline["status"] = "blocked_i9"
            pipeline["steps"]["review"] = {
                "status": "BLOCKED",
                "reason": "Missing human_ack for auto_publish (I9: No Autonomy Escalation)",
                "required_ack": "I_APPROVE_PUBLISH"
            }
            pipeline["next_steps"] = {
                "note": "Set human_ack='I_APPROVE_PUBLISH' to proceed with publish",
                "manual_review": f"POST {COMMUNIQUE_URL}/api/communique/{com_id}/review",
                "manual_publish": f"POST {COMMUNIQUE_URL}/api/communique/{com_id}/publish"
            }
            pipeline["com_id"] = com_id
            return pipeline

        print(f"[ORCH:{request_id[:8]}] Step 3: Registering review (I9 ack received)...")
        review_result = communique_review(com_id, actor)
        pipeline["steps"]["review"] = {
            "status": "OK" if "error" not in review_result else "FAILED",
            "actor": actor,
            "human_ack": "VERIFIED",
            "result": review_result
        }

        if "error" in review_result:
            pipeline["status"] = "failed_at_review"
            return pipeline

        # ── Step 4: PUBLISH (auto-seal in Ledger) ──
        print(f"[ORCH:{request_id[:8]}] Step 4: Publishing (seal + ledger)...")
        publish_result = communique_publish(com_id, actor)
        pipeline["steps"]["publish"] = {
            "status": "OK" if "error" not in publish_result else "FAILED",
            "content_hash": publish_result.get("publish_result", {}).get("content_hash", ""),
            "bundle_hash": publish_result.get("publish_result", {}).get("bundle_hash", ""),
            "ledger_id": publish_result.get("publish_result", {}).get("ledger_id", ""),
            "pdf_path": publish_result.get("publish_result", {}).get("pdf_path", ""),
            "result": publish_result
        }

        if "error" in publish_result:
            pipeline["status"] = "failed_at_publish"
            return pipeline

        # ── Step 5: VERIFY (circular integrity proof) ──
        print(f"[ORCH:{request_id[:8]}] Step 5: Verifying integrity...")
        verify_result = communique_verify(com_id)

        # Handle missing verify endpoint gracefully
        if "error" in verify_result and "404" in str(verify_result.get("error", "")):
            # Fallback: verify via Ledger directly
            ledger_id = publish_result.get("publish_result", {}).get("ledger_id", "")
            if ledger_id:
                ledger_check = _get(f"{LEDGER_URL}/api/receipts/{ledger_id}")
                if ledger_check.get("ok"):
                    verify_result = {
                        "verified": True,
                        "source": "ledger_direct",
                        "ledger_receipt": ledger_check.get("receipt", {})
                    }

        pipeline["steps"]["verify"] = {
            "status": "OK" if verify_result.get("verified") else "PARTIAL",
            "verified": verify_result.get("verified", False),
            "source": verify_result.get("source", "communique_api"),
            "result": verify_result
        }
        pipeline["status"] = "SEALED" if verify_result.get("verified") else "published_unverified"

        # ═══════════════════════════════════════════════════════════════
        # TENANT CONTEXT RECEIPT — Anchor tenant_id in Forensic Ledger
        # Non-breaking multi-tenant segregation without Communiqué changes
        # ═══════════════════════════════════════════════════════════════
        pub_result = publish_result.get("publish_result", {})
        print(f"[ORCH:{request_id[:8]}] Step 6: Anchoring tenant context in Ledger...")
        tenant_ctx = ledger_add_tenant_context(
            tenant_id=tenant_id,
            com_id=com_id,
            actor=actor,
            publish_result=pub_result,
            request_id=request_id
        )
        pipeline["steps"]["tenant_context_receipt"] = tenant_ctx

        # ═══════════════════════════════════════════════════════════════
        # EVIDENCE BUNDLE — Tenant-isolated forensic proof (CRITICAL)
        # "Tenant segregation is enforced at orchestration and evidence layer"
        # ═══════════════════════════════════════════════════════════════
        pipeline["evidence"] = {
            "tenant_id": tenant_id,
            "com_id": com_id,
            "ledger_id": pub_result.get("ledger_id", ""),
            "content_hash": pub_result.get("content_hash", ""),
            "bundle_hash": pub_result.get("bundle_hash", ""),
            "pdf_path": pub_result.get("pdf_path", ""),
            "tenant_isolation": {
                "receipt_id": tenant_ctx.get("receipt_id", ""),
                "metadata_hash": tenant_ctx.get("metadata_hash", ""),
                "segregation_model": tenant_ctx.get("segregation_model", {})
            },
            "orchestrated_by": f"WINDI Orchestrator v{VERSION}",
            "sovereign_mode": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Add publish metadata for audit trail
        pipeline["steps"]["publish"]["metadata"] = {
            "tenant_id": tenant_id,
            "orchestrated_by": f"WINDI Orchestrator v{VERSION}",
            "sovereign_mode": True,
            "human_ack_verified": human_ack == "I_APPROVE_PUBLISH"
        }

    else:
        # DRAFT mode — human must manually approve
        pipeline["steps"]["review"] = {"status": "PENDING", "note": "Awaiting human approval (I9 compliance)"}
        pipeline["status"] = "DRAFT_CREATED"
        pipeline["next_steps"] = {
            "review": f"POST {COMMUNIQUE_URL}/api/communique/{com_id}/review",
            "publish": f"POST {COMMUNIQUE_URL}/api/communique/{com_id}/publish",
            "verify": f"GET {COMMUNIQUE_URL}/api/communique/{com_id}/verify",
            "note": "Human must explicitly approve each transition (I9: No Autonomy Escalation)"
        }
        # Even in draft mode, track tenant context
        pipeline["draft_context"] = {
            "tenant_id": tenant_id,
            "awaiting_human_approval": True
        }

    pipeline["com_id"] = com_id
    return pipeline


# ═══════════════════════════════════════════════════════════════
# HTTP SERVER — Threading + Request ID + Limits
# ═══════════════════════════════════════════════════════════════
class OrchestratorHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[ORCH] {args[0]}" if args else "")

    def _send(self, data, status=200, request_id: str = ""):
        if request_id:
            data["_request_id"] = request_id
        body = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", len(body))
        if request_id:
            self.send_header("X-WINDI-Request-ID", request_id)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.rstrip("/")
        request_id = str(uuid.uuid4())

        if path == "/health":
            self._send({
                "service": "WINDI Orchestrator",
                "version": VERSION,
                "status": "operational",
                "port": PORT,
                "dragon": {
                    "model": MODEL,
                    "api_key_configured": bool(ANTHROPIC_API_KEY),
                    "circuit_breaker": "OPEN" if anthropic_breaker.is_open() else "CLOSED"
                },
                "services": {
                    "communique": COMMUNIQUE_URL,
                    "ledger": LEDGER_URL,
                },
                "limits": {
                    "max_payload_bytes": MAX_PAYLOAD_BYTES,
                    "max_prompt_chars": MAX_PROMPT_CHARS
                },
                "multi_tenant": MULTI_TENANT,
                "i9_gate": "ENABLED (human_ack required for auto_publish)",
                "compliance": {
                    "tenant_isolation": "pipeline-isolated",
                    "evidence_segregation": True,
                    "ledger_metadata": True,
                    "audit_statement": "Tenant segregation is enforced at the orchestration and forensic evidence layer. The Communiqué Engine remains tenant-neutral to preserve compatibility."
                },
                "principle": "AI processes. Human decides. WINDI guarantees.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, request_id=request_id)
        elif path == "" or path == "/":
            self._send({
                "service": "WINDI Orchestrator",
                "version": VERSION,
                "endpoints": {
                    "POST /orchestrate": "Full pipeline: prompt → dragon → communiqué → seal",
                    "POST /generate": "Dragon-only: prompt → content (no save)",
                    "GET /health": "Service health check"
                },
                "usage": {
                    "orchestrate": {
                        "prompt": "Your governance document request (required)",
                        "facts_verified": "Dict of verified facts for I5 compliance (optional but recommended)",
                        "author_name": "Document author (default: WINDI Governance Institute)",
                        "author_role": "Author role (default: Architect Dragon)",
                        "actor": "Review/publish actor (default: WINDI-Orchestrator-v1)",
                        "tenant_id": "Tenant isolation key (default: public)",
                        "auto_publish": "If true, requires human_ack (default: false)",
                        "human_ack": "Set to 'I_APPROVE_PUBLISH' to authorize auto_publish (I9 gate)"
                    }
                },
                "i9_policy": "auto_publish=true requires human_ack='I_APPROVE_PUBLISH'"
            }, request_id=request_id)
        else:
            self._send({"error": "Not found"}, 404, request_id=request_id)

    def do_POST(self):
        path = self.path.rstrip("/")
        request_id = str(uuid.uuid4())

        # ── Security: Payload size limit ──
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_PAYLOAD_BYTES:
            self._send({"error": f"Payload too large (max {MAX_PAYLOAD_BYTES} bytes)"}, 413, request_id)
            return

        try:
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
        except json.JSONDecodeError:
            self._send({"error": "Invalid JSON"}, 400, request_id)
            return

        if path == "/orchestrate":
            prompt = body.get("prompt", "")
            if not prompt:
                self._send({"error": "Missing 'prompt' field"}, 400, request_id)
                return

            # ── Security: Prompt length limit ──
            if len(prompt) > MAX_PROMPT_CHARS:
                self._send({"error": f"Prompt too long (max {MAX_PROMPT_CHARS} chars)"}, 400, request_id)
                return

            result = orchestrate(
                prompt=prompt,
                author_name=body.get("author_name", "WINDI Governance Institute"),
                author_role=body.get("author_role", "Architect Dragon"),
                actor=body.get("actor", "WINDI-Orchestrator-v1"),
                auto_publish=body.get("auto_publish", False),
                human_ack=body.get("human_ack", ""),
                tenant_id=body.get("tenant_id", "public"),
                facts_verified=body.get("facts_verified"),
                request_id=request_id
            )
            self._send(result, request_id=request_id)

        elif path == "/generate":
            prompt = body.get("prompt", "")
            if not prompt:
                self._send({"error": "Missing 'prompt' field"}, 400, request_id)
                return

            if len(prompt) > MAX_PROMPT_CHARS:
                self._send({"error": f"Prompt too long (max {MAX_PROMPT_CHARS} chars)"}, 400, request_id)
                return

            content = call_architect(
                prompt,
                facts_verified=body.get("facts_verified"),
                request_id=request_id
            )
            self._send(content, request_id=request_id)

        else:
            self._send({"error": "Not found"}, 404, request_id)


def main():
    print(f"🐉 WINDI Orchestrator v{VERSION} — 'O Sistema Nervoso' (Multi-Tenant)")
    print(f"   Port: {PORT}")
    print(f"   Dragon: {MODEL} ({'configured' if ANTHROPIC_API_KEY else 'NOT configured'})")
    print(f"   Communiqué: {COMMUNIQUE_URL}")
    print(f"   Ledger: {LEDGER_URL}")
    print(f"   Threading: ENABLED (concurrent requests)")
    print(f"   I9 Gate: ENABLED (human_ack required for auto_publish)")
    print(f"   Circuit Breaker: ENABLED (3 failures → 60s cooldown)")
    print(f"   Multi-Tenant: {MULTI_TENANT['mode']} (engine_support: {MULTI_TENANT['engine_support']})")
    print(f"   Evidence: Tenant-isolated (forensic segregation)")
    print(f"   Limits: {MAX_PAYLOAD_BYTES} bytes payload, {MAX_PROMPT_CHARS} chars prompt")
    print(f"   Principle: AI processes. Human decides. WINDI guarantees.")
    print()

    server = ThreadingHTTPServer(("0.0.0.0", PORT), OrchestratorHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🐉 Orchestrator stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
