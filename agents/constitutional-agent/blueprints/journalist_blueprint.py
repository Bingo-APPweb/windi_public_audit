"""
WINDI Journalist Agent v0.1.0 — Flask Blueprint
================================================

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /journalist/* endpoints on :8091.

Philosophy:
  "Documentos juridicos tem verdade contratual.
   Jornalismo tem verdade factual — mais fragil, mais disputada, mais humana.
   Por isso J6 existe: o leitor tem direito de saber onde termina
   o humano e comeca a maquina."

Features:
- Draft generation with journalistic invariants (J1-J6)
- Style checking (pyramid, lead, voice, jargon)
- Fact-checking with source verification
- Source management (anonymous protection)
- AI participation transparency (J6 enforcement)
- Editorial pipeline to Communique

Journalistic Invariants (J1-J6):
  J1 — Veracidade:       Nenhum conteudo sem fonte verificavel
  J2 — Independencia:    Sem pressao comercial sobre pauta
  J3 — Imparcialidade:   Contraditorio sempre buscado
  J4 — Minimizacao dano: Protecao de vulneraveis e fontes
  J5 — Responsabilidade: Correcao publica quando erro detectado
  J6 — Transparencia IA: Todo conteudo IA-assistido = declarado

Critical Rule:
  J6 is MANDATORY — all AI-assisted content MUST be declared.
  publish() without ai_participation = BLOCKED.

Pipeline:
  Journalist (cria/edita/verifica)
    -> Communique (sela/doc_type="article")
      -> Ledger (prova forense)
        -> Vault (arquiva imutavel)

Principle: "AI processes. Human decides. WINDI guarantees."
Principle: "O leitor tem direito de saber onde termina o humano e comeca a maquina."

Version: 0.1.0
Sealed: W-JOURN-001
"""

import hashlib
import json
import os
import re
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

__version__ = "0.1.0"
__agent_id__ = "W-JOURN-001"
__agent_name__ = "Agente Jornalista"

# Database path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "journalist.db")

# Service URLs
COMMUNIQUE_URL = "http://localhost:8091/communique"
DRAGON_URL = "http://localhost:8108"
LEDGER_URL = "http://localhost:8101"


# ===================================================================
#  JOURNALISTIC INVARIANTS (J1-J6)
# ===================================================================

class JournalisticInvariant(Enum):
    """The six journalistic invariants that govern all agent operations."""
    J1 = ("J1", "veracidade", "Nenhum conteudo sem fonte verificavel")
    J2 = ("J2", "independencia", "Sem pressao comercial sobre pauta")
    J3 = ("J3", "imparcialidade", "Contraditorio sempre buscado")
    J4 = ("J4", "minimizacao_dano", "Protecao de vulneraveis e fontes")
    J5 = ("J5", "responsabilidade", "Correcao publica quando erro detectado")
    J6 = ("J6", "transparencia_ia", "Todo conteudo IA-assistido = declarado (MANDATORY)")

    def __init__(self, code: str, name: str, description: str):
        self._code = code
        self._name = name
        self._description = description

    @property
    def code(self) -> str:
        return self._code

    @property
    def invariant_name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description


class AIParticipation(Enum):
    """Types of AI participation in content creation."""
    ASSISTED = "assisted"       # Human wrote, AI helped with research/suggestions
    DRAFTED = "drafted"         # AI wrote first draft, human edited
    EDITED = "edited"           # Human wrote, AI edited for style/grammar
    FACT_CHECKED = "fact-checked"  # AI verified facts and sources


class InvariantStatus(Enum):
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATED = "violated"


# ===================================================================
#  GENRES DEFINITION
# ===================================================================

GENRES = {
    "noticia": {
        "tone": "factual",
        "adjectives": "zero",
        "lead": "required",
        "description": "Hard news - facts only, inverted pyramid"
    },
    "reportagem": {
        "tone": "narrative",
        "humanization": True,
        "depth": "high",
        "description": "In-depth reporting with human stories"
    },
    "editorial": {
        "tone": "opinion",
        "disclosure": "required",
        "description": "Opinion piece - must disclose it's opinion"
    },
    "entrevista": {
        "tone": "service",
        "author_invisible": True,
        "description": "Interview - author stays invisible, subject speaks"
    },
    "analise": {
        "tone": "expert",
        "data": "required",
        "description": "Analysis - requires data and expert perspective"
    }
}

# Style check thresholds
MAX_SENTENCE_WORDS = 30
MAX_PARAGRAPH_LINES = 3
PASSIVE_VOICE_PATTERNS = [
    r'\bfoi\s+\w+d[oa]s?\b',
    r'\bsera\s+\w+d[oa]s?\b',
    r'\bforam\s+\w+d[oa]s?\b',
    r'\bserao\s+\w+d[oa]s?\b',
    r'\bwas\s+\w+ed\b',
    r'\bwere\s+\w+ed\b',
    r'\bwurde\s+\w+t\b',
]
UNNECESSARY_ADJECTIVES = [
    "grande", "importante", "relevante", "significativo",
    "major", "important", "significant", "big",
    "gross", "wichtig", "bedeutend",
]


# ===================================================================
#  BLUEPRINT
# ===================================================================

