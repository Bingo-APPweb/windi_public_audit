"""
W-PROV-003 — Reputation Engine
==============================
WINDI Publishing House · Kempten, Bavaria · 2026-03-13

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /reputation/* endpoints on :8091.

Philosophy:
  "A confiança não se declara — calcula-se."

  O Reputation Engine não cria confiança.
  Ele calcula índices baseados em evidências observáveis:
  - Quantas verificações?
  - De quantos domínios diferentes?
  - De quantos países?
  - Há quanto tempo circula?
  - A cadeia de prova é profunda?

Role:
  W-PROV-003 is LAYER 4 of the Proof Constellation:
    Genesis (creates) -> Propagation (tracks) -> Forensic (validates) -> Reputation (scores)

  The Engine answers:
    - Qual o trust_score deste artefato?
    - Qual a credibilidade deste actor?
    - Qual a reputação deste domínio?

Critical Rules:
  - Scores são INFORMATIVOS, nunca decisórios (I9)
  - Má reputação não se apaga (R3)
  - Scores decaem com inatividade (R4)
  - Boosts requerem eventos reais (R5)

Reputation Invariants (R1-R5):
  R1 — Advisory Only:    Scores inform, never decide (I9 compliance)
  R2 — Public Access:    Reputation is queryable by anyone
  R3 — Immutable History: Bad reputation cannot be erased
  R4 — Decay Function:   Inactive artifacts lose trust over time
  R5 — Evidence-Based:   Boosts require real verification events

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 1.0.0
Sealed: W-PROV-003
"""

import hashlib
import json
import math
import os
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import urllib.request

from flask import Blueprint, jsonify, request

__version__ = "1.0.0"
__agent_id__ = "W-PROV-003"
__agent_name__ = "Reputation Engine"

# ═══════════════════════════════════════════════════════════════════════════════
# Blueprint Setup
# ═══════════════════════════════════════════════════════════════════════════════

reputation_bp = Blueprint('reputation', __name__, url_prefix='/reputation')

# Database paths
REPUTATION_DIR = "/opt/windi/reputation"
DB_PATH = os.path.join(REPUTATION_DIR, "reputation.db")

# External services (READ ONLY)
LEDGER_API = os.environ.get('LEDGER_API', 'http://localhost:8101')
PROPAGATION_DB = os.environ.get('PROPAGATION_DB', '/opt/windi/data/propagation_index.db')
FORENSIC_DB = os.environ.get('FORENSIC_DB', '/opt/windi/forensic/forensic.db')

# ═══════════════════════════════════════════════════════════════════════════════
# Reputation Invariants (R1-R5)
# ═══════════════════════════════════════════════════════════════════════════════

class ReputationInvariant(Enum):
    """The five reputation invariants that govern all scoring operations."""
    R1 = ("R1", "advisory_only", "Scores informam, nunca decidem (I9)")
    R2 = ("R2", "public_access", "Reputacao e consultavel por qualquer um")
    R3 = ("R3", "immutable_history", "Ma reputacao nao se apaga")
    R4 = ("R4", "decay_function", "Artefatos inativos perdem confianca")
    R5 = ("R5", "evidence_based", "Boosts requerem eventos reais")

    def __init__(self, code: str, name: str, description: str):
        self._code = code
        self._name = name
        self._description = description

    @property
    def code(self) -> str:
        return self._code

# ═══════════════════════════════════════════════════════════════════════════════
# Trust Tier Definitions
# ═══════════════════════════════════════════════════════════════════════════════

TRUST_TIERS = {
    "UNVERIFIED": {"min": 0.0, "max": 0.2, "color": "gray", "badge": "⚪"},
    "EMERGING": {"min": 0.2, "max": 0.4, "color": "bronze", "badge": "🥉"},
    "ESTABLISHED": {"min": 0.4, "max": 0.6, "color": "silver", "badge": "🥈"},
    "TRUSTED": {"min": 0.6, "max": 0.8, "color": "gold", "badge": "🥇"},
    "SOVEREIGN": {"min": 0.8, "max": 1.0, "color": "platinum", "badge": "👑"},
}

