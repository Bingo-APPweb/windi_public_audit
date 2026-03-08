"""
WINDI Guardian — Language Detection v1.0.0
==========================================
Lightweight language detection using character patterns and word frequency.
No external dependencies (fastText can be added later for higher accuracy).

Supports: pt, de, en, fr, ar, es
Fallback: en
"""

import re
from typing import Tuple
from collections import Counter

# ─── Language Signatures ─────────────────────────────────────────────────────
# Common short words and unique character patterns per language

LANG_SIGNATURES = {
    "pt": {
        "words": {
            "o", "a", "os", "as", "de", "do", "da", "dos", "das", "em", "no", "na",
            "um", "uma", "para", "por", "com", "como", "que", "não", "se", "mais",
            "mas", "ou", "eu", "tu", "ele", "ela", "nós", "meu", "minha", "seu",
            "sua", "este", "esta", "isso", "tudo", "bem", "sim", "aqui", "quero",
            "posso", "preciso", "criar", "fazer", "olá", "obrigado", "obrigada",
            "bom", "dia", "boa", "tarde", "noite", "tchau", "muito", "também",
        },
        "char_patterns": [r"[ãõç]", r"nh", r"lh"],
        "boost": 0.0,
    },
    "de": {
        "words": {
            "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer",
            "und", "oder", "aber", "ich", "du", "er", "sie", "wir", "ihr",
            "ist", "sind", "war", "hat", "haben", "wird", "kann", "muss",
            "nicht", "auch", "noch", "nur", "schon", "sehr", "gut", "wie",
            "was", "wer", "wo", "hallo", "danke", "bitte", "ja", "nein",
            "mit", "von", "für", "auf", "aus", "bei", "nach", "über",
            "möchte", "brauche", "dokument", "brief",
        },
        "char_patterns": [r"[äöüß]", r"sch", r"ung\b", r"lich\b"],
        "boost": 0.0,
    },
    "en": {
        "words": {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "can", "could", "should", "may", "not", "no", "yes", "i",
            "you", "he", "she", "it", "we", "they", "my", "your", "his",
            "her", "this", "that", "what", "who", "how", "when", "where",
            "hello", "hi", "thank", "thanks", "please", "want", "need",
            "help", "create", "document", "letter",
        },
        "char_patterns": [r"th", r"ing\b", r"tion\b"],
        "boost": -0.05,  # slight penalty since en is fallback
    },
    "fr": {
        "words": {
            "le", "la", "les", "un", "une", "des", "de", "du", "au", "aux",
            "et", "ou", "mais", "donc", "car", "je", "tu", "il", "elle",
            "nous", "vous", "ils", "elles", "est", "sont", "suis", "a",
            "ont", "pas", "ne", "qui", "que", "quoi", "comment", "où",
            "bonjour", "merci", "oui", "non", "bien", "très", "avec",
            "pour", "dans", "sur", "par", "ce", "cette", "mon", "ma",
            "veux", "peux", "besoin", "créer", "lettre", "document",
        },
        "char_patterns": [r"[àâéèêëîïôùûç]", r"eau\b", r"eux\b", r"ment\b"],
        "boost": 0.0,
    },
    "ar": {
        "words": set(),  # Arabic detection relies on script
        "char_patterns": [r"[\u0600-\u06FF]"],  # Arabic Unicode block
        "boost": 0.3,  # strong boost for script match
    },
    "es": {
        "words": {
            "el", "la", "los", "las", "un", "una", "unos", "unas", "de",
            "del", "al", "en", "con", "por", "para", "y", "o", "pero",
            "que", "no", "si", "yo", "tú", "él", "ella", "nosotros",
            "es", "son", "está", "hola", "gracias", "sí", "también",
            "muy", "bien", "como", "qué", "quién", "cómo", "dónde",
            "quiero", "necesito", "crear", "documento", "carta",
        },
        "char_patterns": [r"[ñ¿¡]", r"ción\b", r"dad\b"],
        "boost": 0.0,
    },
}

# Words shared between PT and ES that shouldn't count for either
PT_ES_OVERLAP = {"de", "como", "um", "uma", "que", "para", "por", "com", "mais", "ou", "se", "no", "na"}


def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect language of text.
    
    Returns:
        (lang_code, confidence)  where lang_code in {pt, de, en, fr, ar, es}
    """
    text_lower = text.lower().strip()

    # ── Quick check: Arabic script ───────────────────────────────────
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
    if arabic_chars > len(text) * 0.3:
        return "ar", 0.95

    # ── Tokenize ─────────────────────────────────────────────────────
    words = set(re.findall(r"\b\w+\b", text_lower, re.UNICODE))

    if not words:
        return "en", 0.3  # fallback

    # ── Score each language ──────────────────────────────────────────
    scores = {}
    for lang, sig in LANG_SIGNATURES.items():
        if lang == "ar":
            # Already handled above
            scores[lang] = arabic_chars / max(len(text), 1)
            continue

        # Word overlap score
        matching = words & sig["words"]
        word_score = len(matching) / max(len(words), 1)

        # Character pattern score
        char_hits = 0
        for pattern in sig["char_patterns"]:
            if re.search(pattern, text_lower, re.UNICODE):
                char_hits += 1
        char_score = char_hits / max(len(sig["char_patterns"]), 1) * 0.3

        scores[lang] = word_score + char_score + sig["boost"]

    # ── Resolve PT vs ES ambiguity ───────────────────────────────────
    if abs(scores.get("pt", 0) - scores.get("es", 0)) < 0.1:
        # Check for distinguishing features
        if re.search(r"[ãõ]|nh|lh", text_lower):
            scores["pt"] += 0.2
        elif re.search(r"[ñ¿¡]", text_lower):
            scores["es"] += 0.2

    # ── Pick winner ──────────────────────────────────────────────────
    if not scores or max(scores.values()) < 0.05:
        return "en", 0.3

    best_lang = max(scores, key=scores.get)
    best_score = scores[best_lang]

    # Normalize confidence to 0-1
    confidence = min(best_score * 1.5, 0.99)
    confidence = max(confidence, 0.3)

    return best_lang, round(confidence, 2)


# ─── Quick Test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        "Olá, bom dia! Como estás?",
        "Hello, how are you?",
        "Hallo, wie geht es dir?",
        "Bonjour, comment allez-vous?",
        "مرحبا، كيف حالك؟",
        "¡Hola! ¿Cómo estás?",
        "Quero criar uma carta",
        "I want to create a letter",
        "Ich möchte einen Brief erstellen",
        "Je veux créer une lettre",
        "أريد إنشاء رسالة",
        "Quiero crear una carta",
        "Bom dia como vc se chama?",
        "O que esta dentro da tarifa free?",
    ]

    for t in tests:
        lang, conf = detect_language(t)
        print(f"  [{lang}] {conf:.2f} | {t}")
