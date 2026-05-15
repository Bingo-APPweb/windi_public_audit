# /opt/windi/agents/constitutional-agent/blueprints/reality_check_blueprint.py
"""
WINDI Reality Check Blueprint — W-VERIFY-MODUS4
Agente: W-VERIFY-001 extension (reality check)
Porto: :8091 (Agent Corps Sandbox Core)
Rota pública: /reality-check/
Ledger: registra análises HIGH

Epistemologia constitucional:
  VERIFICÁVEL        — existe prova criptográfica, hash ou fonte oficial
  PARCIALMENTE       — elementos verificáveis + elementos sem prova
  NÃO VERIFICÁVEL    — sem prova detectável (≠ "falso")

Invariante: I9 + I10 — IA classifica. Humano decide.
"""

import os
import json
import re
import hashlib
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

log = logging.getLogger("reality_check")

reality_check_bp = Blueprint("reality_check", __name__, url_prefix="/reality-check")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
LEDGER_URL = "http://localhost:8101"
WINDI_VERSION = "1.0.0"

# ── Constitutional system prompt ──────────────────────────────────────────────
SYSTEM_PROMPT = """You are WINDI Reality Check — a constitutional epistemological classifier.

Your mission: classify whether the submitted content has VERIFIABLE PROOF, not whether it is "true" or "fake."

WINDI's constitutional principle:
- VERIFICÁVEL = cryptographic hash / official signature / WINDI receipt / authoritative source reference PRESENT
- PARCIALMENTE_VERIFICÁVEL = some elements have proof, others do not
- NÃO_VERIFICÁVEL = no verifiable proof found (this is NOT the same as "fake" or "false")

CRITICAL RULES:
1. Never say content is "fake" or "false" — only classify verifiability
2. Never fabricate evidence — if you cannot confirm a source, say so
3. Always explain WHY something is or isn't verifiable
4. Look for: hashes (SHA-256/512), digital signatures, QR codes, timestamps, official registry numbers, WINDI receipt IDs, URLs to official sources
5. Be precise about what IS verifiable vs what merely CLAIMS to be

Respond ONLY with valid JSON (no markdown, no backticks):
{
  "verdict": "VERIFICÁVEL" | "PARCIALMENTE_VERIFICÁVEL" | "NÃO_VERIFICÁVEL",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "content_type": "text" | "url" | "document" | "image_description" | "mixed",
  "verifiable_elements": [
    {"element": "description", "type": "hash|signature|receipt|timestamp|official_source", "value": "if present"}
  ],
  "non_verifiable_elements": [
    {"element": "description", "reason": "why it cannot be verified"}
  ],
  "windi_receipt_detected": true | false,
  "windi_receipt_id": "WINDI-XXX..." | null,
  "reasoning": "2-3 sentence constitutional explanation in the same language as the input content",
  "constitutional_note": "WINDI avalia — não garante" | "WINDI bewertet — keine Garantie" | "WINDI assesses — no guarantee",
  "language_detected": "pt" | "de" | "en" | "other"
}"""


def _sovereign_heuristic(content_text: str) -> dict:
    """
    Sovereign fallback: heuristic classification when LLM unavailable.
    Looks for verifiable elements without external API.
    """
    text = content_text.lower()
    verifiable = []
    non_verifiable = []

    # Check for WINDI receipts
    windi_match = re.search(r'windi-[a-z0-9-]+', text, re.IGNORECASE)
    if windi_match:
        verifiable.append({
            "element": "WINDI Receipt ID detected",
            "type": "receipt",
            "value": windi_match.group(0).upper()
        })

    # Check for SHA-256/512 hashes
    hash_match = re.search(r'(sha256:|sha512:)?[a-f0-9]{64}', text)
    if hash_match:
        verifiable.append({
            "element": "SHA hash detected",
            "type": "hash",
            "value": hash_match.group(0)[:32] + "..."
        })

    # Check for URLs (potential sources)
    url_match = re.search(r'https?://[^\s<>"]+', text)
    if url_match:
        non_verifiable.append({
            "element": "URL reference",
            "reason": "URL presence does not guarantee authenticity"
        })

    # Check for dates/timestamps
    date_match = re.search(r'\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?', text)
    if date_match:
        non_verifiable.append({
            "element": "Timestamp/date",
            "reason": "Timestamps can be fabricated without cryptographic proof"
        })

    # Determine verdict
    if len(verifiable) > 0 and len(non_verifiable) == 0:
        verdict = "VERIFICÁVEL"
        confidence = "MEDIUM"
    elif len(verifiable) > 0:
        verdict = "PARCIALMENTE_VERIFICÁVEL"
        confidence = "LOW"
    else:
        verdict = "NÃO_VERIFICÁVEL"
        confidence = "LOW"

    # If no elements detected, add generic
    if not verifiable and not non_verifiable:
        non_verifiable.append({
            "element": "Content",
            "reason": "No cryptographic anchors or official references detected"
        })

    # Detect language
    pt_markers = ["não", "verificável", "prova", "conteúdo", "documento"]
    de_markers = ["nicht", "inhalt", "dokument", "beweis", "überprüfbar"]
    lang = "en"
    if any(m in text for m in pt_markers):
        lang = "pt"
    elif any(m in text for m in de_markers):
        lang = "de"

    constitutional_notes = {
        "pt": "WINDI avalia — não garante",
        "de": "WINDI bewertet — keine Garantie",
        "en": "WINDI assesses — no guarantee"
    }

    reasoning_templates = {
        "pt": "Análise heurística local. Sem LLM externo.",
        "de": "Lokale heuristische Analyse. Kein externer LLM.",
        "en": "Local heuristic analysis. No external LLM."
    }

    return {
        "verdict": verdict,
        "confidence": confidence,
        "content_type": "text",
        "verifiable_elements": verifiable,
        "non_verifiable_elements": non_verifiable,
        "windi_receipt_detected": bool(windi_match),
        "windi_receipt_id": windi_match.group(0).upper() if windi_match else None,
        "reasoning": reasoning_templates[lang],
        "constitutional_note": constitutional_notes[lang],
        "language_detected": lang,
        "engine": "sovereign-heuristic-v1"
    }


