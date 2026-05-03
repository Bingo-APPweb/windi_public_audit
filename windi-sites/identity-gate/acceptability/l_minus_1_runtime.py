"""
L-1 Runtime — Pre-generation INPUT Filter
==========================================
§C-ACCEPTABILITY-001 · Layer L-1

Architecture: Hybrid (Galho A + Galho B)
  - Galho A (local): Regex detection for obvious Cardinal Sins
  - Galho B (Ollama): Semantic analysis for ambiguous cases

Invariants: I1, I9, I12, I14

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
"""

import os
import re
import json
import hashlib
import httpx
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Catalog path
CATALOG_PATH = Path(__file__).parent / "catalog_cardinal_sins.json"

# Galho B (Ollama) configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://85.215.131.0:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral:7b")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "10.0"))

# Enforcement mode
# shadow = log but don't block (except CS-1)
# enforce = full blocking
ACCEPTABILITY_MODE = os.environ.get("ACCEPTABILITY_MODE", "shadow")

# Ledger URL for sealing attempts
LEDGER_URL = os.environ.get("LEDGER_URL", "http://127.0.0.1:8101/api/receipts")

# ═══════════════════════════════════════════════════════════════════════════
# CATALOG LOADER
# ═══════════════════════════════════════════════════════════════════════════

_catalog_cache: Optional[Dict] = None


def load_catalog() -> Dict:
    """Load Cardinal Sins catalog with caching."""
    global _catalog_cache
    if _catalog_cache is None:
        with open(CATALOG_PATH, "r") as f:
            _catalog_cache = json.load(f)
    return _catalog_cache


def get_compiled_patterns() -> Dict[str, List[re.Pattern]]:
    """Compile regex patterns from catalog."""
    catalog = load_catalog()
    patterns = {}
    for cs_id, cs_data in catalog["cardinal_sins"].items():
        patterns[cs_id] = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in cs_data.get("keywords_regex", [])
        ]
    return patterns


# Compile patterns at module load
_compiled_patterns: Dict[str, List[re.Pattern]] = {}


def _ensure_patterns():
    """Lazy-load compiled patterns."""
    global _compiled_patterns
    if not _compiled_patterns:
        _compiled_patterns = get_compiled_patterns()


# ═══════════════════════════════════════════════════════════════════════════
# GALHO A: LOCAL REGEX DETECTION
# ═══════════════════════════════════════════════════════════════════════════

def detect_cardinal_sin_regex(text: str) -> Optional[Tuple[str, str, float]]:
    """
    Detect Cardinal Sin using local regex (Galho A).

    Returns:
        (cs_id, matched_pattern, confidence) or None if clean
    """
    _ensure_patterns()

    for cs_id, patterns in _compiled_patterns.items():
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return (cs_id, match.group(0), 0.95)  # High confidence for regex

    return None


# ═══════════════════════════════════════════════════════════════════════════
# GALHO B: SEMANTIC ANALYSIS VIA OLLAMA
# ═══════════════════════════════════════════════════════════════════════════

SEMANTIC_PROMPT = """You are a content safety classifier for a document generation system.

Analyze the following user input and determine if it contains any of these Cardinal Sins:
- CS-1: CSAM (child sexual abuse material)
- CS-2: Violence/harm instructions against identifiable persons
- CS-3: Impersonation of real persons without consent
- CS-4: Extremist material or incitement
- CS-5: Documentary fraud (fake official documents)
- CS-6: Deepfake intent for real persons
- CS-7: Third-party PII exposure

Respond with EXACTLY ONE of these formats:
- If CLEAN: {{"verdict": "CLEAN", "confidence": 0.95}}
- If BLOCKED: {{"verdict": "BLOCKED", "cs_id": "CS-X", "reason": "brief reason", "confidence": 0.85}}

User input to analyze:
---
{input}
---

JSON response:"""


