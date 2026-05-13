"""
AI Writer Runtime — W-CORTEX-001 Canal Único Soberano
======================================================
§241 Phase 2 · Tier Routing · Multi-Backend

Orchestration layer for AI content generation with:
- 4-layer DID Gate (defense in depth)
- Tier routing (FREE→Ollama B, MED→Mistral, HIGH→Claude)
- L0 input filter → Routing → L-1 output filter
- Explicit failure per tier (no silent fallback)

Invariants: I1, I9, I10, I11, I14

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import hashlib
import httpx
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

from .ollama_writer_client import generate_content, OllamaWriterError, check_ollama_health

# ═══════════════════════════════════════════════════════════════════════════
# §241 — TIER ROUTING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Service tier mapping from DID tier_level
# tier_level 1-2 (SEED/NODAL) → max FREE
# tier_level 3 (SOVEREIGN) → max MED
# tier_level 4 (ORACLE) → max HIGH
DID_TIER_TO_MAX_SERVICE = {
    1: "FREE",   # SEED
    2: "FREE",   # NODAL
    3: "MED",    # SOVEREIGN
    4: "HIGH",   # ORACLE
}

# Service tier hierarchy for comparison
SERVICE_TIER_LEVEL = {
    "FREE": 1,
    "MED": 2,
    "HIGH": 3,
}

# External API configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
GENESIS_URL = os.environ.get("GENESIS_URL", "http://127.0.0.1:8096")

# Cost estimates per model (EUR)
COST_PER_1K_TOKENS = {
    "mistral:7b": 0.0,           # FREE - local Ollama
    "mistral-small-latest": 0.000007,  # MED - Mistral API
    "claude-sonnet-4-20250514": 0.0196,   # HIGH - Anthropic API
}

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

# Valid template types (§245 — 8 templates total)
VALID_TEMPLATES = [
    "article", "landing", "about",  # Original templates
    "profile", "press", "portfolio", "record", "custom"  # §245 new templates
]

# §245.2 — Tier routing per template
# Each template has a default tier and minimum tier
TEMPLATE_TIER_CONFIG = {
    "record": {"default": "HIGH", "min": "MED"},     # Institutional, irreversible
    "press": {"default": "HIGH", "min": "MED"},      # Reputational, embargos
    "profile": {"default": "MED", "min": "FREE"},    # Sectoral, regulated
    "landing": {"default": "MED", "min": "FREE"},    # Commercial, verifiable
    "portfolio": {"default": "FREE", "min": "FREE"}, # Descriptive, low risk
    "custom": {"default": "MED", "min": "MED"},      # NEVER FREE — attack vector
    "article": {"default": "FREE", "min": "FREE"},   # General content
    "about": {"default": "FREE", "min": "FREE"},     # Institutional about
}


def get_template_tier_config(template_type: str) -> dict:
    """Get tier configuration for a template type."""
    return TEMPLATE_TIER_CONFIG.get(template_type, {"default": "FREE", "min": "FREE"})


def language_tier_override(detected_lang: str, requested_tier: str) -> str:
    """
    §245.5 — Override tier for Portuguese content.
    Ollama (FREE tier) has asymmetric performance: DE/EN > PT.
    For PT content, upgrade to MED minimum.
    """
    if detected_lang.lower() == "pt" and requested_tier == "FREE":
        return "MED"  # PT quality lower in Ollama mistral:7b
    return requested_tier


# ═══════════════════════════════════════════════════════════════════════════
# §241 — TIER RESOLUTION (DID as authority)
# ═══════════════════════════════════════════════════════════════════════════

async def resolve_effective_tier(caller_did: str, requested_tier: Optional[str] = None) -> Tuple[str, Dict]:
    """
    Resolve effective service tier based on DID authority.

    Rules:
    1. DID tier_level determines MAX allowed service tier
    2. requested_tier can DOWNGRADE but never UPGRADE
    3. Tier escalation attempt → returns error info for 403

    Returns:
        Tuple of (effective_tier, resolution_info)
    """
    resolution_info = {
        "did": caller_did,
        "requested_tier": requested_tier,
        "authoritative_tier": None,
        "effective_tier": None,
        "escalation_blocked": False,
        "lookup_source": None,
    }

    # Default to FREE if no DID (shouldn't happen due to DID gate, but defensive)
    if not caller_did:
        resolution_info["effective_tier"] = "FREE"
        resolution_info["authoritative_tier"] = "FREE"
        resolution_info["lookup_source"] = "no_did_default"
        return "FREE", resolution_info

    # Lookup DID tier from Genesis
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{GENESIS_URL}/api/genesis/lookup/{caller_did}")
            if resp.status_code == 200:
                data = resp.json()
                tier_level = data.get("tier_level", 1)
                authoritative_tier = DID_TIER_TO_MAX_SERVICE.get(tier_level, "FREE")
                resolution_info["authoritative_tier"] = authoritative_tier
                resolution_info["lookup_source"] = "genesis"
                resolution_info["did_tier_level"] = tier_level
                resolution_info["did_tier_name"] = data.get("tier", "UNKNOWN")
            else:
                # DID not found - default to FREE
                authoritative_tier = "FREE"
                resolution_info["authoritative_tier"] = "FREE"
                resolution_info["lookup_source"] = "genesis_not_found"
    except Exception as e:
        # Genesis unavailable - fail closed to FREE
        authoritative_tier = "FREE"
        resolution_info["authoritative_tier"] = "FREE"
        resolution_info["lookup_source"] = f"genesis_error: {str(e)[:50]}"

    # Determine effective tier
    if requested_tier is None:
        # No preference - use authoritative
        effective_tier = authoritative_tier
    else:
        req_level = SERVICE_TIER_LEVEL.get(requested_tier.upper(), 1)
        auth_level = SERVICE_TIER_LEVEL.get(authoritative_tier, 1)

        if req_level > auth_level:
            # Escalation attempt BLOCKED
            resolution_info["escalation_blocked"] = True
            resolution_info["escalation_attempted"] = requested_tier.upper()
            effective_tier = None  # Signal 403
        else:
            # Downgrade allowed
            effective_tier = requested_tier.upper()

    resolution_info["effective_tier"] = effective_tier
    return effective_tier, resolution_info


# ═══════════════════════════════════════════════════════════════════════════
# §241 — EXTERNAL ROUTING FUNCTIONS (private)
# ═══════════════════════════════════════════════════════════════════════════

async def _route_external_claude(prompt: str) -> Dict[str, Any]:
    """
    Route to Claude API (HIGH tier).

    Returns dict with: ok, content, model, tokens, duration_ms
    Raises on failure (explicit, no fallback).
    """
    if not ANTHROPIC_API_KEY:
        raise OllamaWriterError(
            reason="ANTHROPIC_API_KEY not configured",
            details={"tier": "HIGH", "model": "claude-sonnet-4-20250514"}
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )

            if resp.status_code != 200:
                raise OllamaWriterError(
                    reason=f"Claude API error: HTTP {resp.status_code}",
                    details={"response": resp.text[:200], "tier": "HIGH"}
                )

            data = resp.json()
            content = data["content"][0]["text"]
            tokens = data.get("usage", {}).get("output_tokens", 0)

            return {
                "ok": True,
                "content": content,
                "model": "claude-sonnet-4-20250514",
                "tokens": {"completion": tokens},
                "tier": "HIGH",
                "cost_eur": tokens * COST_PER_1K_TOKENS["claude-sonnet-4-20250514"] / 1000,
            }

    except httpx.TimeoutException:
        raise OllamaWriterError(
            reason="Claude API timeout",
            details={"tier": "HIGH", "timeout": 60}
        )
    except Exception as e:
        raise OllamaWriterError(
            reason=f"Claude API error: {str(e)}",
            details={"tier": "HIGH"}
        )


class TierUnavailableError(Exception):
    """
    §242 — TIER_UNAVAILABLE error for 503 responses.

    Used when a tier's provider is not configured.
    Includes available_tiers for client-side recovery.
    """
    def __init__(self, tier: str, reason: str, available_tiers: list):
        self.tier = tier
        self.reason = reason
        self.available_tiers = available_tiers
        super().__init__(f"TIER_UNAVAILABLE: {tier} - {reason}")

    def to_response(self) -> Dict[str, Any]:
        """Return 503-ready response payload."""
        return {
            "ok": False,
            "error": {
                "code": "TIER_UNAVAILABLE",
                "tier_requested": self.tier,
                "message": f"{self.tier} tier temporarily unavailable (provider key not configured)",
                "available_tiers": self.available_tiers,
                "action": f"Choose {' or '.join(self.available_tiers)} tier"
            }
        }


def _get_available_tiers() -> list:
    """Return list of currently available tiers based on config."""
    available = ["FREE"]  # Ollama B always available (local)
    if MISTRAL_API_KEY and MISTRAL_API_KEY != "SUBSTITUIR":
        available.append("MED")
    if ANTHROPIC_API_KEY:
        available.append("HIGH")
    return available


async def _route_external_mistral(prompt: str) -> Dict[str, Any]:
    """
    Route to Mistral API (MED tier).

    Returns dict with: ok, content, model, tokens, duration_ms
    Raises TierUnavailableError (503) if key not configured.
    Raises OllamaWriterError on API failure.
    """
    if not MISTRAL_API_KEY or MISTRAL_API_KEY == "SUBSTITUIR":
        raise TierUnavailableError(
            tier="MED",
            reason="provider key not configured",
            available_tiers=_get_available_tiers()
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mistral-small-latest",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )

            if resp.status_code != 200:
                raise OllamaWriterError(
                    reason=f"Mistral API error: HTTP {resp.status_code}",
                    details={"response": resp.text[:200], "tier": "MED"}
                )

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("completion_tokens", 0)

            return {
                "ok": True,
                "content": content,
                "model": "mistral-small-latest",
                "tokens": {"completion": tokens},
                "tier": "MED",
                "cost_eur": tokens * COST_PER_1K_TOKENS["mistral-small-latest"] / 1000,
            }

    except httpx.TimeoutException:
        raise OllamaWriterError(
            reason="Mistral API timeout",
            details={"tier": "MED", "timeout": 60}
        )
    except Exception as e:
        raise OllamaWriterError(
            reason=f"Mistral API error: {str(e)}",
            details={"tier": "MED"}
        )


async def _route_ollama_b(prompt: str) -> Dict[str, Any]:
    """
    Route to Ollama B (FREE tier) - Galho B local.

    Returns dict with: ok, content, model, tokens, duration_ms
    Raises on failure (explicit, no fallback).
    """
    result = await generate_content(prompt)

    if not result.get("ok"):
        raise OllamaWriterError(
            reason="Ollama B generation failed",
            details={"tier": "FREE", "model": "mistral:7b"}
        )

    return {
        "ok": True,
        "content": result.get("content", ""),
        "model": "mistral:7b",
        "tokens": result.get("tokens", {}),
        "tier": "FREE",
        "cost_eur": 0.0,
        "duration_ms": result.get("duration_ms", 0),
    }


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
    §241: tier_used, model_used, cost_eur for routing audit.
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
        template_type: Optional[str] = None,  # article/landing/about/legal/null
        # §241 Tier Routing metadata
        tier_used: Optional[str] = None,      # FREE | MED | HIGH
        model_used: Optional[str] = None,     # mistral:7b | mistral-small-latest | claude-sonnet-4-20250514
        cost_eur: float = 0.0,                # Cost estimate in EUR
        tier_resolution: Optional[Dict] = None  # Full resolution info for audit
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
        # §241 Tier Routing
        self.tier_used = tier_used
        self.model_used = model_used
        self.cost_eur = cost_eur
        self.tier_resolution = tier_resolution
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
            "timestamp": self.timestamp,
            # §241 Tier Routing
            "tier_used": self.tier_used,
            "model_used": self.model_used,
            "cost_eur": self.cost_eur,
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
    did_gate_fn: Optional[Any] = None,  # Custom DID gate function (default: internal)
    requested_tier: Optional[str] = None  # §241: Requested service tier (can only downgrade)
) -> GenerationResult:
    """
    W-CORTEX-001 — Canal Único Soberano de Inferência.

    Full pipeline with tier routing. ALL model calls MUST pass through here.
    "Duas entradas são aceitáveis. Dois pipelines são proibidos."

    §241 Pipeline Order:
        1. Input validation (template XOR free_prompt)
        2. DID Gate (configurable: internal or public)
        3. Tier Resolution (DID authoritative, requested_tier for downgrade only)
        4. Build prompt (branching point - ONLY HERE)
        5. L0 acceptability check (INPUT — before spending tokens)
        6. Tier Routing (HIGH→Claude, MED→Mistral, FREE→Ollama B)
        7. L-1 acceptability check (OUTPUT — before seal)
        8. Return result with tier_used, model_used, cost_eur

    Args:
        caller_did: DID making the request
        caller_tier: Tier of the caller (legacy, used for DID gate)
        request_host: Host header
        acceptability_l_minus_1_fn: L-1 check function (OUTPUT filter)
        acceptability_l_zero_fn: L0 check function (INPUT filter)
        template_type: article/landing/about/legal (mutually exclusive with free_prompt)
        template_variables: Variables to fill template
        free_prompt: Direct prompt text (mutually exclusive with template_type)
        did_gate_fn: Authorization function (default: assert_internal_writer_authorized)
        requested_tier: Service tier preference (can downgrade, cannot escalate)

    Returns:
        GenerationResult with content, tier_used, model_used, cost_eur for audit
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

    # ─── STEP 3: Tier Resolution (DID authoritative) ─────────────────────────
    # §241: DID tier_level determines MAX allowed service tier
    # requested_tier can DOWNGRADE but never UPGRADE
    effective_tier, tier_resolution = await resolve_effective_tier(caller_did, requested_tier)

    # Escalation blocked → 403-style error
    if tier_resolution.get("escalation_blocked"):
        return GenerationResult(
            ok=False,
            error=f"TIER_ESCALATION_BLOCKED: Requested {tier_resolution.get('escalation_attempted')} "
                  f"exceeds authorized {tier_resolution.get('authoritative_tier')}",
            tier_resolution=tier_resolution,
            source_mode=source_mode,
            template_type=template_type
        )

    # effective_tier is None only if escalation blocked (already handled above)
    if effective_tier is None:
        return GenerationResult(
            ok=False,
            error="TIER_RESOLUTION_FAILED: Unable to determine effective tier",
            tier_resolution=tier_resolution,
            source_mode=source_mode,
            template_type=template_type
        )

    # ─── STEP 4: Build prompt — ONLY branching point in pipeline ─────────────
    # W-CORTEX-001: After this step, pipeline is IDENTICAL for both modes
    if template_type is not None:
        try:
            prompt = build_prompt(template_type, template_variables or {})
        except ValueError as e:
            return GenerationResult(
                ok=False,
                error=f"TEMPLATE_ERROR: {str(e)}",
                source_mode=source_mode,
                template_type=template_type,
                tier_resolution=tier_resolution
            )
    else:
        # Free prompt mode — direct pass-through
        prompt = free_prompt

    # ─── STEP 5: INPUT filter (before spending tokens) ─────────────────────────
    # §241: Input filter runs BEFORE routing — catch bad prompts before they cost money
    # Note: acceptability_l_minus_1_fn was designed for input (looks for 'prompt' key)
    input_allowed, input_log = await acceptability_l_minus_1_fn({"prompt": prompt})

    if not input_allowed:
        # CS-1 triggers 451 + lockdown
        cs_id = input_log.get("cs_id", "UNKNOWN")
        if cs_id == "CS-1":
            return GenerationResult(
                ok=False,
                error=f"INPUT_BLOCKED_CS1: CSAM content prohibited",
                l_minus_1_log=input_log,
                source_mode=source_mode,
                template_type=template_type,
                tier_used=effective_tier,
                tier_resolution=tier_resolution
            )
        # Other CS blocks
        return GenerationResult(
            ok=False,
            error=f"INPUT_BLOCKED: {input_log.get('reason', 'input_check_failed')}",
            l_minus_1_log=input_log,
            source_mode=source_mode,
            template_type=template_type,
            tier_used=effective_tier,
            tier_resolution=tier_resolution
        )

    # ─── STEP 6: Tier Routing (HIGH→Claude, MED→Mistral, FREE→Ollama B) ─────
    # §241: No fallback — explicit failure per tier
    # §242: TierUnavailableError for 503 (provider not configured)
    try:
        if effective_tier == "HIGH":
            gen_result = await _route_external_claude(prompt)
        elif effective_tier == "MED":
            gen_result = await _route_external_mistral(prompt)
        else:  # FREE
            gen_result = await _route_ollama_b(prompt)

        generated_content = gen_result.get("content", "")
        model_used = gen_result.get("model")
        cost_eur = gen_result.get("cost_eur", 0.0)

        generation_log = {
            "model": model_used,
            "tokens": gen_result.get("tokens"),
            "duration_ms": gen_result.get("duration_ms"),
            "tier": effective_tier,
            "cost_eur": cost_eur,
            "source_mode": source_mode,  # W-CORTEX-001 audit trail
            "timestamp": now
        }

    except TierUnavailableError as e:
        # §242: 503 Service Unavailable — tier not configured
        # Return structured error for client-side tier selection
        return GenerationResult(
            ok=False,
            error=f"TIER_UNAVAILABLE:{e.tier}",
            l_minus_1_log=input_log,
            generation_log={
                "tier_unavailable": e.to_response(),
                "available_tiers": e.available_tiers,
                "timestamp": now
            },
            source_mode=source_mode,
            template_type=template_type,
            tier_used=effective_tier,
            tier_resolution=tier_resolution
        )

    except OllamaWriterError as e:
        # I14: Explicit failure, no silent fallback
        return GenerationResult(
            ok=False,
            error=f"ROUTING_FAILED[{effective_tier}]: {e.reason}",
            l_minus_1_log=input_log,
            generation_log=e.to_dict(),
            source_mode=source_mode,
            template_type=template_type,
            tier_used=effective_tier,
            tier_resolution=tier_resolution
        )

    # ─── STEP 7: OUTPUT filter (before seal) ───────────────────────────────────
    # §241: Output filter runs AFTER routing — validate generated content before sealing
    # Note: acceptability_l_zero_fn was designed for output (looks for 'content' key)
    output_allowed, output_log = await acceptability_l_zero_fn({"content": generated_content})

    l1_review_pending = False

    if not output_allowed:
        return GenerationResult(
            ok=False,
            error=f"OUTPUT_BLOCKED: {output_log.get('reason', 'output_check_failed')}",
            l_minus_1_log=input_log,
            l_zero_log=output_log,
            generation_log=generation_log,
            source_mode=source_mode,
            template_type=template_type,
            tier_used=effective_tier,
            model_used=model_used,
            cost_eur=cost_eur,
            tier_resolution=tier_resolution
        )

    # Check if L1 review pending (low confidence)
    if output_log.get("l1_review_pending"):
        l1_review_pending = True

    # ─── STEP 8: Prepare result (sealing done by caller) ─────────────────────
    content_hash = f"sha256:{hashlib.sha256(generated_content.encode()).hexdigest()}"

    return GenerationResult(
        ok=True,
        content=generated_content,
        content_hash=content_hash,
        l_minus_1_log=input_log,
        l_zero_log=output_log,
        generation_log=generation_log,
        l1_review_pending=l1_review_pending,
        source_mode=source_mode,
        template_type=template_type,
        tier_used=effective_tier,
        model_used=model_used,
        cost_eur=cost_eur,
        tier_resolution=tier_resolution
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
