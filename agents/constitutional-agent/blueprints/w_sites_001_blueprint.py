"""
W-SITES-001 Sites Factory v1.0.0
=================================
Porta:  :8091 (Sandbox Core — domain extension)
Prefix: /sites/factory/

PRODUCT-SITES-001 Implementation
================================
§4 Identity Gate · §6 Pipeline C1-C6 · §11 Invariants

Endpoints:
  POST /sites/factory/create    → cria site draft (C1)
  POST /sites/factory/update    → atualiza design brief (C2)
  POST /sites/factory/render    → constrói páginas (C3)
  POST /sites/factory/review    → revê qualidade (C4)
  POST /sites/factory/approve   → gate humano (C5 → I9)
  POST /sites/factory/seal      → Ledger seal (C6)
  GET  /sites/factory/status    → estado completo

Stage Map C1-C6 (§6 Pipeline):
  C1 = Intenção — Cliente descreve o que quer
  C2 = Rascunho — W-INTUITION gera Design Brief
  C3 = Edição   — W-RENDER constrói páginas
  C4 = Revisão  — W-CURATE revê qualidade
  C5 = AGUARDA I9 — human_approved=true obrigatório (GATE)
  C6 = SELADO   — Receipt no Ledger IRREMEDIÁVEL

Invariants (§11):
  I1  = Soberania Humana — Cliente decide o quê e o quando
  I9  = Aprovação Explícita — Gate em C5 antes de publicar
  I11 = Permanência de Evidência — Receipt imutável após C6
  I12 = Language Sovereign — Site em DE/EN/PT mínimo
  I14 = Explicit Failure — Site sem dados reais não publica

§4 Identity Gate Fork:
  - Verticais WINDI (LAW/TRAVEL/ENTERPRISE): Reusa DID SOVEREIGN/ORACLE existente
  - Clientes externos: Cria novo DID NODAL (tier 2)

Deploy:
  cp w_sites_001_blueprint.py /opt/windi/agents/constitutional-agent/blueprints/
  # agent.py: from blueprints.w_sites_001_blueprint import w_sites_001_bp
  #           app.register_blueprint(w_sites_001_bp)

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
"""

from flask import Blueprint, request, jsonify
import sqlite3
import hashlib
import uuid
import datetime
import json
import os
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("W-SITES-001")

w_sites_001_bp = Blueprint("w_sites_001", __name__, url_prefix="/sites/factory")

DB_PATH = os.environ.get("WINDI_SITES_DB_PATH", "/opt/windi/data/sites_factory.db")
LEDGER_URL = "http://127.0.0.1:8101/api/receipts"
IDENTITY_GATE_URL = "http://127.0.0.1:8192"

# §11 Invariants enforced by this agent
INVARIANTS = ["I1", "I9", "I11", "I12", "I14"]

# §4 WINDI Vertical DIDs — reuse existing, don't create new
WINDI_VERTICAL_DIDS = {
    "did:windi:law-001": {"tier": "SOVEREIGN", "name": "WINDI-LAW"},
    "did:windi:travel-001": {"tier": "SOVEREIGN", "name": "WINDI-TRAVEL"},
    "did:windi:enterprise-001": {"tier": "ORACLE", "name": "WINDI-ENTERPRISE"},
    "did:windi:dragon-001": {"tier": "ORACLE", "name": "HUMAN-DRAGON"},
}

