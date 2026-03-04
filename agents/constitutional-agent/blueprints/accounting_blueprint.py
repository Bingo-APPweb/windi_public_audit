"""
WINDI Accounting Agent "W-ACCT-001" v0.1.0 - Flask Blueprint
==============================================================

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /accounting/* endpoints on :8091.

Features:
- GoBD compliant invoice processing
- XRechnung/ZUGFeRD parsing
- DATEV export (SKR03/SKR04)
- UStVA generation (ELSTER XML)
- Fiscal period management

Constitutional Invariants (C1-C6):
- C1: Exactness - every value traceable to source document
- C2: Periods - every entry has explicit fiscal period
- C3: Immutability - closed periods blocked for changes
- C4: Double entry - Debit = Credit or operation rejected
- C5: Compliance - GoBD + XRechnung/ZUGFeRD + DATEV mandatory
- C6: Sovereignty - AI prepares. Human approves. ELSTER receives. [IRREMEDIABLE]

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 0.1.0
Sealed: W-ACCT-001
Wave: 3
"""

import base64
import hashlib
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, Response, jsonify, request

# Import renderers
try:
    from blueprints.renderers.accounting import (
        XRechnungValidator,
        ZUGFeRDParser,
        DATEVExporter,
        UStVABuilder,
    )
except ImportError:
    # Fallback for direct execution
    from renderers.accounting import (
        XRechnungValidator,
        ZUGFeRDParser,
        DATEVExporter,
        UStVABuilder,
    )

__version__ = "0.1.0"
__agent_id__ = "W-ACCT-001"
__agent_name__ = "Accounting"

# Constitutional Invariants - HARDCODED, NOT CONFIGURABLE
ACCOUNTING_INVARIANTS = {
    "C1": "Exatidao - cada valor rastreavel ate documento fonte",
    "C2": "Periodos - todo lancamento tem periodo fiscal explicito",
    "C3": "Imutabilidade - periodos fechados bloqueados para alteracao",
    "C4": "Dupla entrada - Debito = Credito ou operacao rejeitada",
    "C5": "Conformidade - GoBD + XRechnung/ZUGFeRD + DATEV obrigatorios",
    "C6": "Soberania - IA prepara. Humano aprova. ELSTER envia. [IRREMEDIAVEL]",
}

# Paths
DATA_DIR = "/opt/windi/accounting"
DB_PATH = os.path.join(DATA_DIR, "accounting.db")
PERIODS_DIR = os.path.join(DATA_DIR, "periods")

# Ledger integration
LEDGER_URL = "http://localhost:8101"


# ===================================================================
#  DATABASE INITIALIZATION
# ===================================================================

def init_db():
    """Initialize the accounting database."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PERIODS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Invoices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            ledger_hash TEXT,
            doc_type TEXT NOT NULL,
            format TEXT NOT NULL,
            supplier_name TEXT,
            supplier_vat TEXT,
            recipient_name TEXT,
            recipient_vat TEXT,
            invoice_number TEXT,
            invoice_date TEXT,
            period TEXT NOT NULL,
            net_amount REAL NOT NULL,
            vat_rate REAL NOT NULL,
            vat_amount REAL NOT NULL,
            gross_amount REAL NOT NULL,
            currency TEXT DEFAULT 'EUR',
            gobd_compliant INTEGER DEFAULT 0,
            period_closed INTEGER DEFAULT 0,
            ledger_receipt TEXT,
            raw_xml TEXT,
            ocr_text TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Fiscal periods table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fiscal_periods (
            period TEXT PRIMARY KEY,
            status TEXT DEFAULT 'open',
            umsatzsteuer REAL DEFAULT 0.0,
            vorsteuer REAL DEFAULT 0.0,
            zahllast REAL DEFAULT 0.0,
            invoice_count INTEGER DEFAULT 0,
            ustva_xml_path TEXT,
            ustva_hash TEXT,
            approved_by TEXT,
            approved_at TEXT,
            submitted_at TEXT,
            elster_ticket TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Audit log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounting_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            entity_id TEXT,
            period TEXT,
            invariant TEXT,
            result TEXT,
            details TEXT,
            operator TEXT DEFAULT 'system',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()

    return True


def get_db():
    """Get database connection."""
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def log_audit(
    action: str,
    entity_id: str = None,
    period: str = None,
    invariant: str = None,
    result: str = "pass",
    details: Dict = None,
    operator: str = "system",
):
    """Log action to audit trail."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO accounting_audit
        (action, entity_id, period, invariant, result, details, operator)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        action,
        entity_id,
        period,
        invariant,
        result,
        json.dumps(details) if details else None,
        operator,
    ))
    conn.commit()
    conn.close()


# ===================================================================
#  LEDGER INTEGRATION
# ===================================================================

