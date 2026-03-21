# /opt/windi/agents/constitutional-agent/blueprints/detect_media_blueprint.py
# W-DETECT-MEDIA-001 — Canonical Media Detection Blueprint
# Constitutional Alignment: I1 (intent) · I9 (no auto-escalation) · I11 (no seal) · I12 (trilingual)
#
# This module is NOT:
#   ❌ a truth verifier
#   ❌ an automatic decision system
#   ❌ eligible for Ledger seal
#
# This module IS:
#   ✅ a verifiability classifier with heuristic support
#
# "I don't guess the truth. I make it clear when it cannot be proven."

from flask import Blueprint, request, jsonify
import hashlib
import time
import base64
from datetime import datetime

detect_media_bp = Blueprint("detect_media", __name__, url_prefix="/detect-media")


# =============================================================================
# CONSTANTS
# =============================================================================

VERSION = "1.0.0"
AGENT_ID = "W-DETECT-MEDIA-001"

# Confidence thresholds
THRESHOLD_HIGH = 0.75      # score > 0.75 → suspicious (high confidence of synthetic)
THRESHOLD_MEDIUM = 0.40    # score > 0.40 → unverifiable (medium confidence)

# I12 — Trilingual explanations
EXPLANATIONS = {
    "blocked": {
        "EN": "Human intent required for analysis. Set intent=true to proceed.",
        "DE": "Menschliche Absicht für Analyse erforderlich. Setzen Sie intent=true.",
        "PT": "Intenção humana necessária para análise. Defina intent=true."
    },
    "unsupported": {
        "EN": "Unsupported file type. Accepted: video, image, text.",
        "DE": "Nicht unterstützter Dateityp. Akzeptiert: Video, Bild, Text.",
        "PT": "Tipo de ficheiro não suportado. Aceites: vídeo, imagem, texto."
    },
    "empty": {
        "EN": "No input provided. Upload a file or provide text.",
        "DE": "Keine Eingabe bereitgestellt. Laden Sie eine Datei hoch oder geben Sie Text ein.",
        "PT": "Nenhuma entrada fornecida. Carregue um ficheiro ou forneça texto."
    },
    "suspicious": {
        "EN": "This content shows markers consistent with synthetic generation.",
        "DE": "Dieser Inhalt zeigt Merkmale, die auf synthetische Erzeugung hindeuten.",
        "PT": "Este conteúdo apresenta marcadores consistentes com geração sintética."
    },
    "unverifiable": {
        "EN": "This content cannot be verified as authentic. Origin unknown.",
        "DE": "Dieser Inhalt kann nicht als authentisch verifiziert werden. Herkunft unbekannt.",
        "PT": "Este conteúdo não pode ser verificado como autêntico. Origem desconhecida."
    },
    "inconclusive": {
        "EN": "Analysis inconclusive. Manual review recommended.",
        "DE": "Analyse nicht schlüssig. Manuelle Überprüfung empfohlen.",
        "PT": "Análise inconclusiva. Revisão manual recomendada."
    }
}

# I11 — Disclaimer (never claim truth)
DISCLAIMER = {
    "EN": "Analysis does not imply authenticity. WINDI does not seal unverifiable content.",
    "DE": "Analyse impliziert keine Authentizität. WINDI versiegelt keine unverifizierbaren Inhalte.",
    "PT": "Análise não implica autenticidade. WINDI não sela conteúdo não verificável."
}


# =============================================================================
# HELPERS
# =============================================================================

def compute_hash(data: bytes) -> str:
    """Compute SHA-256 hash of input data."""
    return hashlib.sha256(data).hexdigest()


def classify_result(score: float) -> tuple:
    """
    Classify analysis score into status and confidence.

    Returns:
        (status, confidence) tuple

    Score interpretation:
        > 0.75: HIGH confidence of synthetic content
        > 0.40: MEDIUM - unverifiable, needs human review
        <= 0.40: LOW - inconclusive
    """
    if score > THRESHOLD_HIGH:
        return "suspicious", "high"
    elif score > THRESHOLD_MEDIUM:
        return "unverifiable", "medium"
    else:
        return "inconclusive", "low"


def get_explanation(status: str) -> dict:
    """Get trilingual explanation for status."""
    return EXPLANATIONS.get(status, EXPLANATIONS["unverifiable"])