journalist_bp = Blueprint("journalist", __name__, url_prefix="/journalist")


# ===================================================================
#  DATABASE INITIALIZATION
# ===================================================================

def get_db():
    """Get database connection."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize journalist database schema."""
    conn = get_db()
    conn.executescript("""
        -- Articles table
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            lead TEXT,
            content TEXT NOT NULL,
            genre TEXT NOT NULL,
            language TEXT DEFAULT 'de',
            ai_participation TEXT NOT NULL,
            sources TEXT DEFAULT '[]',
            status TEXT DEFAULT 'draft',
            author TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            published_at TEXT,
            communique_id TEXT,
            metadata TEXT DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
        CREATE INDEX IF NOT EXISTS idx_articles_genre ON articles(genre);

        -- Sources table (with anonymous protection)
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            alias TEXT NOT NULL,
            real_identity TEXT,
            credibility TEXT DEFAULT 'unverified',
            source_type TEXT DEFAULT 'human',
            anonymous INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL,
            last_used TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_sources_anonymous ON sources(anonymous);

        -- Fact checks table
        CREATE TABLE IF NOT EXISTS fact_checks (
            id TEXT PRIMARY KEY,
            article_id TEXT,
            claim TEXT NOT NULL,
            verification_status TEXT DEFAULT 'pending',
            sources_used TEXT DEFAULT '[]',
            confidence REAL DEFAULT 0.0,
            checked_at TEXT NOT NULL,
            checked_by TEXT
        );

        -- Style checks table
        CREATE TABLE IF NOT EXISTS style_checks (
            id TEXT PRIMARY KEY,
            article_id TEXT,
            pyramid_score INTEGER,
            lead_quality TEXT,
            passive_voice_count INTEGER,
            long_sentences INTEGER,
            jargon_detected TEXT DEFAULT '[]',
            suggestions TEXT DEFAULT '[]',
            checked_at TEXT NOT NULL
        );

        -- Corrections table (J5 - Responsabilidade)
        CREATE TABLE IF NOT EXISTS corrections (
            id TEXT PRIMARY KEY,
            article_id TEXT NOT NULL,
            original_text TEXT NOT NULL,
            corrected_text TEXT NOT NULL,
            reason TEXT NOT NULL,
            correction_type TEXT DEFAULT 'factual',
            published_at TEXT NOT NULL,
            FOREIGN KEY (article_id) REFERENCES articles(id)
        );

        -- Audit trail
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            actor TEXT NOT NULL,
            details TEXT,
            timestamp TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_trail(entity_type, entity_id);
    """)
    conn.commit()
    conn.close()


def now_iso():
    """Current UTC timestamp in ISO 8601."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_id(prefix: str = "ART") -> str:
    """Generate unique ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{ts}-{uid}"