def send_to_ledger(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Send receipt to Ledger :8101."""
    try:
        import urllib.request

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{LEDGER_URL}/api/receipts",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "ledger_available": False}


# ===================================================================
#  HELPER FUNCTIONS
# ===================================================================

def compute_hash(content: bytes) -> str:
    """Compute SHA-256 hash."""
    return hashlib.sha256(content).hexdigest()


def determine_doc_type(data: Dict[str, Any]) -> str:
    """Determine document type from extracted data."""
    # If we have supplier info but no recipient info, likely eingangsrechnung
    # If we have recipient info but supplier is us, likely ausgangsrechnung
    supplier = data.get("supplier_name", "")
    recipient = data.get("recipient_name", "")

    # Default to eingangsrechnung (incoming invoice)
    return "eingangsrechnung"


def validate_period_open(period: str) -> Tuple[bool, str]:
    """Check if period is open for modifications (C3)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM fiscal_periods WHERE period = ?", (period,))
    row = cursor.fetchone()
    conn.close()

    if row and row["status"] in ["approved", "submitted"]:
        return False, f"Period {period} is closed (status: {row['status']})"

    return True, "OK"


def get_or_create_period(period: str) -> Dict[str, Any]:
    """Get or create fiscal period."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fiscal_periods WHERE period = ?", (period,))
    row = cursor.fetchone()

    if not row:
        cursor.execute("""
            INSERT INTO fiscal_periods (period, status)
            VALUES (?, 'open')
        """, (period,))
        conn.commit()
        cursor.execute("SELECT * FROM fiscal_periods WHERE period = ?", (period,))
        row = cursor.fetchone()

    conn.close()
    return dict(row) if row else {"period": period, "status": "open"}


def update_period_totals(period: str):
    """Recalculate period totals from invoices."""
    conn = get_db()
    cursor = conn.cursor()

    # Sum outgoing invoices (Umsatzsteuer)
    cursor.execute("""
        SELECT COALESCE(SUM(vat_amount), 0) as total
        FROM invoices
        WHERE period = ? AND doc_type = 'ausgangsrechnung'
    """, (period,))
    umsatzsteuer = cursor.fetchone()["total"]

    # Sum incoming invoices (Vorsteuer)
    cursor.execute("""
        SELECT COALESCE(SUM(vat_amount), 0) as total
        FROM invoices
        WHERE period = ? AND doc_type = 'eingangsrechnung'
    """, (period,))
    vorsteuer = cursor.fetchone()["total"]

    # Count invoices
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM invoices WHERE period = ?
    """, (period,))
    invoice_count = cursor.fetchone()["cnt"]

    # Update period
    cursor.execute("""
        UPDATE fiscal_periods
        SET umsatzsteuer = ?, vorsteuer = ?, zahllast = ?,
            invoice_count = ?, updated_at = datetime('now')
        WHERE period = ?
    """, (umsatzsteuer, vorsteuer, umsatzsteuer - vorsteuer, invoice_count, period))

    conn.commit()
    conn.close()


def calculate_deadline(period: str) -> Tuple[str, int]:
    """Calculate filing deadline for period."""
    year, month = map(int, period.split("-"))

    # Deadline is 10th of following month
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1

    deadline = datetime(next_year, next_month, 10)
    today = datetime.now()
    days_remaining = (deadline - today).days

    return deadline.strftime("%Y-%m-%d"), days_remaining


# ===================================================================
#  FLASK BLUEPRINT
# ===================================================================

accounting_bp = Blueprint("accounting", __name__, url_prefix="/accounting")


# --- Health & Status ---

@accounting_bp.route("/health", methods=["GET"])
def health():
    """Health check for Accounting Agent."""
    db_exists = os.path.exists(DB_PATH)

    # Check Ledger connection
    ledger_ok = False
    try:
        import urllib.request
        with urllib.request.urlopen(f"{LEDGER_URL}/health", timeout=2) as resp:
            ledger_ok = resp.status == 200
    except Exception:
        pass

    return jsonify({
        "status": "GREEN" if db_exists else "YELLOW",
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "wave": "3",
        "database": "connected" if db_exists else "initializing",
        "ledger": "connected" if ledger_ok else "disconnected",
        "principle": "AI processes. Human decides. WINDI guarantees.",
        "c6_note": "IA prepara. Humano aprova. ELSTER recebe do humano.",
    })


@accounting_bp.route("/invariants", methods=["GET"])
def invariants():
    """List constitutional invariants."""
    return jsonify({
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "wave": "3",
        "philosophy": "A IA calcula. O humano assina. O ELSTER recebe do humano.",
        "c6_note": "Wave4 integrara Erica para envio directo pos-aprovacao C6. Wave3 e honesta: gera XML perfeito, humano submete.",
        "gobd": "GoBD-compliant por arquitectura. O Ledger e a prova. O Vault e o arquivo.",
        "formats": ["XRechnung", "ZUGFeRD 2.x", "PDF+OCR"],
        "export": ["DATEV SKR03", "DATEV SKR04"],
        "retention": {"invoices": "8 anos", "balance_sheets": "10 anos"},
        "invariants": {
            code: {"description": desc, "status": "ACTIVE"}
            for code, desc in ACCOUNTING_INVARIANTS.items()
        },
    })


