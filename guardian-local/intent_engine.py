"""
WINDI Guardian — Intent Classification Engine v1.0.0
====================================================
Classifies user messages into 23 intents across 5 groups.
Uses regex patterns with confidence scoring.
No LLM required.

Groups:
  A = Social (greeting, farewell, thanks, identity, chitchat, want_to_talk)
  B = Navigation (what_is_windi, what_is_free, tiers, dragons, seal, help, privacy)
  C = Document creation (letter, memo, email, doc_generic, send_image)
  D = System operations (seal_document, verify_document, my_documents)
  E = Complex / requires LLM (creative_writing, deep_analysis, open_question)
"""

import re
from typing import Tuple, Dict, List

# ─── Intent Pattern Definitions ──────────────────────────────────────────────

INTENT_PATTERNS: Dict[str, dict] = {

    # ── GROUP A: Social ──────────────────────────────────────────────────────

    "greeting": {
        "group": "A",
        "patterns": [
            r"\b(ol[áa]|oi|hi|hello|hallo|bonjour|salut|ciao|hej)\b",
            r"\b(bom\s*dia|boa\s*(tarde|noite))\b",
            r"\b(guten\s*(morgen|tag|abend))\b",
            r"\b(good\s*(morning|afternoon|evening))\b",
            r"^(hey|hola|مرحبا|أهلاً|السلام)\b",
        ],
        "confidence": 0.95,
        "requires_llm": False,
    },

    "farewell": {
        "group": "A",
        "patterns": [
            r"\b(tchau|bye|adeus|tsch[üu]ss|goodbye|au\s*revoir|até\s*(logo|breve))\b",
            r"\b(see\s*you|bis\s*bald|à\s*bient[ôo]t|adiós|مع السلامة)\b",
        ],
        "confidence": 0.95,
        "requires_llm": False,
    },

    "thanks": {
        "group": "A",
        "patterns": [
            r"\b(obrigad[oa]|danke|thank(s|\s*you)|merci|valeu|gracias|شكرا)\b",
        ],
        "confidence": 0.95,
        "requires_llm": False,
    },

    "identity_ask": {
        "group": "A",
        "patterns": [
            r"(como|qual).*(teu\s*nome|te\s*chama|chamas|vc\s*se\s*chama|voc[êe]\s*se\s*chama)",
            r"(quem|what|who|wer)\s*.*(és|[ée]s\s*tu|are\s*you|bist\s*du)",
            r"(what.?s|what\s+is)\s+your\s+name",
            r"(wie|como)\s+(hei[ßs]|chama)",
            r"(quel|comment).*(nom|appel)",
            r"ما\s*اسمك|من\s*أنت",
            r"(se\s*chama|chamas|your\s*name|dein\s*name|ton\s*nom)",
        ],
        "confidence": 0.95,
        "requires_llm": False,
    },

    "chitchat": {
        "group": "A",
        "patterns": [
            r"(como\s*(est[áa]s|vai|vais)|tudo\s*bem|e\s*a[íi])",
            r"(how\s*are\s*you|how.?s\s*it\s*going|what.?s\s*up)",
            r"(wie\s*geht.?s|alles\s*gut|wie\s*l[äa]uft)",
            r"([çc]a\s*va|comment\s*vas|tu\s*vas\s*bien)",
            r"كيف\s*حالك",
        ],
        "confidence": 0.90,
        "requires_llm": False,
    },

    "want_to_talk": {
        "group": "A",
        "patterns": [
            r"(quero|vamos|gostava|posso)\s*(conversar|falar|bater\s*papo)",
            r"(let.?s|can\s*we|i\s*want\s*to)\s*(chat|talk|converse)",
            r"(lass\s*uns|ich\s*m[öo]chte)\s*(reden|plaudern|sprechen)",
            r"(on\s*peut|je\s*veux)\s*(parler|discuter|bavarder)",
        ],
        "confidence": 0.90,
        "requires_llm": False,
    },

    # ── GROUP B: Navigation & Information ─────────────────────────────────────

    "what_is_windi": {
        "group": "B",
        "patterns": [
            r"(o\s*que|what|was|qu.?est)\s*(é|is|ist).*(windi)",
            r"(explica|explain|erkl[äa]r|expliqu).*(windi)",
            r"(windi).*(o\s*que|what|was|que\s*fait)",
            r"(conta|tell|erz[äa]hl).*(sobre|about|[üu]ber).*(windi)",
        ],
        "confidence": 0.90,
        "requires_llm": False,
    },

    "what_is_free": {
        "group": "B",
        "patterns": [
            r"(tarifa|plano|tier|plan).*(free|gr[áa]ti|kostenlos|gratuit)",
            r"(free|gr[áa]ti|kostenlos|gratuit).*(tarifa|plano|tier|plan|inclui|include)",
            r"(o\s*que|what|was).*(posso|can|kann|puis).*(fazer|do|machen|faire)",
            r"(dentro|included|enthalten).*(free|gr[áa]ti)",
            r"(free|livre)\s*(inclui|tem|has|includes|enth[äa]lt)",
        ],
        "confidence": 0.90,
        "requires_llm": False,
    },

    "what_are_tiers": {
        "group": "B",
        "patterns": [
            r"\b(planos|pricing|pre[çc]os|tiers|tarif|preise)\b",
            r"(quanto|how\s*much|was|wieviel|combien).*(custa|cost|kostet|co[ûu]te)",
            r"(medium|gold|premium)\s*(plan|plano|tarif)",
            r"(upgrade|atualizar|verbessern|am[ée]liorer)",
        ],
        "confidence": 0.90,
        "requires_llm": False,
    },

    "what_are_dragons": {
        "group": "B",
        "patterns": [
            r"\b(drag[õo]es|dragons|drachen)\b",
            r"(quem|who|wer).*(guardian|architect|witness)",
            r"(tr[êe]s|three|drei)\s*(drag[õo]|dragon|drach)",
            r"(guardian|architect|witness).*(qu[ée]m|what|who|was|wer)",
        ],
        "confidence": 0.90,
        "requires_llm": False,
    },

    "how_seal_works": {
        "group": "B",
        "patterns": [
            r"\b(selagem|seal|hash|sha[-\s]*256|siegelung|versieg|scell[ée])\b",
            r"(como|how|wie|comment).*(sela|seal|versieg|scell)",
            r"(o\s*que|what|was|qu.est).*(selo|seal|siegel|sceau)",
            r"(impressão\s*digital|fingerprint|Fingerabdruck|empreinte)",
        ],
        "confidence": 0.85,
        "requires_llm": False,
    },

    "help": {
        "group": "B",
        "patterns": [
            r"\b(ajuda|help|hilfe|socorro|aide|مساعدة|ayuda)\b",
            r"(n[ãa]o|don.?t|nicht|ne\s*pas).*(entendo|understand|versteh|comprend)",
            r"(perdid[oa]|lost|verloren|perdu)",
            r"(como|how|wie|comment)\s*(funciona|começ|work|start|anfang|commenc)",
        ],
        "confidence": 0.90,
        "requires_llm": False,
    },

    "privacy_question": {
        "group": "B",
        "patterns": [
            r"\b(privacidade|privacy|datenschutz|gdpr|dsgvo|vie\s*priv[ée]e)\b",
            r"(meus|my|meine|mes)\s*(dados|data|daten|donn[ée]es)",
            r"(segur[oa]|safe|sicher|s[ûu]r).*(dados|data|daten|donn[ée]es)",
            r"(quem|who|wer|qui)\s*(acessa|access|zugreif|acc[èe]de)",
        ],
        "confidence": 0.85,
        "requires_llm": False,
    },

    # ── GROUP C: Document Creation ────────────────────────────────────────────

    "create_letter": {
        "group": "C",
        "patterns": [
            r"(criar|create|write|escrever|schreiben|erstellen|r[ée]diger|كتب).*(carta|letter|brief|lettre|رسالة)",
            r"(carta|letter|brief|lettre|رسالة).*(criar|create|make|escrever|write|schreib|r[ée]dig)",
            r"(preciso|need|brauche|besoin)\s*(de\s*)?(uma\s*)?(carta|letter|brief|lettre)",
            r"(veux|quiero|want|m[öo]chte)\s*(cr[ée]er|crear|create|erstellen)\s*(une?|uma?|a|ein)\s*(lettre|carta|letter|brief)",
        ],
        "confidence": 0.85,
        "requires_llm": False,
        "escalate_if": "user_wants_ai_content",
    },

    "create_memo": {
        "group": "C",
        "patterns": [
            r"(criar|create|write|escrever|schreiben|r[ée]diger).*(memo|memorando|notiz|note|nota|مذكرة)",
            r"\b(memo|memorando)\b",
        ],
        "confidence": 0.85,
        "requires_llm": False,
        "escalate_if": "user_wants_ai_content",
    },

    "create_email": {
        "group": "C",
        "patterns": [
            r"(criar|create|write|escrever|schreiben|r[ée]diger).*(e-?mail|correo|بريد)",
            r"(e-?mail).*(criar|create|escrever|write|schreib|r[ée]dig|enviar|send)",
        ],
        "confidence": 0.85,
        "requires_llm": False,
        "escalate_if": "user_wants_ai_content",
    },

    "create_doc_generic": {
        "group": "C",
        "patterns": [
            r"(criar|create|make|escrever|write|schreiben|erstellen|r[ée]diger).*(documento|document|dokument)",
            r"(documento|document|dokument).*(criar|create|novo|new|neu|nouveau)",
        ],
        "confidence": 0.80,
        "requires_llm": False,
        "escalate_if": "user_wants_ai_content",
    },

    "send_image": {
        "group": "C",
        "patterns": [
            r"(enviar|send|schicken|envoyer).*(imagem|image|foto|photo|bild|صورة)",
            r"(imagem|image|foto|photo|bild|صورة).*(enviar|send|upload|hochladen|envoyer)",
            r"(reproduz|reproduce|copy|copiar|kopier).*(carta|letter|brief).*(imagem|image|foto|photo|bild)",
            r"(vou\s*enviar|i.?ll\s*send|ich\s*schicke).*(imagem|image|foto|photo|bild)",
            r"(tirei|took)\s*(uma\s*)?(foto|photo|imagem)",
        ],
        "confidence": 0.80,
        "requires_llm": True,
        "credit_cost": 1,
        "offer_alternative": True,
    },

    # ── GROUP D: System Operations ────────────────────────────────────────────

    "seal_document": {
        "group": "D",
        "patterns": [
            r"\b(selar|seal|siegeln|sceller|ختم)\b",
            r"(quero|want|m[öo]chte|veux)\s*(selar|seal|versiegeln|sceller)",
        ],
        "confidence": 0.90,
        "requires_llm": False,
    },

    "verify_document": {
        "group": "D",
        "patterns": [
            r"(verificar|verify|pr[üu]fen|v[ée]rifier|check|التحقق)",
            r"(autenticidade|authenticity|Echtheit|authenticit[ée])",
            r"(documento.*v[áa]lido|document.*valid|Dokument.*g[üu]ltig)",
        ],
        "confidence": 0.90,
        "requires_llm": False,
    },

    "my_documents": {
        "group": "D",
        "patterns": [
            r"(meus|my|meine|mes)\s*(documento|document|dokument|doc)",
            r"(hist[óo]rico|history|verlauf|historique)",
            r"(onde|where|wo|o[ùu]).*(documento|document|dokument)",
            r"(lista|list|liste)\s*(de\s*)?(documento|document|dokument)",
        ],
        "confidence": 0.85,
        "requires_llm": False,
    },

    # ── GROUP E: Complex / Requires LLM ───────────────────────────────────────

    "creative_writing": {
        "group": "E",
        "patterns": [
            r"(escreve|write|schreib|[ée]cris)[\s\-]*(me\s*)?(um|uma|a|ein|une?)\s*(poema|poem|gedicht|po[èe]me)",
            r"(escreve|write|schreib|[ée]cris)[\s\-]*(me\s*)?(um|uma|a|ein|une?)\s*(hist[óo]ria|story|Geschichte|histoire)",
            r"(cria|create|erstell|cr[ée]e)\s*(um|uma|a|ein|une?)\s*(texto|text|conte[úu]do|content|poema|poem)",
            r"(inventa|invent|erfind|invent)\s",
            r"(poema|poem|gedicht)\s*(sobre|about|[üu]ber)",
        ],
        "confidence": 0.75,
        "requires_llm": True,
        "credit_cost": 1,
    },

    "deep_analysis": {
        "group": "E",
        "patterns": [
            r"(analisa|analyze|analyse|analysier|analys).*(contrato|contract|vertrag|contrat)",
            r"(analisa|analyze|analyse|analysier).*(risco|risk|risiko|risque)",
            r"(revisa|review|[üu]berpr[üu]f|r[ée]vis)\s",
            r"(risco|risk|risiko|risque).*(avalia|assess|beurt|[ée]valu)",
        ],
        "confidence": 0.70,
        "requires_llm": True,
        "credit_cost": 2,
    },
}


