"""
AI Writer Package — §3b W-SITES-001
====================================

Internal-Only Mode Content Generation with:
- 4-layer DID Gate
- 8-step pipeline
- PoE-structured templates
- Galho B (Ollama mistral:7b) backend

Environment Variables:
  - AI_WRITER_MODE: "internal" (required for operation)
  - OLLAMA_URL: Galho B endpoint (default: http://85.215.131.0:11434)
  - OLLAMA_WRITER_MODEL: Model to use (default: mistral:7b)
  - OLLAMA_WRITER_TIMEOUT: Generation timeout (default: 30.0)
  - OLLAMA_WRITER_TEMP: Temperature (default: 0.4)
  - OLLAMA_WRITER_MAX_TOKENS: Max tokens (default: 1500)

Liga IA+H · Kempten, Bavaria · 2026
"""

from .ai_writer_runtime import (
    generate_with_pipeline,
    assert_internal_writer_authorized,
    InternalModeViolation,
    GenerationResult,
    writer_health,
    load_template,
    build_prompt,
    VALID_TEMPLATES,
    AI_WRITER_MODE,
    INTERNAL_DIDS_ALLOWLIST
)

from .ollama_writer_client import (
    generate_content,
    check_ollama_health,
    OllamaWriterError
)

__all__ = [
    # Runtime
    "generate_with_pipeline",
    "assert_internal_writer_authorized",
    "InternalModeViolation",
    "GenerationResult",
    "writer_health",
    "load_template",
    "build_prompt",
    "VALID_TEMPLATES",
    "AI_WRITER_MODE",
    "INTERNAL_DIDS_ALLOWLIST",
    # Client
    "generate_content",
    "check_ollama_health",
    "OllamaWriterError",
]

__version__ = "0.1.0"