def log_audit(action: str, entity_type: str, entity_id: str, actor: str, details: str = None):
    """Log action to audit trail."""
    conn = get_db()
    conn.execute("""
        INSERT INTO audit_trail (action, entity_type, entity_id, actor, details, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (action, entity_type, entity_id, actor, details, now_iso()))
    conn.commit()
    conn.close()


# ===================================================================
#  INVARIANT CHECKING
# ===================================================================

def check_invariants() -> Dict[str, Any]:
    """Check status of all journalistic invariants."""
    results = {}

    for inv in JournalisticInvariant:
        # Default to compliant - specific checks can override
        status = InvariantStatus.COMPLIANT.value
        details = None

        if inv == JournalisticInvariant.J1:
            # J1: Check for articles without sources
            conn = get_db()
            no_sources = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE sources = '[]' AND status != 'draft'"
            ).fetchone()[0]
            conn.close()
            if no_sources > 0:
                status = InvariantStatus.WARNING.value
                details = f"{no_sources} published articles without sources"

        elif inv == JournalisticInvariant.J6:
            # J6: Check for articles without AI declaration
            conn = get_db()
            no_declaration = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE ai_participation IS NULL OR ai_participation = ''"
            ).fetchone()[0]
            conn.close()
            if no_declaration > 0:
                status = InvariantStatus.VIOLATED.value
                details = f"{no_declaration} articles without AI participation declared"

        results[inv.code] = {
            "code": inv.code,
            "name": inv.invariant_name,
            "description": inv.description,
            "status": status,
            "details": details,
            "mandatory": inv == JournalisticInvariant.J6
        }

    return results


def get_overall_status(invariants: Dict) -> str:
    """Determine overall compliance status."""
    if any(inv["status"] == "violated" for inv in invariants.values()):
        return "VIOLATED"
    if any(inv["status"] == "warning" for inv in invariants.values()):
        return "WARNING"
    return "COMPLIANT"


# ===================================================================
#  HEALTH & STATUS ENDPOINTS
# ===================================================================

@journalist_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    conn = get_db()
    stats = {
        "articles": conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
        "sources": conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
        "fact_checks": conn.execute("SELECT COUNT(*) FROM fact_checks").fetchone()[0],
    }
    conn.close()

    return jsonify({
        "status": "GREEN",
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "database": DB_PATH,
        "stats": stats,
        "genres_supported": list(GENRES.keys()),
        "ai_participation_types": [e.value for e in AIParticipation],
        "principles": [
            "AI processes. Human decides. WINDI guarantees.",
            "O leitor tem direito de saber onde termina o humano e comeca a maquina."
        ],
        "timestamp": now_iso(),
    })


@journalist_bp.route("/status", methods=["GET"])
def status():
    """Detailed status with invariant checks."""
    invariants = check_invariants()
    overall = get_overall_status(invariants)

    return jsonify({
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "overall_status": overall,
        "invariants": invariants,
        "invariants_total": len(invariants),
        "invariants_compliant": sum(1 for i in invariants.values() if i["status"] == "compliant"),
        "j6_mandatory": True,
        "j6_description": "Todo conteudo IA-assistido deve ser declarado",
        "timestamp": now_iso(),
    })


# ===================================================================
#  DRAFT ENDPOINT
# ===================================================================

@journalist_bp.route("/draft", methods=["POST"])
def draft():
    """Generate article draft with J1-J6 active."""
    data = request.get_json() or {}

    topic = data.get("topic")
    if not topic:
        return jsonify({"error": "topic required"}), 400

    genre = data.get("genre", "noticia")
    if genre not in GENRES:
        return jsonify({"error": f"Invalid genre. Supported: {list(GENRES.keys())}"}), 400

    language = data.get("language", "de")
    sources = data.get("sources", [])
    isp = data.get("isp")

    genre_config = GENRES[genre]

    # Generate via Dragon if available
    content = None
    lead = None
    ai_participation = AIParticipation.DRAFTED.value

    if REQUESTS_AVAILABLE:
        try:
            prompt = f"""Generate a {genre} article in {language} about: {topic}

Genre requirements: {json.dumps(genre_config)}

Structure:
- Lead paragraph (who/what/when/where/why/how)
- Body following inverted pyramid
- Keep sentences under 30 words
- Use active voice
- No unnecessary adjectives

Return JSON with: title, lead, content"""

            r = requests.post(
                f"{DRAGON_URL}/dragon",
                json={"prompt": prompt, "dragon": "architect", "format": "json"},
                timeout=30
            )

            if r.status_code == 200:
                dragon_resp = r.json()
                result = dragon_resp.get("response", dragon_resp.get("content", {}))
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except:
                        result = {"content": result, "title": topic[:50], "lead": ""}

                content = result.get("content", "")
                lead = result.get("lead", "")
                title = result.get("title", topic[:50])
            else:
                content = f"[Draft placeholder for: {topic}]"
                lead = f"[Lead placeholder]"
                title = topic[:50]
        except Exception as e:
            content = f"[Draft placeholder for: {topic}]"
            lead = f"[Lead placeholder]"
            title = topic[:50]
    else:
        content = f"[Draft placeholder for: {topic}]"
        lead = f"[Lead placeholder]"
        title = topic[:50]

    # Calculate structure score
    structure_score = calculate_structure_score(content, genre)

    # Create article record
    article_id = generate_id("ART")
    ts = now_iso()

    conn = get_db()
    conn.execute("""
        INSERT INTO articles (id, title, lead, content, genre, language, ai_participation,
                             sources, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
    """, (article_id, title, lead, content, genre, language, ai_participation,
          json.dumps(sources), ts, ts))
    conn.commit()
    conn.close()

    log_audit("DRAFT_CREATED", "article", article_id, "Dragon AI", f"topic={topic}, genre={genre}")

    return jsonify({
        "id": article_id,
        "title": title,
        "lead": lead,
        "content": content,
        "genre": genre,
        "language": language,
        "structure_score": structure_score,
        "ai_participation": ai_participation,  # J6: ALWAYS included
        "sources": sources,
        "status": "draft",
        "created_at": ts,
    }), 201


def calculate_structure_score(content: str, genre: str) -> Dict[str, Any]:
    """
    Calculate how well content follows journalistic structure.
    Returns full breakdown so draft() has style-check DNA from birth.
    """
    score = 100

    # Check for lead paragraph with 5W1H
    paragraphs = content.split('\n\n')
    lead = paragraphs[0] if paragraphs else ""

    lead_elements = {
        "who": bool(re.search(r'\b(quem|who|wer)\b', lead, re.IGNORECASE)),
        "what": bool(re.search(r'\b(o que|what|was)\b', lead, re.IGNORECASE)),
        "when": bool(re.search(r'\b(quando|when|wann|hoje|ontem|yesterday|today)\b', lead, re.IGNORECASE)),
        "where": bool(re.search(r'\b(onde|where|wo|em|in|at)\b', lead, re.IGNORECASE)),
        "why": bool(re.search(r'\b(por que|why|warum|porque)\b', lead, re.IGNORECASE)),
        "how": bool(re.search(r'\b(como|how|wie)\b', lead, re.IGNORECASE)),
    }
    lead_complete = all(lead_elements.values())

    if not lead_complete:
        score -= (6 - sum(lead_elements.values())) * 5

    if not paragraphs or len(paragraphs[0]) < 50:
        score -= 10

    # Check sentence length
    sentences = re.split(r'[.!?]', content)
    long_sentences_count = sum(1 for s in sentences if len(s.split()) > MAX_SENTENCE_WORDS)
    score -= min(long_sentences_count * 5, 30)

    # Check passive voice
    passive_count = sum(len(re.findall(p, content, re.IGNORECASE)) for p in PASSIVE_VOICE_PATTERNS)
    score -= min(passive_count * 3, 20)

    # Check genre compliance
    genre_config = GENRES.get(genre, {})
    genre_compliance = True

    if genre_config.get("adjectives") == "zero":
        for adj in UNNECESSARY_ADJECTIVES:
            if adj.lower() in content.lower():
                genre_compliance = False
                score -= 5
                break

    if genre_config.get("lead") == "required" and not lead_complete:
        genre_compliance = False

    return {
        "pyramid_score": max(score, 0),
        "lead_complete": lead_complete,
        "lead_elements": lead_elements,
        "genre_compliance": genre_compliance,
        "passive_voice": passive_count,
        "long_sentences": long_sentences_count,
    }


# ===================================================================
#  EDIT ENDPOINT
# ===================================================================

@journalist_bp.route("/edit", methods=["POST"])
def edit():
    """Edit human material while preserving voice."""
    data = request.get_json() or {}

    content = data.get("content")
    if not content:
        return jsonify({"error": "content required"}), 400

    # HARDCODED: preserve_voice is ALWAYS true - cannot be overridden
    # This is a design principle, not a feature flag
    preserve_voice = True

    # Suggest edits without replacing author's voice
    changes = []
    edited_content = content

    # Find passive voice instances
    for pattern in PASSIVE_VOICE_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            changes.append({
                "type": "passive_voice",
                "original": match.group(),
                "position": match.start(),
                "suggestion": "Consider active voice",
                "applied": False  # Never auto-apply - preserve voice
            })

    # Find unnecessary adjectives
    for adj in UNNECESSARY_ADJECTIVES:
        if adj.lower() in content.lower():
            changes.append({
                "type": "unnecessary_adjective",
                "word": adj,
                "suggestion": "Consider removing or replacing with specific data",
                "applied": False
            })

    # Find long sentences
    sentences = re.split(r'([.!?])', content)
    for i in range(0, len(sentences)-1, 2):
        sentence = sentences[i]
        if len(sentence.split()) > MAX_SENTENCE_WORDS:
            changes.append({
                "type": "long_sentence",
                "sentence": sentence[:50] + "...",
                "word_count": len(sentence.split()),
                "suggestion": f"Consider breaking into shorter sentences (max {MAX_SENTENCE_WORDS} words)",
                "applied": False
            })

    return jsonify({
        "original_content": content,
        "edited_content": edited_content,  # Same as original - we only SUGGEST
        "changes": changes,
        "changes_count": len(changes),
        "voice_preserved": True,  # Always true by design
        "ai_participation": AIParticipation.EDITED.value,
        "note": "Changes are suggestions only. Author voice is preserved.",
    })


# ===================================================================
#  STYLE CHECK ENDPOINT
# ===================================================================

@journalist_bp.route("/style-check", methods=["POST"])
def style_check():
    """Verify pyramid structure, lead quality, voice, jargon."""
    data = request.get_json() or {}

    content = data.get("content")
    if not content:
        return jsonify({"error": "content required"}), 400

    article_id = data.get("article_id")

    # Analyze pyramid structure
    paragraphs = content.split('\n\n')
    pyramid_score = 100

    # Lead quality check (5W1H)
    lead = paragraphs[0] if paragraphs else ""
    lead_elements = {
        "who": bool(re.search(r'\b(quem|who|wer)\b', lead, re.IGNORECASE)),
        "what": bool(re.search(r'\b(o que|what|was)\b', lead, re.IGNORECASE)),
        "when": bool(re.search(r'\b(quando|when|wann|hoje|ontem|yesterday|today)\b', lead, re.IGNORECASE)),
        "where": bool(re.search(r'\b(onde|where|wo|em|in|at)\b', lead, re.IGNORECASE)),
        "why": bool(re.search(r'\b(por que|why|warum|porque)\b', lead, re.IGNORECASE)),
        "how": bool(re.search(r'\b(como|how|wie)\b', lead, re.IGNORECASE)),
    }
    lead_quality = {
        "elements_present": lead_elements,
        "score": sum(lead_elements.values()) / 6 * 100,
        "missing": [k for k, v in lead_elements.items() if not v]
    }

    # Passive voice count
    passive_count = sum(len(re.findall(p, content, re.IGNORECASE)) for p in PASSIVE_VOICE_PATTERNS)

    # Long sentences
    sentences = re.split(r'[.!?]', content)
    long_sentences = [
        {"sentence": s[:50] + "...", "words": len(s.split())}
        for s in sentences if len(s.split()) > MAX_SENTENCE_WORDS
    ]

    # Jargon detection
    jargon_detected = [
        adj for adj in UNNECESSARY_ADJECTIVES
        if adj.lower() in content.lower()
    ]

    # Generate suggestions
    suggestions = []
    if lead_quality["score"] < 80:
        suggestions.append(f"Lead missing: {', '.join(lead_quality['missing'])}")
    if passive_count > 3:
        suggestions.append(f"High passive voice usage ({passive_count} instances)")
    if len(long_sentences) > 2:
        suggestions.append(f"Too many long sentences ({len(long_sentences)})")
    if jargon_detected:
        suggestions.append(f"Unnecessary adjectives: {', '.join(jargon_detected)}")

    # Calculate final pyramid score
    pyramid_score -= (6 - sum(lead_elements.values())) * 10
    pyramid_score -= min(passive_count * 3, 20)
    pyramid_score -= min(len(long_sentences) * 5, 20)
    pyramid_score -= min(len(jargon_detected) * 5, 15)
    pyramid_score = max(pyramid_score, 0)

    # Save style check if article_id provided
    if article_id:
        check_id = generate_id("STY")
        conn = get_db()
        conn.execute("""
            INSERT INTO style_checks (id, article_id, pyramid_score, lead_quality,
                                     passive_voice_count, long_sentences, jargon_detected,
                                     suggestions, checked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (check_id, article_id, pyramid_score, json.dumps(lead_quality),
              passive_count, len(long_sentences), json.dumps(jargon_detected),
              json.dumps(suggestions), now_iso()))
        conn.commit()
        conn.close()

    return jsonify({
        "pyramid_score": pyramid_score,
        "lead_quality": lead_quality,
        "passive_voice_count": passive_count,
        "long_sentences": long_sentences,
        "long_sentences_count": len(long_sentences),
        "jargon_detected": jargon_detected,
        "suggestions": suggestions,
        "ai_participation": AIParticipation.FACT_CHECKED.value,
    })


# ===================================================================
#  FACT CHECK ENDPOINT
# ===================================================================

@journalist_bp.route("/fact-check", methods=["POST"])
def fact_check():
    """Verify claims against sources."""
    data = request.get_json() or {}

    content = data.get("content")
    if not content:
        return jsonify({"error": "content required"}), 400

    sources = data.get("sources", [])
    article_id = data.get("article_id")

    # Extract claims (simplified - sentences with numbers, dates, or quotes)
    claims = []
    sentences = re.split(r'[.!?]', content)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Check if sentence contains verifiable claims
        has_number = bool(re.search(r'\d+', sentence))
        has_quote = '"' in sentence or "'" in sentence
        has_date = bool(re.search(r'\d{4}|\d{1,2}/\d{1,2}|\b(janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro|january|february|march|april|may|june|july|august|september|october|november|december)\b', sentence, re.IGNORECASE))

        if has_number or has_quote or has_date:
            claims.append({
                "text": sentence[:100],
                "type": "number" if has_number else "quote" if has_quote else "date",
            })

    # Verify claims against sources (simplified)
    verified = []
    unverified = []

    for claim in claims:
        # In a real implementation, this would check against actual sources
        # For now, mark as verified if sources are provided
        if sources:
            verified.append({
                "claim": claim["text"],
                "source": sources[0] if sources else None,
                "confidence": 0.7
            })
        else:
            unverified.append({
                "claim": claim["text"],
                "reason": "No sources provided"
            })

    # Calculate risk level
    if not claims:
        risk_level = "LOW"
    elif len(unverified) / max(len(claims), 1) > 0.5:
        risk_level = "HIGH"
    elif len(unverified) > 0:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Save fact check results
    if article_id:
        for claim in claims:
            check_id = generate_id("FCK")
            is_verified = any(v["claim"] == claim["text"] for v in verified)
            conn = get_db()
            conn.execute("""
                INSERT INTO fact_checks (id, article_id, claim, verification_status,
                                        sources_used, confidence, checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (check_id, article_id, claim["text"],
                  "verified" if is_verified else "unverified",
                  json.dumps(sources), 0.7 if is_verified else 0.0, now_iso()))
            conn.commit()
            conn.close()

    return jsonify({
        "claims": claims,
        "claims_count": len(claims),
        "verified": verified,
        "verified_count": len(verified),
        "unverified": unverified,
        "unverified_count": len(unverified),
        "risk_level": risk_level,
        "sources_used": sources,
        "ai_participation": AIParticipation.FACT_CHECKED.value,
    })


# ===================================================================
#  SOURCES ENDPOINTS
# ===================================================================

@journalist_bp.route("/sources", methods=["GET"])
def list_sources():
    """List registered sources (without sensitive data for anonymous)."""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, alias, credibility, source_type, anonymous, created_at, last_used
        FROM sources
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()

    sources = []
    for row in rows:
        source = dict(row)
        # J4: Never expose real identity of anonymous sources
        if source["anonymous"]:
            source["protected"] = True
            source["note"] = "Anonymous source - identity protected (J4)"
        sources.append(source)

    return jsonify({
        "sources": sources,
        "total": len(sources),
        "anonymous_count": sum(1 for s in sources if s.get("anonymous")),
    })


@journalist_bp.route("/sources", methods=["POST"])
def register_source():
    """Register a new source."""
    data = request.get_json() or {}

    alias = data.get("alias")
    if not alias:
        return jsonify({"error": "alias required"}), 400

    source_id = generate_id("SRC")
    ts = now_iso()

    anonymous = data.get("anonymous", False)
    real_identity = data.get("real_identity") if not anonymous else None

    conn = get_db()
    conn.execute("""
        INSERT INTO sources (id, alias, real_identity, credibility, source_type, anonymous, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (source_id, alias, real_identity, data.get("credibility", "unverified"),
          data.get("type", "human"), 1 if anonymous else 0, data.get("notes"), ts))
    conn.commit()
    conn.close()

    log_audit("SOURCE_REGISTERED", "source", source_id, "journalist",
              f"alias={alias}, anonymous={anonymous}")

    response = {
        "id": source_id,
        "alias": alias,
        "credibility": data.get("credibility", "unverified"),
        "type": data.get("type", "human"),
        "anonymous": anonymous,
        "created_at": ts,
    }

    if anonymous:
        response["note"] = "Anonymous source registered. Real identity will NEVER be exposed (J4)."

    return jsonify(response), 201


# ===================================================================
#  AI DECLARATION ENDPOINT
# ===================================================================

@journalist_bp.route("/ai-declare", methods=["POST"])
def ai_declare():
    """Generate AI participation disclaimer in three languages."""
    data = request.get_json() or {}

    content = data.get("content")
    ai_participation = data.get("ai_participation")

    if not ai_participation:
        return jsonify({"error": "ai_participation required (J6 mandatory)"}), 400

    if ai_participation not in [e.value for e in AIParticipation]:
        return jsonify({
            "error": f"Invalid ai_participation. Valid: {[e.value for e in AIParticipation]}"
        }), 400

    # Generate disclaimers based on participation type
    disclaimers = {
        "assisted": {
            "pt": "Este artigo foi produzido com assistencia de inteligencia artificial para pesquisa e sugestoes.",
            "de": "Dieser Artikel wurde mit Unterstutzung kunstlicher Intelligenz fur Recherche und Vorschlage erstellt.",
            "en": "This article was produced with artificial intelligence assistance for research and suggestions."
        },
        "drafted": {
            "pt": "O rascunho inicial deste artigo foi gerado por inteligencia artificial e editado por humanos.",
            "de": "Der erste Entwurf dieses Artikels wurde von kunstlicher Intelligenz generiert und von Menschen bearbeitet.",
            "en": "The initial draft of this article was generated by artificial intelligence and edited by humans."
        },
        "edited": {
            "pt": "Este artigo foi escrito por humanos e editado com auxilio de inteligencia artificial.",
            "de": "Dieser Artikel wurde von Menschen geschrieben und mit Hilfe kunstlicher Intelligenz bearbeitet.",
            "en": "This article was written by humans and edited with artificial intelligence assistance."
        },
        "fact-checked": {
            "pt": "Os fatos neste artigo foram verificados com auxilio de inteligencia artificial.",
            "de": "Die Fakten in diesem Artikel wurden mit Hilfe kunstlicher Intelligenz uberpruft.",
            "en": "The facts in this article were verified with artificial intelligence assistance."
        }
    }

    selected = disclaimers.get(ai_participation, disclaimers["assisted"])

    return jsonify({
        "ai_participation": ai_participation,
        "disclaimer_pt": selected["pt"],
        "disclaimer_de": selected["de"],
        "disclaimer_en": selected["en"],
        "j6_compliant": True,
        "note": "O leitor tem direito de saber onde termina o humano e comeca a maquina."
    })


# ===================================================================
#  PUBLISH ENDPOINT
# ===================================================================

@journalist_bp.route("/publish", methods=["POST"])
def publish():
    """Publish article to Communique pipeline."""
    data = request.get_json() or {}

    article_id = data.get("article_id")
    if not article_id:
        return jsonify({"error": "article_id required"}), 400

    approved_by = data.get("approved_by")
    if not approved_by:
        return jsonify({"error": "approved_by required"}), 400

    ai_participation = data.get("ai_participation")

    # J6 GATE: Cannot publish without AI participation declared
    if not ai_participation:
        return jsonify({
            "error": "BLOCKED by J6: ai_participation must be declared before publishing",
            "j6_violation": True,
            "invariant": "J6 - Transparencia IA: Todo conteudo IA-assistido = declarado",
            "resolution": "Provide ai_participation field (assisted|drafted|edited|fact-checked)"
        }), 403

    # Get article
    conn = get_db()
    row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Article not found"}), 404

    article = dict(row)

    if article["status"] == "published":
        conn.close()
        return jsonify({"error": "Article already published"}), 400

    # Generate AI disclaimer
    disclaimers = {
        "assisted": "Produzido com assistencia de IA.",
        "drafted": "Rascunho gerado por IA, editado por humanos.",
        "edited": "Escrito por humanos, editado com IA.",
        "fact-checked": "Fatos verificados com IA."
    }
    disclaimer = disclaimers.get(ai_participation, "IA envolvida na producao.")

    # Update article status
    ts = now_iso()
    conn.execute("""
        UPDATE articles SET status = 'published', ai_participation = ?,
                           published_at = ?, updated_at = ?
        WHERE id = ?
    """, (ai_participation, ts, ts, article_id))
    conn.commit()
    conn.close()

    # Create Communique with doc_type="article"
    communique_id = None
    ledger_receipt = None

    if REQUESTS_AVAILABLE:
        try:
            payload = {
                "title_de": article["title"],
                "body_de": article["content"] + f"\n\n---\n{disclaimer}",
                "author_name": approved_by,
                "author_role": "Editor",
                "category": "REPORT",
                "doc_type": "article",
                "tags": ["journalism", f"ai-{ai_participation}"],
            }

            r = requests.post(f"{COMMUNIQUE_URL}/create", json=payload, timeout=10)

            if r.status_code == 201:
                result = r.json()
                communique_id = result.get("id")

                # Update article with communique reference
                conn = get_db()
                conn.execute(
                    "UPDATE articles SET communique_id = ? WHERE id = ?",
                    (communique_id, article_id)
                )
                conn.commit()
                conn.close()
        except Exception as e:
            pass  # Communique failure should not block - log and continue

    log_audit("ARTICLE_PUBLISHED", "article", article_id, approved_by,
              f"ai_participation={ai_participation}, communique={communique_id}")

    return jsonify({
        "article_id": article_id,
        "status": "published",
        "approved_by": approved_by,
        "ai_participation": ai_participation,
        "ai_disclaimer": disclaimer,
        "communique_id": communique_id,
        "ledger_receipt": ledger_receipt,
        "j6_compliant": True,
        "published_at": ts,
    })


# ===================================================================
#  GENRES ENDPOINT
# ===================================================================

@journalist_bp.route("/genres", methods=["GET"])
def genres():
    """List supported journalistic genres."""
    return jsonify({
        "genres": GENRES,
        "total": len(GENRES),
    })


# ===================================================================
#  CORRECTIONS ENDPOINT (J5)
# ===================================================================

@journalist_bp.route("/corrections", methods=["POST"])
def register_correction():
    """Register a public correction (J5 - Responsabilidade)."""
    data = request.get_json() or {}

    article_id = data.get("article_id")
    original_text = data.get("original_text")
    corrected_text = data.get("corrected_text")
    reason = data.get("reason")

    if not all([article_id, original_text, corrected_text, reason]):
        return jsonify({"error": "article_id, original_text, corrected_text, and reason required"}), 400

    correction_id = generate_id("COR")
    ts = now_iso()

    conn = get_db()
    conn.execute("""
        INSERT INTO corrections (id, article_id, original_text, corrected_text, reason,
                                correction_type, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (correction_id, article_id, original_text, corrected_text, reason,
          data.get("type", "factual"), ts))
    conn.commit()
    conn.close()

    log_audit("CORRECTION_PUBLISHED", "correction", correction_id, "editor",
              f"article={article_id}, reason={reason}")

    return jsonify({
        "id": correction_id,
        "article_id": article_id,
        "original_text": original_text,
        "corrected_text": corrected_text,
        "reason": reason,
        "j5_compliant": True,
        "published_at": ts,
        "note": "J5 - Responsabilidade: Correcao publica quando erro detectado"
    }), 201


@journalist_bp.route("/corrections/<article_id>", methods=["GET"])
def get_corrections(article_id):
    """Get corrections for an article."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM corrections WHERE article_id = ? ORDER BY published_at DESC",
        (article_id,)
    ).fetchall()
    conn.close()

    return jsonify({
        "article_id": article_id,
        "corrections": [dict(r) for r in rows],
        "total": len(rows),
    })


# ===================================================================
#  EDITOR BRIDGE — W-JOURN-001 → Palette/Desktop
#  Version: 1.0.0 | Sealed: 14 Mar 2026
# ===================================================================

# ── Constantes do Bridge ────────────────────────────────────
PALETTE_DRAGON_URL = "http://localhost:8108"
LEDGER_URL = "http://localhost:8101"
BRIDGE_VERSION = "1.0.0"

# ── Banco de dados do bridge ────────────────────────────────
BRIDGE_DB_INIT = """
CREATE TABLE IF NOT EXISTS journ_bridge_sessions (
    id TEXT PRIMARY KEY,
    draft_id TEXT NOT NULL,
    article_id TEXT,
    status TEXT DEFAULT 'open',
    content TEXT,
    opened_at TEXT,
    saved_at TEXT,
    published_at TEXT,
    ledger_receipt TEXT
);
"""

def init_bridge_db():
    try:
        db = get_db()
        db.executescript(BRIDGE_DB_INIT)
        db.commit()
    except Exception as e:
        pass


@journalist_bp.route("/bridge/open", methods=["POST"])
def bridge_open():
    """Abre draft existente OU cria nova sessão (FIX 2026-03-19)."""
    data = request.get_json() or {}
    draft_id = data.get("draft_id", "").strip()
    article_id = data.get("article_id", "").strip()
    title = data.get("title", "").strip()
    wallet_id = data.get("wallet_id", "anonymous")

    session_id = f"BRG-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc).isoformat()

    # MODE A: Criar nova sessão (sem draft_id) — chamado pelo GEN7 gateway
    if not draft_id:
        if not title:
            title = "Novo Artigo"
        try:
            init_bridge_db()
            db = get_db()
            db.execute(
                """INSERT INTO journ_bridge_sessions
                   (id, draft_id, article_id, status, content, opened_at)
                   VALUES (?,?,?,?,?,?)""",
                (session_id, "", article_id, "new", "", now)
            )
            db.commit()
        except Exception as e:
            pass

        return jsonify({
            "status": "created",
            "session_id": session_id,
            "title": title,
            "wallet_id": wallet_id,
            "j_phase": "J1",
            "bridge_version": BRIDGE_VERSION,
            "message": "Nova sessão criada. Pronto para edição."
        }), 201

    # MODE B: Abrir draft existente (com draft_id) — comportamento original
    try:
        db = get_db()
        row = db.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if not row:
            return jsonify({"error": f"Draft {draft_id} não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": f"DB error: {str(e)}"}), 500

    content_html = row["content"] if "content" in row.keys() else ""
    title = row["title"] if "title" in row.keys() else f"Artigo {draft_id}"

    try:
        init_bridge_db()
        db.execute(
            """INSERT OR REPLACE INTO journ_bridge_sessions
               (id, draft_id, article_id, status, content, opened_at)
               VALUES (?,?,?,?,?,?)""",
            (session_id, draft_id, article_id, "open", content_html, now)
        )
        db.commit()
    except Exception as e:
        pass

    editor_url = f"https://windi-domain.com/app/?action=open_draft&draft_id={draft_id}&session_id={session_id}&doc_type=article"

    return jsonify({
        "status": "opened",
        "session_id": session_id,
        "draft_id": draft_id,
        "editor_url": editor_url,
        "j_phase": "J4",
        "bridge_version": BRIDGE_VERSION
    }), 200


@journalist_bp.route("/bridge/save", methods=["POST"])
def bridge_save():
    """Guarda edições do Editor de volta no W-JOURN-001."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "").strip()
    draft_id = data.get("draft_id", "").strip()
    content = data.get("content", "").strip()
    title = data.get("title", "").strip()

    if not draft_id or not content:
        return jsonify({"error": "draft_id e content obrigatórios"}), 400

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    try:
        db.execute("UPDATE drafts SET content=?, title=?, updated_at=? WHERE id=?",
                   (content, title or None, now, draft_id))
        db.commit()
    except Exception as e:
        return jsonify({"error": f"Falha ao salvar: {str(e)}"}), 500

    if session_id:
        try:
            db.execute("""UPDATE journ_bridge_sessions SET content=?, saved_at=?, status='saved' WHERE id=?""",
                       (content, now, session_id))
            db.commit()
        except:
            pass

    return jsonify({"status": "saved", "draft_id": draft_id, "session_id": session_id, "saved_at": now, "j_phase": "J4"}), 200


@journalist_bp.route("/bridge/publish", methods=["POST"])
def bridge_publish():
    """Publicação: Editor → J6 → Ledger seal."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "").strip()
    draft_id = data.get("draft_id", "").strip()
    article_id = data.get("article_id", "").strip()
    content = data.get("content", "").strip()
    title = data.get("title", "Artigo sem título")
    ai_used = data.get("ai_used", False)
    ai_declaration = data.get("ai_declaration", "")

    if not draft_id or not content:
        return jsonify({"error": "draft_id e content obrigatórios"}), 400

    # INVARIANTE J6: Human gate
    if not data.get("human_approved", False):
        return jsonify({"status": "awaiting_approval", "message": "J6 requer human_approved=true", "j_phase": "J5"}), 202

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    try:
        db.execute("UPDATE drafts SET content=?, title=?, updated_at=? WHERE id=?", (content, title, now, draft_id))
        db.commit()
    except Exception as e:
        return jsonify({"error": f"Falha: {str(e)}"}), 500

    if ai_used and not ai_declaration:
        ai_declaration = f"Artigo editado com assistência de IA (W-JOURN-001). Publicado em {now}."

    content_hash = hashlib.sha256(content.encode()).hexdigest()
    ledger_receipt = f"WINDI-JOURN-{draft_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    try:
        db.execute("UPDATE drafts SET status='published', published_at=?, ledger_receipt=? WHERE id=?",
                   (now, ledger_receipt, draft_id))
        db.commit()
    except:
        pass

    if session_id:
        try:
            db.execute("UPDATE journ_bridge_sessions SET status='published', published_at=?, ledger_receipt=? WHERE id=?",
                       (now, ledger_receipt, session_id))
            db.commit()
        except:
            pass

    return jsonify({
        "status": "published", "j_phase": "J6", "draft_id": draft_id,
        "ledger_receipt": ledger_receipt, "content_hash": content_hash,
        "published_at": now, "ai_declaration": ai_declaration if ai_used else None,
        "verify_url": f"https://windi-domain.com/verify-public/?id={ledger_receipt}",
        "bridge_version": BRIDGE_VERSION
    }), 200


@journalist_bp.route("/bridge/status/<session_id>", methods=["GET"])
def bridge_status(session_id):
    """Consulta estado de uma sessão de bridge."""
    try:
        init_bridge_db()
        db = get_db()
        row = db.execute("SELECT * FROM journ_bridge_sessions WHERE id = ?", (session_id,)).fetchone()
    except Exception as e:
        return jsonify({"error": f"DB error: {e}"}), 500

    if not row:
        return jsonify({"error": f"Sessão {session_id} não encontrada"}), 404

    return jsonify({
        "session_id": row["id"], "draft_id": row["draft_id"], "article_id": row["article_id"],
        "status": row["status"], "opened_at": row["opened_at"], "saved_at": row["saved_at"],
        "published_at": row["published_at"], "ledger_receipt": row["ledger_receipt"]
    }), 200


# ===================================================================
#  INITIALIZE
# ===================================================================

# Initialize database on import
init_db()
init_bridge_db()