def classify_intent(text: str) -> Tuple[str, float, dict]:
    """
    Classify user message into an intent.
    
    Returns:
        (intent_id, confidence, metadata)
        
    metadata includes:
        group, requires_llm, credit_cost, escalate_if, offer_alternative
    """
    text_lower = text.lower().strip()

    # Short-circuit: very short greetings (3 chars or less)
    if len(text_lower) <= 3 and re.match(r"^(oi|hi|ol[áa]|hey)$", text_lower):
        cfg = INTENT_PATTERNS["greeting"]
        return "greeting", 0.99, _meta(cfg)

    # Collect ALL matching intents (not just the best)
    matches: List[Tuple[str, float, dict]] = []

    for intent_id, config in INTENT_PATTERNS.items():
        for pattern in config["patterns"]:
            if re.search(pattern, text_lower, re.IGNORECASE | re.UNICODE):
                matches.append((intent_id, config["confidence"], config))
                break  # one match per intent is enough

    if not matches:
        return "open_question", 0.0, _meta({
            "group": "E", "requires_llm": True, "credit_cost": 1,
        })

    # If multiple intents match and one is 'greeting' or 'chitchat',
    # prefer the non-social intent (user is greeting AND asking something)
    SOCIAL_INTENTS = {"greeting", "farewell", "thanks", "chitchat"}

    if len(matches) > 1:
        non_social = [(i, c, cfg) for i, c, cfg in matches if i not in SOCIAL_INTENTS]
        if non_social:
            matches = non_social

    # Pick highest confidence from remaining
    best = max(matches, key=lambda x: x[1])
    return best[0], best[1], _meta(best[2])


def _meta(config: dict) -> dict:
    """Extract metadata from intent config."""
    return {
        "group": config.get("group", "E"),
        "requires_llm": config.get("requires_llm", True),
        "credit_cost": config.get("credit_cost", 0),
        "escalate_if": config.get("escalate_if", None),
        "offer_alternative": config.get("offer_alternative", False),
    }


# ─── Quick Test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        "Olá",
        "Bom dia como vc se chama?",
        "Quero conversar contigo",
        "O que esta dentro da tarifa free?",
        "criar um documento",
        "quero que vc reproduza uma carta que vou enviar imagem?",
        "Hello, what is WINDI?",
        "Wie heißt du?",
        "Bonjour, je veux créer une lettre",
        "مرحبا، كيف حالك؟",
        "analisa este contrato",
        "escreve-me um poema sobre o mar",
        "Quero selar o meu documento",
        "quanto custa o plano medium?",
        "os meus dados estão seguros?",
    ]

    for t in tests:
        intent, conf, meta = classify_intent(t)
        llm = "🔴 LLM" if meta["requires_llm"] else "🟢 LOCAL"
        print(f"  [{llm}] {conf:.2f} | {intent:20s} | {t}")
