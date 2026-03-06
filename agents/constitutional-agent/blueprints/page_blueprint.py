"""
WINDI Page Agent "Sovereign Page Generator" v0.1.0 — Flask Blueprint
======================================================================

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /page/* endpoints on :8091.

Features:
- 4-phase pipeline: PLAN → BUILD → VERIFY → SEAL
- UI Provenance with 5 hashes
- Safety filter (eval/innerHTML rejection)
- Preview with TTL (60 min)
- Ledger integration (:8101)
- Export pipeline (PDF/DOCX/Evidence/JSON)

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 0.1.0
Sealed: W-PAGE-001
"""

import hashlib
import io
import json
import os
import sqlite3
import tempfile
import time
import uuid
import zipfile
from dataclasses import asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request, Response, send_file

# PDF/DOCX exports
try:
    from weasyprint import HTML as WeasyHTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Local imports
from blueprints.page_safety import verify as safety_verify, SafetyResult
from blueprints.page_renderer import (
    render_page, render_card, render_seal_badge, render_ledger_status,
    render_button, render_dragon_orb, render_verification_panel,
    PagePlan, UIProvenance, RenderedPage, compute_provenance,
    generate_page_html, TOKENS_CSS, COMPONENTS_CSS,
)

__version__ = "0.1.0"
__agent_id__ = "W-PAGE-001"
__agent_name__ = "Sovereign Page Generator"

# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "page_agent.db")
PAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pages")
PREVIEWS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "previews")
EXPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")

# Preview TTL in minutes
PREVIEW_TTL_MINUTES = 60

# Ledger API
LEDGER_URL = "http://localhost:8101/api/receipts"

# Verify Public URL
VERIFY_PUBLIC_URL = "https://www.windi-domain.com/verify-public/"


# ═══════════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════════

class PageStatus(Enum):
    PREVIEW = "preview"
    PENDING_SEAL = "pending_seal"
    SEALED = "sealed"


class DocType(Enum):
    LEGAL_EVIDENCE = "legal_evidence"
    NOTARIAL_AUDIT = "notarial_audit"
    COMPLIANCE_REPORT = "compliance_report"
    COMMUNIQUE = "communique"
    FORENSIC_TIMELINE = "forensic_timeline"
    XRECHNUNG = "xrechnung"
    VERIFY_PAGE = "verify_page"
    GENERIC = "generic"