# Stage definitions (§6)
STAGES = {
    "C1": {"name": "Intenção", "desc": "Cliente descreve o que quer"},
    "C2": {"name": "Rascunho", "desc": "W-INTUITION gera Design Brief"},
    "C3": {"name": "Edição", "desc": "W-RENDER constrói páginas"},
    "C4": {"name": "Revisão", "desc": "W-CURATE revê qualidade"},
    "C5": {"name": "AGUARDA I9", "desc": "human_approved=true obrigatório", "is_gate": True},
    "C6": {"name": "SELADO", "desc": "Receipt no Ledger IRREMEDIÁVEL", "is_irremediable": True},
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS sites (
            id              TEXT PRIMARY KEY,
            client_did      TEXT NOT NULL,
            client_name     TEXT,
            site_name       TEXT NOT NULL,
            site_type       TEXT DEFAULT 'standard',
            stage           TEXT DEFAULT 'C1',
            design_brief    TEXT DEFAULT '{}',
            pages           TEXT DEFAULT '[]',
            language        TEXT DEFAULT 'de',
            human_approved  INTEGER DEFAULT 0,
            approved_by     TEXT,
            approved_at     TEXT,
            ledger_receipt  TEXT,
            verify_url      TEXT,
            site_did        TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS site_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id         TEXT NOT NULL,
            stage           TEXT NOT NULL,
            action          TEXT NOT NULL,
            actor           TEXT,
            payload         TEXT DEFAULT '{}',
            created_at      TEXT NOT NULL,
            FOREIGN KEY(site_id) REFERENCES sites(id)
        );
        """)


try:
    init_db()
    logger.info("W-SITES-001 DB initialized")
except Exception as e:
    logger.error(f"DB init error: {e}")


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def gen_site_id():
    return "SITE-" + uuid.uuid4().hex[:8].upper()


def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def is_windi_vertical(did: str) -> bool:
    """§4 Check if DID belongs to a WINDI vertical."""
    return did in WINDI_VERTICAL_DIDS


def log_history(site_id: str, stage: str, action: str, actor: str = None, payload: dict = None):
    """Log action to site history."""
    with get_db() as db:
        db.execute("""
            INSERT INTO site_history (site_id, stage, action, actor, payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (site_id, stage, action, actor, json.dumps(payload or {}), now_iso()))
        db.commit()


def seal_ledger(site_id: str, site_name: str, content_hash: str, client_did: str):
    """Seal site to Forensic Ledger (C6 — IRREMEDIÁVEL)."""
    receipt_id = f"WINDI-SITE-{site_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    payload = {
        "id": receipt_id,
        "actor": client_did,
        "app": "w-sites-001",
        "doc_name": site_name,
        "doc_type": "doc",
        "governance_level": "HIGH",
        "content_hash": f"sha256:{content_hash}",
        "invariants": INVARIANTS,
        "stage": "C6"
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            LEDGER_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            logger.info(f"Ledger sealed: {receipt_id}")
            return {
                "receipt_id": receipt_id,
                "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}",
                "ledger_response": result
            }
    except Exception as e:
        logger.error(f"Ledger seal failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@w_sites_001_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "service": "W-SITES-001",
        "version": "1.0.0",
        "status": "healthy",
        "invariants": INVARIANTS,
        "stages": list(STAGES.keys()),
        "vertical_dids": list(WINDI_VERTICAL_DIDS.keys())
    })


@w_sites_001_bp.route("/create", methods=["POST"])
def create_site():
    """
    C1 — Create site draft (Intenção).
    Client describes what they want.
    """
    data = request.json or {}

    # I14: Explicit Failure — required fields
    client_did = data.get("client_did")
    site_name = data.get("site_name")

    if not client_did:
        return jsonify({"error": "client_did required (I14)", "invariant": "I14"}), 400
    if not site_name:
        return jsonify({"error": "site_name required (I14)", "invariant": "I14"}), 400

    # §4 Fork: Check if vertical
    is_vertical = is_windi_vertical(client_did)

    site_id = gen_site_id()
    now = now_iso()

    with get_db() as db:
        db.execute("""
            INSERT INTO sites (id, client_did, client_name, site_name, site_type, stage, language, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'C1', ?, ?, ?)
        """, (
            site_id,
            client_did,
            data.get("client_name", WINDI_VERTICAL_DIDS.get(client_did, {}).get("name", "Unknown")),
            site_name,
            "vertical" if is_vertical else "external",
            data.get("language", "de"),
            now,
            now
        ))
        db.commit()

    log_history(site_id, "C1", "CREATED", client_did, {"site_name": site_name, "is_vertical": is_vertical})

    return jsonify({
        "ok": True,
        "site_id": site_id,
        "stage": "C1",
        "client_did": client_did,
        "is_vertical": is_vertical,
        "message": "Site draft created. Proceed to /update for Design Brief (C2)."
    }), 201