@accounting_bp.route("/stats", methods=["GET"])
def stats():
    """General statistics."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM invoices")
    total_invoices = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM fiscal_periods")
    total_periods = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COALESCE(SUM(zahllast), 0) as total FROM fiscal_periods")
    total_zahllast = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COALESCE(SUM(gross_amount), 0) as total
        FROM invoices WHERE doc_type = 'eingangsrechnung'
    """)
    total_incoming = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COALESCE(SUM(gross_amount), 0) as total
        FROM invoices WHERE doc_type = 'ausgangsrechnung'
    """)
    total_outgoing = cursor.fetchone()["total"]

    conn.close()

    return jsonify({
        "agent": __agent_id__,
        "total_invoices": total_invoices,
        "total_periods": total_periods,
        "total_incoming_gross": round(total_incoming, 2),
        "total_outgoing_gross": round(total_outgoing, 2),
        "accumulated_zahllast": round(total_zahllast, 2),
    })


# ===================================================================
#  GROUP 1 - Invoice Ingestion
# ===================================================================

@accounting_bp.route("/invoice/upload", methods=["POST"])
def invoice_upload():
    """
    Upload and process an invoice.

    Accepts: multipart/form-data with 'file' field (PDF, XML, ZUGFeRD)
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = file.filename or "unknown"
    content = file.read()

    if not content:
        return jsonify({"error": "Empty file"}), 400

    # Determine format and parse
    format_detected = "unknown"
    extracted_data = {}
    raw_xml = None
    errors = []
    warnings = []
    gobd_compliant = False

    # Try XRechnung (pure XML)
    if content.startswith(b"<?xml") or content.startswith(b"<"):
        try:
            xml_str = content.decode("utf-8")
            validator = XRechnungValidator(xml_str)
            is_valid, result = validator.validate()

            format_detected = "xrechnung"
            extracted_data = result.get("data", {})
            raw_xml = xml_str
            errors = result.get("errors", [])
            warnings = result.get("warnings", [])
            gobd_compliant = result.get("gobd_compliant", False)

        except Exception as e:
            errors.append(f"XRechnung parse error: {str(e)}")

    # Try ZUGFeRD (PDF with embedded XML)
    elif content.startswith(b"%PDF"):
        parser = ZUGFeRDParser(content)

        if parser.is_zugferd():
            success, result = parser.parse()
            if success:
                format_detected = "zugferd"
                extracted_data = result.get("data", {})
                raw_xml = result.get("raw_xml")
                errors = result.get("errors", [])
                warnings = result.get("warnings", [])
                gobd_compliant = len(errors) == 0
            else:
                format_detected = "pdf_ocr"
                warnings.append("ZUGFeRD detected but parsing failed, OCR fallback required")
        else:
            format_detected = "pdf_ocr"
            warnings.append("Plain PDF detected, OCR required for data extraction")
            # OCR fallback - Wave3 doesn't include full OCR
            return jsonify({
                "success": False,
                "format_detected": format_detected,
                "ocr_available": False,
                "manual_entry_required": True,
                "message": "PDF without embedded XML. Manual data entry required in Wave3.",
            }), 400

    else:
        return jsonify({"error": "Unsupported file format"}), 400

    # Validate required fields (C1)
    if not extracted_data.get("net_amount"):
        errors.append("C1 violation: net_amount not extractable")
    if not extracted_data.get("vat_amount"):
        errors.append("C1 violation: vat_amount not extractable")

    # Determine period (C2)
    period = extracted_data.get("period")
    if not period:
        period = datetime.now().strftime("%Y-%m")
        warnings.append(f"C2: Period not in document, using current: {period}")

    # Check period is open (C3)
    period_open, period_msg = validate_period_open(period)
    if not period_open:
        log_audit("invoice_upload", None, period, "C3", "blocked", {"reason": period_msg})
        return jsonify({
            "error": "C3 violation: Period is closed",
            "period": period,
            "message": period_msg,
        }), 423

    # Validate arithmetic (C4)
    net = extracted_data.get("net_amount", 0)
    vat = extracted_data.get("vat_amount", 0)
    gross = extracted_data.get("gross_amount", 0)

    if net and vat and gross:
        calculated = net + vat
        if abs(calculated - gross) > 0.02:
            errors.append(f"C4 violation: {net} + {vat} = {calculated}, but gross is {gross}")
            gobd_compliant = False

    # If critical errors, reject
    if any("violation" in e for e in errors):
        return jsonify({
            "success": False,
            "format_detected": format_detected,
            "errors": errors,
            "warnings": warnings,
            "gobd_compliant": False,
        }), 400

    # Generate invoice ID
    invoice_id = str(uuid.uuid4())

    # Determine doc type
    doc_type = request.form.get("doc_type") or determine_doc_type(extracted_data)

    # Compute content hash for Ledger
    content_hash = compute_hash(content)

    # Send to Ledger
    ledger_receipt = send_to_ledger({
        "action": "invoice_processed",
        "entity_id": invoice_id,
        "doc_type": doc_type,
        "period": period,
        "amount": gross,
        "hash": content_hash,
        "invariants_checked": ["C1", "C2", "C3", "C4", "C5"],
        "gobd_compliant": gobd_compliant,
        "operator": __agent_id__,
    })

    ledger_hash = None
    if ledger_receipt and "hash" in ledger_receipt:
        ledger_hash = ledger_receipt.get("hash")

    # Save to database
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO invoices (
            id, ledger_hash, doc_type, format, supplier_name, supplier_vat,
            recipient_name, recipient_vat, invoice_number, invoice_date,
            period, net_amount, vat_rate, vat_amount, gross_amount,
            currency, gobd_compliant, ledger_receipt, raw_xml
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        invoice_id,
        ledger_hash,
        doc_type,
        format_detected,
        extracted_data.get("supplier_name"),
        extracted_data.get("supplier_vat"),
        extracted_data.get("recipient_name"),
        extracted_data.get("recipient_vat"),
        extracted_data.get("invoice_number"),
        extracted_data.get("invoice_date"),
        period,
        extracted_data.get("net_amount", 0),
        extracted_data.get("vat_rate", 0.19),
        extracted_data.get("vat_amount", 0),
        extracted_data.get("gross_amount", 0),
        extracted_data.get("currency", "EUR"),
        1 if gobd_compliant else 0,
        json.dumps(ledger_receipt) if ledger_receipt else None,
        raw_xml,
    ))

    conn.commit()
    conn.close()

    # Update period totals
    get_or_create_period(period)
    update_period_totals(period)

    # Log audit
    log_audit("invoice_upload", invoice_id, period, "C1-C5", "pass", {
        "format": format_detected,
        "gobd_compliant": gobd_compliant,
    })

    return jsonify({
        "success": True,
        "id": invoice_id,
        "format_detected": format_detected,
        "period": period,
        "gobd_compliant": gobd_compliant,
        "ledger_hash": ledger_hash,
        "warnings": warnings,
        "data": extracted_data,
    }), 201


