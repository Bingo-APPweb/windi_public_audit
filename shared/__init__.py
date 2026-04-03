"""
WINDI Shared Modules
Central utilities for all WINDI services

Liga IA+H · Kempten, Bavaria · 2026
"""

from .identity_semantics import (
    IdentityMode,
    detect_identity_mode,
    get_mode_from_user,
    semantic_response,
    get_semantic_context,
    validate_response,
    sanitize_response,
    FORBIDDEN_PATTERNS,
    ALLOWED_PATTERNS
)

__all__ = [
    "IdentityMode",
    "detect_identity_mode",
    "get_mode_from_user",
    "semantic_response",
    "get_semantic_context",
    "validate_response",
    "sanitize_response",
    "FORBIDDEN_PATTERNS",
    "ALLOWED_PATTERNS"
]