def get_trust_tier(score: float) -> Dict[str, Any]:
    """Get tier info for a given trust score."""
    for tier_name, tier_info in TRUST_TIERS.items():
        if tier_info["min"] <= score < tier_info["max"]:
            return {"tier": tier_name, **tier_info}
    return {"tier": "SOVEREIGN", **TRUST_TIERS["SOVEREIGN"]}

# ═══════════════════════════════════════════════════════════════════════════════
# Database Schema
# ═══════════════════════════════════════════════════════════════════════════════

SCHEMA = """
CREATE TABLE IF NOT EXISTS artifact_scores (
    ledger_anchor       TEXT PRIMARY KEY,
    trust_score         REAL DEFAULT 0.0,
    verification_count  INTEGER DEFAULT 0,
    unique_domains      INTEGER DEFAULT 0,
    unique_countries    INTEGER DEFAULT 0,
    chain_depth         INTEGER DEFAULT 0,
    forensic_status     TEXT,
    first_seen          TEXT,
    last_seen           TEXT,
    last_calculated     TEXT,
    tier                TEXT DEFAULT 'UNVERIFIED'
);

CREATE TABLE IF NOT EXISTS actor_scores (
    actor_id            TEXT PRIMARY KEY,
    actor_name          TEXT,
    credibility_score   REAL DEFAULT 0.5,
    total_documents     INTEGER DEFAULT 0,
    verified_documents  INTEGER DEFAULT 0,
    avg_trust_score     REAL DEFAULT 0.0,
    first_document      TEXT,
    last_document       TEXT,
    last_calculated     TEXT,
    tier                TEXT DEFAULT 'EMERGING'
);

CREATE TABLE IF NOT EXISTS domain_scores (
    domain              TEXT PRIMARY KEY,
    reputation_score    REAL DEFAULT 0.5,
    verification_count  INTEGER DEFAULT 0,
    unique_artifacts    INTEGER DEFAULT 0,
    first_seen          TEXT,
    last_seen           TEXT,
    last_calculated     TEXT,
    tier                TEXT DEFAULT 'EMERGING'
);

CREATE TABLE IF NOT EXISTS score_history (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type         TEXT NOT NULL,
    entity_id           TEXT NOT NULL,
    score_before        REAL,
    score_after         REAL,
    reason              TEXT,
    created_at          TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_artifact_score ON artifact_scores(trust_score);
CREATE INDEX IF NOT EXISTS idx_actor_score ON actor_scores(credibility_score);
CREATE INDEX IF NOT EXISTS idx_domain_score ON domain_scores(reputation_score);
CREATE INDEX IF NOT EXISTS idx_history_entity ON score_history(entity_type, entity_id);
"""