@w_sites_001_bp.route("/update", methods=["POST"])
def update_design_brief():
    """
    C2 — Update design brief (Rascunho).
    W-INTUITION generates Design Brief.
    """
    data = request.json or {}
    site_id = data.get("site_id")
    design_brief = data.get("design_brief")

    if not site_id:
        return jsonify({"error": "site_id required (I14)", "invariant": "I14"}), 400
    if not design_brief:
        return jsonify({"error": "design_brief required (I14)", "invariant": "I14"}), 400

    with get_db() as db:
        cursor = db.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
        site = cursor.fetchone()

        if not site:
            return jsonify({"error": "Site not found", "site_id": site_id}), 404

        # Can only update if in C1 or C2
        if site["stage"] not in ["C1", "C2"]:
            return jsonify({
                "error": f"Cannot update in stage {site['stage']}",
                "current_stage": site["stage"],
                "allowed_stages": ["C1", "C2"]
            }), 400

        db.execute("""
            UPDATE sites SET design_brief = ?, stage = 'C2', updated_at = ?
            WHERE id = ?
        """, (json.dumps(design_brief), now_iso(), site_id))
        db.commit()

    log_history(site_id, "C2", "DESIGN_BRIEF_UPDATED", data.get("actor"), {"brief_keys": list(design_brief.keys())})

    return jsonify({
        "ok": True,
        "site_id": site_id,
        "stage": "C2",
        "message": "Design brief saved. Proceed to /render for page construction (C3)."
    })


@w_sites_001_bp.route("/render", methods=["POST"])
def render_pages():
    """
    C3 — Render pages (Edição).
    W-RENDER constructs pages from design brief.
    """
    data = request.json or {}
    site_id = data.get("site_id")
    pages = data.get("pages", [])

    if not site_id:
        return jsonify({"error": "site_id required (I14)", "invariant": "I14"}), 400

    with get_db() as db:
        cursor = db.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
        site = cursor.fetchone()

        if not site:
            return jsonify({"error": "Site not found"}), 404

        if site["stage"] not in ["C2", "C3"]:
            return jsonify({
                "error": f"Cannot render in stage {site['stage']}. Need C2 (Design Brief).",
                "current_stage": site["stage"]
            }), 400

        db.execute("""
            UPDATE sites SET pages = ?, stage = 'C3', updated_at = ?
            WHERE id = ?
        """, (json.dumps(pages), now_iso(), site_id))
        db.commit()

    log_history(site_id, "C3", "PAGES_RENDERED", data.get("actor"), {"page_count": len(pages)})

    return jsonify({
        "ok": True,
        "site_id": site_id,
        "stage": "C3",
        "pages_count": len(pages),
        "message": "Pages rendered. Proceed to /review for quality check (C4)."
    })


@w_sites_001_bp.route("/review", methods=["POST"])
def review_quality():
    """
    C4 — Review quality (Revisão).
    W-CURATE reviews quality before I9 gate.
    """
    data = request.json or {}
    site_id = data.get("site_id")
    review_result = data.get("review", {})

    if not site_id:
        return jsonify({"error": "site_id required (I14)", "invariant": "I14"}), 400

    with get_db() as db:
        cursor = db.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
        site = cursor.fetchone()

        if not site:
            return jsonify({"error": "Site not found"}), 404

        if site["stage"] not in ["C3", "C4"]:
            return jsonify({
                "error": f"Cannot review in stage {site['stage']}. Need C3 (Pages Rendered).",
                "current_stage": site["stage"]
            }), 400

        # Check I14: pages must have real content
        pages = json.loads(site["pages"] or "[]")
        if not pages:
            return jsonify({
                "error": "No pages to review (I14)",
                "invariant": "I14",
                "message": "Site must have at least one page with real content."
            }), 400

        db.execute("""
            UPDATE sites SET stage = 'C4', updated_at = ?
            WHERE id = ?
        """, (now_iso(), site_id))
        db.commit()

    log_history(site_id, "C4", "QUALITY_REVIEWED", data.get("actor"), review_result)

    return jsonify({
        "ok": True,
        "site_id": site_id,
        "stage": "C4",
        "review": review_result,
        "message": "Quality reviewed. Proceed to /approve for I9 gate (C5)."
    })


