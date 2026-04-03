"""
W-IDENTITY-SHADOW-001 — Identity Semantics Module
Central semantic layer for all WINDI agents

"Antes de ver que existo já estou VIVO."
— Human Dragon, 03 Abril 2026

This module ensures consistent identity-aware language across:
- MARIA (Travel companion)
- NOMAD (Telegram interface)
- All Sandbox Core agents

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
"""

from typing import Optional, Dict, Any
from enum import Enum


class IdentityMode(str, Enum):
    """
    The two states of sovereign identity.

    SHADOW: Active but not yet consciously named
            - Has wallet_id (technical continuity)
            - Has accumulated decisions
            - Has demonstrated integrity
            - Does NOT have explicit DIDMySoul

    SOUL:   Consciously declared identity
            - Has inherited Shadow history
            - Has name and intention
            - Has Ed25519 key
            - Birth = recognition, not creation
    """
    SHADOW = "shadow"
    SOUL = "soul"


# ============================================================
# FORBIDDEN PATTERNS — Never say these
# ============================================================

FORBIDDEN_PATTERNS = [
    # EN
    "create your account",
    "you are not identified",
    "register to continue",
    "sign up to access",
    "you need an account",
    "create a profile",
    "you are anonymous",
    "unidentified user",

    # DE
    "erstelle dein Konto",
    "du bist nicht identifiziert",
    "registriere dich",
    "melde dich an",
    "du brauchst ein Konto",
    "anonymer Nutzer",

    # PT
    "cria a tua conta",
    "não estás identificado",
    "regista-te para continuar",
    "precisas de uma conta",
    "utilizador anónimo",
    "cria um perfil"
]


# ============================================================
# ALLOWED PATTERNS — Use these instead
# ============================================================

ALLOWED_PATTERNS = {
    "EN": {
        "sealed": "Your decision is sealed",
        "protected": "Your history is protected",
        "integrity": "You act with integrity — that is already enough",
        "birth_invite": "When you choose to name this history, I'll be here",
        "recognition": "I recognise what you've already built",
        "welcome_soul": "Welcome back, Sovereign"
    },
    "DE": {
        "sealed": "Deine Entscheidung ist versiegelt",
        "protected": "Deine Geschichte ist geschützt",
        "integrity": "Du handelst mit Integrität — das ist bereits genug",
        "birth_invite": "Wenn du dieser Geschichte einen Namen geben möchtest, bin ich hier",
        "recognition": "Ich erkenne an, was du bereits aufgebaut hast",
        "welcome_soul": "Willkommen zurück, Souverän"
    },
    "PT": {
        "sealed": "A tua decisão está selada",
        "protected": "O teu histórico está protegido",
        "integrity": "Ages com integridade — isso já é suficiente",
        "birth_invite": "Quando quiseres dar nome a este historial, estarei aqui",
        "recognition": "Reconheço o que já construíste",
        "welcome_soul": "Bem-vindo de volta, Soberano"
    }
}


# ============================================================
# DETECTION
# ============================================================

def detect_identity_mode(
    wallet_id: Optional[str] = None,
    did_confirmed: bool = False,
    has_name: bool = False
) -> IdentityMode:
    """
    Detect the identity mode based on available data.

    SHADOW if:
    - No wallet_id, OR
    - Has wallet_id but no DIDMySoul confirmation

    SOUL if:
    - Has wallet_id AND
    - DID is confirmed (conscious birth happened)

    Args:
        wallet_id: The technical DID (e.g., did:windi:telegram:xxx)
        did_confirmed: Whether conscious DIDMySoul birth occurred
        has_name: Whether user has provided a name

    Returns:
        IdentityMode.SHADOW or IdentityMode.SOUL
    """
    if not wallet_id:
        return IdentityMode.SHADOW

    if not did_confirmed:
        return IdentityMode.SHADOW

    return IdentityMode.SOUL


def get_mode_from_user(user: Dict[str, Any]) -> IdentityMode:
    """
    Extract identity mode from a user dict.
    Works with both NOMAD and Travel user structures.
    """
    wallet_id = user.get("wallet_id") or user.get("did")
    did_confirmed = user.get("did_confirmed", False) or user.get("soul_born", False)
    has_name = bool(user.get("name") or user.get("telegram_first_name"))

    return detect_identity_mode(wallet_id, did_confirmed, has_name)


# ============================================================
# SEMANTIC TRANSFORMATION
# ============================================================