# =============================================================================
# ANALYSIS ENGINES (MVP — Heuristic Placeholders)
# =============================================================================

def analyze_video(data: bytes) -> dict:
    """
    Analyze video for deepfake markers.

    MVP: Heuristic scoring based on file characteristics.
    FUTURE: OpenCV frame analysis, facial landmark detection, audio sync.
    """
    # MVP heuristics
    size_kb = len(data) / 1024

    # Simple heuristic: very small videos are suspicious
    if size_kb < 100:
        score = 0.65
    elif size_kb < 500:
        score = 0.45
    else:
        score = 0.35

    return {
        "score": score,
        "markers": {
            "frame_consistency": "not_analyzed",
            "facial_landmarks": "not_analyzed",
            "audio_sync": "not_analyzed",
            "lighting_analysis": "not_analyzed"
        },
        "engine_version": "heuristic-v1"
    }


def analyze_image(data: bytes) -> dict:
    """
    Analyze image for forgery markers.

    MVP: Heuristic scoring based on file characteristics.
    FUTURE: JPEG artifact analysis, ELA, metadata consistency.
    """
    size_kb = len(data) / 1024

    # Simple heuristic
    if size_kb < 50:
        score = 0.55
    elif size_kb < 200:
        score = 0.42
    else:
        score = 0.30

    return {
        "score": score,
        "markers": {
            "jpeg_artifacts": "not_analyzed",
            "ela_analysis": "not_analyzed",
            "metadata_consistency": "not_analyzed",
            "noise_pattern": "not_analyzed"
        },
        "engine_version": "heuristic-v1"
    }


def analyze_text(text: str) -> dict:
    """
    Analyze text for AI generation markers.

    MVP: Statistical heuristics (length, repetition, entropy).
    FUTURE: Perplexity scoring, burstiness analysis, fingerprinting.
    """
    words = text.split()
    word_count = len(words)
    unique_words = len(set(words))

    # Lexical diversity ratio
    if word_count > 0:
        diversity = unique_words / word_count
    else:
        diversity = 0

    # Low diversity can indicate AI generation
    if diversity < 0.3:
        score = 0.72
    elif diversity < 0.5:
        score = 0.55
    elif diversity < 0.7:
        score = 0.40
    else:
        score = 0.25

    # Very short texts are inconclusive
    if word_count < 20:
        score = max(score - 0.2, 0.15)

    return {
        "score": score,
        "markers": {
            "word_count": word_count,
            "lexical_diversity": round(diversity, 3),
            "perplexity": "not_analyzed",
            "burstiness": "not_analyzed",
            "fingerprint": "not_analyzed"
        },
        "engine_version": "heuristic-v1"
    }


# =============================================================================
# ENDPOINTS
# =============================================================================