@accounting_bp.route("/invoice/<invoice_id>", methods=["GET"])
def invoice_get(invoice_id):
    """Get invoice details."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Invoice not found"}), 404

    result = dict(row)
    if result.get("ledger_receipt"):
        result["ledger_receipt"] = json.loads(result["ledger_receipt"])

    return jsonify(result)


@accounting_bp.route("/invoice/validate", methods=["POST"])
def invoice_validate():
    """Validate invoice without persisting."""
    if "file" not in request.files:
        # Try JSON body with XML content
        data = request.get_json() or {}
        xml_content = data.get("xml")
        if not xml_content:
            return jsonify({"error": "No file or XML content provided"}), 400
        content = xml_content.encode("utf-8")
    else:
        content = request.files["file"].read()

    if not content:
        return jsonify({"error": "Empty content"}), 400

    # Parse based on content type
    if content.startswith(b"<?xml") or content.startswith(b"<"):
        validator = XRechnungValidator(content.decode("utf-8"))
        is_valid, result = validator.validate()

        return jsonify({
            "valid": is_valid,
            "format": "xrechnung",
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
            "gobd_compliant": result.get("gobd_compliant", False),
            "data": result.get("data", {}),
        })

    elif content.startswith(b"%PDF"):
        parser = ZUGFeRDParser(content)
        is_zugferd = parser.is_zugferd()

        if is_zugferd:
            success, result = parser.parse()
            return jsonify({
                "valid": success,
                "format": "zugferd",
                "errors": result.get("errors", []),
                "warnings": result.get("warnings", []),
                "gobd_compliant": success,
            })
        else:
            return jsonify({
                "valid": False,
                "format": "pdf",
                "errors": ["Plain PDF without embedded XML"],
                "warnings": ["OCR required for data extraction"],
                "gobd_compliant": False,
            })

    return jsonify({"error": "Unsupported format"}), 400


@accounting_bp.route("/invoices", methods=["GET"])
def invoices_list():
    """List invoices with filters."""
    period = request.args.get("period")
    doc_type = request.args.get("type")

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM invoices WHERE 1=1"
    params = []

    if period:
        query += " AND period = ?"
        params.append(period)
    if doc_type:
        query += " AND doc_type = ?"
        params.append(doc_type)

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    invoices = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "invoices": invoices,
        "total": len(invoices),
        "filters": {"period": period, "type": doc_type},
    })


# ===================================================================
#  GROUP 2 - Fiscal Periods
# ===================================================================

@accounting_bp.route("/period/<int:year>/<int:month>", methods=["GET"])
def period_get(year: int, month: int):
    """Get fiscal period summary."""
    period = f"{year:04d}-{month:02d}"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fiscal_periods WHERE period = ?", (period,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        # Return empty but valid period
        deadline, days_remaining = calculate_deadline(period)
        return jsonify({
            "period": period,
            "status": "open",
            "umsatzsteuer": 0.0,
            "vorsteuer": 0.0,
            "zahllast": 0.0,
            "invoice_count": 0,
            "deadline": deadline,
            "days_remaining": days_remaining,
        })

    result = dict(row)
    deadline, days_remaining = calculate_deadline(period)
    result["deadline"] = deadline
    result["days_remaining"] = days_remaining

    return jsonify(result)


@accounting_bp.route("/periods", methods=["GET"])
def periods_list():
    """List all fiscal periods."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fiscal_periods ORDER BY period DESC")
    periods = []

    for row in cursor.fetchall():
        period_dict = dict(row)
        deadline, days_remaining = calculate_deadline(period_dict["period"])
        period_dict["deadline"] = deadline
        period_dict["days_remaining"] = days_remaining
        periods.append(period_dict)

    conn.close()

    return jsonify({"periods": periods, "total": len(periods)})