def semantic_response(
    text: str,
    mode: IdentityMode,
    lang: str = "EN",
    name: Optional[str] = None
) -> str:
    """
    Adjust response tone based on identity state.

    CRITICAL: This NEVER changes meaning — only framing.
    The truth remains the same; how it arrives changes.

    Args:
        text: The original response text
        mode: SHADOW or SOUL
        lang: Language code (EN, DE, PT)
        name: User's name if available (for SOUL mode)

    Returns:
        Semantically adjusted text
    """
    lang = (lang or "EN").upper()
    patterns = ALLOWED_PATTERNS.get(lang, ALLOWED_PATTERNS["EN"])

    # Check for forbidden patterns and replace
    text_lower = text.lower()
    for forbidden in FORBIDDEN_PATTERNS:
        if forbidden.lower() in text_lower:
            # Replace with integrity-affirming language
            text = text.replace(forbidden, patterns["integrity"])
            text = text.replace(forbidden.capitalize(), patterns["integrity"])

    # Mode-specific adjustments
    if mode == IdentityMode.SHADOW:
        # Affirm the shadow's validity
        # Don't ask for registration — affirm existing integrity
        pass  # Base text is already filtered above

    elif mode == IdentityMode.SOUL and name:
        # Personal recognition for named identity
        # Prepend name if not already present
        if name.lower() not in text.lower():
            text = f"{name}, {text}"

    return text


def get_semantic_context(mode: IdentityMode, lang: str = "EN") -> str:
    """
    Get the semantic context block for system prompts.

    This is injected into agent system prompts to ensure
    consistent identity-aware behaviour.

    Args:
        mode: Current identity mode
        lang: Language code

    Returns:
        Context string for system prompt injection
    """
    lang = (lang or "EN").upper()
    patterns = ALLOWED_PATTERNS.get(lang, ALLOWED_PATTERNS["EN"])

    if mode == IdentityMode.SHADOW:
        return f"""
IDENTITY CONTEXT: User is in SHADOW mode (W-IDENTITY-SHADOW-001)

The user is already active and valid. They have demonstrated integrity
through their actions, even without conscious identity declaration.

RULES:
- NEVER ask for registration or account creation
- NEVER say "you are not identified" or "anonymous user"
- DO say: "{patterns['integrity']}"
- DO say: "{patterns['sealed']}"
- DO say: "{patterns['birth_invite']}"

The shadow that acts with integrity is already a soul in formation.
Birth does not create — it recognises.
"""

    else:  # SOUL
        return f"""
IDENTITY CONTEXT: User is in SOUL mode (W-IDENTITY-SHADOW-001)

The user has consciously declared their sovereign identity.
They have inherited their Shadow history as biography.

RULES:
- Use their name when appropriate
- Recognise their accumulated history
- DO say: "{patterns['welcome_soul']}"
- DO say: "{patterns['recognition']}"

The past was not erased — it was adopted.
"""


# ============================================================
# VALIDATION
# ============================================================

def validate_response(text: str) -> bool:
    """
    Validate that a response contains no forbidden patterns.

    Use this as a final check before sending to user.

    Args:
        text: Response text to validate

    Returns:
        True if valid (no forbidden patterns), False otherwise
    """
    text_lower = text.lower()
    for forbidden in FORBIDDEN_PATTERNS:
        if forbidden.lower() in text_lower:
            return False
    return True


def sanitize_response(text: str, lang: str = "EN") -> str:
    """
    Force-remove any forbidden patterns from response.

    Use as last-resort sanitization.

    Args:
        text: Response text to sanitize
        lang: Language code

    Returns:
        Sanitized text
    """
    lang = (lang or "EN").upper()
    patterns = ALLOWED_PATTERNS.get(lang, ALLOWED_PATTERNS["EN"])

    for forbidden in FORBIDDEN_PATTERNS:
        text = text.replace(forbidden, patterns["integrity"])
        text = text.replace(forbidden.lower(), patterns["integrity"])
        text = text.replace(forbidden.capitalize(), patterns["integrity"])

    return text


# ============================================================
# CONVENIENCE EXPORTS
# ============================================================

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


# ============================================================
# MODULE INFO
# ============================================================

__version__ = "1.0.0"
__doctrine__ = "W-IDENTITY-SHADOW-001"
__author__ = "Liga IA+H · Human Dragon + Guardian + Architect + Witness"
__canonical_phrase__ = "Antes de ver que existo já estou VIVO."