async def detect_cardinal_sin_semantic(text: str) -> Optional[Tuple[str, str, float]]:
    """
    Detect Cardinal Sin using semantic analysis (Galho B / Ollama).

    Returns:
        (cs_id, reason, confidence) or None if clean
    """
    prompt = SEMANTIC_PROMPT.format(input=text[:2000])  # Truncate for safety

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistency
                        "num_predict": 100,
                    }
                }
            )

            if resp.status_code != 200:
                # Galho B unavailable — fail open (I10 LLM Sovereignty)
                return None

            result = resp.json()
            response_text = result.get("response", "")

            # Parse JSON from response
            try:
                # Find JSON in response
                json_match = re.search(r'\{[^}]+\}', response_text)
                if json_match:
                    verdict_data = json.loads(json_match.group())
                    if verdict_data.get("verdict") == "BLOCKED":
                        return (
                            verdict_data.get("cs_id", "CS-UNKNOWN"),
                            verdict_data.get("reason", "Semantic analysis blocked"),
                            verdict_data.get("confidence", 0.7)
                        )
            except json.JSONDecodeError:
                pass

            return None

    except Exception as e:
        # Galho B failure — fail open (I10)
        print(f"[L-1] Galho B error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# HYBRID DETECTION (A + B)
# ═══════════════════════════════════════════════════════════════════════════

async def detect_cardinal_sin(text: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Hybrid Cardinal Sin detection.

    1. Try Galho A (regex) first — fast, deterministic
    2. If regex finds nothing, try Galho B (semantic) — slower, nuanced

    Args:
        text: User input to analyze

    Returns:
        (blocked, log_entry)
    """
    now = datetime.now(timezone.utc).isoformat()
    catalog = load_catalog()

    # Step 1: Galho A (regex)
    regex_result = detect_cardinal_sin_regex(text)

    if regex_result:
        cs_id, matched, confidence = regex_result
        cs_data = catalog["cardinal_sins"].get(cs_id, {})

        log_entry = {
            "layer": "L-1",
            "detection": "regex",
            "galho": "A",
            "cs_id": cs_id,
            "cs_name": cs_data.get("name", "UNKNOWN"),
            "severity": cs_data.get("severity", "HIGH"),
            "matched": matched[:50],  # Truncate for safety
            "confidence": confidence,
            "enforcement": cs_data.get("enforcement", "SHADOW_THEN_ENFORCE"),
            "mode": ACCEPTABILITY_MODE,
            "blocked": False,  # Will be set below
            "ts": now
        }

        # Determine if we actually block
        if cs_data.get("enforcement") == "ALWAYS_ENFORCE":
            # CS-1 (CSAM) — always block, no shadow
            log_entry["blocked"] = True
            return (True, log_entry)
        elif ACCEPTABILITY_MODE == "enforce":
            log_entry["blocked"] = True
            return (True, log_entry)
        else:
            # Shadow mode — log but don't block
            log_entry["blocked"] = False
            log_entry["shadow_verdict"] = "WOULD_BLOCK"
            return (False, log_entry)

    # Step 2: Galho B (semantic) for ambiguous cases
    # Only if regex found nothing and text is substantial
    if len(text) > 50:
        semantic_result = await detect_cardinal_sin_semantic(text)

        if semantic_result:
            cs_id, reason, confidence = semantic_result
            cs_data = catalog["cardinal_sins"].get(cs_id, {})

            log_entry = {
                "layer": "L-1",
                "detection": "semantic",
                "galho": "B",
                "cs_id": cs_id,
                "cs_name": cs_data.get("name", "UNKNOWN"),
                "severity": cs_data.get("severity", "MEDIUM"),
                "reason": reason,
                "confidence": confidence,
                "enforcement": cs_data.get("enforcement", "SHADOW_THEN_ENFORCE"),
                "mode": ACCEPTABILITY_MODE,
                "blocked": False,
                "ts": now
            }

            # CS-1 always blocks
            if cs_id == "CS-1":
                log_entry["blocked"] = True
                return (True, log_entry)
            elif ACCEPTABILITY_MODE == "enforce" and confidence >= 0.75:
                log_entry["blocked"] = True
                return (True, log_entry)
            else:
                log_entry["blocked"] = False
                log_entry["shadow_verdict"] = "WOULD_BLOCK" if confidence >= 0.75 else "UNCERTAIN"
                return (False, log_entry)

    # Clean — no Cardinal Sin detected
    log_entry = {
        "layer": "L-1",
        "detection": "none",
        "galho": "A",
        "blocked": False,
        "mode": ACCEPTABILITY_MODE,
        "ts": now
    }
    return (False, log_entry)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN INTERFACE (called from sites_crud.py)
# ═══════════════════════════════════════════════════════════════════════════

async def acceptability_l_minus_1(payload: dict) -> Tuple[bool, dict]:
    """
    L-1: Pre-generation INPUT filter.

    This replaces the pass-through stub from §236.
    Interface is frozen — only body changed.

    Args:
        payload: The incoming request payload

    Returns:
        (allowed, log_entry) — allowed=False means block
    """
    # Extract text to analyze
    text_fields = []

    # Common text fields in container payloads
    for field in ["prompt", "content", "text", "input", "query", "message"]:
        if field in payload and isinstance(payload[field], str):
            text_fields.append(payload[field])

    # Config might have nested text
    # NOTE: Low threshold (5) because Cardinal Sins can be in short prompts
    if "config" in payload and isinstance(payload["config"], dict):
        for key, value in payload["config"].items():
            if isinstance(value, str) and len(value) > 5:
                text_fields.append(value)

    # Combine all text
    combined_text = " ".join(text_fields)

    if not combined_text.strip():
        # No text to analyze — pass through
        return (True, {
            "layer": "L-1",
            "detection": "none",
            "blocked": False,
            "reason": "no_text_content",
            "mode": ACCEPTABILITY_MODE,
            "ts": datetime.now(timezone.utc).isoformat()
        })

    # Run detection
    blocked, log_entry = await detect_cardinal_sin(combined_text)

    # Invert for return (blocked=True means allowed=False)
    return (not blocked, log_entry)


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY: HASH INPUT FOR LEDGER (without storing content)
# ═══════════════════════════════════════════════════════════════════════════

def hash_input_for_ledger(text: str) -> str:
    """
    Create SHA-256 hash of input for Ledger sealing.
    Content is NEVER stored — only the hash.
    """
    return f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"
