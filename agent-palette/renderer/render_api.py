#!/usr/bin/env python3
"""
WINDI Render API — HTTP Endpoints for Document Generation
Integrates with the Agent Palette server (BaseHTTPRequestHandler).

Endpoints:
  POST /api/dragon/render    → Generate a document file
  GET  /api/dragon/download/<filename>  → Download generated file
  GET  /api/dragon/renderer/health      → Renderer engine status

Usage (integration with palette server):
  from render_api import handle_render_request
  # In your do_POST handler, delegate to handle_render_request()
"""

import json
import mimetypes
import os
import sys
import uuid
from pathlib import Path
from download_security import generate_signed_url, verify_token, start_cleanup
from ledger_sync import get_ledger_sync, TIER_TO_LEVEL
from spec_sanitizer import sanitize_spec, sanitize_filename
from urllib.parse import unquote
from hash_injector import seal_document
from serial_engine import get_serial_engine
from qr_engine import generate_verify_url, generate_qr_image
import base64
from datetime import datetime, timezone

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from document_renderer import init as renderer_init, render_document, health as renderer_health


# Initialize on import
_init_result = renderer_init()


MIME_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "pdf": "application/pdf",
}

OUTPUT_DIR = Path(__file__).parent / "output"
STAGING_DIR = Path(__file__).parent.parent / "staging"
start_cleanup(str(OUTPUT_DIR))


