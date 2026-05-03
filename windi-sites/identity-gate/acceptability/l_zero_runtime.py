"""
L0 Runtime — Pre-seal OUTPUT Filter
====================================
§C-ACCEPTABILITY-001 · Layer L0

Purpose: Classify generated content BEFORE sealing to Ledger.
Decision: Binary (allow seal) or (block + reason).
Edge cases: If uncertain, allow seal but set l1_review_pending=TRUE.

Architecture: Hybrid (Galho A + Galho B)
  - Galho A: Quick heuristics and structure checks
  - Galho B: Semantic quality assessment

Invariants: I1, I9, I11, I14

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
"""

import os
import re
import json
import hashlib
import httpx
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

# Import L-1 for Cardinal Sin check on output too
from .l_minus_1_runtime import detect_cardinal_sin, ACCEPTABILITY_MODE

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Galho B (Ollama) configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://85.215.131.0:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral:7b")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "10.0"))

# Confidence threshold for automatic seal
CONFIDENCE_THRESHOLD = float(os.environ.get("L0_CONFIDENCE_THRESHOLD", "0.85"))

# ═══════════════════════════════════════════════════════════════════════════
# GALHO A: STRUCTURAL CHECKS
# ═══════════════════════════════════════════════════════════════════════════

def check_structural_quality(content: dict) -> Tuple[bool, float, Optional[str]]:
    """
    Quick structural checks on generated content.

    Returns:
        (passed, confidence, reason_if_failed)
    """
    # Extract text content
    text = ""
    if isinstance(content, dict):
        text = content.get("text", content.get("content", content.get("output", "")))
    elif isinstance(content, str):
        text = content

    if not text:
        return (False, 0.0, "empty_content")

    # Check minimum length
    if len(text.strip()) < 10:
        return (False, 0.3, "content_too_short")

    # Check for placeholder patterns (I14 violation)
    placeholder_patterns = [
        r'\[INSERT\s+.*?\]',
        r'\{YOUR\s+.*?\}',
        r'<PLACEHOLDER>',
        r'TODO:',
        r'FIXME:',
        r'\*\*\*\s*MISSING\s*\*\*\*',
    ]
    for pattern in placeholder_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return (False, 0.9, f"placeholder_detected: {pattern}")

    # Check for gibberish (repetitive characters)
    if re.search(r'(.)\1{10,}', text):
        return (False, 0.85, "repetitive_content")

    # Check for code injection attempts
    injection_patterns = [
        r'<script\b',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'document\.cookie',
    ]
    for pattern in injection_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return (False, 0.95, f"injection_attempt: {pattern}")

    return (True, 0.9, None)


# ═══════════════════════════════════════════════════════════════════════════
# GALHO B: SEMANTIC QUALITY CHECK
# ═══════════════════════════════════════════════════════════════════════════

QUALITY_PROMPT = """You are a content quality assessor for a document generation system.

Evaluate the following generated content for:
1. Coherence: Does it make logical sense?
2. Completeness: Does it appear finished?
3. Appropriateness: Is it suitable for professional use?
4. Authenticity: Does it avoid harmful hallucinations?

Respond with EXACTLY this JSON format:
{{
  "quality": "GOOD" or "POOR" or "UNCERTAIN",
  "confidence": 0.0 to 1.0,
  "issues": ["issue1", "issue2"] or [],
  "recommend_review": true or false
}}

Content to evaluate:
---
{content}
---

JSON response:"""


async def check_semantic_quality(content: str) -> Tuple[str, float, list, bool]:
    """
    Semantic quality check using Galho B (Ollama).

    Returns:
        (quality, confidence, issues, recommend_review)
    """
    prompt = QUALITY_PROMPT.format(content=content[:3000])

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 150,
                    }
                }
            )

            if resp.status_code != 200:
                # Galho B unavailable — return uncertain
                return ("UNCERTAIN", 0.5, ["galho_b_unavailable"], True)

            result = resp.json()
            response_text = result.get("response", "")

            # Parse JSON from response
            try:
                json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    return (
                        data.get("quality", "UNCERTAIN"),
                        data.get("confidence", 0.5),
                        data.get("issues", []),
                        data.get("recommend_review", True)
                    )
            except json.JSONDecodeError:
                pass

            return ("UNCERTAIN", 0.5, ["parse_error"], True)

    except Exception as e:
        print(f"[L0] Galho B error: {e}")
        return ("UNCERTAIN", 0.5, [str(e)], True)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN INTERFACE (called from sites_crud.py)