# ═══════════════════════════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Initialize the page_agent database."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PAGES_DIR, exist_ok=True)
    os.makedirs(PREVIEWS_DIR, exist_ok=True)
    os.makedirs(EXPORTS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id              TEXT PRIMARY KEY,
            version         INTEGER DEFAULT 1,
            parent_id       TEXT,
            preview_id      TEXT UNIQUE,
            title           TEXT NOT NULL,
            doc_type        TEXT NOT NULL,
            theme           TEXT DEFAULT 'noir',
            tier            TEXT DEFAULT 'MED',
            wallet_id       TEXT,
            lang            TEXT DEFAULT 'en',

            -- Content
            html_content    TEXT NOT NULL,
            html_size_bytes INTEGER,

            -- UI Provenance
            html_hash       TEXT NOT NULL,
            css_hash        TEXT,
            js_hash         TEXT,
            combined_hash   TEXT,
            content_hash    TEXT,

            -- Template and generator
            template_version TEXT DEFAULT 'windi-ui-v1.0',
            generator        TEXT DEFAULT 'W-PAGE-001 v0.1.0',

            -- Ledger
            ledger_anchor   INTEGER,
            receipt_id      TEXT,

            -- Timestamps
            created_at      TEXT NOT NULL,
            sealed_at       TEXT,
            preview_expires TEXT,

            -- Status
            status          TEXT DEFAULT 'preview',

            -- Constitutional
            invariants      TEXT DEFAULT 'C6,I9,I11',
            safety_passed   INTEGER DEFAULT 0,
            safety_violations TEXT,

            -- Intent (original request)
            intent          TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS page_exports (
            id          TEXT PRIMARY KEY,
            page_id     TEXT REFERENCES pages(id),
            export_type TEXT,
            created_at  TEXT NOT NULL,
            size_bytes  INTEGER,
            downloaded  INTEGER DEFAULT 0
        )
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_wallet ON pages(wallet_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_status ON pages(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_created ON pages(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_preview ON pages(preview_id)")

    conn.commit()
    conn.close()
    print(f"  [Page] Database initialized: {DB_PATH}")


def get_db() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Initialize database on import
init_db()


# ═══════════════════════════════════════════════════════════════
#  BLUEPRINT
# ═══════════════════════════════════════════════════════════════

page_bp = Blueprint("page", __name__, url_prefix="/page")


# ═══════════════════════════════════════════════════════════════
#  HEALTH & STATUS
# ═══════════════════════════════════════════════════════════════

@page_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    conn = get_db()
    stats = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status='sealed' THEN 1 ELSE 0 END) as sealed,
            SUM(CASE WHEN status='preview' THEN 1 ELSE 0 END) as previews
        FROM pages
    """).fetchone()
    conn.close()

    return jsonify({
        "service": f"WINDI {__agent_name__} v{__version__}",
        "agent_id": __agent_id__,
        "status": "healthy",
        "db": DB_PATH,
        "pages": {
            "total": stats["total"] or 0,
            "sealed": stats["sealed"] or 0,
            "previews": stats["previews"] or 0,
        },
        "preview_ttl_minutes": PREVIEW_TTL_MINUTES,
        "principle": "AI processes. Human decides. WINDI guarantees.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@page_bp.route("/status/<page_id>", methods=["GET"])
def page_status(page_id: str):
    """Get status of a specific page."""
    conn = get_db()
    page = conn.execute(
        "SELECT * FROM pages WHERE id = ? OR preview_id = ?",
        (page_id, page_id)
    ).fetchone()
    conn.close()

    if not page:
        return jsonify({"error": "Page not found", "page_id": page_id}), 404

    return jsonify({
        "id": page["id"],
        "preview_id": page["preview_id"],
        "title": page["title"],
        "status": page["status"],
        "doc_type": page["doc_type"],
        "created_at": page["created_at"],
        "sealed_at": page["sealed_at"],
        "html_hash": page["html_hash"],
        "css_hash": page["css_hash"],
        "js_hash": page["js_hash"],
        "combined_hash": page["combined_hash"],
        "content_hash": page["content_hash"],
        "template_version": page["template_version"],
        "receipt_id": page["receipt_id"],
        "ledger_anchor": page["ledger_anchor"],
    })


@page_bp.route("/list", methods=["GET"])
def list_pages():
    """List pages with optional filters."""
    wallet_id = request.args.get("wallet_id")
    status = request.args.get("status")
    limit = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))

    conn = get_db()
    query = "SELECT id, preview_id, title, status, doc_type, created_at, sealed_at, html_hash FROM pages WHERE 1=1"
    params = []

    if wallet_id:
        query += " AND wallet_id = ?"
        params.append(wallet_id)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    pages = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify({
        "pages": [dict(p) for p in pages],
        "limit": limit,
        "offset": offset,
        "count": len(pages),
    })


# ═══════════════════════════════════════════════════════════════
#  PHASE 1-3: GENERATE (PLAN → BUILD → VERIFY)
# ═══════════════════════════════════════════════════════════════

@page_bp.route("/generate", methods=["POST"])
def generate():
    """
    Generate a page from intent.

    Executes phases 1-3: PLAN → BUILD → VERIFY
    Returns preview_id for human review before SEAL (phase 4).
    """
    data = request.get_json() or {}

    # Extract parameters
    intent = data.get("intent", "")
    doc_type = data.get("doc_type", "generic")
    theme = data.get("theme", "noir")
    tier = data.get("tier", "MED")
    wallet_id = data.get("wallet_id", "")
    lang = data.get("lang", "en")
    title = data.get("title", "")

    if not intent and not title:
        return jsonify({
            "error": "Missing required field: intent or title",
            "required": ["intent or title"],
        }), 400

    # ═══ PHASE 1: PLAN ═══
    plan = PagePlan(
        doc_type=doc_type,
        theme=theme,
        title=title or f"WINDI Document — {doc_type}",
        description=intent,
        tier=tier,
        lang=lang,
        components=["windi-card", "seal-badge", "ledger-status", "verification-panel"],
    )

    # ═══ PHASE 2: BUILD ═══
    preview_id = f"prev_{uuid.uuid4().hex[:8]}"

    # Build content based on doc_type
    content_blocks = build_content_for_type(plan, intent, preview_id)

    # Render full page
    rendered = render_page(plan, content_blocks, preview_id)

    # ═══ PHASE 3: VERIFY ═══
    safety_result = safety_verify(rendered.html)

    if not safety_result.passed:
        return jsonify({
            "error": "Safety verification failed",
            "status": "rejected",
            "safety": safety_result.to_dict(),
        }), 400

    # Calculate preview expiry
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=PREVIEW_TTL_MINUTES)

    # Generate page ID
    page_id = f"WINDI-PAGE-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # Save to database
    conn = get_db()
    conn.execute("""
        INSERT INTO pages (
            id, preview_id, title, doc_type, theme, tier, wallet_id, lang,
            html_content, html_size_bytes,
            html_hash, css_hash, js_hash, combined_hash, content_hash,
            template_version, generator,
            created_at, preview_expires, status,
            safety_passed, intent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        page_id, preview_id, plan.title, plan.doc_type, plan.theme, plan.tier,
        wallet_id, plan.lang,
        rendered.html, rendered.provenance.size_bytes,
        rendered.provenance.html_hash, rendered.provenance.css_hash,
        rendered.provenance.js_hash, rendered.provenance.combined_hash,
        rendered.provenance.content_hash,
        rendered.provenance.template_version, rendered.provenance.generator,
        now.isoformat(), expires.isoformat(), PageStatus.PENDING_SEAL.value,
        1, intent,
    ))
    conn.commit()
    conn.close()

    # Save preview HTML to file
    preview_path = os.path.join(PREVIEWS_DIR, f"{preview_id}.html")
    with open(preview_path, 'w', encoding='utf-8') as f:
        f.write(rendered.html)

    # Build consciousness summary
    consciousness_summary = {
        "message": "A tua página está pronta para revisão.",
        "guarantees": [
            f"✓ Safety filter: {len(safety_result.violations)} violações detectadas",
            "✓ HTML válido: estrutura verificada",
            "✓ Design tokens WINDI aplicados",
            "✓ UI Provenance calculada",
            f"✓ Componentes constitucionais: {len(plan.components)} usados",
        ],
        "pending": [
            "⏳ Aguarda a tua confirmação para selar no Ledger"
        ],
        "decision": "Confirmas a publicação deste documento?",
        "seal_url": f"/page/seal/{preview_id}",
        "preview_url": f"/page/preview/{preview_id}",
        "expires_in_minutes": PREVIEW_TTL_MINUTES,
    }

    return jsonify({
        "status": "pending_seal",
        "page_id": page_id,
        "preview_id": preview_id,
        "preview_url": f"/page/preview/{preview_id}",
        "plan": {
            "doc_type": plan.doc_type,
            "components": plan.components,
            "theme": plan.theme,
            "title": plan.title,
        },
        "provenance": rendered.provenance.to_dict(),
        "ttl_minutes": PREVIEW_TTL_MINUTES,
        "seal_url": f"/page/seal/{preview_id}",
        "consciousness_summary": consciousness_summary,
    })


def build_content_for_type(plan: PagePlan, intent: str, preview_id: str) -> List[str]:
    """Build content blocks based on document type."""

    # Common header info
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")

    if plan.doc_type == "legal_evidence":
        return [
            render_card(
                title="Legal Evidence Package",
                subtitle=f"Generated {timestamp}",
                body=f'''
                    <p style="color: var(--w-text-muted); margin-bottom: var(--w-space-4);">
                        {intent or "Legal evidence documentation package."}
                    </p>
                    <div style="display: flex; gap: var(--w-space-4); flex-wrap: wrap;">
                        {render_seal_badge("pending", preview_id[:16] + "...", timestamp)}
                        {render_ledger_status(False)}
                    </div>
                ''',
                elevation="md",
            ),
            render_verification_panel(
                preview_id,
                "Hash will be computed after sealing",
                VERIFY_PUBLIC_URL,
            ),
        ]

    elif plan.doc_type == "compliance_report":
        return [
            render_card(
                title="Compliance Report",
                subtitle=f"WINDI Governance · {timestamp}",
                body=f'''
                    <p style="color: var(--w-text-muted); margin-bottom: var(--w-space-4);">
                        {intent or "Compliance verification report."}
                    </p>
                    <div style="display: flex; gap: var(--w-space-4); align-items: center; flex-wrap: wrap;">
                        {render_dragon_orb("WITNESS")}
                        {render_seal_badge("pending")}
                    </div>
                ''',
                elevation="md",
            ),
        ]

    elif plan.doc_type == "communique":
        return [
            render_card(
                title=plan.title or "Communiqué",
                subtitle=f"WINDI Publishing House · {timestamp}",
                body=f'''
                    <div style="font-family: var(--w-font-serif); font-size: 18px; line-height: 1.8; color: var(--w-text);">
                        {intent or "Official communication."}
                    </div>
                    <div style="margin-top: var(--w-space-6); display: flex; gap: var(--w-space-4); flex-wrap: wrap;">
                        {render_seal_badge("pending")}
                        {render_ledger_status(False)}
                    </div>
                ''',
                elevation="lg",
            ),
        ]

    else:  # generic
        return [
            render_card(
                title=plan.title or "WINDI Document",
                subtitle=f"Generated {timestamp}",
                body=f'''
                    <p style="color: var(--w-text-muted); margin-bottom: var(--w-space-4);">
                        {intent or "Document content."}
                    </p>
                    <div style="display: flex; gap: var(--w-space-4); flex-wrap: wrap; margin-top: var(--w-space-4);">
                        {render_seal_badge("pending")}
                        {render_ledger_status(False)}
                    </div>
                ''',
                elevation="md",
            ),
            render_verification_panel(
                preview_id,
                "Pending verification...",
                VERIFY_PUBLIC_URL,
            ),
        ]


# ═══════════════════════════════════════════════════════════════
#  PREVIEW
# ═══════════════════════════════════════════════════════════════

@page_bp.route("/preview/<preview_id>", methods=["GET"])
def preview(preview_id: str):
    """Serve preview HTML."""
    conn = get_db()
    page = conn.execute(
        "SELECT * FROM pages WHERE preview_id = ?",
        (preview_id,)
    ).fetchone()
    conn.close()

    if not page:
        return jsonify({"error": "Preview not found", "preview_id": preview_id}), 404

    # Check if expired
    if page["status"] == "preview":
        expires = datetime.fromisoformat(page["preview_expires"])
        if datetime.now(timezone.utc) > expires:
            return jsonify({
                "error": "Preview expired",
                "preview_id": preview_id,
                "expired_at": page["preview_expires"],
            }), 410  # Gone

    # Serve HTML
    return Response(
        page["html_content"],
        mimetype="text/html",
        headers={
            "X-WINDI-Preview": "true",
            "X-WINDI-Preview-ID": preview_id,
            "X-WINDI-Status": page["status"],
        }
    )


# ═══════════════════════════════════════════════════════════════
#  PHASE 4: SEAL (requires CGO confirmation)
# ═══════════════════════════════════════════════════════════════

@page_bp.route("/seal/<preview_id>", methods=["POST"])
def seal(preview_id: str):
    """
    Seal a preview page to the Ledger.

    This is PHASE 4 — requires explicit human confirmation.
    C6 applied: AI prepares. Human confirms. WINDI seals.
    """
    data = request.get_json() or {}

    confirm = data.get("confirm", False)
    wallet_id = data.get("wallet_id", "")
    page_title = data.get("page_title")
    impact_level = data.get("impact_level", "MED")

    if not confirm:
        return jsonify({
            "error": "Confirmation required",
            "message": "Set confirm=true to seal this document. C6: Human must explicitly confirm.",
        }), 400

    # Get page from database
    conn = get_db()
    page = conn.execute(
        "SELECT * FROM pages WHERE preview_id = ?",
        (preview_id,)
    ).fetchone()

    if not page:
        conn.close()
        return jsonify({"error": "Preview not found", "preview_id": preview_id}), 404

    if page["status"] == "sealed":
        conn.close()
        return jsonify({
            "error": "Already sealed",
            "page_id": page["id"],
            "receipt_id": page["receipt_id"],
        }), 409

    page_id = page["id"]
    now = datetime.now(timezone.utc)

    # Update title if provided
    if page_title:
        conn.execute(
            "UPDATE pages SET title = ? WHERE id = ?",
            (page_title, page_id)
        )

    # ═══ SEAL TO LEDGER ═══
    import requests

    ledger_payload = {
        "id": page_id,
        "actor": wallet_id or "CGO@windi.dev",
        "app": "pages",
        "doc_name": page_title or page["title"],
        "doc_type": "doc",
        "content_hash": page["html_hash"].replace("sha256:", ""),
        "governance_level": impact_level,
        "sge_score": 0.95,
        "tags": ["living-document", "w-page-001", page["doc_type"]],
        "metadata": {
            "document_type": "W-PAGE-001",
            "combined_hash": page["combined_hash"],
            "generator": page["generator"],
            "theme": page["theme"],
        }
    }

    try:
        ledger_response = requests.post(
            LEDGER_URL,
            json=ledger_payload,
            timeout=10,
        )
        ledger_data = ledger_response.json()

        if not ledger_data.get("ok"):
            conn.close()
            return jsonify({
                "error": "Ledger seal failed",
                "ledger_response": ledger_data,
            }), 500

    except Exception as e:
        conn.close()
        return jsonify({
            "error": "Ledger connection failed",
            "details": str(e),
        }), 500

    # Update database with sealed status
    conn.execute("""
        UPDATE pages SET
            status = ?,
            sealed_at = ?,
            receipt_id = ?,
            wallet_id = ?
        WHERE id = ?
    """, (
        PageStatus.SEALED.value,
        now.isoformat(),
        page_id,  # receipt_id = page_id
        wallet_id,
        page_id,
    ))
    conn.commit()

    # Move preview to permanent pages directory
    preview_path = os.path.join(PREVIEWS_DIR, f"{preview_id}.html")
    pages_path = os.path.join(PAGES_DIR, page_id)
    os.makedirs(pages_path, exist_ok=True)

    # Update HTML with sealed status and save
    sealed_html = page["html_content"].replace(
        'data-status="pending"',
        'data-status="sealed"'
    ).replace(
        'data-verified="false"',
        'data-verified="true"'
    ).replace(
        "UNVERIFIED",
        "ANCHORED"
    ).replace(
        "#—",
        f"#{page_id[-6:]}"
    )

    with open(os.path.join(pages_path, "index.html"), 'w', encoding='utf-8') as f:
        f.write(sealed_html)

    # Save metadata
    meta = {
        "page_id": page_id,
        "title": page_title or page["title"],
        "doc_type": page["doc_type"],
        "created_at": page["created_at"],
        "sealed_at": now.isoformat(),
        "provenance": {
            "html_hash": page["html_hash"],
            "css_hash": page["css_hash"],
            "js_hash": page["js_hash"],
            "combined_hash": page["combined_hash"],
            "content_hash": page["content_hash"],
            "template_version": page["template_version"],
            "generator": page["generator"],
        },
        "receipt_id": page_id,
        "invariants": "C6,I9,I11",
    }

    with open(os.path.join(pages_path, "meta.json"), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    # Clean up preview file
    if os.path.exists(preview_path):
        os.remove(preview_path)

    conn.close()

    return jsonify({
        "status": "sealed",
        "page_id": page_id,
        "page_url": f"/p/{page_id}",
        "receipt_id": page_id,
        "provenance": {
            "html_hash": page["html_hash"],
            "css_hash": page["css_hash"],
            "js_hash": page["js_hash"],
            "combined_hash": page["combined_hash"],
            "content_hash": page["content_hash"],
            "ledger_anchor": page_id,
            "sealed_at": now.isoformat(),
            "receipt_id": page_id,
            "template_version": page["template_version"],
            "generator": page["generator"],
        },
        "exports": {
            "pdf": f"/page/export/pdf/{page_id}",
            "docx": f"/page/export/docx/{page_id}",
            "evidence": f"/page/export/evidence/{page_id}",
            "json": f"/page/export/json/{page_id}",
        },
        "verify_url": f"{VERIFY_PUBLIC_URL}?id={page_id}",
    })


# ═══════════════════════════════════════════════════════════════
#  SERVE SEALED PAGES
# ═══════════════════════════════════════════════════════════════

@page_bp.route("/p/<page_id>", methods=["GET"])
def serve_page(page_id: str):
    """Serve a sealed page."""
    conn = get_db()
    page = conn.execute(
        "SELECT * FROM pages WHERE id = ? AND status = 'sealed'",
        (page_id,)
    ).fetchone()
    conn.close()

    if not page:
        return jsonify({"error": "Page not found or not sealed", "page_id": page_id}), 404

    # Try to serve from file first
    page_path = os.path.join(PAGES_DIR, page_id, "index.html")
    if os.path.exists(page_path):
        with open(page_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    else:
        html_content = page["html_content"]

    return Response(
        html_content,
        mimetype="text/html",
        headers={
            "X-WINDI-Document": page_id,
            "X-WINDI-Hash": page["html_hash"],
            "X-WINDI-Sealed": "true",
            "X-WINDI-Type": "W-PAGE-001",
            "X-WINDI-Living-Document": "true",
            "Cache-Control": "no-cache",
        }
    )


# ═══════════════════════════════════════════════════════════════
#  EXPORT ENDPOINTS (Stubs for FASE D)
# ═══════════════════════════════════════════════════════════════

@page_bp.route("/export/json/<page_id>", methods=["GET"])
def export_json(page_id: str):
    """Export page metadata as JSON."""
    conn = get_db()
    page = conn.execute(
        "SELECT * FROM pages WHERE id = ? AND status = 'sealed'",
        (page_id,)
    ).fetchone()
    conn.close()

    if not page:
        return jsonify({"error": "Page not found or not sealed"}), 404

    return jsonify({
        "page_id": page["id"],
        "title": page["title"],
        "doc_type": page["doc_type"],
        "created_at": page["created_at"],
        "sealed_at": page["sealed_at"],
        "ui_provenance": {
            "html_hash": page["html_hash"],
            "css_hash": page["css_hash"],
            "js_hash": page["js_hash"],
            "combined_hash": page["combined_hash"],
            "content_hash": page["content_hash"],
            "template_version": page["template_version"],
            "generator": page["generator"],
            "ledger_anchor": page["ledger_anchor"],
            "receipt_id": page["receipt_id"],
        },
        "verify_url": f"{VERIFY_PUBLIC_URL}?id={page_id}",
        "exports": {
            "pdf": f"/page/export/pdf/{page_id}",
            "docx": f"/page/export/docx/{page_id}",
            "evidence": f"/page/export/evidence/{page_id}",
        }
    })


@page_bp.route("/export/pdf/<page_id>", methods=["GET"])
def export_pdf(page_id: str):
    """
    Export sealed page as PDF using WeasyPrint.

    The PDF includes:
    - Full HTML content rendered
    - Embedded fonts (system fallback)
    - Footer with page ID and seal timestamp
    """
    if not WEASYPRINT_AVAILABLE:
        return jsonify({
            "error": "PDF export unavailable",
            "message": "WeasyPrint not installed on server",
        }), 503

    conn = get_db()
    page = conn.execute(
        "SELECT * FROM pages WHERE id = ? AND status = 'sealed'",
        (page_id,)
    ).fetchone()
    conn.close()

    if not page:
        return jsonify({"error": "Page not found or not sealed"}), 404

    html_content = page["html_content"]

    # Add PDF-specific styles for printing
    pdf_styles = """
    <style>
    @page {
        size: A4;
        margin: 2cm;
        @bottom-center {
            content: "WINDI Sealed Document — """ + page_id + """";
            font-size: 8pt;
            color: #666;
        }
        @bottom-right {
            content: counter(page);
            font-size: 8pt;
        }
    }
    @media print {
        body {
            background: white !important;
            color: black !important;
        }
        .windi-card {
            break-inside: avoid;
            border: 1px solid #ccc !important;
            background: #fafafa !important;
        }
        .seal-badge, .ledger-status, .verification-panel {
            break-inside: avoid;
        }
    }
    </style>
    """

    # Inject PDF styles before </head>
    if "</head>" in html_content:
        html_content = html_content.replace("</head>", pdf_styles + "</head>")

    try:
        # Generate PDF in memory
        pdf_buffer = io.BytesIO()
        WeasyHTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)

        filename = f"{page_id}.pdf"

        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({
            "error": "PDF generation failed",
            "message": str(e),
            "page_id": page_id,
        }), 500


@page_bp.route("/export/docx/<page_id>", methods=["GET"])
def export_docx(page_id: str):
    """
    Export sealed page as DOCX (Word document).

    The DOCX includes:
    - Title and metadata
    - Content extracted from HTML
    - Provenance footer with hashes
    """
    if not DOCX_AVAILABLE:
        return jsonify({
            "error": "DOCX export unavailable",
            "message": "python-docx not installed on server",
        }), 503

    conn = get_db()
    page = conn.execute(
        "SELECT * FROM pages WHERE id = ? AND status = 'sealed'",
        (page_id,)
    ).fetchone()
    conn.close()

    if not page:
        return jsonify({"error": "Page not found or not sealed"}), 404

    try:
        # Create document
        doc = DocxDocument()

        # Set document properties
        core_properties = doc.core_properties
        core_properties.title = page["title"]
        core_properties.author = "WINDI Constitutional System"
        core_properties.comments = f"Sealed Document ID: {page_id}"

        # Add title
        title = doc.add_heading(page["title"], 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Add metadata paragraph
        meta_para = doc.add_paragraph()
        meta_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        meta_run = meta_para.add_run(f"WINDI Sealed Document — {page['doc_type'].upper()}")
        meta_run.font.size = Pt(10)
        meta_run.font.color.rgb = RGBColor(100, 100, 100)

        doc.add_paragraph()  # Spacer

        # Extract text content from HTML (simple extraction)
        import re
        html_content = page["html_content"]

        # Extract card contents
        card_pattern = r'<div class="windi-card[^"]*"[^>]*>.*?<div class="card-title[^"]*">([^<]*)</div>.*?<div class="card-content[^"]*">(.*?)</div>'
        cards = re.findall(card_pattern, html_content, re.DOTALL | re.IGNORECASE)

        for card_title, card_content in cards:
            # Add card title as heading
            doc.add_heading(card_title.strip(), level=2)

            # Clean HTML tags from content
            clean_content = re.sub(r'<[^>]+>', '', card_content)
            clean_content = clean_content.strip()

            if clean_content:
                doc.add_paragraph(clean_content)

            doc.add_paragraph()  # Spacer

        # Add provenance section
        doc.add_page_break()
        doc.add_heading("WINDI Provenance Chain", level=1)

        provenance_table = doc.add_table(rows=8, cols=2)
        provenance_table.style = "Table Grid"

        provenance_data = [
            ("Document ID", page_id),
            ("Sealed At", page["sealed_at"] or "N/A"),
            ("HTML Hash", page["html_hash"] or "N/A"),
            ("CSS Hash", page["css_hash"] or "N/A"),
            ("Combined Hash", page["combined_hash"] or "N/A"),
            ("Content Hash", page["content_hash"] or "N/A"),
            ("Receipt ID", page["receipt_id"] or "N/A"),
            ("Ledger Anchor", page["ledger_anchor"] or "N/A"),
        ]

        for i, (label, value) in enumerate(provenance_data):
            row = provenance_table.rows[i]
            row.cells[0].text = label
            row.cells[1].text = value

        # Add footer
        doc.add_paragraph()
        footer_para = doc.add_paragraph()
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer_run = footer_para.add_run(
            f"This document was generated by WINDI W-PAGE-001 v{__version__}\n"
            f"Verify at: {VERIFY_PUBLIC_URL}?id={page_id}"
        )
        footer_run.font.size = Pt(8)
        footer_run.font.color.rgb = RGBColor(128, 128, 128)

        # Save to buffer
        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)

        filename = f"{page_id}.docx"

        return send_file(
            docx_buffer,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({
            "error": "DOCX generation failed",
            "message": str(e),
            "page_id": page_id,
        }), 500


@page_bp.route("/export/evidence/<page_id>", methods=["GET"])
def export_evidence(page_id: str):
    """
    Export complete evidence bundle as ZIP.

    The evidence bundle contains:
    - document.html — The sealed HTML document
    - provenance.json — Complete UI Provenance chain
    - hashes.txt — All hashes for manual verification
    - ledger_receipt.json — Snapshot of Ledger receipt (if available)
    - manifest.json — Bundle manifest with checksums
    """
    conn = get_db()
    page = conn.execute(
        "SELECT * FROM pages WHERE id = ? AND status = 'sealed'",
        (page_id,)
    ).fetchone()
    conn.close()

    if not page:
        return jsonify({"error": "Page not found or not sealed"}), 404

    try:
        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. document.html
            html_content = page["html_content"]
            zf.writestr("document.html", html_content)

            # 2. provenance.json
            provenance = {
                "document_id": page_id,
                "title": page["title"],
                "doc_type": page["doc_type"],
                "created_at": page["created_at"],
                "sealed_at": page["sealed_at"],
                "generator": page["generator"],
                "template_version": page["template_version"],
                "ui_provenance": {
                    "html_hash": page["html_hash"],
                    "css_hash": page["css_hash"],
                    "js_hash": page["js_hash"],
                    "combined_hash": page["combined_hash"],
                    "content_hash": page["content_hash"],
                },
                "ledger": {
                    "receipt_id": page["receipt_id"],
                    "ledger_anchor": page["ledger_anchor"],
                },
                "verify_url": f"{VERIFY_PUBLIC_URL}?id={page_id}",
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "exporter": f"W-PAGE-001 v{__version__}",
            }
            zf.writestr("provenance.json", json.dumps(provenance, indent=2))

            # 3. hashes.txt (for manual verification)
            hashes_content = f"""WINDI Evidence Bundle — Hash Verification
==========================================
Document ID: {page_id}
Generated:   {datetime.now(timezone.utc).isoformat()}

UI PROVENANCE HASHES
--------------------
HTML Hash:     {page["html_hash"]}
CSS Hash:      {page["css_hash"]}
JS Hash:       {page["js_hash"]}
Combined Hash: {page["combined_hash"]}
Content Hash:  {page["content_hash"]}

VERIFICATION COMMANDS
---------------------
# Verify HTML hash (Unix/Mac):
sha256sum document.html

# Verify HTML hash (Windows PowerShell):
Get-FileHash document.html -Algorithm SHA256

# Expected HTML Hash:
{page["html_hash"]}

LEDGER VERIFICATION
-------------------
Receipt ID:    {page["receipt_id"]}
Ledger Anchor: {page["ledger_anchor"]}
Verify URL:    {VERIFY_PUBLIC_URL}?id={page_id}

CONSTITUTIONAL GUARANTEE
------------------------
"AI processes. Human decides. WINDI guarantees."

This document was sealed by the WINDI Constitutional System.
The hashes above can be independently verified against the
Forensic Ledger to prove document integrity and provenance.
"""
            zf.writestr("hashes.txt", hashes_content)

            # 4. ledger_receipt.json (fetch from Ledger API if available)
            try:
                import urllib.request
                ledger_url = f"http://localhost:8101/api/receipts/{page['receipt_id']}"
                req = urllib.request.Request(ledger_url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    ledger_data = json.loads(response.read().decode())
                    zf.writestr("ledger_receipt.json", json.dumps(ledger_data, indent=2))
            except Exception:
                # Ledger receipt not available, include placeholder
                zf.writestr("ledger_receipt.json", json.dumps({
                    "note": "Ledger receipt snapshot not available at export time",
                    "receipt_id": page["receipt_id"],
                    "verify_manually": f"http://localhost:8101/api/receipts/{page['receipt_id']}",
                }, indent=2))

            # 5. manifest.json (bundle integrity)
            import hashlib as hl
            manifest = {
                "bundle_id": f"EVIDENCE-{page_id}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "generator": f"W-PAGE-001 v{__version__}",
                "contents": [
                    {"file": "document.html", "size": len(html_content.encode())},
                    {"file": "provenance.json", "description": "UI Provenance chain"},
                    {"file": "hashes.txt", "description": "Human-readable hash verification"},
                    {"file": "ledger_receipt.json", "description": "Forensic Ledger snapshot"},
                ],
                "document_hash": page["html_hash"],
                "constitutional_seal": True,
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        zip_buffer.seek(0)
        filename = f"EVIDENCE-{page_id}.zip"

        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({
            "error": "Evidence bundle generation failed",
            "message": str(e),
            "page_id": page_id,
        }), 500