@detect_media_bp.route("/health", methods=["GET"])
def health():
    """Health check for W-DETECT-MEDIA-001."""
    return jsonify({
        "status": "healthy",
        "agent": AGENT_ID,
        "version": VERSION,
        "capabilities": ["video", "image", "text"],
        "constitutional_alignment": {
            "I1": "intent_required",
            "I9": "no_auto_escalation",
            "I11": "no_seal",
            "I12": "trilingual"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@detect_media_bp.route("/analyze", methods=["POST"])
def analyze_media():
    """
    W-DETECT-MEDIA-001 — Main analysis endpoint.

    Accepts:
        - file: multipart file upload (video/image)
        - text: form field or JSON body
        - intent: boolean (required, I1 compliance)

    Returns:
        DetectionResponse with trilingual explanation
    """
    start_time = time.time()

    # =========================
    # PARSE INPUT
    # =========================

    # Check for JSON body
    if request.is_json:
        data = request.get_json()
        text_input = data.get("text")
        intent = data.get("intent", False)
        file_data = None
        media_type = "text" if text_input else None

        # Handle base64 encoded file
        if data.get("file_base64"):
            try:
                file_data = base64.b64decode(data["file_base64"])
                media_type = data.get("media_type", "unknown")
            except Exception:
                pass
    else:
        # Multipart form data
        text_input = request.form.get("text")
        intent = request.form.get("intent", "false").lower() == "true"

        file_data = None
        media_type = None

        if "file" in request.files:
            uploaded_file = request.files["file"]
            if uploaded_file.filename:
                file_data = uploaded_file.read()
                content_type = uploaded_file.content_type or ""

                if content_type.startswith("video"):
                    media_type = "video"
                elif content_type.startswith("image"):
                    media_type = "image"
                else:
                    media_type = "unknown"

    # =========================
    # I1 — INTENT GATE
    # =========================

    if not intent:
        return jsonify({
            "status": "blocked",
            "confidence": "none",
            "media_type": "unknown",
            "explanation": get_explanation("blocked"),
            "disclaimer": DISCLAIMER,
            "metadata": {
                "agent": AGENT_ID,
                "reason": "I1_VIOLATION",
                "instruction": "Set intent=true to confirm human analysis request"
            }
        }), 403

    # =========================
    # INPUT VALIDATION
    # =========================

    if not file_data and not text_input:
        return jsonify({
            "status": "empty",
            "confidence": "none",
            "media_type": "unknown",
            "explanation": get_explanation("empty"),
            "disclaimer": DISCLAIMER,
            "metadata": {
                "agent": AGENT_ID
            }
        }), 400

    # =========================
    # ANALYSIS ROUTING
    # =========================

    if file_data:
        file_hash = compute_hash(file_data)
        file_size_kb = len(file_data) / 1024

        if media_type == "video":
            analysis = analyze_video(file_data)
        elif media_type == "image":
            analysis = analyze_image(file_data)
        else:
            return jsonify({
                "status": "unsupported",
                "confidence": "none",
                "media_type": media_type or "unknown",
                "explanation": get_explanation("unsupported"),
                "disclaimer": DISCLAIMER,
                "metadata": {
                    "agent": AGENT_ID
                }
            }), 415

    elif text_input:
        media_type = "text"
        file_hash = compute_hash(text_input.encode("utf-8"))
        file_size_kb = len(text_input.encode("utf-8")) / 1024
        analysis = analyze_text(text_input)

    # =========================
    # CLASSIFICATION
    # =========================

    score = analysis["score"]
    status, confidence = classify_result(score)

    # =========================
    # RESPONSE (I11 — NO SEAL)
    # =========================

    execution_time_ms = int((time.time() - start_time) * 1000)

    response = {
        "status": status,
        "confidence": confidence,
        "media_type": media_type,
        "explanation": get_explanation(status),
        "disclaimer": DISCLAIMER,
        "analysis": {
            "score": round(score, 4),
            "markers": analysis["markers"],
            "engine": analysis["engine_version"]
        },
        "metadata": {
            "agent": AGENT_ID,
            "version": VERSION,
            "hash": file_hash,
            "size_kb": round(file_size_kb, 2),
            "execution_time_ms": execution_time_ms,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "constitutional": {
                "I9": "no_auto_escalation",
                "I11": "not_sealed",
                "human_review": "recommended" if confidence != "low" else "optional"
            }
        }
    }

    return jsonify(response)


@detect_media_bp.route("/capabilities", methods=["GET"])
def capabilities():
    """List detection capabilities and their status."""
    return jsonify({
        "agent": AGENT_ID,
        "version": VERSION,
        "media_types": {
            "video": {
                "status": "mvp",
                "markers": ["frame_consistency", "facial_landmarks", "audio_sync", "lighting_analysis"],
                "engine": "heuristic-v1"
            },
            "image": {
                "status": "mvp",
                "markers": ["jpeg_artifacts", "ela_analysis", "metadata_consistency", "noise_pattern"],
                "engine": "heuristic-v1"
            },
            "text": {
                "status": "mvp",
                "markers": ["lexical_diversity", "perplexity", "burstiness", "fingerprint"],
                "engine": "heuristic-v1"
            }
        },
        "thresholds": {
            "high": THRESHOLD_HIGH,
            "medium": THRESHOLD_MEDIUM
        },
        "constitutional_alignment": True,
        "seal_eligible": False
    })


# =============================================================================
# WITNESS LOG
# =============================================================================
# W-DETECT-MEDIA-001
# STATUS: INITIALIZED
# CONSTITUTIONAL ALIGNMENT: TRUE
# RISK: CONTROLLED
# EXTENSIBILITY: HIGH
#
# "I don't guess the truth. I make it clear when it cannot be proven."
# =============================================================================