# ═══════════════════════════════════════════════════════════════════════════

async def acceptability_l_zero(content: dict) -> Tuple[bool, dict]:
    """
    L0: Pre-seal OUTPUT filter.

    This replaces the pass-through stub from §236.
    Interface is frozen — only body changed.

    Args:
        content: The generated content before seal

    Returns:
        (allowed, log_entry) — allowed=False means block seal
    """
    now = datetime.now(timezone.utc).isoformat()

    # Extract text content
    text = ""
    if isinstance(content, dict):
        text = content.get("text", content.get("content", content.get("output", "")))
        if isinstance(text, dict):
            text = json.dumps(text)
    elif isinstance(content, str):
        text = content

    # Step 1: Run Cardinal Sin check on OUTPUT too
    # (Generated content could violate policies)
    if text and len(text) > 20:
        blocked, cs_log = await detect_cardinal_sin(text)
        if blocked:
            return (False, {
                "layer": "L0",
                "blocked": True,
                "reason": "cardinal_sin_in_output",
                "cs_data": cs_log,
                "mode": ACCEPTABILITY_MODE,
                "ts": now
            })

    # Step 2: Structural quality check (Galho A)
    struct_passed, struct_conf, struct_reason = check_structural_quality(content)

    if not struct_passed:
        log_entry = {
            "layer": "L0",
            "check": "structural",
            "galho": "A",
            "blocked": ACCEPTABILITY_MODE == "enforce",
            "reason": struct_reason,
            "confidence": struct_conf,
            "mode": ACCEPTABILITY_MODE,
            "ts": now
        }
        if ACCEPTABILITY_MODE == "enforce":
            return (False, log_entry)
        else:
            log_entry["shadow_verdict"] = "WOULD_BLOCK"
            return (True, log_entry)

    # Step 3: Semantic quality check (Galho B) for substantial content
    recommend_review = False

    if text and len(text) > 100:
        quality, confidence, issues, recommend_review = await check_semantic_quality(text)

        if quality == "POOR" and confidence >= CONFIDENCE_THRESHOLD:
            log_entry = {
                "layer": "L0",
                "check": "semantic",
                "galho": "B",
                "quality": quality,
                "confidence": confidence,
                "issues": issues,
                "blocked": ACCEPTABILITY_MODE == "enforce",
                "mode": ACCEPTABILITY_MODE,
                "ts": now
            }
            if ACCEPTABILITY_MODE == "enforce":
                return (False, log_entry)
            else:
                log_entry["shadow_verdict"] = "WOULD_BLOCK"
                return (True, log_entry)

        # Uncertain or low confidence — mark for L1 review
        if quality == "UNCERTAIN" or confidence < CONFIDENCE_THRESHOLD:
            recommend_review = True

    # Passed all checks
    log_entry = {
        "layer": "L0",
        "blocked": False,
        "structural": {
            "passed": True,
            "confidence": struct_conf
        },
        "l1_review_pending": recommend_review,
        "mode": ACCEPTABILITY_MODE,
        "ts": now
    }

    return (True, log_entry)


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY: Determine if L1 review needed
# ═══════════════════════════════════════════════════════════════════════════

def should_flag_for_l1_review(log_entry: dict) -> bool:
    """
    Determine if content should be flagged for L1 post-seal review.

    Returns True if:
    - L0 passed but with low confidence
    - Semantic check returned UNCERTAIN
    - Any shadow_verdict was recorded
    """
    if log_entry.get("l1_review_pending"):
        return True

    if log_entry.get("shadow_verdict"):
        return True

    structural = log_entry.get("structural", {})
    if structural.get("confidence", 1.0) < 0.8:
        return True

    return False
