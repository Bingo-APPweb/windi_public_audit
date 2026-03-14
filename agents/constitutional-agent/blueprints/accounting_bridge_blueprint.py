"""
W-ACCOUNTING-001 Accounting Bridge v1.0.0
==========================================
Padrão: mesmo do W-JOURN/COMM/LEGAL/NOTARY/AUDIT/COMPLIANCE
Porta:  :8091 (Sandbox Core — domínio extension)
Prefix: /accounting/bridge/

Endpoints:
  POST /accounting/bridge/open     → cria sessão contabilística (F1)
  POST /accounting/bridge/save     → auto-save lançamentos/valores
  POST /accounting/bridge/publish  → gate humano + Ledger seal + QR
  GET  /accounting/bridge/status   → estado completo da sessão

Stage Map (F1-F6):
  F1 = Documento financeiro recebido
  F2 = Classificação contabilística
  F3 = Validação de valores
  F4 = Reconciliação
  F5 = Aguarda aprovação humana (I9 GATE)
  F6 = Selado no Ledger + QR gerado

Invariants:
  I9  — Prohibition of Autonomy Escalation (aprovação financeira exige human_approved)
  I11 — Permanência de Evidência Criptográfica (Ledger IRREMEDIÁVEL)
  C6  — IA prepara, humano aprova (documentos financeiros)
"""

from flask import Blueprint, request, jsonify
import sqlite3, hashlib, uuid, datetime, json, os, logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger("W-ACCOUNTING-001")

accounting_bridge_bp = Blueprint("accounting_bridge", __name__, url_prefix="/accounting/bridge")