def handle_render_request(handler):
    """
    Handle POST /api/dragon/render
    
    Expected JSON body:
    {
        "text": "Document content from Dragon API...",
        "intent": {"doc_type": "memo", "language": "de", "formality": "formal", ...},
        "isp": {...},        // optional ISP profile data
        "sge": {...},        // optional SGE analysis
        "receipt": {...},    // optional forensic receipt
        "tier": "HIGH"       // FREE/MED/HIGH
    }
    
    Returns JSON:
    {
        "success": true,
        "download_url": "/api/dragon/download/WINDI_Memo_20260221_ab1234.docx",
        "filename": "WINDI_Memo_20260221_ab1234.docx",
        "format": "docx",
        "size_bytes": 12345,
        "content_hash": "sha256:...",
        "bundle_hash": "sha256:...",
        "render_ms": 234
    }
    """
    try:
        content_length = int(handler.headers.get("Content-Length", 0))
        body = handler.rfile.read(content_length).decode("utf-8")
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError) as e:
        return _json_response(handler, 400, {"error": f"Invalid JSON: {e}"})

    intent = data.get("intent", {"doc_type": "note", "language": "de"})
    text = data.get("text", "")
    user_input = data.get("userInput", "")

    # For "criar"/"create" action: generate template text if none provided
    if not text:
        action = intent.get("action", data.get("action", ""))
        if action in ("criar", "create", "erstellen", "neu", "novo", "new", ""):
            text = _generate_template_text(intent)
        else:
            return _json_response(handler, 400, {"error": "Missing 'text' field"})
    isp = data.get("isp")
    sge = data.get("sge")
    receipt = data.get("receipt")
    tier = data.get("tier", "HIGH")

    # Render the document
    result = render_document(
        text=text,
        intent=intent,
        isp=isp,
        sge=sge,
        receipt=receipt,
        tier=tier,
        user_input=user_input,
    )

    if not result["success"]:
        return _json_response(handler, 500, {
            "success": False,
            "error": result["error"],
            "render_ms": result["render_ms"],
        })

    # ═══════════════════════════════════════════════════════════════════════════
    # N2+N3: SHA-256 SEAL + SERIAL NUMBER INJECTION
    # Pipeline: render → serial(N3) → seal(N2) → ledger(N1) → download
    # ═══════════════════════════════════════════════════════════════════════════

    # N3: Generate unique sequential serial number
    serial_engine = get_serial_engine()
    serial = serial_engine.next_serial()

    # Generate receipt_id and governance level (shared between N2 footer and N1 ledger)
    receipt_id = f"VR-PAL-{uuid.uuid4().hex[:12]}"
    governance_level = TIER_TO_LEVEL.get(tier.upper(), "LOW")

    # Read pre-footer document bytes
    filepath = Path(result["filepath"])
    pre_footer_bytes = filepath.read_bytes()

    # Inject WINDI seal into footer + metadata (N2+N3)
    # Hash is computed from PRE-footer content (not circular)
    # Serial is included in footer and metadata
    sealed_bytes, content_hash = seal_document(
        doc_bytes=pre_footer_bytes,
        doc_format=result["format"],
        receipt_id=receipt_id,
        governance_level=governance_level,
        doc_name=result["filename"],
        serial=serial,
    )

    # Save sealed document back to file
    filepath.write_bytes(sealed_bytes)

    # Update result with sealed content info
    result["size_bytes"] = len(sealed_bytes)
    result["content_hash"] = content_hash  # Pre-footer hash (verification fingerprint)

    # Build signed download URL with TTL
    signed = generate_signed_url(result["filename"])

    # ═══════════════════════════════════════════════════════════════════════════
    # SOVEREIGNTY DATA — Trust Panel fields
    # ═══════════════════════════════════════════════════════════════════════════

    # Generate verification URL and QR code
    verify_url = generate_verify_url(serial, content_hash)
    qr_bytes = generate_qr_image(verify_url, size=150)
    qr_base64 = base64.b64encode(qr_bytes).decode("ascii") if qr_bytes else None

    # Extract SGE risk class from input
    sge_data = data.get("sge", {})
    sge_risk = sge_data.get("risk", "R0") if sge_data else "R0"
    sge_score = sge_data.get("score", 0) if sge_data else 0
    sge_blocked = sge_data.get("blocked", False) if sge_data else False
    human_required = sge_data.get("humanRequired", False) if sge_data else False

    # Determine if I9 gate is active (human decision required for high-impact actions)
    i9_active = human_required or sge_blocked or governance_level == "HIGH"

    # Compliance status based on tier
    compliance_status = "GOLD" if tier.upper() == "HIGH" else "SILVER" if tier.upper() == "MED" else "BRONZE"

    # Timestamp
    created_at = datetime.now(timezone.utc).isoformat()

    response = {
        "success": True,
        "download_url": signed["download_url"],
        "expires_at": signed["expires_at"],
        "ttl_minutes": signed["ttl_minutes"],
        "filename": result["filename"],
        "format": result["format"],
        "size_bytes": result["size_bytes"],
        "content_hash": result["content_hash"],
        "bundle_hash": result["bundle_hash"],
        "render_ms": result["render_ms"],
        "serial": serial,
        "receipt_id": receipt_id,
        "governance_level": governance_level,
        # ── Sovereignty Data (Trust Panel) ──
        "sovereignty": {
            "serial_id": serial,
            "sha256_hash": content_hash,
            "short_hash": content_hash[:16] if content_hash else None,
            "verify_url": verify_url,
            "qr_image_base64": qr_base64,
            "created_at": created_at,
            "sge_risk_class": sge_risk,
            "sge_score": sge_score,
            "compliance_tier": compliance_status,
            "human_decision_required": human_required,
            "i9_active": i9_active,
            "ledger_status": "PENDING",  # Updated below after sync
            "ledger_receipt_id": receipt_id,
            "vault_url": f"https://windi-domain.com/vault/verify?serial={serial}&hash={content_hash[:16]}",
        },
    }

    # Async Ledger sync (N1) with pre-computed hash from N2 and serial from N3
    # Ensures: serial + hash in footer = serial + hash in Ledger = same truth
    try:
        ls = get_ledger_sync()
        tier_l = data.get("tier", "ANON")
        acct = data.get("account_id", "anonymous")
        sync_r = ls.sync_render(
            result, data, tier_l, acct,
            content_hash=content_hash,
            receipt_id=receipt_id,
            governance_level=governance_level,
            serial=serial,
        )
        response["ledger_status"] = sync_r["status"]
        response["sovereignty"]["ledger_status"] = sync_r["status"]
    except Exception:
        response["ledger_status"] = "SKIP"
        response["sovereignty"]["ledger_status"] = "FAILED"

    return _json_response(handler, 200, response)