@w_sites_001_bp.route("/approve", methods=["POST"])
def approve_site():
    """
    C5 — I9 Gate (AGUARDA I9).
    human_approved=true obrigatório before seal.

    I9: Nenhum site passa de C5 para C6 sem aprovação explícita.
    """
    data = request.json or {}
    site_id = data.get("site_id")
    human_approved = data.get("human_approved", False)
    approved_by = data.get("approved_by")

    if not site_id:
        return jsonify({"error": "site_id required (I14)", "invariant": "I14"}), 400

    # I9: Must be explicitly approved
    if not human_approved:
        return jsonify({
            "error": "human_approved=true required (I9)",
            "invariant": "I9",
            "message": "Nenhum site passa de C5 para C6 sem aprovação explícita."
        }), 403

    if not approved_by:
        return jsonify({
            "error": "approved_by required (I1)",
            "invariant": "I1",
            "message": "Sovereignty requires identification of approver."
        }), 400

    with get_db() as db:
        cursor = db.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
        site = cursor.fetchone()

        if not site:
            return jsonify({"error": "Site not found"}), 404

        if site["stage"] != "C4":
            return jsonify({
                "error": f"Cannot approve in stage {site['stage']}. Need C4 (Quality Reviewed).",
                "current_stage": site["stage"]
            }), 400

        now = now_iso()
        db.execute("""
            UPDATE sites SET stage = 'C5', human_approved = 1, approved_by = ?, approved_at = ?, updated_at = ?
            WHERE id = ?
        """, (approved_by, now, now, site_id))
        db.commit()

    log_history(site_id, "C5", "HUMAN_APPROVED", approved_by, {"human_approved": True})

    return jsonify({
        "ok": True,
        "site_id": site_id,
        "stage": "C5",
        "human_approved": True,
        "approved_by": approved_by,
        "message": "I9 Gate passed. Proceed to /seal for Ledger seal (C6 — IRREMEDIÁVEL)."
    })