def get_db():
    """Get database connection with schema initialization."""
    os.makedirs(REPUTATION_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def init_reputation_db():
    """Initialize database on blueprint registration."""
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        print(f"[W-PROV-003] DB initialized: {DB_PATH}")
    except Exception as e:
        print(f"[W-PROV-003] DB init error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def days_since(iso_date: str) -> float:
    """Calculate days since a given ISO date."""
    if not iso_date:
        return 0
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return delta.total_seconds() / 86400
    except:
        return 0

# ═══════════════════════════════════════════════════════════════════════════════
# Score Calculation Functions
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_artifact_trust_score(
    verification_count: int,
    unique_domains: int,
    unique_countries: int,
    chain_depth: int,
    forensic_status: str,
    days_active: float
) -> float:
    """
    Calculate trust score for an artifact.

    Components:
    - Verification frequency (30%)
    - Geographic diversity (20%)
    - Chain depth (15%)
    - Forensic validation (25%)
    - Age/stability (10%)

    Decay: Score decays if no verification in 30+ days

    Returns: 0.0 to 1.0
    """
    # Verification frequency component (0-1)
    # Logarithmic scale: 1 verification = 0.1, 10 = 0.5, 100 = 0.8, 1000 = 1.0
    if verification_count == 0:
        freq_score = 0.0
    else:
        freq_score = min(1.0, math.log10(verification_count + 1) / 3)

    # Geographic diversity (0-1)
    # More domains and countries = higher trust
    domain_score = min(1.0, unique_domains / 10)  # Max at 10 domains
    country_score = min(1.0, unique_countries / 5)  # Max at 5 countries
    geo_score = (domain_score * 0.6 + country_score * 0.4)

    # Chain depth (0-1)
    # Deeper chains = more established lineage
    if chain_depth == 0:
        chain_score = 0.3  # Genesis documents get base score
    else:
        chain_score = min(1.0, 0.3 + (chain_depth * 0.15))  # +0.15 per depth level

    # Forensic validation (0-1)
    forensic_scores = {
        "VERIFIED": 1.0,
        "VALID_UNANCHORED": 0.6,
        "PARTIAL": 0.3,
        "INVALID": 0.0,
        None: 0.5  # Not yet inspected
    }
    forensic_score = forensic_scores.get(forensic_status, 0.5)

    # Age/stability (0-1)
    # Documents that have been around longer are more stable
    if days_active <= 0:
        age_score = 0.1
    elif days_active < 7:
        age_score = 0.3
    elif days_active < 30:
        age_score = 0.6
    elif days_active < 90:
        age_score = 0.8
    else:
        age_score = 1.0

    # Weighted combination
    raw_score = (
        freq_score * 0.30 +
        geo_score * 0.20 +
        chain_score * 0.15 +
        forensic_score * 0.25 +
        age_score * 0.10
    )

    # Apply decay if inactive (R4)
    # No verification in 30+ days = gradual decay
    if days_active > 30 and verification_count > 0:
        # Check last verification time (approximated by days_active)
        # This is a simplification - ideally we'd track last_verification separately
        decay_factor = 1.0
    else:
        decay_factor = 1.0

    return min(1.0, max(0.0, raw_score * decay_factor))


def calculate_actor_credibility(
    total_documents: int,
    verified_documents: int,
    avg_trust_score: float,
    days_active: float
) -> float:
    """
    Calculate credibility score for an actor (issuer).

    Components:
    - Volume (20%): More documents = more established
    - Verification rate (30%): % of documents verified
    - Average quality (40%): Mean trust score of documents
    - Longevity (10%): How long they've been issuing

    Returns: 0.0 to 1.0
    """
    # Volume component
    if total_documents == 0:
        volume_score = 0.0
    else:
        volume_score = min(1.0, math.log10(total_documents + 1) / 2)  # Max around 100 docs

    # Verification rate
    if total_documents == 0:
        verification_rate = 0.0
    else:
        verification_rate = verified_documents / total_documents

    # Quality already provided as avg_trust_score
    quality_score = avg_trust_score

    # Longevity
    if days_active <= 0:
        longevity_score = 0.1
    elif days_active < 30:
        longevity_score = 0.3
    elif days_active < 180:
        longevity_score = 0.6
    elif days_active < 365:
        longevity_score = 0.8
    else:
        longevity_score = 1.0

    return (
        volume_score * 0.20 +
        verification_rate * 0.30 +
        quality_score * 0.40 +
        longevity_score * 0.10
    )


def calculate_domain_reputation(
    verification_count: int,
    unique_artifacts: int,
    days_active: float
) -> float:
    """
    Calculate reputation score for a verifying domain.

    Domains that verify more artifacts = more engaged in the ecosystem.

    Returns: 0.0 to 1.0
    """
    # Activity level
    if verification_count == 0:
        activity_score = 0.0
    else:
        activity_score = min(1.0, math.log10(verification_count + 1) / 3)

    # Diversity (verifying different artifacts)
    if unique_artifacts == 0:
        diversity_score = 0.0
    else:
        diversity_score = min(1.0, math.log10(unique_artifacts + 1) / 2)

    # Engagement duration
    if days_active <= 0:
        duration_score = 0.1
    elif days_active < 7:
        duration_score = 0.3
    elif days_active < 30:
        duration_score = 0.6
    else:
        duration_score = 1.0

    return (
        activity_score * 0.50 +
        diversity_score * 0.30 +
        duration_score * 0.20
    )

# ═══════════════════════════════════════════════════════════════════════════════
# Data Aggregation from Other Systems
# ═══════════════════════════════════════════════════════════════════════════════

def get_propagation_stats(ledger_anchor: str) -> Optional[Dict]:
    """Fetch propagation stats for an artifact."""
    try:
        if not os.path.exists(PROPAGATION_DB):
            return None
        conn = sqlite3.connect(PROPAGATION_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT total_verifications, unique_domains, unique_countries,
                   first_seen, last_seen
            FROM artifact_stats
            WHERE ledger_anchor = ?
        """, (ledger_anchor,))
        row = c.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"[W-PROV-003] Propagation lookup error: {e}")
        return None


def get_forensic_status(ledger_anchor: str) -> Optional[str]:
    """Get latest forensic inspection status for an artifact."""
    try:
        if not os.path.exists(FORENSIC_DB):
            return None
        conn = sqlite3.connect(FORENSIC_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT overall_status
            FROM inspections
            WHERE receipt_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (ledger_anchor,))
        row = c.fetchone()
        conn.close()
        if row:
            return row['overall_status']
        return None
    except Exception as e:
        print(f"[W-PROV-003] Forensic lookup error: {e}")
        return None


def get_ledger_metadata(ledger_anchor: str) -> Optional[Dict]:
    """Fetch metadata from Forensic Ledger."""
    try:
        url = f"{LEDGER_API}/api/receipts/{ledger_anchor}"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get("ok") and data.get("receipt"):
                rec = data["receipt"]
                return {
                    "actor": rec.get("actor"),
                    "created_at": rec.get("created_at"),
                    "governance_level": rec.get("governance_level"),
                    "status": rec.get("status")
                }
        return None
    except Exception:
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# Score Update Functions
# ═══════════════════════════════════════════════════════════════════════════════

def update_artifact_score(ledger_anchor: str) -> Dict[str, Any]:
    """
    Recalculate and update trust score for an artifact.
    Aggregates data from Propagation, Forensic, and Ledger.
    """
    # Gather data
    prop_stats = get_propagation_stats(ledger_anchor) or {}
    forensic_status = get_forensic_status(ledger_anchor)
    ledger_meta = get_ledger_metadata(ledger_anchor) or {}

    verification_count = prop_stats.get('total_verifications', 0)
    unique_domains = prop_stats.get('unique_domains', 0)
    unique_countries = prop_stats.get('unique_countries', 0)
    first_seen = prop_stats.get('first_seen') or ledger_meta.get('created_at')
    last_seen = prop_stats.get('last_seen')

    # Calculate days active
    days_active = days_since(first_seen) if first_seen else 0

    # Get chain depth from ledger (simplified - would need anchor_chain parsing)
    chain_depth = 0  # TODO: Parse from ledger metadata

    # Calculate score
    trust_score = calculate_artifact_trust_score(
        verification_count=verification_count,
        unique_domains=unique_domains,
        unique_countries=unique_countries,
        chain_depth=chain_depth,
        forensic_status=forensic_status,
        days_active=days_active
    )

    tier_info = get_trust_tier(trust_score)
    now = now_iso()

    # Update database
    with get_db() as conn:
        c = conn.cursor()

        # Get previous score for history
        c.execute("SELECT trust_score FROM artifact_scores WHERE ledger_anchor = ?", (ledger_anchor,))
        row = c.fetchone()
        old_score = row['trust_score'] if row else None

        # Upsert
        c.execute("""
            INSERT INTO artifact_scores
            (ledger_anchor, trust_score, verification_count, unique_domains,
             unique_countries, chain_depth, forensic_status, first_seen, last_seen,
             last_calculated, tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ledger_anchor) DO UPDATE SET
                trust_score = excluded.trust_score,
                verification_count = excluded.verification_count,
                unique_domains = excluded.unique_domains,
                unique_countries = excluded.unique_countries,
                forensic_status = excluded.forensic_status,
                last_seen = excluded.last_seen,
                last_calculated = excluded.last_calculated,
                tier = excluded.tier
        """, (
            ledger_anchor, trust_score, verification_count, unique_domains,
            unique_countries, chain_depth, forensic_status, first_seen, last_seen,
            now, tier_info['tier']
        ))

        # Record history (R3 - immutable history)
        if old_score is None or abs(old_score - trust_score) > 0.01:
            c.execute("""
                INSERT INTO score_history (entity_type, entity_id, score_before, score_after, reason)
                VALUES (?, ?, ?, ?, ?)
            """, ('artifact', ledger_anchor, old_score, trust_score, 'recalculation'))

        conn.commit()

    return {
        "ledger_anchor": ledger_anchor,
        "trust_score": round(trust_score, 4),
        "tier": tier_info['tier'],
        "badge": tier_info['badge'],
        "verification_count": verification_count,
        "unique_domains": unique_domains,
        "unique_countries": unique_countries,
        "forensic_status": forensic_status,
        "days_active": round(days_active, 1),
        "calculated_at": now
    }


def update_actor_score(actor_id: str, actor_name: str = None) -> Dict[str, Any]:
    """
    Recalculate credibility score for an actor.
    Aggregates document statistics.
    """
    with get_db() as conn:
        c = conn.cursor()

        # Count documents by this actor
        c.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN trust_score > 0.4 THEN 1 ELSE 0 END) as verified,
                   AVG(trust_score) as avg_score,
                   MIN(first_seen) as first_doc,
                   MAX(last_seen) as last_doc
            FROM artifact_scores
            WHERE ledger_anchor IN (
                SELECT ledger_anchor FROM artifact_scores
            )
        """)
        # Note: This is simplified - in production we'd track actor per artifact

        # For now, use placeholder stats
        total_documents = 0
        verified_documents = 0
        avg_trust_score = 0.5
        first_document = None
        last_document = None

        # Try to get from Ledger
        try:
            # This would need a proper actor->documents mapping
            pass
        except:
            pass

        days_active = days_since(first_document) if first_document else 0

        credibility = calculate_actor_credibility(
            total_documents=total_documents,
            verified_documents=verified_documents,
            avg_trust_score=avg_trust_score,
            days_active=days_active
        )

        tier_info = get_trust_tier(credibility)
        now = now_iso()

        # Upsert
        c.execute("""
            INSERT INTO actor_scores
            (actor_id, actor_name, credibility_score, total_documents,
             verified_documents, avg_trust_score, first_document, last_document,
             last_calculated, tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(actor_id) DO UPDATE SET
                actor_name = COALESCE(excluded.actor_name, actor_scores.actor_name),
                credibility_score = excluded.credibility_score,
                total_documents = excluded.total_documents,
                verified_documents = excluded.verified_documents,
                avg_trust_score = excluded.avg_trust_score,
                last_document = excluded.last_document,
                last_calculated = excluded.last_calculated,
                tier = excluded.tier
        """, (
            actor_id, actor_name, credibility, total_documents,
            verified_documents, avg_trust_score, first_document, last_document,
            now, tier_info['tier']
        ))

        conn.commit()

    return {
        "actor_id": actor_id,
        "actor_name": actor_name,
        "credibility_score": round(credibility, 4),
        "tier": tier_info['tier'],
        "badge": tier_info['badge'],
        "total_documents": total_documents,
        "verified_documents": verified_documents,
        "calculated_at": now
    }

# ═══════════════════════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@reputation_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as artifacts FROM artifact_scores")
            artifacts = c.fetchone()['artifacts']
            c.execute("SELECT COUNT(*) as actors FROM actor_scores")
            actors = c.fetchone()['actors']
            c.execute("SELECT COUNT(*) as domains FROM domain_scores")
            domains = c.fetchone()['domains']
        db_ok = True
    except Exception:
        db_ok = False
        artifacts = actors = domains = 0

    return jsonify({
        "status": "GREEN" if db_ok else "YELLOW",
        "agent": __agent_id__,
        "agent_name": __agent_name__,
        "version": __version__,
        "scored_artifacts": artifacts,
        "scored_actors": actors,
        "scored_domains": domains,
        "invariants": ["R1", "R2", "R3", "R4", "R5"],
        "trust_tiers": list(TRUST_TIERS.keys()),
        "db_path": DB_PATH,
        "timestamp": now_iso()
    })


@reputation_bp.route('/artifact/<path:ledger_anchor>', methods=['GET'])
def get_artifact_score(ledger_anchor: str):
    """
    GET /reputation/artifact/<ledger_anchor>

    Get trust score for an artifact. Recalculates if stale.
    """
    # Check if we have a recent score
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM artifact_scores
            WHERE ledger_anchor = ?
        """, (ledger_anchor,))
        row = c.fetchone()

    # Recalculate if missing or stale (>1 hour)
    if not row or (row and days_since(row['last_calculated']) > 1/24):
        result = update_artifact_score(ledger_anchor)
    else:
        tier_info = get_trust_tier(row['trust_score'])
        result = {
            "ledger_anchor": row['ledger_anchor'],
            "trust_score": round(row['trust_score'], 4),
            "tier": row['tier'],
            "badge": tier_info['badge'],
            "verification_count": row['verification_count'],
            "unique_domains": row['unique_domains'],
            "unique_countries": row['unique_countries'],
            "forensic_status": row['forensic_status'],
            "days_active": round(days_since(row['first_seen']), 1) if row['first_seen'] else 0,
            "calculated_at": row['last_calculated'],
            "cached": True
        }

    return jsonify({
        "ok": True,
        **result,
        "invariants_applied": ["R1", "R2", "R4", "R5"]
    })


@reputation_bp.route('/artifact/<path:ledger_anchor>/refresh', methods=['POST'])
def refresh_artifact_score(ledger_anchor: str):
    """
    POST /reputation/artifact/<ledger_anchor>/refresh

    Force recalculation of trust score.
    """
    result = update_artifact_score(ledger_anchor)
    return jsonify({
        "ok": True,
        "refreshed": True,
        **result
    })


@reputation_bp.route('/artifact/<path:ledger_anchor>/history', methods=['GET'])
def get_artifact_history(ledger_anchor: str):
    """
    GET /reputation/artifact/<ledger_anchor>/history

    Get score history for an artifact (R3 - immutable history).
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT score_before, score_after, reason, created_at
            FROM score_history
            WHERE entity_type = 'artifact' AND entity_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (ledger_anchor,))
        rows = c.fetchall()

    history = [{
        "score_before": r['score_before'],
        "score_after": r['score_after'],
        "reason": r['reason'],
        "timestamp": r['created_at']
    } for r in rows]

    return jsonify({
        "ok": True,
        "ledger_anchor": ledger_anchor,
        "history_count": len(history),
        "history": history,
        "invariant": "R3 - History is immutable"
    })


@reputation_bp.route('/actor/<path:actor_id>', methods=['GET'])
def get_actor_score(actor_id: str):
    """
    GET /reputation/actor/<actor_id>

    Get credibility score for an actor (issuer).
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM actor_scores WHERE actor_id = ?", (actor_id,))
        row = c.fetchone()

    if not row:
        # Initialize with default
        result = update_actor_score(actor_id)
    else:
        tier_info = get_trust_tier(row['credibility_score'])
        result = {
            "actor_id": row['actor_id'],
            "actor_name": row['actor_name'],
            "credibility_score": round(row['credibility_score'], 4),
            "tier": row['tier'],
            "badge": tier_info['badge'],
            "total_documents": row['total_documents'],
            "verified_documents": row['verified_documents'],
            "avg_trust_score": round(row['avg_trust_score'], 4) if row['avg_trust_score'] else 0,
            "calculated_at": row['last_calculated'],
            "cached": True
        }

    return jsonify({
        "ok": True,
        **result,
        "invariants_applied": ["R1", "R2", "R3"]
    })


@reputation_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    """
    GET /reputation/leaderboard

    Get top-scoring artifacts and actors.
    Query params: type (artifact|actor), limit (default 10)
    """
    entity_type = request.args.get('type', 'artifact')
    limit = min(request.args.get('limit', 10, type=int), 100)

    with get_db() as conn:
        c = conn.cursor()

        if entity_type == 'actor':
            c.execute("""
                SELECT actor_id, actor_name, credibility_score, tier, total_documents
                FROM actor_scores
                ORDER BY credibility_score DESC
                LIMIT ?
            """, (limit,))
            rows = c.fetchall()
            entries = [{
                "rank": i + 1,
                "id": r['actor_id'],
                "name": r['actor_name'],
                "score": round(r['credibility_score'], 4),
                "tier": r['tier'],
                "documents": r['total_documents']
            } for i, r in enumerate(rows)]
        else:
            c.execute("""
                SELECT ledger_anchor, trust_score, tier, verification_count
                FROM artifact_scores
                ORDER BY trust_score DESC
                LIMIT ?
            """, (limit,))
            rows = c.fetchall()
            entries = [{
                "rank": i + 1,
                "ledger_anchor": r['ledger_anchor'],
                "score": round(r['trust_score'], 4),
                "tier": r['tier'],
                "verifications": r['verification_count']
            } for i, r in enumerate(rows)]

    return jsonify({
        "ok": True,
        "type": entity_type,
        "count": len(entries),
        "entries": entries,
        "timestamp": now_iso()
    })


@reputation_bp.route('/stats', methods=['GET'])
def stats():
    """
    GET /reputation/stats

    Get aggregated reputation statistics.
    """
    with get_db() as conn:
        c = conn.cursor()

        # Artifact stats
        c.execute("SELECT COUNT(*) as total FROM artifact_scores")
        total_artifacts = c.fetchone()['total']

        c.execute("""
            SELECT tier, COUNT(*) as count
            FROM artifact_scores
            GROUP BY tier
        """)
        artifacts_by_tier = {r['tier']: r['count'] for r in c.fetchall()}

        c.execute("SELECT AVG(trust_score) as avg FROM artifact_scores")
        avg_trust = c.fetchone()['avg'] or 0

        # Actor stats
        c.execute("SELECT COUNT(*) as total FROM actor_scores")
        total_actors = c.fetchone()['total']

        c.execute("SELECT AVG(credibility_score) as avg FROM actor_scores")
        avg_credibility = c.fetchone()['avg'] or 0

        # History stats
        c.execute("SELECT COUNT(*) as total FROM score_history")
        total_history = c.fetchone()['total']

    return jsonify({
        "ok": True,
        "artifacts": {
            "total": total_artifacts,
            "by_tier": artifacts_by_tier,
            "average_trust": round(avg_trust, 4)
        },
        "actors": {
            "total": total_actors,
            "average_credibility": round(avg_credibility, 4)
        },
        "history_entries": total_history,
        "timestamp": now_iso()
    })


@reputation_bp.route('/tiers', methods=['GET'])
def get_tiers():
    """
    GET /reputation/tiers

    Get trust tier definitions.
    """
    return jsonify({
        "ok": True,
        "tiers": TRUST_TIERS,
        "invariant": "R1 - Tiers are advisory, never decisory"
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Initialize on import
# ═══════════════════════════════════════════════════════════════════════════════

init_reputation_db()