def handle_download_request(handler, filename):
    """
    Handle GET /api/dragon/download/<filename>
    Serves the generated document file for download.
    Checks both OUTPUT_DIR (renderer) and STAGING_DIR (dragon generate).
    """
    # Sanitize filename (prevent path traversal)
    safe_name = Path(filename).name
    filepath = OUTPUT_DIR / safe_name

    # Fallback to staging directory (Sprint 1+2 document generation)
    if not filepath.exists():
        filepath = STAGING_DIR / safe_name

    if not filepath.exists():
        return _json_response(handler, 404, {"error": f"File not found: {safe_name}"})

    # Determine MIME type
    ext = filepath.suffix.lstrip(".")
    content_type = MIME_TYPES.get(ext, "application/octet-stream")

    # Serve file
    file_bytes = filepath.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(file_bytes)))
    handler.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("X-WINDI-Renderer", "1.0.0")
    handler.end_headers()
    handler.wfile.write(file_bytes)


def handle_renderer_health(handler):
    """Handle GET /api/dragon/renderer/health"""
    status = renderer_health()
    status["init"] = _init_result
    return _json_response(handler, 200, status)


def route_render_api(handler, method, path):
    """
    Route dispatcher for render API endpoints.
    Call this from your main server's do_GET/do_POST handlers.
    
    Returns True if the request was handled, False otherwise.
    """
    # Normalize path
    clean_path = path.rstrip("/")

    if method == "POST" and clean_path == "/api/dragon/render":
        handle_render_request(handler)
        return True

    if method == "GET" and clean_path.startswith("/api/dragon/download/"):
        filename = unquote(clean_path.split("/api/dragon/download/", 1)[1].split("?")[0])
        # Verify signed URL token
        qs = handler.path.split("?")[1] if "?" in handler.path else ""
        params = dict(p.split("=", 1) for p in qs.split("&") if "=" in p) if qs else {}
        if params.get("token") and params.get("expires"):
            valid, err = verify_token(filename, params["token"], int(params["expires"]))
            if not valid:
                send_json(handler, {"error": err, "code": "LINK_EXPIRED"}, 410)
                return True
        handle_download_request(handler, filename)
        return True

    if method == "GET" and clean_path == "/api/dragon/renderer/health":
        handle_renderer_health(handler)
        return True

    return False




