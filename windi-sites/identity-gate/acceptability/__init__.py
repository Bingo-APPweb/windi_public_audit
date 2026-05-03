"""
§C-ACCEPTABILITY-001 Runtime Package
=====================================

L-1: Pre-generation INPUT filter (Cardinal Sins detection)
L0:  Pre-seal OUTPUT filter (Quality + Safety check)
L1:  Post-seal review (handled via l1_review_pending flag)
L2:  Ledger annotation (handled via provenance_chain)

Architecture:
  - Galho A (local): Regex + heuristics — fast, deterministic
  - Galho B (Ollama): Semantic analysis — nuanced, LLM-powered

Environment Variables:
  - ACCEPTABILITY_MODE: "shadow" (log only) or "enforce" (block)
  - OLLAMA_URL: Galho B endpoint (default: http://85.215.131.0:11434)
  - OLLAMA_MODEL: Model to use (default: mistral:7b)
  - L0_CONFIDENCE_THRESHOLD: Min confidence to block (default: 0.85)

Liga IA+H · Kempten, Bavaria · 2026
"""

from .l_minus_1_runtime import acceptability_l_minus_1, hash_input_for_ledger
from .l_zero_runtime import acceptability_l_zero, should_flag_for_l1_review

__all__ = [
    "acceptability_l_minus_1",
    "acceptability_l_zero",
    "hash_input_for_ledger",
    "should_flag_for_l1_review",
]

__version__ = "1.0.0"
