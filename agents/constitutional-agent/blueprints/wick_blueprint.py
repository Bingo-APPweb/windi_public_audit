"""
WINDI WICK Agent "Evidence Graph" v0.1.0 — Flask Blueprint
===========================================================

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /wick/* endpoints on :8091.

Features:
- W-WICKTHIS: Publish sealed documents to Evidence Graph
- Artifact management with UI Provenance
- Visibility: private | workspace | public
- Feed forense (public artifacts)
- Evidence Graph with link_edges

Principle: "AI processes. Human decides. WINDI guarantees."

Invariant I12: "Relações entre documentos são evidências.
               Evidências têm prova. Provas são imutáveis."

Version: 0.1.0
Component: W-WICK-001
"""

import hashlib
import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request, Response

__version__ = "0.1.0"
__agent_id__ = "W-WICK-001"
__agent_name__ = "Evidence Graph"

# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "wick_agent.db")

# External services
LEDGER_URL = "http://localhost:8101/api/receipts"
PAGE_AGENT_URL = "http://localhost:8091/page"
VERIFY_PUBLIC_URL = "https://www.windi-domain.com/verify-public/"

# Schema version for migrations
SCHEMA_VERSION = "w-wick-001-v1.0"


# ═══════════════════════════════════════════════════════════════
#  ENUMS & TYPES
# ═══════════════════════════════════════════════════════════════

class Visibility(str, Enum):
    PRIVATE = "private"      # Only author sees
    WORKSPACE = "workspace"  # Team members see
    PUBLIC = "public"        # Forensic feed, anyone sees


class ArtifactType(str, Enum):
    DOC = "doc"
    PAGE = "page"        # NEW: W-PAGE-001 living documents
    MEDIA = "media"
    SNIPPET = "snippet"
    DATASET = "dataset"
    LINK = "link"


class RelationType(str, Enum):
    REFERENCES = "references"
    SUPERSEDES = "supersedes"
    DERIVES_FROM = "derives_from"
    CONTESTS = "contests"
    CONFIRMS = "confirms"
    ANNOTATES = "annotates"


