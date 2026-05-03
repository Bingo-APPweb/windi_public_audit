"""
Ollama Writer Client — Galho B Interface
==========================================
§3b AI Writer · W-SITES-001

Wrapper for Ollama API with:
- Retry logic (3 attempts)
- Timeout handling (180s read, 10s connect)
- I14 Explicit Failure (no silent degradation)

Invariants: I10, I14

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://85.215.131.0:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_WRITER_MODEL", "mistral:7b")
MAX_RETRIES = int(os.environ.get("OLLAMA_WRITER_RETRIES", "3"))  # 3 retries

# Timeout configuration (generation can take 60-90s on mistral:7b)
OLLAMA_CONNECT_TIMEOUT = float(os.environ.get("OLLAMA_WRITER_CONNECT_TIMEOUT", "10.0"))
OLLAMA_READ_TIMEOUT = float(os.environ.get("OLLAMA_WRITER_READ_TIMEOUT", "180.0"))  # 3min for large generations
OLLAMA_TIMEOUT = httpx.Timeout(
    connect=OLLAMA_CONNECT_TIMEOUT,
    read=OLLAMA_READ_TIMEOUT,
    write=30.0,
    pool=30.0
)

# Default generation parameters
DEFAULT_TEMPERATURE = float(os.environ.get("OLLAMA_WRITER_TEMP", "0.4"))
DEFAULT_MAX_TOKENS = int(os.environ.get("OLLAMA_WRITER_MAX_TOKENS", "1500"))


# ═══════════════════════════════════════════════════════════════════════════
# EXPLICIT FAILURE EXCEPTION (I14)
# ═══════════════════════════════════════════════════════════════════════════

class OllamaWriterError(Exception):
    """
    Explicit failure for Ollama Writer operations.

    I14: No silent degradation. If generation fails, we fail loudly.
    """
    def __init__(self, reason: str, details: Optional[Dict] = None):
        self.reason = reason
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        super().__init__(f"OllamaWriterError: {reason}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": "ollama_writer_failure",
            "reason": self.reason,
            "details": self.details,
            "invariant": "I14",
            "timestamp": self.timestamp
        }


# ═══════════════════════════════════════════════════════════════════════════
# WRITER CLIENT
# ═══════════════════════════════════════════════════════════════════════════

async def generate_content(
    prompt: str,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    stop_sequences: Optional[list] = None
) -> Dict[str, Any]:
    """
    Generate content using Ollama (Galho B).

    Args:
        prompt: The full prompt to send to the model
        temperature: Creativity level (0.0-1.0), default 0.4
        max_tokens: Maximum tokens to generate, default 1500
        stop_sequences: Optional list of stop sequences

    Returns:
        {
            "ok": True,
            "content": "generated text",
            "model": "mistral:7b",
            "tokens": {"prompt": N, "completion": M},
            "duration_ms": N,
            "timestamp": "ISO8601"
        }

    Raises:
        OllamaWriterError: If generation fails after retries (I14)
    """
    now = datetime.now(timezone.utc).isoformat()

    request_body = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
    }

    if stop_sequences:
        request_body["options"]["stop"] = stop_sequences

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
                resp = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json=request_body
                )

                if resp.status_code != 200:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    continue

                result = resp.json()

                # Validate response structure
                if "response" not in result:
                    last_error = "Missing 'response' field in Ollama response"
                    continue

                generated_text = result.get("response", "")

                if not generated_text.strip():
                    last_error = "Empty response from Ollama"
                    continue

                # Success - return result
                return {
                    "ok": True,
                    "content": generated_text,
                    "model": OLLAMA_MODEL,
                    "tokens": {
                        "prompt": result.get("prompt_eval_count", 0),
                        "completion": result.get("eval_count", 0)
                    },
                    "duration_ms": result.get("total_duration", 0) // 1_000_000,
                    "attempt": attempt,
                    "timestamp": now
                }

        except httpx.TimeoutException:
            last_error = f"Timeout after {OLLAMA_READ_TIMEOUT}s read timeout (attempt {attempt})"

        except httpx.ConnectError as e:
            last_error = f"Connection error: {str(e)} (attempt {attempt})"

        except Exception as e:
            last_error = f"Unexpected error: {str(e)} (attempt {attempt})"

    # All retries exhausted - I14 Explicit Failure
    raise OllamaWriterError(
        reason="generation_failed_after_retries",
        details={
            "last_error": last_error,
            "attempts": MAX_RETRIES,
            "model": OLLAMA_MODEL,
            "ollama_url": OLLAMA_URL,
            "read_timeout": OLLAMA_READ_TIMEOUT,
            "connect_timeout": OLLAMA_CONNECT_TIMEOUT
        }
    )


async def check_ollama_health() -> Dict[str, Any]:
    """
    Check if Ollama is available and the model is loaded.

    Returns:
        {"ok": True/False, "model": str, "status": str}
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")

            if resp.status_code != 200:
                return {
                    "ok": False,
                    "status": f"HTTP {resp.status_code}",
                    "model": OLLAMA_MODEL
                }

            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]

            # Check if our model is available
            model_available = any(OLLAMA_MODEL in m for m in models)

            return {
                "ok": model_available,
                "status": "model_ready" if model_available else "model_not_found",
                "model": OLLAMA_MODEL,
                "available_models": models
            }

    except Exception as e:
        return {
            "ok": False,
            "status": f"connection_error: {str(e)}",
            "model": OLLAMA_MODEL
        }
