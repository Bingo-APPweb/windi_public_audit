"""
AI Writer Runtime — Internal-Only Mode
========================================
§3b AI Writer · W-SITES-001 · Caminho C

Orchestration layer for AI content generation with:
- 4-layer DID Gate (defense in depth)
- 8-step pipeline (no shortcuts)
- PoE-structured prompts
- Internal shadow validation mode

Invariants: I1, I9, I10, I11, I14

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

from .ollama_writer_client import generate_content, OllamaWriterError, check_ollama_health

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Internal mode configuration
AI_WRITER_MODE = os.environ.get("AI_WRITER_MODE", "internal")

# Allowlisted DIDs for internal mode (SOVEREIGN tier only)
INTERNAL_DIDS_ALLOWLIST = [
    "did:windi:dragon-001",  # Human Dragon
    "did:windi:a79c3cdf-85cc-453a-9072-8677a1fe6b09",  # Test DID for internal validation
    # Add Liga IA+H DIDs as needed
]

# Allowlisted hosts for internal mode
INTERNAL_HOSTS_ALLOWLIST = [
    "localhost",
    "127.0.0.1",
    "windi-domain.com",
    "87.106.29.233",  # Server A
]

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "prompt_templates"

# Valid template types
VALID_TEMPLATES = ["article", "landing", "about"]


# ═══════════════════════════════════════════════════════════════════════════
# 4-LAYER DID GATE (I9 Defense in Depth)
# ═══════════════════════════════════════════════════════════════════════════

class InternalModeViolation(Exception):
    """
    Exception for internal mode access violations.

    I9: Any unauthorized access attempt is explicit failure.
    """
    def __init__(self, layer: str, reason: str):
        self.layer = layer
        self.reason = reason
        self.timestamp = datetime.now(timezone.utc).isoformat()
        super().__init__(f"InternalModeViolation[{layer}]: {reason}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": "internal_mode_violation",
            "layer": self.layer,
            "reason": self.reason,
            "invariant": "I9",
            "timestamp": self.timestamp
        }


def assert_internal_writer_authorized(
    caller_did: str,
    caller_tier: Optional[str],
    request_host: str
) -> None:
    """
    4-layer authorization gate for internal writer mode.

    Layers:
        1. DID exact match against allowlist
        2. Tier verification (SOVEREIGN required)
        3. ENV flag check (AI_WRITER_MODE=internal)
        4. Host allowlist check

    Args:
        caller_did: The DID making the request
        caller_tier: The tier of the caller (from DB)
        request_host: The host header from the request

    Raises:
        InternalModeViolation: If any layer fails
    """
    # Layer 1: DID exact match
    if caller_did not in INTERNAL_DIDS_ALLOWLIST:
        raise InternalModeViolation(
            layer="DID_MATCH",
            reason=f"DID '{caller_did}' not in internal allowlist"
        )

    # Layer 2: Tier verification
    if caller_tier != "SOVEREIGN":
        raise InternalModeViolation(
            layer="TIER_CHECK",
            reason=f"Tier '{caller_tier}' is not SOVEREIGN"
        )

    # Layer 3: ENV flag check
    if AI_WRITER_MODE != "internal":
        raise InternalModeViolation(
            layer="ENV_FLAG",
            reason=f"AI_WRITER_MODE is '{AI_WRITER_MODE}', not 'internal'"
        )

    # Layer 4: Host allowlist
    # Extract hostname without port
    host_clean = request_host.split(":")[0] if request_host else ""
    if host_clean not in INTERNAL_HOSTS_ALLOWLIST:
        raise InternalModeViolation(
            layer="HOST_CHECK",
            reason=f"Host '{host_clean}' not in internal hosts allowlist"
        )

    # All 4 layers passed
    return None


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE LOADING
# ═══════════════════════════════════════════════════════════════════════════

def load_template(template_type: str) -> str:
    """
    Load a prompt template by type.

    Args:
        template_type: One of 'article', 'landing', 'about'

    Returns:
        Template string

    Raises:
        ValueError: If template type is invalid (I14)
    """
    if template_type not in VALID_TEMPLATES:
        raise ValueError(f"Invalid template type: {template_type}. Valid: {VALID_TEMPLATES}")

    template_path = TEMPLATE_DIR / f"{template_type}.txt"

    if not template_path.exists():
        raise ValueError(f"Template file not found: {template_path}")

    return template_path.read_text()


def build_prompt(template_type: str, variables: Dict[str, str]) -> str:
    """
    Build a prompt from template and variables.

    Args:
        template_type: Template to use
        variables: Dict of {variable_name: value}

    Returns:
        Formatted prompt string
    """
    template = load_template(template_type)

    # Fill in variables, leave unfilled ones as placeholders
    for key, value in variables.items():
        template = template.replace(f"{{{key}}}", str(value))

    return template


# ═══════════════════════════════════════════════════════════════════════════
# GENERATION RESULT
# ═══════════════════════════════════════════════════════════════════════════

class GenerationResult:
    """
    Result of a content generation operation.

    Contains all data needed for sealing and provenance.

    W-CORTEX-001: source_mode tracks origin for audit trail.
    """
    def __init__(
        self,
        ok: bool,
        content: Optional[str] = None,
        content_hash: Optional[str] = None,
        error: Optional[str] = None,
        l_minus_1_log: Optional[Dict] = None,
        l_zero_log: Optional[Dict] = None,
        generation_log: Optional[Dict] = None,
        l1_review_pending: bool = False,
        source_mode: str = "template",  # "template" | "free"
        template_type: Optional[str] = None  # article/landing/about/legal/null
    ):
        self.ok = ok
        self.content = content
        self.content_hash = content_hash
        self.error = error
        self.l_minus_1_log = l_minus_1_log
        self.l_zero_log = l_zero_log
        self.generation_log = generation_log
        self.l1_review_pending = l1_review_pending
        self.source_mode = source_mode
        self.template_type = template_type
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "content": self.content,
            "content_hash": self.content_hash,
            "error": self.error,
            "l_minus_1_log": self.l_minus_1_log,
            "l_zero_log": self.l_zero_log,
            "generation_log": self.generation_log,
            "l1_review_pending": self.l1_review_pending,
            "timestamp": self.timestamp
        }


# ═══════════════════════════════════════════════════════════════════════════
# 8-STEP PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def assert_public_writer_authorized(caller_did: str, caller_tier: Optional[str], request_host: str) -> None:
    """
    Public authorization gate — requires valid DID only.

    For public-facing generation endpoints (e.g., /sites/generate).
    Less restrictive than internal mode but still requires identity.
    """
    if not caller_did:
        raise InternalModeViolation(
            layer="DID_REQUIRED",
            reason="No DID provided — anonymous generation prohibited"
        )
    # DID exists = authorized for public generation


async def generate_with_pipeline(
    caller_did: str,
    caller_tier: str,
    request_host: str,
    acceptability_l_minus_1_fn,
    acceptability_l_zero_fn,
    template_type: Optional[str] = None,
    template_variables: Optional[Dict[str, str]] = None,
    free_prompt: Optional[str] = None,
    did_gate_fn: Optional[Any] = None  # Custom DID gate function (default: internal)
) -> GenerationResult:
    """
    W-CORTEX-001 — Canal Único Soberano de Inferência.

    Full 8-step generation pipeline. ALL model calls MUST pass through here.
    "Duas entradas são aceitáveis. Dois pipelines são proibidos."

    Steps:
        1. Input validation (template XOR free_prompt)
        2. DID Gate (configurable: internal or public)
        3. Build prompt (branching point - ONLY HERE)
        4. L-1 acceptability check (input prompt)
        5. Ollama generate (mistral:7b @ Galho B)
        6. L0 acceptability check (output)
        7. [Seal handled by caller]
        8. Return result with source_mode for audit

    Args:
        caller_did: DID making the request
        caller_tier: Tier of the caller
        request_host: Host header
        acceptability_l_minus_1_fn: L-1 check function
        acceptability_l_zero_fn: L0 check function
        template_type: article/landing/about/legal (mutually exclusive with free_prompt)
        template_variables: Variables to fill template
        free_prompt: Direct prompt text (mutually exclusive with template_type)
        did_gate_fn: Authorization function (default: assert_internal_writer_authorized)
                     Use assert_public_writer_authorized for public endpoints

    Returns:
        GenerationResult with content, source_mode, and template_type for audit
    """
    now = datetime.now(timezone.utc).isoformat()

    # ─── STEP 1: Input validation — EXACTLY ONE of template_type OR free_prompt ─
    # W-CORTEX-001 Guardrail: No ambiguity allowed
    if (template_type is None) == (free_prompt is None):
        return GenerationResult(
            ok=False,
            error="CORTEX_INPUT_ERROR: Exactly one of template_type or free_prompt must be provided",
            source_mode="invalid"
        )

    # Determine source mode (for audit trail)
    if template_type is not None:
        source_mode = "template"
    else:
        source_mode = "free"

    # ─── STEP 2: DID Gate (configurable) ─────────────────────────────────────
    # Default to internal mode if no gate provided
    gate_fn = did_gate_fn if did_gate_fn is not None else assert_internal_writer_authorized
    try:
        gate_fn(caller_did, caller_tier, request_host)
    except InternalModeViolation as e:
        return GenerationResult(
            ok=False,
            error=f"DID_GATE_FAILED: {e.reason}",
            l_minus_1_log={"layer": "DID_GATE", "blocked": True, "reason": e.reason},
            source_mode=source_mode,
            template_type=template_type
        )

    # ─── STEP 3: Build prompt — ONLY branching point in pipeline ─────────────
    # W-CORTEX-001: After this step, pipeline is IDENTICAL for both modes
    if template_type is not None:
        try:
            prompt = build_prompt(template_type, template_variables or {})
        except ValueError as e:
            return GenerationResult(
                ok=False,
                error=f"TEMPLATE_ERROR: {str(e)}",
                source_mode=source_mode,
                template_type=template_type
            )
    else:
        # Free prompt mode — direct pass-through
        prompt = free_prompt

    # ─── STEP 4: L-1 check on input prompt ──────────────────────────────────
    # W-CORTEX-001: From here, pipeline is IDENTICAL for template and free modes
    l1_allowed, l1_log = await acceptability_l_minus_1_fn({"prompt": prompt})

    if not l1_allowed:
        # CS-1 triggers 451 + lockdown
        cs_id = l1_log.get("cs_id", "UNKNOWN")
        if cs_id == "CS-1":
            return GenerationResult(
                ok=False,
                error=f"L-1_BLOCKED_CS1: CSAM content prohibited",
                l_minus_1_log=l1_log,
                source_mode=source_mode,
                template_type=template_type
            )
        # Other CS in shadow mode - should not block but log
        # This is a fallback; shadow mode CS-2..7 should pass L-1

    # ─── STEP 5: Ollama generation (Galho B) ─────────────────────────────────
    try:
        gen_result = await generate_content(prompt)
        generated_content = gen_result.get("content", "")
        generation_log = {
            "model": gen_result.get("model"),
            "tokens": gen_result.get("tokens"),
            "duration_ms": gen_result.get("duration_ms"),
            "attempt": gen_result.get("attempt"),
            "source_mode": source_mode,  # W-CORTEX-001 audit trail
            "timestamp": now
        }
    except OllamaWriterError as e:
        # I14: Explicit failure, no silent degradation
        return GenerationResult(
            ok=False,
            error=f"OLLAMA_FAILED: {e.reason}",
            l_minus_1_log=l1_log,
            generation_log=e.to_dict(),
            source_mode=source_mode,
            template_type=template_type
        )

    # ─── STEP 6: L0 check on output ──────────────────────────────────────────
    l0_allowed, l0_log = await acceptability_l_zero_fn({"content": generated_content})

    l1_review_pending = False

    if not l0_allowed:
        return GenerationResult(
            ok=False,
            error=f"L0_BLOCKED: {l0_log.get('reason', 'quality_check_failed')}",
            l_minus_1_log=l1_log,
            l_zero_log=l0_log,
            generation_log=generation_log,
            source_mode=source_mode,
            template_type=template_type
        )

    # Check if L1 review pending (low confidence)
    if l0_log.get("l1_review_pending"):
        l1_review_pending = True

    # ─── STEP 7-8: Prepare result (sealing done by caller) ───────────────────
    content_hash = f"sha256:{hashlib.sha256(generated_content.encode()).hexdigest()}"

    return GenerationResult(
        ok=True,
        content=generated_content,
        content_hash=content_hash,
        l_minus_1_log=l1_log,
        l_zero_log=l0_log,
        generation_log=generation_log,
        l1_review_pending=l1_review_pending,
        source_mode=source_mode,
        template_type=template_type
    )


# ═══════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════

async def writer_health() -> Dict[str, Any]:
    """
    Check AI Writer health status.

    Returns:
        {
            "service": "ai-writer",
            "mode": "internal",
            "ollama": {...},
            "templates": [...],
            "status": "healthy"/"degraded"
        }
    """
    ollama_status = await check_ollama_health()

    # Check templates
    templates_ok = all(
        (TEMPLATE_DIR / f"{t}.txt").exists()
        for t in VALID_TEMPLATES
    )

    return {
        "service": "ai-writer",
        "mode": AI_WRITER_MODE,
        "ollama": ollama_status,
        "templates": VALID_TEMPLATES,
        "templates_ok": templates_ok,
        "status": "healthy" if (ollama_status.get("ok") and templates_ok) else "degraded"
    }