# ═══════════════════════════════════════════════════════════════
#  DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Initialize the WICK database with artifacts and link_edges tables."""
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── Artifacts table (with UI Provenance for pages) ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
            id                  TEXT PRIMARY KEY,
            wick_id             TEXT,
            type                TEXT NOT NULL CHECK(type IN ('doc', 'page', 'media', 'snippet', 'dataset', 'link')),
            title               TEXT NOT NULL,
            description         TEXT,

            -- Authorship
            author_actor_id     TEXT NOT NULL,
            author_name         TEXT,

            -- Source reference
            source_id           TEXT,
            source_type         TEXT,
            page_url            TEXT,

            -- UI Provenance (for type='page')
            html_hash           TEXT,
            css_hash            TEXT,
            js_hash             TEXT,
            combined_hash       TEXT,
            content_hash        TEXT,
            template_version    TEXT,

            -- Ledger integration
            ledger_receipt_id   TEXT,
            ledger_anchor       TEXT,

            -- Visibility (I12 constitutional rule)
            visibility          TEXT DEFAULT 'private' CHECK(visibility IN ('private', 'workspace', 'public')),
            published_at        TEXT,

            -- Metadata
            tags                TEXT,
            metadata            TEXT,
            schema_version      TEXT DEFAULT 'w-wick-001-v1.0',

            -- Timestamps
            created_at          TEXT NOT NULL,
            updated_at          TEXT,

            -- Governance
            governance_level    TEXT DEFAULT 'MED',
            sge_score           REAL DEFAULT 0.95
        )
    """)

    # ── Link Edges table (Evidence Graph relations) ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS link_edges (
            id                  TEXT PRIMARY KEY,
            source_artifact_id  TEXT NOT NULL,
            target_artifact_id  TEXT NOT NULL,
            relation_type       TEXT NOT NULL CHECK(relation_type IN (
                'references', 'supersedes', 'derives_from', 'contests', 'confirms', 'annotates'
            )),

            -- Proof chain (I12)
            relation_hash       TEXT,
            ledger_anchor_id    TEXT,

            -- Metadata
            description         TEXT,
            created_by          TEXT NOT NULL,
            created_at          TEXT NOT NULL,

            -- Constraints
            FOREIGN KEY (source_artifact_id) REFERENCES artifacts(id),
            FOREIGN KEY (target_artifact_id) REFERENCES artifacts(id),
            UNIQUE(source_artifact_id, target_artifact_id, relation_type)
        )
    """)

    # ── Indexes ──
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_visibility ON artifacts(visibility)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_author ON artifacts(author_actor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_wick ON artifacts(wick_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_link_edges_source ON link_edges(source_artifact_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_link_edges_target ON link_edges(target_artifact_id)")

    conn.commit()
    conn.close()

    print(f"  [WICK] Database initialized: {DB_PATH}")


def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Initialize on import
init_db()


# ═══════════════════════════════════════════════════════════════
#  BLUEPRINT
# ═══════════════════════════════════════════════════════════════

wick_bp = Blueprint("wick", __name__, url_prefix="/wick")


# ═══════════════════════════════════════════════════════════════
#  HEALTH & STATUS
# ═══════════════════════════════════════════════════════════════

@wick_bp.route("/health", methods=["GET"])
def health():
    """Health check for WICK agent."""
    conn = get_db()
    stats = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN visibility='public' THEN 1 ELSE 0 END) as public_count,
            SUM(CASE WHEN visibility='workspace' THEN 1 ELSE 0 END) as workspace_count,
            SUM(CASE WHEN visibility='private' THEN 1 ELSE 0 END) as private_count,
            SUM(CASE WHEN type='page' THEN 1 ELSE 0 END) as pages
        FROM artifacts
    """).fetchone()

    edges = conn.execute("SELECT COUNT(*) as count FROM link_edges").fetchone()
    conn.close()

    return jsonify({
        "service": f"WINDI {__agent_name__} v{__version__}",
        "agent_id": __agent_id__,
        "status": "healthy",
        "db": DB_PATH,
        "artifacts": {
            "total": stats["total"] or 0,
            "public": stats["public_count"] or 0,
            "workspace": stats["workspace_count"] or 0,
            "private": stats["private_count"] or 0,
            "pages": stats["pages"] or 0,
        },
        "link_edges": edges["count"] or 0,
        "invariant": "I12 — Web of Proofs",
        "principle": "AI processes. Human decides. WINDI guarantees.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ═══════════════════════════════════════════════════════════════
#  W-WICKTHIS: PUBLISH TO EVIDENCE GRAPH
# ═══════════════════════════════════════════════════════════════

@wick_bp.route("/publish", methods=["POST"])
def publish():
    """
    W-WICKTHIS: Publish a sealed document to the Evidence Graph.

    This is the constitutional moment where the human decides to
    make a document part of the verifiable evidence network.

    Requires:
    - artifact_id: The sealed page/document ID
    - visibility: private | workspace | public
    - confirm: true (I9 Gate - human must explicitly confirm)

    Pipeline:
    1. Validate: page sealed? (ledger_receipt_id NOT NULL)
    2. Validate: confirm === true (I9 Gate)
    3. Create artifact record with type="page"
    4. Attach provenance hashes
    5. Set visibility
    6. Index in Evidence Graph
    7. Return artifact_id, public_url, receipt
    """
    data = request.get_json() or {}

    # Required fields
    artifact_id = data.get("artifact_id") or data.get("page_id")
    visibility = data.get("visibility", "private")
    confirm = data.get("confirm", False)

    # Optional fields
    wick_id = data.get("wick_id")
    author_actor_id = data.get("author_actor_id", "CGO@windi.dev")
    author_name = data.get("author_name", "CGO Human Dragon")
    description = data.get("description", "")
    tags = data.get("tags", [])

    # ── I9 Gate: Human confirmation required ──
    if not confirm:
        return jsonify({
            "error": "I9 VIOLATION: Human confirmation required",
            "message": "Set confirm=true to publish this document. W-WICKTHIS requires explicit human decision.",
            "artifact_id": artifact_id,
        }), 403

    if not artifact_id:
        return jsonify({"error": "artifact_id or page_id required"}), 400

    if visibility not in [v.value for v in Visibility]:
        return jsonify({
            "error": "Invalid visibility",
            "allowed": [v.value for v in Visibility],
        }), 400

    # ── Fetch document data (try W-PAGE-001 first, then Ledger) ──
    import urllib.request
    page_data = None
    source_type = None

    # Try W-PAGE-001 first
    try:
        page_url = f"{PAGE_AGENT_URL}/status/{artifact_id}"
        req = urllib.request.Request(page_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            page_data = json.loads(response.read().decode())
            source_type = "W-PAGE-001"
    except Exception:
        pass  # Will try Ledger next

    # Fallback: Try Forensic Ledger directly
    if not page_data:
        try:
            ledger_url = f"{LEDGER_URL.replace('/api/receipts', '')}/api/receipts/{artifact_id}"
            req = urllib.request.Request(ledger_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as response:
                ledger_response = json.loads(response.read().decode())
                if ledger_response.get("ok") and ledger_response.get("receipt"):
                    receipt = ledger_response["receipt"]
                    # Map Ledger receipt to page_data format
                    page_data = {
                        "id": receipt["id"],
                        "title": receipt.get("doc_name", artifact_id),
                        "doc_type": receipt.get("doc_type", "doc"),
                        "status": receipt.get("status", "sealed"),
                        "receipt_id": receipt["id"],
                        "html_hash": receipt.get("content_hash"),
                        "content_hash": receipt.get("content_hash"),
                        "ledger_anchor": receipt["id"],
                        "created_at": receipt.get("created_at"),
                        "metadata": receipt.get("metadata", {}),
                    }
                    source_type = "LEDGER"
        except Exception:
            pass

    if not page_data:
        return jsonify({
            "error": "Document not found",
            "message": f"Could not find document {artifact_id} in W-PAGE-001 or Forensic Ledger.",
        }), 404

    # ── Validate: Document must be sealed ──
    if page_data.get("status") not in ["sealed", "SEALED"]:
        return jsonify({
            "error": "Document not sealed",
            "message": "Only sealed documents can be published to the Evidence Graph.",
            "current_status": page_data.get("status"),
        }), 400

    # ── Check if already published ──
    conn = get_db()
    existing = conn.execute(
        "SELECT id, visibility FROM artifacts WHERE id = ?",
        (artifact_id,)
    ).fetchone()

    if existing:
        # Already published - check visibility upgrade
        if existing["visibility"] == "public":
            conn.close()
            return jsonify({
                "error": "Already public",
                "message": "Public visibility is irrevocable. Document already in public Evidence Graph.",
                "artifact_id": artifact_id,
            }), 400

        # Update visibility if upgrading
        if visibility == "public" or (visibility == "workspace" and existing["visibility"] == "private"):
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE artifacts
                SET visibility = ?, published_at = ?, updated_at = ?
                WHERE id = ?
            """, (
                visibility,
                datetime.now(timezone.utc).isoformat() if visibility == "public" else None,
                datetime.now(timezone.utc).isoformat(),
                artifact_id,
            ))
            conn.commit()
            conn.close()

            return jsonify({
                "status": "visibility_upgraded",
                "artifact_id": artifact_id,
                "old_visibility": existing["visibility"],
                "new_visibility": visibility,
                "message": "Visibility upgraded successfully.",
                "public_url": f"/p/{artifact_id}" if visibility == "public" else None,
            })

        conn.close()
        return jsonify({
            "status": "already_published",
            "artifact_id": artifact_id,
            "visibility": existing["visibility"],
        })

    # ── Create artifact record ──
    now = datetime.now(timezone.utc).isoformat()

    cursor = conn.cursor()
    # Determine artifact type based on source
    artifact_type = "page" if source_type == "W-PAGE-001" else "doc"
    page_url_value = f"/p/{artifact_id}" if source_type == "W-PAGE-001" else None

    cursor.execute("""
        INSERT INTO artifacts (
            id, wick_id, type, title, description,
            author_actor_id, author_name,
            source_id, source_type, page_url,
            html_hash, css_hash, js_hash, combined_hash, content_hash,
            template_version, ledger_receipt_id, ledger_anchor,
            visibility, published_at, tags, schema_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        artifact_id,
        wick_id,
        artifact_type,
        page_data.get("title", artifact_id),
        description,
        author_actor_id,
        author_name,
        artifact_id,
        source_type,
        page_url_value,
        page_data.get("html_hash") or page_data.get("content_hash"),
        page_data.get("css_hash"),
        page_data.get("js_hash"),
        page_data.get("combined_hash"),
        page_data.get("content_hash"),
        page_data.get("template_version"),
        page_data.get("receipt_id"),
        page_data.get("ledger_anchor"),
        visibility,
        now if visibility == "public" else None,
        json.dumps(tags) if tags else None,
        SCHEMA_VERSION,
        now,
    ))

    conn.commit()
    conn.close()

    # ── Build response ──
    response_data = {
        "status": "published",
        "artifact_id": artifact_id,
        "type": "page",
        "visibility": visibility,
        "title": page_data.get("title"),
        "provenance": {
            "html_hash": page_data.get("html_hash"),
            "combined_hash": page_data.get("combined_hash"),
            "ledger_receipt_id": page_data.get("receipt_id"),
        },
        "urls": {
            "page": f"/p/{artifact_id}",
            "artifact": f"/wick/artifact/{artifact_id}",
            "verify": f"{VERIFY_PUBLIC_URL}?id={artifact_id}",
        },
        "published_at": now,
        "message": f"Document published to Evidence Graph with visibility: {visibility}",
    }

    if visibility == "public":
        response_data["constitutional_note"] = "Public visibility is irrevocable. Only versioning or contestation allowed."

    return jsonify(response_data), 201


# ═══════════════════════════════════════════════════════════════
#  ARTIFACT ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@wick_bp.route("/artifact/<artifact_id>", methods=["GET"])
def get_artifact(artifact_id: str):
    """Get a specific artifact by ID."""
    conn = get_db()
    artifact = conn.execute(
        "SELECT * FROM artifacts WHERE id = ?",
        (artifact_id,)
    ).fetchone()

    if not artifact:
        conn.close()
        return jsonify({"error": "Artifact not found", "id": artifact_id}), 404

    # Get related edges
    edges = conn.execute("""
        SELECT * FROM link_edges
        WHERE source_artifact_id = ? OR target_artifact_id = ?
    """, (artifact_id, artifact_id)).fetchall()

    conn.close()

    return jsonify({
        "artifact": dict(artifact),
        "edges": [dict(e) for e in edges],
        "urls": {
            "page": artifact["page_url"],
            "verify": f"{VERIFY_PUBLIC_URL}?id={artifact_id}",
        },
    })


@wick_bp.route("/artifacts", methods=["GET"])
def list_artifacts():
    """List artifacts with optional filters."""
    visibility = request.args.get("visibility")
    artifact_type = request.args.get("type")
    wick_id = request.args.get("wick_id")
    author = request.args.get("author")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    conn = get_db()
    query = """
        SELECT id, type, title, visibility, author_name,
               page_url, combined_hash, ledger_receipt_id,
               created_at, published_at
        FROM artifacts WHERE 1=1
    """
    params = []

    if visibility:
        query += " AND visibility = ?"
        params.append(visibility)
    if artifact_type:
        query += " AND type = ?"
        params.append(artifact_type)
    if wick_id:
        query += " AND wick_id = ?"
        params.append(wick_id)
    if author:
        query += " AND author_actor_id = ?"
        params.append(author)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    artifacts = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify({
        "artifacts": [dict(a) for a in artifacts],
        "count": len(artifacts),
        "limit": limit,
        "offset": offset,
    })


# ═══════════════════════════════════════════════════════════════
#  FEED FORENSE (PUBLIC ARTIFACTS)
# ═══════════════════════════════════════════════════════════════

@wick_bp.route("/feed", methods=["GET"])
def public_feed():
    """
    Public forensic feed — all public artifacts.

    This is the constitutional transparency layer where
    verified documents are visible to anyone.
    """
    limit = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))
    artifact_type = request.args.get("type")

    conn = get_db()
    query = """
        SELECT id, type, title, author_name, page_url,
               combined_hash, ledger_receipt_id, published_at
        FROM artifacts
        WHERE visibility = 'public'
    """
    params = []

    if artifact_type:
        query += " AND type = ?"
        params.append(artifact_type)

    query += " ORDER BY published_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    artifacts = conn.execute(query, params).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) as count FROM artifacts WHERE visibility = 'public'"
    ).fetchone()["count"]

    conn.close()

    return jsonify({
        "feed": "WINDI Evidence Graph — Public Feed",
        "principle": "Transparency through verifiable evidence",
        "invariant": "I12 — Web of Proofs",
        "artifacts": [
            {
                **dict(a),
                "verify_url": f"{VERIFY_PUBLIC_URL}?id={a['id']}",
            }
            for a in artifacts
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ═══════════════════════════════════════════════════════════════
#  EVIDENCE GRAPH (LINK EDGES)
# ═══════════════════════════════════════════════════════════════

@wick_bp.route("/graph", methods=["GET"])
def evidence_graph():
    """
    Get the Evidence Graph — nodes and edges.

    I12: "Relações entre documentos são evidências.
          Evidências têm prova. Provas são imutáveis."
    """
    visibility = request.args.get("visibility", "public")

    conn = get_db()

    # Get nodes (artifacts)
    nodes = conn.execute("""
        SELECT id, type, title, visibility, combined_hash, ledger_receipt_id
        FROM artifacts
        WHERE visibility = ? OR ? = 'all'
        ORDER BY created_at DESC
        LIMIT 100
    """, (visibility, visibility)).fetchall()

    node_ids = [n["id"] for n in nodes]

    # Get edges between these nodes
    if node_ids:
        placeholders = ",".join(["?" for _ in node_ids])
        edges = conn.execute(f"""
            SELECT * FROM link_edges
            WHERE source_artifact_id IN ({placeholders})
               OR target_artifact_id IN ({placeholders})
        """, node_ids + node_ids).fetchall()
    else:
        edges = []

    conn.close()

    return jsonify({
        "graph": "WINDI Evidence Graph",
        "invariant": "I12 — Web of Proofs",
        "nodes": [dict(n) for n in nodes],
        "edges": [dict(e) for e in edges],
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        "visibility_filter": visibility,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@wick_bp.route("/link", methods=["POST"])
def create_link():
    """
    Create a link between two artifacts.

    I12: Relations are evidence. Evidence has proof.
    """
    data = request.get_json() or {}

    source_id = data.get("source_artifact_id")
    target_id = data.get("target_artifact_id")
    relation_type = data.get("relation_type")
    description = data.get("description", "")
    created_by = data.get("created_by", "CGO@windi.dev")
    confirm = data.get("confirm", False)

    # I9 Gate
    if not confirm:
        return jsonify({
            "error": "I9 VIOLATION: Human confirmation required",
            "message": "Set confirm=true to create this evidence link.",
        }), 403

    if not all([source_id, target_id, relation_type]):
        return jsonify({
            "error": "Missing required fields",
            "required": ["source_artifact_id", "target_artifact_id", "relation_type"],
        }), 400

    if relation_type not in [r.value for r in RelationType]:
        return jsonify({
            "error": "Invalid relation_type",
            "allowed": [r.value for r in RelationType],
        }), 400

    conn = get_db()

    # Verify both artifacts exist
    source = conn.execute("SELECT id FROM artifacts WHERE id = ?", (source_id,)).fetchone()
    target = conn.execute("SELECT id FROM artifacts WHERE id = ?", (target_id,)).fetchone()

    if not source or not target:
        conn.close()
        return jsonify({
            "error": "Artifact not found",
            "source_exists": source is not None,
            "target_exists": target is not None,
        }), 404

    # Create relation hash (I12 proof)
    relation_data = f"{source_id}|{relation_type}|{target_id}|{datetime.now(timezone.utc).isoformat()}"
    relation_hash = hashlib.sha256(relation_data.encode()).hexdigest()

    edge_id = f"EDGE-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc).isoformat()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO link_edges (
                id, source_artifact_id, target_artifact_id, relation_type,
                relation_hash, description, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            edge_id, source_id, target_id, relation_type,
            relation_hash, description, created_by, now,
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({
            "error": "Link already exists",
            "message": f"Relation {relation_type} between these artifacts already exists.",
        }), 409

    conn.close()

    return jsonify({
        "status": "linked",
        "edge_id": edge_id,
        "source": source_id,
        "target": target_id,
        "relation_type": relation_type,
        "relation_hash": relation_hash,
        "created_at": now,
        "invariant": "I12 — This relation is now immutable evidence.",
    }), 201


# ═══════════════════════════════════════════════════════════════
#  GROVE ARENA EVIDENCE SUBMISSION
# ═══════════════════════════════════════════════════════════════

@wick_bp.route("/evidence", methods=["POST"])
def submit_evidence():
    """
    Submit evidence directly from Grove Arena.

    This endpoint allows consultants to publish Grove Parecer
    (consolidated reports) directly to the Evidence Graph without
    requiring a pre-sealed document.

    Payload:
    - title: Topic/title of the consultation
    - content: Full debate + parecer content
    - type: Evidence type (e.g., 'grove_parecer')
    - source: Source identifier (e.g., 'grove-arena')
    - agents: List of participating agents
    - session_id: Grove session ID (optional)

    Returns:
    - evidence_id: Unique evidence identifier
    - content_hash: SHA-256 hash of content
    - created_at: Timestamp
    """
    data = request.get_json() or {}

    title = data.get("title", "Grove Arena Evidence")
    content = data.get("content", "")
    evidence_type = data.get("type", "grove_parecer")
    source = data.get("source", "grove-arena")
    agents = data.get("agents", [])
    session_id = data.get("session_id")
    author_actor_id = data.get("author_actor_id", "CGO@windi.dev")
    author_name = data.get("author_name", "Grove Consultant")
    visibility = data.get("visibility", "workspace")

    if not content:
        return jsonify({"error": "content is required"}), 400

    # Generate evidence ID and content hash
    now = datetime.now(timezone.utc).isoformat()
    evidence_id = f"GE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    # Store metadata
    metadata = {
        "type": evidence_type,
        "source": source,
        "agents": agents,
        "session_id": session_id,
        "content_length": len(content),
    }

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO artifacts (
                id, type, title, description,
                author_actor_id, author_name,
                source_id, source_type,
                content_hash, visibility,
                tags, metadata, schema_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            evidence_id,
            "snippet",  # Using 'snippet' type for text-based evidence
            title[:200],  # Truncate title
            content[:5000],  # Store first 5000 chars as description
            author_actor_id,
            author_name,
            session_id,
            source,
            content_hash,
            visibility,
            json.dumps(agents) if agents else None,
            json.dumps(metadata),
            SCHEMA_VERSION,
            now,
        ))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

    conn.close()

    return jsonify({
        "status": "submitted",
        "evidence_id": evidence_id,
        "id": evidence_id,  # Alias for frontend compatibility
        "content_hash": content_hash,
        "title": title[:200],
        "type": evidence_type,
        "source": source,
        "agents": agents,
        "visibility": visibility,
        "created_at": now,
        "urls": {
            "artifact": f"/wick/artifact/{evidence_id}",
            "feed": "/wick/feed",
        },
        "invariant": "I12 — Evidence recorded in the Graph.",
    }), 201