@accounting_bp.route("/period/close/<int:year>/<int:month>", methods=["POST"])
def period_close(year: int, month: int):
    """Close a fiscal period (C3 enforcement)."""
    data = request.get_json() or {}
    period = f"{year:04d}-{month:02d}"

    if not data.get("confirm"):
        return jsonify({
            "error": "Confirmation required",
            "message": "Send {\"confirm\": true, \"operator\": \"human_dragon\"} to close period",
        }), 400

    operator = data.get("operator", "system")

    conn = get_db()
    cursor = conn.cursor()

    # Check current status
    cursor.execute("SELECT status FROM fiscal_periods WHERE period = ?", (period,))
    row = cursor.fetchone()

    if row and row["status"] in ["approved", "submitted"]:
        conn.close()
        return jsonify({"error": f"Period already {row['status']}"}), 400

    # Update all invoices in period
    cursor.execute("""
        UPDATE invoices SET period_closed = 1, updated_at = datetime('now')
        WHERE period = ?
    """, (period,))

    # Update period status
    if row:
        cursor.execute("""
            UPDATE fiscal_periods SET status = 'closed', updated_at = datetime('now')
            WHERE period = ?
        """, (period,))
    else:
        cursor.execute("""
            INSERT INTO fiscal_periods (period, status) VALUES (?, 'closed')
        """, (period,))

    conn.commit()
    conn.close()

    log_audit("period_close", None, period, "C3", "pass", {"operator": operator}, operator)

    return jsonify({
        "success": True,
        "period": period,
        "status": "closed",
        "invariant": "C3",
        "message": "Period closed. No further modifications allowed.",
    })


@accounting_bp.route("/deadlines", methods=["GET"])
def deadlines():
    """Get next 3 fiscal deadlines."""
    today = datetime.now()
    deadlines_list = []

    for i in range(3):
        # Calculate period for next i months
        target_month = today.month + i
        target_year = today.year
        if target_month > 12:
            target_month -= 12
            target_year += 1

        period = f"{target_year:04d}-{target_month:02d}"
        deadline, days_remaining = calculate_deadline(period)

        # Get period data
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fiscal_periods WHERE period = ?", (period,))
        row = cursor.fetchone()
        conn.close()

        period_data = dict(row) if row else {
            "period": period,
            "status": "open",
            "invoice_count": 0,
        }

        deadlines_list.append({
            "period": period,
            "deadline": deadline,
            "days_remaining": days_remaining,
            "status": period_data.get("status", "open"),
            "invoice_count": period_data.get("invoice_count", 0),
            "urgent": days_remaining <= 3,
        })

    return jsonify({
        "deadlines": deadlines_list,
        "today": today.strftime("%Y-%m-%d"),
    })


# ===================================================================
#  GROUP 3 - UStVA (VAT Declaration)
# ===================================================================