# ── Template text generator for "criar" action ──────────────
TEMPLATE_TEXTS = {
    "rechnung": {
        "de": "# Rechnung\n\n| Position | Beschreibung | Menge | Einzelpreis | Gesamt |\n|----------|-------------|-------|-------------|--------|\n| 1 | Dienstleistung | 1 | 0,00 € | 0,00 € |\n\n**Zwischensumme:** 0,00 €\n**MwSt. (19%):** 0,00 €\n**Gesamtbetrag:** 0,00 €",
        "en": "# Invoice\n\n| Item | Description | Qty | Unit Price | Total |\n|------|------------|-----|-----------|-------|\n| 1 | Service | 1 | €0.00 | €0.00 |\n\n**Subtotal:** €0.00\n**VAT (19%):** €0.00\n**Total:** €0.00",
        "pt": "# Fatura\n\n| Item | Descrição | Qtd | Preço Unit. | Total |\n|------|-----------|-----|-------------|-------|\n| 1 | Serviço | 1 | €0,00 | €0,00 |\n\n**Subtotal:** €0,00\n**IVA (19%):** €0,00\n**Total:** €0,00",
    },
    "invoice": {
        "de": "# Rechnung\n\n| Position | Beschreibung | Menge | Einzelpreis | Gesamt |\n|----------|-------------|-------|-------------|--------|\n| 1 | Dienstleistung | 1 | 0,00 € | 0,00 € |\n\n**Gesamtbetrag:** 0,00 €",
        "en": "# Invoice\n\n| Item | Description | Qty | Unit Price | Total |\n|------|------------|-----|-----------|-------|\n| 1 | Service | 1 | €0.00 | €0.00 |\n\n**Total:** €0.00",
        "pt": "# Fatura\n\n| Item | Descrição | Qtd | Preço Unit. | Total |\n|------|-----------|-----|-------------|-------|\n| 1 | Serviço | 1 | €0,00 | €0,00 |\n\n**Total:** €0,00",
    },
    "letter": {
        "de": "# Brief\n\nSehr geehrte Damen und Herren,\n\n[Ihr Text hier]\n\nMit freundlichen Grüßen",
        "en": "# Letter\n\nDear Sir/Madam,\n\n[Your text here]\n\nKind regards",
        "pt": "# Carta\n\nPresado(a) Senhor(a),\n\n[Seu texto aqui]\n\nAtenciosamente",
    },
    "memo": {
        "de": "# Memorandum\n\n**An:** [Empfänger]\n**Von:** [Absender]\n**Datum:** [Datum]\n**Betreff:** [Betreff]\n\n---\n\n[Inhalt]",
        "en": "# Memorandum\n\n**To:** [Recipient]\n**From:** [Sender]\n**Date:** [Date]\n**Subject:** [Subject]\n\n---\n\n[Content]",
        "pt": "# Memorando\n\n**Para:** [Destinatário]\n**De:** [Remetente]\n**Data:** [Data]\n**Assunto:** [Assunto]\n\n---\n\n[Conteúdo]",
    },
    "report": {
        "de": "# Bericht\n\n## Zusammenfassung\n\n[Zusammenfassung]\n\n## Details\n\n[Details]\n\n## Empfehlung\n\n[Empfehlung]",
        "en": "# Report\n\n## Summary\n\n[Summary]\n\n## Details\n\n[Details]\n\n## Recommendation\n\n[Recommendation]",
        "pt": "# Relatório\n\n## Resumo\n\n[Resumo]\n\n## Detalhes\n\n[Detalhes]\n\n## Recomendação\n\n[Recomendação]",
    },
    "contract": {
        "de": "# Vertrag\n\n**Zwischen:** [Partei A] und [Partei B]\n\n## §1 Gegenstand\n\n[Vertragsgegenstand]\n\n## §2 Laufzeit\n\n[Laufzeit]\n\n## §3 Vergütung\n\n[Vergütung]",
        "en": "# Contract\n\n**Between:** [Party A] and [Party B]\n\n## §1 Subject\n\n[Subject]\n\n## §2 Duration\n\n[Duration]\n\n## §3 Compensation\n\n[Compensation]",
        "pt": "# Contrato\n\n**Entre:** [Parte A] e [Parte B]\n\n## §1 Objeto\n\n[Objeto]\n\n## §2 Vigência\n\n[Vigência]\n\n## §3 Remuneração\n\n[Remuneração]",
    },
    "protocol": {
        "de": "# Protokoll\n\n**Datum:** [Datum]\n**Teilnehmer:** [Teilnehmer]\n\n## Tagesordnung\n\n1. [Punkt 1]\n2. [Punkt 2]\n\n## Beschlüsse\n\n[Beschlüsse]",
        "en": "# Minutes\n\n**Date:** [Date]\n**Attendees:** [Attendees]\n\n## Agenda\n\n1. [Item 1]\n2. [Item 2]\n\n## Decisions\n\n[Decisions]",
        "pt": "# Ata\n\n**Data:** [Data]\n**Participantes:** [Participantes]\n\n## Pauta\n\n1. [Item 1]\n2. [Item 2]\n\n## Decisões\n\n[Decisões]",
    },
}

def _generate_template_text(intent):
    """Generate template text for 'criar' action when no text is provided."""
    doc_type = intent.get("doc_type", "note")
    language = intent.get("language", "de")

    # Try specific template
    tmpl = TEMPLATE_TEXTS.get(doc_type, {})
    text = tmpl.get(language, tmpl.get("de", ""))

    if not text:
        # Generic fallback
        labels = {"de": "Dokument", "en": "Document", "pt": "Documento"}
        label = labels.get(language, "Document")
        text = f"# {label}\n\n[Inhalt / Content / Conteúdo]"

    return text


def _json_response(handler, status_code, data):
    """Send a JSON response."""
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)