# ─────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────
DB_PATH = os.environ.get("WINDI_ACCOUNTING_DB", "/opt/windi/data/accounting_bridge.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS accounting_sessions (
            id              TEXT PRIMARY KEY,
            wallet_id       TEXT,
            title           TEXT NOT NULL,
            doc_type        TEXT DEFAULT 'invoice',
            currency        TEXT DEFAULT 'EUR',
            total_amount    REAL DEFAULT 0.0,
            tax_amount      REAL DEFAULT 0.0,
            net_amount      REAL DEFAULT 0.0,
            fiscal_year     TEXT,
            fiscal_period   TEXT,
            counterparty    TEXT,
            status          TEXT DEFAULT 'draft',
            stage           TEXT DEFAULT 'F1',
            notes           TEXT DEFAULT '',
            metadata        TEXT DEFAULT '{}',
            ledger_receipt  TEXT,
            verify_url      TEXT,
            qr_hash         TEXT,
            human_approved  INTEGER DEFAULT 0,
            approver_name   TEXT,
            approver_role   TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS accounting_entries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            entry_id        TEXT NOT NULL,
            account_code    TEXT,
            account_name    TEXT,
            debit           REAL DEFAULT 0.0,
            credit          REAL DEFAULT 0.0,
            description     TEXT,
            cost_center     TEXT,
            created_at      TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES accounting_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS accounting_taxes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            tax_type        TEXT NOT NULL,
            tax_rate        REAL,
            tax_base        REAL,
            tax_amount      REAL,
            created_at      TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES accounting_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS accounting_revisions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            content     TEXT NOT NULL,
            saved_at    TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES accounting_sessions(id)
        );
        """)

# Init na importação
try:
    init_db()
    logger.info("W-ACCOUNTING-001 DB inicializado")
except Exception as e:
    logger.error(f"DB init error: {e}")


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
STAGES = ["F1", "F2", "F3", "F4", "F5", "F6"]

DOC_TYPES = [
    "invoice",
    "receipt",
    "credit_note",
    "debit_note",
    "balance_sheet",
    "income_statement",
    "cash_flow",
    "budget",
    "expense_report",
    "payroll",
    "tax_return",
    "outro"
]

CURRENCIES = ["EUR", "USD", "BRL", "GBP", "CHF"]

TAX_TYPES = ["VAT", "IVA", "ICMS", "ISS", "IRPF", "IRPJ", "USt", "MwSt"]


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gen_session_id():
    return "ACCT-" + uuid.uuid4().hex[:8].upper()

def gen_entry_id():
    return "ENT-" + uuid.uuid4().hex[:6].upper()

def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def safe_float(value, default=0.0):
    """Converte valor para float de forma segura."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def seal_ledger(session_id: str, title: str, content_hash: str,
                wallet_id: str = "human-dragon", doc_type: str = "financial") -> dict:
    """Envia receipt ao Forensic Ledger :8101"""
    import urllib.request, urllib.error

    receipt_id = f"WINDI-ACCT-{session_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payload = json.dumps({
        "id":               receipt_id,
        "actor":            wallet_id,
        "app":              "accounting-bridge",
        "doc_name":         title,
        "doc_type":         f"accounting_{doc_type}",
        "governance_level": "CRITICAL",
        "content":          f"SHA-256:{content_hash} | Documento financeiro selado via Accounting Bridge F6"
    }).encode()

    try:
        req = urllib.request.Request(
            "http://localhost:8101/api/receipts",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            result = json.loads(r.read())
            verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"
            return {"receipt_id": receipt_id, "hash": content_hash,
                    "verify_url": verify_url, "ledger_status": "SEALED"}
    except Exception as e:
        logger.warning(f"Ledger seal falhou: {e}")
        verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"
        return {"receipt_id": receipt_id, "hash": content_hash,
                "verify_url": verify_url, "ledger_status": "PENDING_RETRY"}


# ─────────────────────────────────────────────
# POST /accounting/bridge/open
# ─────────────────────────────────────────────
@accounting_bridge_bp.route("/open", methods=["POST"])
def bridge_open():
    data = request.get_json(silent=True) or {}
    title         = data.get("title", "Documento Financeiro")
    wallet_id     = data.get("wallet_id", "anonymous")
    doc_type      = data.get("doc_type", "invoice")
    currency      = data.get("currency", "EUR")
    fiscal_year   = data.get("fiscal_year", str(datetime.datetime.now().year))
    fiscal_period = data.get("fiscal_period", "")
    counterparty  = data.get("counterparty", "")

    session_id = gen_session_id()
    ts = now_iso()

    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO accounting_sessions
                  (id, wallet_id, title, doc_type, currency, fiscal_year, fiscal_period, counterparty, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (session_id, wallet_id, title, doc_type, currency, fiscal_year, fiscal_period, counterparty, ts, ts))

        logger.info(f"[ACCOUNTING] Sessão aberta: {session_id} | '{title}' | tipo={doc_type}")
        return jsonify({
            "status":        "ok",
            "session_id":    session_id,
            "stage":         "F1",
            "title":         title,
            "doc_type":      doc_type,
            "currency":      currency,
            "fiscal_year":   fiscal_year,
            "message":       "Sessão contabilística criada. Pronto para lançamentos.",
            "created_at":    ts
        }), 201

    except Exception as e:
        logger.error(f"bridge_open error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# POST /accounting/bridge/save
# ─────────────────────────────────────────────
@accounting_bridge_bp.route("/save", methods=["POST"])
def bridge_save():
    data = request.get_json(silent=True) or {}
    session_id   = data.get("session_id")
    entries      = data.get("entries", [])
    taxes        = data.get("taxes", [])
    total_amount = safe_float(data.get("total_amount"))
    tax_amount   = safe_float(data.get("tax_amount"))
    net_amount   = safe_float(data.get("net_amount"))
    notes        = data.get("notes", "")
    stage        = data.get("stage", "F3")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    ts = now_iso()

    try:
        with get_db() as db:
            row = db.execute("SELECT id, status FROM accounting_sessions WHERE id=?",
                             (session_id,)).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "approved":
                return jsonify({"status": "error",
                                "detail": "Documento já aprovado — I11 IRREMEDIÁVEL"}), 409

            # Adicionar lançamentos
            entries_added = 0
            total_debit = 0.0
            total_credit = 0.0
            for e in entries:
                entry_id = e.get("id", gen_entry_id())
                debit = safe_float(e.get("debit"))
                credit = safe_float(e.get("credit"))
                total_debit += debit
                total_credit += credit
                db.execute("""
                    INSERT INTO accounting_entries
                      (session_id, entry_id, account_code, account_name, debit, credit, description, cost_center, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (session_id, entry_id, e.get("account_code", ""),
                      e.get("account_name", ""), debit, credit,
                      e.get("description", ""), e.get("cost_center", ""), ts))
                entries_added += 1

            # Adicionar impostos
            taxes_added = 0
            for t in taxes:
                db.execute("""
                    INSERT INTO accounting_taxes
                      (session_id, tax_type, tax_rate, tax_base, tax_amount, created_at)
                    VALUES (?,?,?,?,?,?)
                """, (session_id, t.get("tax_type", "VAT"),
                      safe_float(t.get("tax_rate")),
                      safe_float(t.get("tax_base")),
                      safe_float(t.get("tax_amount")), ts))
                taxes_added += 1

            # Calcular net se não fornecido
            if net_amount == 0 and total_amount > 0:
                net_amount = total_amount - tax_amount

            # Atualizar sessão
            db.execute("""
                UPDATE accounting_sessions
                SET total_amount=?, tax_amount=?, net_amount=?, notes=?, stage=?, updated_at=?
                WHERE id=?
            """, (total_amount, tax_amount, net_amount, notes, stage, ts, session_id))

            # Gravar revisão
            revision_content = json.dumps({
                "entries_count": entries_added,
                "taxes_count": taxes_added,
                "total_amount": total_amount,
                "balance_check": abs(total_debit - total_credit) < 0.01
            })
            db.execute("""
                INSERT INTO accounting_revisions (session_id, content, saved_at)
                VALUES (?,?,?)
            """, (session_id, revision_content, ts))

        # Verificar balanceamento
        balanced = abs(total_debit - total_credit) < 0.01
        content_hash = compute_hash(f"{total_amount}{tax_amount}{net_amount}")

        logger.info(f"[ACCOUNTING] Auto-save: {session_id} | stage={stage} | amount={total_amount}")
        return jsonify({
            "status":         "ok",
            "session_id":     session_id,
            "stage":          stage,
            "content_hash":   content_hash,
            "entries_added":  entries_added,
            "taxes_added":    taxes_added,
            "totals": {
                "total_amount": total_amount,
                "tax_amount":   tax_amount,
                "net_amount":   net_amount,
                "total_debit":  round(total_debit, 2),
                "total_credit": round(total_credit, 2),
                "balanced":     balanced
            },
            "saved_at":       ts,
            "message":        "Documento financeiro guardado." + (" ⚠️ Lançamentos não balanceados!" if not balanced else "")
        }), 200

    except Exception as e:
        logger.error(f"bridge_save error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# POST /accounting/bridge/publish
# I9 GATE + C6: documentos financeiros SEMPRE exigem human_approved
# ─────────────────────────────────────────────
@accounting_bridge_bp.route("/publish", methods=["POST"])
def bridge_publish():
    data           = request.get_json(silent=True) or {}
    session_id     = data.get("session_id")
    human_approved = data.get("human_approved", False)
    approver_name  = data.get("approver_name", "Financial Controller")
    approver_role  = data.get("approver_role", "CFO")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, title, total_amount, tax_amount, net_amount, currency,
                       status, wallet_id, doc_type, fiscal_year
                FROM accounting_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "approved":
                return jsonify({
                    "status":     "already_approved",
                    "session_id": session_id,
                    "verify_url": db.execute(
                        "SELECT verify_url FROM accounting_sessions WHERE id=?",
                        (session_id,)).fetchone()["verify_url"],
                    "message":    "I11 — documento já aprovado, imutável."
                }), 200

            # ── I9 GATE + C6 (Financial documents ALWAYS require human) ──
            if not human_approved:
                db.execute("""
                    UPDATE accounting_sessions SET stage='F5', updated_at=? WHERE id=?
                """, (now_iso(), session_id))
                logger.info(f"[ACCOUNTING] I9+C6 Gate: aguarda aprovação — {session_id}")
                return jsonify({
                    "status":     "awaiting_approval",
                    "session_id": session_id,
                    "stage":      "F5",
                    "amount":     row["total_amount"],
                    "currency":   row["currency"],
                    "message":    "I9 + C6 — documento financeiro requer aprovação humana (human_approved=true). "
                                  "AI prepares. Human approves. WINDI guarantees.",
                    "warning":    "Documentos financeiros NUNCA podem ser aprovados automaticamente."
                }), 202
            # ─────────────────────────────────────────

            # Verificar balanceamento dos lançamentos
            entries = db.execute("""
                SELECT SUM(debit) as total_debit, SUM(credit) as total_credit
                FROM accounting_entries WHERE session_id=?
            """, (session_id,)).fetchone()

            total_debit = entries["total_debit"] or 0
            total_credit = entries["total_credit"] or 0
            balanced = abs(total_debit - total_credit) < 0.01

            # Contar lançamentos e impostos
            entries_count = db.execute(
                "SELECT COUNT(*) FROM accounting_entries WHERE session_id=?",
                (session_id,)).fetchone()[0]
            taxes_count = db.execute(
                "SELECT COUNT(*) FROM accounting_taxes WHERE session_id=?",
                (session_id,)).fetchone()[0]

            # Hash do conteúdo final
            full_content = f"{row['total_amount']}|{row['tax_amount']}|{row['net_amount']}|{row['currency']}|{balanced}"
            content_hash = compute_hash(full_content)

            # Selar no Ledger
            seal = seal_ledger(
                session_id  = session_id,
                title       = row["title"],
                content_hash= content_hash,
                wallet_id   = row["wallet_id"] or "human-dragon",
                doc_type    = row["doc_type"] or "financial"
            )

            ts = now_iso()
            db.execute("""
                UPDATE accounting_sessions
                SET status='approved', stage='F6',
                    human_approved=1,
                    approver_name=?, approver_role=?,
                    ledger_receipt=?, verify_url=?, qr_hash=?,
                    updated_at=?
                WHERE id=?
            """, (approver_name, approver_role, seal["receipt_id"],
                  seal["verify_url"], content_hash, ts, session_id))

        logger.info(f"[ACCOUNTING] APPROVED: {session_id} | amount={row['total_amount']} | receipt={seal['receipt_id']}")
        return jsonify({
            "status":         "approved",
            "session_id":     session_id,
            "stage":          "F6",
            "ledger_receipt": seal["receipt_id"],
            "content_hash":   content_hash,
            "verify_url":     seal["verify_url"],
            "qr_payload":     f"WINDI:{seal['receipt_id']}|{content_hash[:16]}",
            "ledger_status":  seal["ledger_status"],
            "financial_summary": {
                "total_amount": row["total_amount"],
                "tax_amount":   row["tax_amount"],
                "net_amount":   row["net_amount"],
                "currency":     row["currency"],
                "entries":      entries_count,
                "taxes":        taxes_count,
                "balanced":     balanced
            },
            "approver": {
                "name":         approver_name,
                "role":         approver_role
            },
            "approved_at":    ts,
            "message":        "Documento financeiro aprovado. I11 IRREMEDIÁVEL. C6 enforced. "
                              "AI prepares. Human approves. WINDI guarantees."
        }), 200

    except Exception as e:
        logger.error(f"bridge_publish error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────
# GET /accounting/bridge/status?session_id=XXX
# ─────────────────────────────────────────────
@accounting_bridge_bp.route("/status", methods=["GET"])
def bridge_status():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, wallet_id, title, doc_type, currency,
                       total_amount, tax_amount, net_amount,
                       fiscal_year, fiscal_period, counterparty,
                       status, stage, human_approved,
                       approver_name, approver_role,
                       ledger_receipt, verify_url, qr_hash,
                       created_at, updated_at
                FROM accounting_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404

            # Obter lançamentos
            entries = db.execute("""
                SELECT entry_id, account_code, account_name, debit, credit, description
                FROM accounting_entries WHERE session_id=?
            """, (session_id,)).fetchall()
            entries_list = [{"id": e["entry_id"], "account_code": e["account_code"],
                            "account_name": e["account_name"], "debit": e["debit"],
                            "credit": e["credit"], "description": e["description"]} for e in entries]

            # Obter impostos
            taxes = db.execute("""
                SELECT tax_type, tax_rate, tax_base, tax_amount
                FROM accounting_taxes WHERE session_id=?
            """, (session_id,)).fetchall()
            taxes_list = [{"tax_type": t["tax_type"], "tax_rate": t["tax_rate"],
                          "tax_base": t["tax_base"], "tax_amount": t["tax_amount"]} for t in taxes]

            # Verificar balanceamento
            total_debit = sum(e["debit"] for e in entries)
            total_credit = sum(e["credit"] for e in entries)
            balanced = abs(total_debit - total_credit) < 0.01

            # Contar revisões
            rev_count = db.execute(
                "SELECT COUNT(*) FROM accounting_revisions WHERE session_id=?",
                (session_id,)).fetchone()[0]

        return jsonify({
            "status":           "ok",
            "session_id":       row["id"],
            "wallet_id":        row["wallet_id"],
            "title":            row["title"],
            "doc_type":         row["doc_type"],
            "currency":         row["currency"],
            "financial": {
                "total_amount": row["total_amount"],
                "tax_amount":   row["tax_amount"],
                "net_amount":   row["net_amount"],
                "total_debit":  round(total_debit, 2),
                "total_credit": round(total_credit, 2),
                "balanced":     balanced
            },
            "fiscal": {
                "year":         row["fiscal_year"],
                "period":       row["fiscal_period"]
            },
            "counterparty":     row["counterparty"],
            "stage":            row["stage"],
            "session_status":   row["status"],
            "human_approved":   bool(row["human_approved"]),
            "approver": {
                "name":         row["approver_name"],
                "role":         row["approver_role"]
            } if row["approver_name"] else None,
            "entries":          entries_list,
            "entries_count":    len(entries_list),
            "taxes":            taxes_list,
            "taxes_count":      len(taxes_list),
            "revisions":        rev_count,
            "ledger_receipt":   row["ledger_receipt"],
            "verify_url":       row["verify_url"],
            "qr_hash":          row["qr_hash"],
            "created_at":       row["created_at"],
            "updated_at":       row["updated_at"],
            "invariants": {
                "I9":  "ENFORCED — aprovação requer human_approved",
                "I11": "ENFORCED — Ledger IRREMEDIÁVEL após F6",
                "C6":  "ENFORCED — IA prepara, humano aprova (financeiro)"
            },
            "stage_map": {
                "F1": "Documento financeiro recebido",
                "F2": "Classificação contabilística",
                "F3": "Validação de valores",
                "F4": "Reconciliação",
                "F5": "Aguarda aprovação",
                "F6": "Selado no Ledger"
            },
            "doc_types_available": DOC_TYPES,
            "currencies_available": CURRENCIES
        }), 200

    except Exception as e:
        logger.error(f"bridge_status error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500