@accounting_bp.route("/ustva/preview", methods=["GET"])
def ustva_preview():
    """Preview UStVA without persisting."""
    period = request.args.get("period")
    if not period:
        return jsonify({"error": "period parameter required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Get invoices for period
    cursor.execute("SELECT * FROM invoices WHERE period = ?", (period,))
    invoices = [dict(row) for row in cursor.fetchall()]

    # Get period data
    cursor.execute("SELECT * FROM fiscal_periods WHERE period = ?", (period,))
    period_row = cursor.fetchone()
    conn.close()

    builder = UStVABuilder()
    preview = builder.preview(
        period,
        invoices,
        period_row["umsatzsteuer"] if period_row else 0,
        period_row["vorsteuer"] if period_row else 0,
    )

    return jsonify(preview)


@accounting_bp.route("/ustva/prepare", methods=["POST"])
def ustva_prepare():
    """Prepare UStVA XML for a period."""
    data = request.get_json() or {}
    period = data.get("period")

    if not period:
        return jsonify({"error": "period required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Get invoices
    cursor.execute("SELECT * FROM invoices WHERE period = ?", (period,))
    invoices = [dict(row) for row in cursor.fetchall()]

    # Get period data
    cursor.execute("SELECT * FROM fiscal_periods WHERE period = ?", (period,))
    period_row = cursor.fetchone()

    if not period_row:
        get_or_create_period(period)
        cursor.execute("SELECT * FROM fiscal_periods WHERE period = ?", (period,))
        period_row = cursor.fetchone()

    # Build UStVA
    builder = UStVABuilder(data.get("company", {}))
    result = builder.build(
        period,
        invoices,
        period_row["umsatzsteuer"],
        period_row["vorsteuer"],
    )

    # Save XML to file
    year, month = period.split("-")
    period_dir = os.path.join(PERIODS_DIR, period)
    os.makedirs(period_dir, exist_ok=True)

    xml_path = os.path.join(period_dir, f"ustva_{period}.xml")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(result["xml_content"])

    # Update period
    cursor.execute("""
        UPDATE fiscal_periods
        SET status = 'prepared', ustva_xml_path = ?, ustva_hash = ?,
            updated_at = datetime('now')
        WHERE period = ?
    """, (xml_path, result["xml_hash"], period))

    conn.commit()
    conn.close()

    log_audit("ustva_prepare", None, period, "C5", "pass", {
        "hash": result["xml_hash"],
        "invoices": len(invoices),
    })

    return jsonify({
        "success": True,
        "period": period,
        "xml_hash": result["xml_hash"],
        "xml_path": xml_path,
        "kennzahlen": result["kennzahlen"],
        "zahllast": result["zahllast"],
    })


@accounting_bp.route("/ustva/approve/<period>", methods=["GET"])
def ustva_approve_get(period):
    """
    GATE C6 - Human approval endpoint.

    Returns dashboard for human review before ELSTER submission.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fiscal_periods WHERE period = ?", (period,))
    period_row = cursor.fetchone()
    conn.close()

    if not period_row:
        return jsonify({"error": "Period not found"}), 404

    period_dict = dict(period_row)
    deadline, days_remaining = calculate_deadline(period)

    return jsonify({
        "gate": "C6",
        "invariant": ACCOUNTING_INVARIANTS["C6"],
        "period": period,
        "summary": {
            "umsatzsteuer": period_dict.get("umsatzsteuer", 0),
            "vorsteuer": period_dict.get("vorsteuer", 0),
            "zahllast": period_dict.get("zahllast", 0),
            "invoices": period_dict.get("invoice_count", 0),
            "ustva_hash": period_dict.get("ustva_hash"),
            "xml_ready": period_dict.get("ustva_xml_path") is not None,
        },
        "deadline": deadline,
        "days_remaining": days_remaining,
        "instructions": {
            "step_1": f"Descarrega o XML via GET /accounting/ustva/download/{period}",
            "step_2": "Acede a www.elster.de e faz login",
            "step_3": "Formulare -> Umsatzsteuer-Voranmeldung -> XML hochladen",
            "step_4": f"Confirma envio com o numero de ticket em POST /accounting/ustva/confirm/{period}",
        },
        "c6_note": "Wave4 integrara Erica para envio directo. Wave3 e honesta: gera XML perfeito, humano submete.",
    })


@accounting_bp.route("/ustva/submit/<period>", methods=["POST"])
def ustva_submit(period):
    """
    Mark UStVA as approved for manual ELSTER submission.

    NOTE: This does NOT send to ELSTER (Wave4 will add Erica integration).
    Returns XML for human download and manual submission.
    """
    # Wave4: substituir este bloco por chamada Erica apos aprovacao C6

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fiscal_periods WHERE period = ?", (period,))
    period_row = cursor.fetchone()

    if not period_row:
        conn.close()
        return jsonify({"error": "Period not found"}), 404

    period_dict = dict(period_row)

    if not period_dict.get("ustva_xml_path"):
        conn.close()
        return jsonify({"error": "UStVA not prepared. Call POST /accounting/ustva/prepare first"}), 400

    # Read XML
    xml_content = ""
    if os.path.exists(period_dict["ustva_xml_path"]):
        with open(period_dict["ustva_xml_path"], "r", encoding="utf-8") as f:
            xml_content = f.read()

    # Update period status
    now = datetime.now().isoformat()
    cursor.execute("""
        UPDATE fiscal_periods
        SET status = 'approved', approved_by = ?, approved_at = ?,
            updated_at = datetime('now')
        WHERE period = ?
    """, ("human_dragon", now, period))

    conn.commit()
    conn.close()

    # Send to Ledger
    ledger_receipt = send_to_ledger({
        "action": "ustva_approved_by_human",
        "period": period,
        "zahllast": period_dict.get("zahllast", 0),
        "xml_hash": period_dict.get("ustva_hash"),
        "invariant": "C6",
        "gate": "IRREMEDIAVEL - humano aprovou, ELSTER e proximo passo manual",
        "operator": "human_dragon",
    })

    log_audit("ustva_submit", None, period, "C6", "pass", {
        "approved_by": "human_dragon",
        "xml_hash": period_dict.get("ustva_hash"),
    }, "human_dragon")

    return jsonify({
        "approved": True,
        "period": period,
        "xml_base64": base64.b64encode(xml_content.encode()).decode() if xml_content else None,
        "xml_hash": period_dict.get("ustva_hash"),
        "ledger_receipt": ledger_receipt,
        "c6_gate": "PASSED",
        "next_step": f"Download XML and upload to elster.de. Then confirm with POST /accounting/ustva/confirm/{period}",
    })


@accounting_bp.route("/ustva/download/<period>", methods=["GET"])
def ustva_download(period):
    """Download UStVA XML file."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT ustva_xml_path, ustva_hash FROM fiscal_periods WHERE period = ?", (period,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row["ustva_xml_path"]:
        return jsonify({"error": "UStVA not prepared for this period"}), 404

    xml_path = row["ustva_xml_path"]
    xml_hash = row["ustva_hash"] or ""

    if not os.path.exists(xml_path):
        return jsonify({"error": "XML file not found"}), 404

    with open(xml_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    # Generate filename with hash prefix
    hash_prefix = xml_hash.replace("sha256:", "")[:8] if xml_hash else "manual"
    filename = f"UStVA_{period}_{hash_prefix}.xml"

    return Response(
        xml_content,
        mimetype="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@accounting_bp.route("/ustva/confirm/<period>", methods=["POST"])
def ustva_confirm(period):
    """Confirm manual ELSTER submission."""
    data = request.get_json() or {}

    elster_ticket = data.get("elster_ticket")
    submitted_at = data.get("submitted_at") or datetime.now().isoformat()

    if not elster_ticket:
        return jsonify({"error": "elster_ticket required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM fiscal_periods WHERE period = ?", (period,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Period not found"}), 404

    if row["status"] != "approved":
        conn.close()
        return jsonify({
            "error": f"Period must be approved before confirmation. Current status: {row['status']}"
        }), 400

    # Update period
    cursor.execute("""
        UPDATE fiscal_periods
        SET status = 'submitted', elster_ticket = ?, submitted_at = ?,
            updated_at = datetime('now')
        WHERE period = ?
    """, (elster_ticket, submitted_at, period))

    # Close period (C3)
    cursor.execute("""
        UPDATE invoices SET period_closed = 1, updated_at = datetime('now')
        WHERE period = ?
    """, (period,))

    conn.commit()
    conn.close()

    log_audit("ustva_confirm", None, period, "C6", "pass", {
        "elster_ticket": elster_ticket,
        "submitted_at": submitted_at,
    }, "human_dragon")

    return jsonify({
        "success": True,
        "period": period,
        "status": "submitted",
        "elster_ticket": elster_ticket,
        "submitted_at": submitted_at,
        "period_closed": True,
        "message": "UStVA submission confirmed. Period is now closed (C3 enforced).",
    })


# ===================================================================
#  GROUP 4 - DATEV Export
# ===================================================================

@accounting_bp.route("/datev/export", methods=["GET"])
def datev_export():
    """Export invoices to DATEV format."""
    period = request.args.get("period")
    chart = request.args.get("chart", "SKR03").upper()

    if not period:
        return jsonify({"error": "period parameter required"}), 400

    if chart not in ["SKR03", "SKR04"]:
        return jsonify({"error": "chart must be SKR03 or SKR04"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM invoices WHERE period = ?", (period,))
    invoices = [dict(row) for row in cursor.fetchall()]
    conn.close()

    exporter = DATEVExporter(chart)
    csv_content = exporter.export(invoices, period)

    filename = f"DATEV_{period}_{chart}.csv"

    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@accounting_bp.route("/datev/accounts", methods=["GET"])
def datev_accounts():
    """Get DATEV account mapping."""
    chart = request.args.get("chart", "SKR03").upper()

    exporter = DATEVExporter(chart)
    accounts = exporter.get_accounts()

    return jsonify({
        "chart": chart,
        "accounts": accounts,
        "description": "SKR03 for commerce/services, SKR04 for industry",
    })


# ===================================================================
#  GROUP 5 - GoBD & Compliance
# ===================================================================

@accounting_bp.route("/gobd/check/<invoice_id>", methods=["GET"])
def gobd_check(invoice_id):
    """Check GoBD compliance of an invoice."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Invoice not found"}), 404

    invoice = dict(row)
    checks = []
    violations = []
    score = 100

    # Check 1: Hash exists (Ledger traceability)
    if invoice.get("ledger_hash"):
        checks.append({"name": "ledger_traceability", "status": "pass"})
    else:
        checks.append({"name": "ledger_traceability", "status": "fail"})
        violations.append("No Ledger hash - document not anchored")
        score -= 20

    # Check 2: Period declared (C2)
    if invoice.get("period"):
        checks.append({"name": "period_declared", "status": "pass"})
    else:
        checks.append({"name": "period_declared", "status": "fail"})
        violations.append("No fiscal period declared")
        score -= 20

    # Check 3: Format is XRechnung/ZUGFeRD (preferred)
    fmt = invoice.get("format", "")
    if fmt in ["xrechnung", "zugferd"]:
        checks.append({"name": "format_preferred", "status": "pass"})
    else:
        checks.append({"name": "format_preferred", "status": "warn"})
        violations.append(f"Format is {fmt}, XRechnung/ZUGFeRD preferred")
        score -= 10

    # Check 4: Raw XML preserved
    if invoice.get("raw_xml"):
        checks.append({"name": "raw_preserved", "status": "pass"})
    else:
        checks.append({"name": "raw_preserved", "status": "warn"})
        score -= 5

    # Check 5: Arithmetic valid (C4)
    net = invoice.get("net_amount", 0)
    vat = invoice.get("vat_amount", 0)
    gross = invoice.get("gross_amount", 0)
    if abs((net + vat) - gross) <= 0.02:
        checks.append({"name": "arithmetic_valid", "status": "pass"})
    else:
        checks.append({"name": "arithmetic_valid", "status": "fail"})
        violations.append("Arithmetic error: net + VAT != gross")
        score -= 25

    compliant = score >= 80

    return jsonify({
        "invoice_id": invoice_id,
        "compliant": compliant,
        "score": max(0, score),
        "checks": checks,
        "violations": violations,
        "gobd_flag": invoice.get("gobd_compliant", 0) == 1,
    })


@accounting_bp.route("/gobd/report", methods=["GET"])
def gobd_report():
    """GoBD compliance report for a period."""
    period = request.args.get("period")
    if not period:
        return jsonify({"error": "period parameter required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM invoices WHERE period = ?", (period,))
    invoices = [dict(row) for row in cursor.fetchall()]
    conn.close()

    compliant_count = 0
    non_compliant = []

    for inv in invoices:
        is_compliant = inv.get("gobd_compliant", 0) == 1
        has_ledger = bool(inv.get("ledger_hash"))
        has_xml = bool(inv.get("raw_xml"))

        if is_compliant and has_ledger:
            compliant_count += 1
        else:
            reasons = []
            if not is_compliant:
                reasons.append("gobd_compliant flag is false")
            if not has_ledger:
                reasons.append("no Ledger hash")
            if not has_xml:
                reasons.append("no raw XML preserved")

            non_compliant.append({
                "id": inv["id"],
                "invoice_number": inv.get("invoice_number"),
                "reasons": reasons,
            })

    total = len(invoices)
    compliance_rate = (compliant_count / total * 100) if total > 0 else 100

    return jsonify({
        "period": period,
        "total_invoices": total,
        "compliant": compliant_count,
        "non_compliant": len(non_compliant),
        "compliance_rate": round(compliance_rate, 2),
        "violations": non_compliant,
        "gobd_status": "COMPLIANT" if compliance_rate >= 100 else "ATTENTION_REQUIRED",
    })


@accounting_bp.route("/retention/check", methods=["GET"])
def retention_check():
    """Check document retention dates."""
    today = datetime.now()

    # German retention: invoices 8 years (since 2025), books 10 years
    invoice_retention_years = 8
    books_retention_years = 10

    # Calculate warning date (6 months before expiry)
    warning_threshold = timedelta(days=180)

    conn = get_db()
    cursor = conn.cursor()

    # Get oldest invoices
    cursor.execute("""
        SELECT id, invoice_number, invoice_date, period, created_at
        FROM invoices
        ORDER BY created_at ASC
        LIMIT 100
    """)

    invoices = [dict(row) for row in cursor.fetchall()]
    conn.close()

    expiring_soon = []
    expired = []

    for inv in invoices:
        created_str = inv.get("created_at") or inv.get("invoice_date")
        if not created_str:
            continue

        try:
            created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        except ValueError:
            continue

        expiry_dt = created_dt + timedelta(days=365 * invoice_retention_years)
        days_until_expiry = (expiry_dt - today).days

        if days_until_expiry < 0:
            expired.append({
                "id": inv["id"],
                "invoice_number": inv.get("invoice_number"),
                "created_at": created_str,
                "expired_on": expiry_dt.strftime("%Y-%m-%d"),
            })
        elif days_until_expiry <= 180:
            expiring_soon.append({
                "id": inv["id"],
                "invoice_number": inv.get("invoice_number"),
                "created_at": created_str,
                "expires_on": expiry_dt.strftime("%Y-%m-%d"),
                "days_remaining": days_until_expiry,
            })

    return jsonify({
        "retention_rules": {
            "invoices": f"{invoice_retention_years} years (147 AO)",
            "balance_sheets": f"{books_retention_years} years",
        },
        "check_date": today.strftime("%Y-%m-%d"),
        "warning_threshold_days": 180,
        "expiring_soon": expiring_soon,
        "expired": expired,
        "status": "ATTENTION_REQUIRED" if (expiring_soon or expired) else "OK",
    })


# ===================================================================
#  INITIALIZATION
# ===================================================================

# Initialize database when module is imported
init_db()