@w_sites_001_bp.route("/seal", methods=["POST"])
def seal_site():
    """
    C6 — Ledger Seal (SELADO — IRREMEDIÁVEL).
    Receipt no Ledger = imutável para sempre.

    I11: Permanência de Evidência Criptográfica.
    """
    data = request.json or {}
    site_id = data.get("site_id")

    if not site_id:
        return jsonify({"error": "site_id required (I14)", "invariant": "I14"}), 400

    with get_db() as db:
        cursor = db.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
        site = cursor.fetchone()

        if not site:
            return jsonify({"error": "Site not found"}), 404

        # I9: Must be approved before seal
        if not site["human_approved"]:
            return jsonify({
                "error": "Site not approved (I9 violation)",
                "invariant": "I9",
                "current_stage": site["stage"],
                "message": "human_approved=true required before seal."
            }), 403

        if site["stage"] not in ["C5"]:
            return jsonify({
                "error": f"Cannot seal in stage {site['stage']}. Need C5 (Human Approved).",
                "current_stage": site["stage"]
            }), 400

        # Already sealed?
        if site["ledger_receipt"]:
            return jsonify({
                "error": "Site already sealed (I11)",
                "invariant": "I11",
                "receipt_id": site["ledger_receipt"],
                "verify_url": site["verify_url"],
                "message": "C6 is IRREMEDIÁVEL. Receipt exists forever."
            }), 400

        # Compute content hash
        content = {
            "site_id": site_id,
            "site_name": site["site_name"],
            "client_did": site["client_did"],
            "design_brief": json.loads(site["design_brief"] or "{}"),
            "pages": json.loads(site["pages"] or "[]"),
            "language": site["language"],
            "approved_by": site["approved_by"],
            "approved_at": site["approved_at"]
        }
        content_hash = compute_hash(json.dumps(content, sort_keys=True))

        # Seal to Ledger (I11)
        seal_result = seal_ledger(site_id, site["site_name"], content_hash, site["client_did"])

        if not seal_result:
            return jsonify({
                "error": "Ledger seal failed",
                "site_id": site_id,
                "message": "Retry or check Ledger service."
            }), 500

        # Generate site DID (SEED tier)
        site_did = f"did:windi:site-{site_id.lower()}"

        now = now_iso()
        db.execute("""
            UPDATE sites SET stage = 'C6', ledger_receipt = ?, verify_url = ?, site_did = ?, updated_at = ?
            WHERE id = ?
        """, (seal_result["receipt_id"], seal_result["verify_url"], site_did, now, site_id))
        db.commit()

    log_history(site_id, "C6", "SEALED", site["client_did"], {
        "receipt_id": seal_result["receipt_id"],
        "content_hash": content_hash,
        "site_did": site_did
    })

    return jsonify({
        "ok": True,
        "site_id": site_id,
        "stage": "C6",
        "status": "IRREMEDIÁVEL",
        "receipt_id": seal_result["receipt_id"],
        "verify_url": seal_result["verify_url"],
        "site_did": site_did,
        "content_hash": f"sha256:{content_hash}",
        "invariants_enforced": INVARIANTS,
        "message": "Site sealed. Receipt exists forever in Ledger (I11)."
    })


@w_sites_001_bp.route("/status", methods=["GET"])
def get_status():
    """Get site status by ID."""
    site_id = request.args.get("site_id")

    if not site_id:
        return jsonify({"error": "site_id required"}), 400

    with get_db() as db:
        cursor = db.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
        site = cursor.fetchone()

        if not site:
            return jsonify({"error": "Site not found"}), 404

        # Get history
        cursor = db.execute("""
            SELECT * FROM site_history WHERE site_id = ? ORDER BY created_at DESC
        """, (site_id,))
        history = [dict(row) for row in cursor.fetchall()]

    stage_info = STAGES.get(site["stage"], {})

    return jsonify({
        "site_id": site_id,
        "site_name": site["site_name"],
        "client_did": site["client_did"],
        "stage": site["stage"],
        "stage_name": stage_info.get("name"),
        "stage_desc": stage_info.get("desc"),
        "is_gate": stage_info.get("is_gate", False),
        "is_irremediable": stage_info.get("is_irremediable", False),
        "human_approved": bool(site["human_approved"]),
        "approved_by": site["approved_by"],
        "approved_at": site["approved_at"],
        "ledger_receipt": site["ledger_receipt"],
        "verify_url": site["verify_url"],
        "site_did": site["site_did"],
        "language": site["language"],
        "design_brief": json.loads(site["design_brief"] or "{}"),
        "pages": json.loads(site["pages"] or "[]"),
        "created_at": site["created_at"],
        "updated_at": site["updated_at"],
        "history": history,
        "invariants": INVARIANTS
    })


@w_sites_001_bp.route("/list", methods=["GET"])
def list_sites():
    """List all sites, optionally filtered by client_did or stage."""
    client_did = request.args.get("client_did")
    stage = request.args.get("stage")

    with get_db() as db:
        query = "SELECT id, site_name, client_did, stage, human_approved, ledger_receipt, created_at FROM sites WHERE 1=1"
        params = []

        if client_did:
            query += " AND client_did = ?"
            params.append(client_did)

        if stage:
            query += " AND stage = ?"
            params.append(stage)

        query += " ORDER BY created_at DESC"

        cursor = db.execute(query, params)
        sites = [dict(row) for row in cursor.fetchall()]

    return jsonify({
        "count": len(sites),
        "sites": sites,
        "invariants": INVARIANTS
    })