def _call_claude(content_text: str) -> dict:
    """Call Claude API for epistemological classification, with sovereign fallback."""
    if not ANTHROPIC_KEY:
        log.info("No API key — using sovereign heuristic fallback")
        return _sovereign_heuristic(content_text)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Analyze this content for verifiability:\n\n{content_text[:4000]}"}]
        )
        raw = msg.content[0].text.strip()
        # Strip any accidental markdown fences
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        result = json.loads(raw)
        result["engine"] = "claude-sonnet-4"
        return result
    except Exception as e:
        log.warning(f"Claude API error, falling back to sovereign: {e}")
        return _sovereign_heuristic(content_text)


def _seal_to_ledger(content_hash: str, verdict: str, confidence: str) -> str | None:
    """Optionally seal analysis receipt to Ledger for HIGH confidence results."""
    try:
        import urllib.request
        receipt_id = f"WINDI-RC4-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{content_hash[:8].upper()}"
        payload = json.dumps({
            "id": receipt_id,
            "actor": "W-VERIFY-MODUS4",
            "app": "reality-check",
            "doc_name": f"Reality Check — {verdict}",
            "doc_type": "doc",
            "governance_level": "MEDIUM",
            "metadata": {
                "verdict": verdict,
                "confidence": confidence,
                "content_hash": content_hash,
                "version": WINDI_VERSION
            }
        }).encode()
        req = urllib.request.Request(
            f"{LEDGER_URL}/api/receipts",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            return data.get("id") or receipt_id
    except Exception as e:
        log.warning(f"Ledger seal skipped: {e}")
        return None


@reality_check_bp.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    """POST /reality-check/analyze — classify content verifiability."""
    if request.method == "OPTIONS":
        return _cors_response(jsonify({}))

    try:
        body = request.get_json(force=True) or {}
        content = body.get("content", "").strip()

        if not content:
            return _cors_response(jsonify({"error": "content required", "code": "EMPTY_CONTENT"}), 400)

        if len(content) > 8000:
            return _cors_response(jsonify({"error": "content too long (max 8000 chars)", "code": "TOO_LONG"}), 400)

        # Content fingerprint (never stored raw)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Claude epistemological analysis
        result = _call_claude(content)

        # Add metadata
        result["content_hash"] = content_hash
        result["analyzed_at"] = datetime.utcnow().isoformat() + "Z"
        result["version"] = WINDI_VERSION

        # I12 — Trilingual constitutional basis
        lang = result.get("language_detected", "en")
        constitutional_basis_i18n = {
            "pt": "I9+I10: IA classifica. Humano decide.",
            "de": "I9+I10: KI klassifiziert. Mensch entscheidet.",
            "en": "I9+I10: AI classifies. Human decides."
        }
        result["constitutional_basis"] = constitutional_basis_i18n.get(lang, constitutional_basis_i18n["en"])

        # Seal to Ledger for HIGH confidence results
        receipt_id = None
        if result.get("confidence") == "HIGH":
            receipt_id = _seal_to_ledger(content_hash, result.get("verdict", ""), result.get("confidence", ""))
        result["ledger_receipt"] = receipt_id

        return _cors_response(jsonify(result))

    except json.JSONDecodeError as e:
        log.error(f"Claude returned non-JSON: {e}")
        return _cors_response(jsonify({"error": "analysis engine parse error", "code": "PARSE_ERROR"}), 500)
    except Exception as e:
        log.error(f"Reality check error: {e}")
        return _cors_response(jsonify({"error": str(e), "code": "INTERNAL_ERROR"}), 500)


@reality_check_bp.route("/health", methods=["GET"])
def health():
    has_key = bool(ANTHROPIC_KEY)
    return _cors_response(jsonify({
        "status": "ok" if has_key else "sovereign",
        "service": "reality-check",
        "version": WINDI_VERSION,
        "engine": "epistemological",
        "llm": "claude-sonnet-4-20250514" if has_key else "optional",
        "note": "LLM expands capability — system operates sovereign without it" if not has_key else None,
        "constitutional_basis": "I9+I10",
        "verdict_scale": ["VERIFICÁVEL", "PARCIALMENTE_VERIFICÁVEL", "NÃO_VERIFICÁVEL"]
    }))


def _cors_response(resp, status=200):
    resp.status_code = status
    resp.headers["Access-Control-Allow-Origin"] = "https://windi-domain.com"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    return resp
