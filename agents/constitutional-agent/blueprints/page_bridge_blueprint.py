"""
W-PAGE-001 Institutional Page Bridge v1.0.0
=============================================
Porta:  :8091 (Sandbox Core — domain extension)
Prefix: /page/bridge/

Endpoints:
  POST /page/bridge/open     → cria sessão documental (W1)
  POST /page/bridge/render   → dispara Export Engine → preview visual (W3) ★ ESPECIAL
  POST /page/bridge/save     → auto-save conteúdo + campos
  POST /page/bridge/publish  → I9 gate + Ledger seal IRREMEDIÁVEL (W6)
  GET  /page/bridge/status   → estado completo + render_status

Stage Map W1-W6:
  W1 = Pedido recebido (tipo, emitente, dados)
  W2 = Campos estruturados (nome, data, cláusulas, ISP)
  W3 = Render gerado → Export Engine (:8103) → PDF preview
  W4 = Revisão visual humana (RENDER_APPROVED obrigatório)
  W5 = Aguarda aprovação final (I9 GATE)
  W6 = Selado no Ledger IRREMEDIÁVEL

RENDER_LOCK — Princípio central:
  O documento DEVE ser renderizado (W3) e visualmente aprovado (W4)
  antes de qualquer publicação. Sem render aprovado = bloqueado.
  Garante que o humano aprova a aparência REAL, não só o texto.

  PENDING   → render ainda não solicitado
  RENDERING → Export Engine a processar
  RENDERED  → preview disponível, aguarda revisão humana
  APPROVED  → humano aprovou a aparência visual
  LOCKED    → após W5, layout imutável (só conteúdo pode ser corrigido)

Doc types suportados:
  certidao · diploma · ato_oficial · declaracao_institucional · atestado · alvara

Deploy:
  cp page_bridge_blueprint.py /opt/windi/agents/constitutional-agent/blueprints/
  # agent.py: from blueprints.page_bridge_blueprint import page_bridge_bp
  #           app.register_blueprint(page_bridge_bp)
"""

from flask import Blueprint, request, jsonify
import sqlite3, hashlib, uuid, datetime, json, os, logging, urllib.request

logger = logging.getLogger("W-PAGE-001")

page_bridge_bp = Blueprint("page_bridge", __name__, url_prefix="/page/bridge")

DB_PATH      = os.environ.get("WINDI_DB_PATH", "/opt/windi/data/page_bridge.db")
EXPORT_URL   = "http://localhost:8103"   # Export Engine
LEDGER_URL   = "http://localhost:8101"   # Forensic Ledger

# ── Tipos de documento suportados ──────────────────────────
DOC_TYPES = {
    "certidao":                "Certidão",
    "diploma":                 "Diploma",
    "ato_oficial":             "Ato Oficial",
    "declaracao_institucional":"Declaração Institucional",
    "atestado":                "Atestado",
    "alvara":                  "Alvará",
}

# ── Estados do Renderer ─────────────────────────────────────
RENDER_STATUS = {
    "PENDING":    "Render ainda não solicitado",
    "RENDERING":  "Export Engine a processar",
    "RENDERED":   "Preview disponível — aguarda revisão humana",
    "APPROVED":   "Aparência visual aprovada pelo humano",
    "LOCKED":     "Layout imutável — documento em fase final",
    "FAILED":     "Render falhou — verificar Export Engine (:8103)",
}

# ── Helpers ─────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS page_sessions (
            id               TEXT PRIMARY KEY,
            wallet_id        TEXT,
            doc_type         TEXT NOT NULL,
            title            TEXT NOT NULL,
            emitter          TEXT,
            isp_id           TEXT,
            fields           TEXT DEFAULT '{}',
            content          TEXT,
            render_status    TEXT DEFAULT 'PENDING',
            render_url       TEXT,
            render_hash      TEXT,
            render_approved  INTEGER DEFAULT 0,
            render_approved_at TEXT,
            status           TEXT DEFAULT 'draft',
            stage            TEXT DEFAULT 'W1',
            ledger_receipt   TEXT,
            verify_url       TEXT,
            content_hash     TEXT,
            human_approved   INTEGER DEFAULT 0,
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS page_revisions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   TEXT NOT NULL,
            fields       TEXT NOT NULL,
            content      TEXT,
            stage        TEXT NOT NULL,
            saved_at     TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES page_sessions(id)
        );
        CREATE TABLE IF NOT EXISTS page_renders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   TEXT NOT NULL,
            render_url   TEXT,
            render_hash  TEXT,
            isp_id       TEXT,
            requested_at TEXT NOT NULL,
            completed_at TEXT,
            status       TEXT DEFAULT 'RENDERING',
            FOREIGN KEY(session_id) REFERENCES page_sessions(id)
        );
        """)

try:
    init_db()
    logger.info("W-PAGE-001 DB inicializado")
except Exception as e:
    logger.error(f"DB init error: {e}")


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gen_session_id():
    return "PAGE-" + uuid.uuid4().hex[:8].upper()

def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def call_export_engine(session_id, doc_type, title, fields, content, isp_id):
    """
    Chama o Export Engine (:8103) para gerar o PDF preview.
    Retorna { render_url, render_hash, status }
    """
    payload = json.dumps({
        "session_id": session_id,
        "doc_type":   doc_type,
        "title":      title,
        "fields":     fields if isinstance(fields, dict) else json.loads(fields or "{}"),
        "content":    content or "",
        "isp_id":     isp_id or "default",
        "output":     "pdf",
        "watermark":  "PREVIEW",          # marca d'água no preview
        "seal":       False               # sem QR até publicação final
    }).encode()
    try:
        req = urllib.request.Request(
            f"{EXPORT_URL}/api/render",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        render_url  = data.get("url") or data.get("render_url", "")
        render_hash = data.get("hash") or compute_hash(render_url + session_id)
        return {"render_url": render_url, "render_hash": render_hash, "status": "RENDERED"}
    except Exception as e:
        logger.error(f"Export Engine falhou: {e}")
        # Fallback: URL de preview direto via parâmetros
        fallback_url = (
            f"{EXPORT_URL}/preview/{session_id}"
            f"?doc_type={doc_type}&isp={isp_id or 'default'}"
        )
        render_hash = compute_hash(fallback_url)
        return {"render_url": fallback_url, "render_hash": render_hash, "status": "FAILED"}


def seal_ledger(session_id, title, content_hash, doc_type, wallet_id="human-dragon"):
    receipt_id = (
        f"WINDI-PAGE-{session_id}-"
        f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )
    payload = json.dumps({
        "id":               receipt_id,
        "actor":            wallet_id,
        "app":              "page-bridge",
        "doc_name":         title,
        "doc_type":         "doc",
        "governance_level": "HIGH",
        "content": (
            f"SHA-256:{content_hash} | "
            f"{DOC_TYPES.get(doc_type, doc_type)} selado via Bridge W6 | "
            "RENDER_LOCK IRREMEDIÁVEL — aparência aprovada pelo humano"
        )
    }).encode()
    try:
        req = urllib.request.Request(
            f"{LEDGER_URL}/api/receipts",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            json.loads(r.read())
        verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"
        return {"receipt_id": receipt_id, "hash": content_hash,
                "verify_url": verify_url, "ledger_status": "SEALED"}
    except Exception as e:
        logger.warning(f"Ledger seal falhou: {e}")
        verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"
        return {"receipt_id": receipt_id, "hash": content_hash,
                "verify_url": verify_url, "ledger_status": "PENDING_RETRY"}


# ══════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════

@page_bridge_bp.route("/open", methods=["POST"])
def bridge_open():
    """
    W1 — Cria sessão documental institucional.
    """
    data      = request.get_json(silent=True) or {}
    doc_type  = data.get("doc_type", "certidao")
    title     = data.get("title", "Documento Institucional")
    emitter   = data.get("emitter", "WINDI Publishing House")
    isp_id    = data.get("isp_id", "windi-default")
    wallet_id = data.get("wallet_id", "anonymous")
    fields    = json.dumps(data.get("fields", {}))

    if doc_type not in DOC_TYPES:
        return jsonify({
            "status": "error",
            "detail": f"doc_type inválido. Suportados: {list(DOC_TYPES.keys())}"
        }), 400

    session_id = gen_session_id()
    ts = now_iso()

    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO page_sessions
                  (id, wallet_id, doc_type, title, emitter, isp_id, fields,
                   created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (session_id, wallet_id, doc_type, title, emitter,
                  isp_id, fields, ts, ts))

        logger.info(
            f"[PAGE] Sessão aberta: {session_id} | "
            f"type={doc_type} | '{title}' | isp={isp_id}"
        )
        return jsonify({
            "status":     "ok",
            "session_id": session_id,
            "stage":      "W1",
            "doc_type":   doc_type,
            "doc_label":  DOC_TYPES[doc_type],
            "title":      title,
            "emitter":    emitter,
            "isp_id":     isp_id,
            "render_lock": {
                "principle":     "RENDER_LOCK — aparência DEVE ser aprovada antes de publicar",
                "render_status": "PENDING",
                "next_step":     "POST /page/bridge/save → POST /page/bridge/render"
            },
            "supported_types": DOC_TYPES,
            "message":   f"Sessão {DOC_TYPES[doc_type]} criada. RENDER_LOCK activo.",
            "created_at": ts
        }), 201

    except Exception as e:
        logger.error(f"bridge_open error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@page_bridge_bp.route("/save", methods=["POST"])
def bridge_save():
    """
    W2 — Guarda campos + conteúdo do documento.
    """
    data       = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    fields     = data.get("fields", {})
    content    = data.get("content", "")
    stage      = data.get("stage", "W2")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    fields_str   = json.dumps(fields) if isinstance(fields, dict) else fields
    content_hash = compute_hash(fields_str + (content or ""))
    ts = now_iso()

    try:
        with get_db() as db:
            row = db.execute(
                "SELECT id, status, render_status FROM page_sessions WHERE id=?",
                (session_id,)
            ).fetchone()
            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({
                    "status": "error",
                    "detail": "Sessão já selada — I11 IRREMEDIÁVEL"
                }), 409

            # Se estava APPROVED/LOCKED, salvar invalida o render anterior
            new_render_status = row["render_status"]
            render_invalidated = False
            if row["render_status"] in ("APPROVED", "LOCKED", "RENDERED"):
                new_render_status  = "PENDING"
                render_invalidated = True
                logger.warning(
                    f"[PAGE] RENDER invalidado por edição: {session_id}"
                )

            db.execute("""
                UPDATE page_sessions
                SET fields=?, content=?, stage=?, content_hash=?,
                    render_status=?, render_approved=0, updated_at=?
                WHERE id=?
            """, (fields_str, content, stage, content_hash,
                  new_render_status, ts, session_id))

            db.execute("""
                INSERT INTO page_revisions
                  (session_id, fields, content, stage, saved_at)
                VALUES (?,?,?,?,?)
            """, (session_id, fields_str, content or "", stage, ts))

        logger.info(f"[PAGE] Save: {session_id} | stage={stage} | hash={content_hash[:8]}")

        response = {
            "status":        "ok",
            "session_id":    session_id,
            "stage":         stage,
            "content_hash":  content_hash,
            "render_status": new_render_status,
            "saved_at":      ts,
            "next_step":     "POST /page/bridge/render para gerar preview visual",
            "message":       "Campos guardados. Solicitar render para continuar."
        }
        if render_invalidated:
            response["render_warning"] = (
                "⚠️ Conteúdo editado — render anterior invalidado. "
                "Re-renderizar antes de publicar."
            )
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"bridge_save error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@page_bridge_bp.route("/render", methods=["POST"])
def bridge_render():
    """
    ★ ENDPOINT ESPECIAL — W3/W4
    Dispara o Export Engine para gerar o PDF preview visual.
    Sem render aprovado, publish é bloqueado.
    """
    data           = request.get_json(silent=True) or {}
    session_id     = data.get("session_id")
    isp_override   = data.get("isp_id")
    approve_render = data.get("approve_render", False)

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    ts = now_iso()

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, doc_type, title, fields, content, isp_id,
                       status, render_status, render_approved, render_url
                FROM page_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404
            if row["status"] == "published":
                return jsonify({
                    "status": "error",
                    "detail": "Sessão já publicada — I11 IRREMEDIÁVEL"
                }), 409

            isp_id = isp_override or row["isp_id"] or "windi-default"

            # ── Aprovar render existente (sem re-renderizar) ──
            if approve_render and row["render_status"] in ("RENDERED", "APPROVED"):
                db.execute("""
                    UPDATE page_sessions
                    SET render_status='APPROVED', render_approved=1,
                        render_approved_at=?, stage='W4', updated_at=?
                    WHERE id=?
                """, (ts, ts, session_id))
                db.execute("""
                    UPDATE page_renders SET status='APPROVED', completed_at=?
                    WHERE session_id=? AND status='RENDERED'
                """, (ts, session_id))

                logger.info(f"[PAGE] Render APROVADO: {session_id}")
                return jsonify({
                    "status":        "ok",
                    "session_id":    session_id,
                    "stage":         "W4",
                    "render_status": "APPROVED",
                    "render_url":    row["render_url"],
                    "message":       "✅ Aparência visual aprovada. Pronto para publicação.",
                    "next_step":     "POST /page/bridge/publish {human_approved: true}"
                }), 200

            # ── Gerar novo render ────────────────────────────
            db.execute("""
                UPDATE page_sessions
                SET render_status='RENDERING', stage='W3',
                    render_approved=0, updated_at=?
                WHERE id=?
            """, (ts, session_id))

            db.execute("""
                INSERT INTO page_renders
                  (session_id, isp_id, requested_at, status)
                VALUES (?,?,?,?)
            """, (session_id, isp_id, ts, "RENDERING"))

        # ── Chamar Export Engine ──
        result = call_export_engine(
            session_id  = session_id,
            doc_type    = row["doc_type"],
            title       = row["title"],
            fields      = row["fields"],
            content     = row["content"],
            isp_id      = isp_id
        )

        render_url    = result["render_url"]
        render_hash   = result["render_hash"]
        final_status  = result["status"]
        completed_ts  = now_iso()

        with get_db() as db:
            db.execute("""
                UPDATE page_sessions
                SET render_status=?, render_url=?, render_hash=?,
                    stage=?, updated_at=?
                WHERE id=?
            """, (
                final_status,
                render_url,
                render_hash,
                "W3" if final_status == "RENDERED" else "W2",
                completed_ts,
                session_id
            ))
            db.execute("""
                UPDATE page_renders
                SET status=?, render_url=?, render_hash=?, completed_at=?
                WHERE session_id=? AND status='RENDERING'
            """, (final_status, render_url, render_hash, completed_ts, session_id))

        logger.info(
            f"[PAGE] Render {final_status}: {session_id} | url={render_url[:60]}"
        )

        response = {
            "status":        "ok",
            "session_id":    session_id,
            "stage":         "W3" if final_status == "RENDERED" else "W2",
            "render_status": final_status,
            "render_status_description": RENDER_STATUS[final_status],
            "render_url":    render_url,
            "render_hash":   render_hash,
            "isp_id":        isp_id,
            "rendered_at":   completed_ts,
        }

        if final_status == "RENDERED":
            response["message"]   = "📄 Preview gerado. Reveja a aparência visual e aprove."
            response["next_step"] = "POST /page/bridge/render {session_id, approve_render: true}"
            response["render_lock_warning"] = "⚠️ RENDER_LOCK — publicação bloqueada até approve_render=true"
        else:
            response["message"]   = "❌ Render falhou. Verificar Export Engine (:8103)."
            response["next_step"] = "Verificar :8103 e re-tentar /page/bridge/render"

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"bridge_render error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@page_bridge_bp.route("/publish", methods=["POST"])
def bridge_publish():
    """
    W5→W6 — Gate humano + Ledger seal IRREMEDIÁVEL.
    RENDER_LOCK: publicação bloqueada se render_status ≠ APPROVED.
    """
    data           = request.get_json(silent=True) or {}
    session_id     = data.get("session_id")
    human_approved = data.get("human_approved", False)
    final_content  = data.get("final_content")

    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    ts = now_iso()

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, doc_type, title, fields, content, isp_id,
                       render_status, render_url, render_hash, render_approved,
                       content_hash, status, wallet_id
                FROM page_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404

            if row["status"] == "published":
                return jsonify({
                    "status":     "already_published",
                    "session_id": session_id,
                    "message":    "I11 — já selado, imutável."
                }), 200

            # ── RENDER_LOCK: bloquear se render não aprovado ──────────
            if row["render_status"] != "APPROVED":
                db.execute(
                    "UPDATE page_sessions SET stage='W4', updated_at=? WHERE id=?",
                    (ts, session_id)
                )
                return jsonify({
                    "status":        "render_lock_active",
                    "session_id":    session_id,
                    "render_status": row["render_status"],
                    "render_status_description": RENDER_STATUS.get(
                        row["render_status"], "Estado desconhecido"
                    ),
                    "render_lock": {
                        "blocked":    True,
                        "principle":  "RENDER_LOCK — aparência visual DEVE ser aprovada",
                        "required":   "render_status = APPROVED antes de publicar",
                        "action":     "1. render → 2. ver PDF → 3. approve → 4. publish"
                    },
                    "message": f"🔒 RENDER_LOCK activo — render_status={row['render_status']}."
                }), 202

            # ── I9 GATE ───────────────────────────────────────────────
            if not human_approved:
                db.execute(
                    "UPDATE page_sessions SET stage='W5', updated_at=? WHERE id=?",
                    (ts, session_id)
                )
                return jsonify({
                    "status":        "awaiting_approval",
                    "session_id":    session_id,
                    "stage":         "W5",
                    "render_status": "APPROVED",
                    "message": "I9 — documento institucional requer human_approved=true. "
                               "AI processes. Human decides. WINDI guarantees."
                }), 202

            # ── Conteúdo final ────────────────────────────────────────
            final = final_content or row["content"] or ""
            content_hash = compute_hash(
                (row["fields"] or "{}") + final + (row["render_hash"] or "")
            )

            # ── Selar no Ledger ───────────────────────────────────────
            seal = seal_ledger(
                session_id = session_id,
                title      = row["title"],
                content_hash = content_hash,
                doc_type   = row["doc_type"],
                wallet_id  = row["wallet_id"] or "human-dragon"
            )

            db.execute("""
                UPDATE page_sessions
                SET status='published', stage='W6', human_approved=1,
                    content=?, content_hash=?,
                    ledger_receipt=?, verify_url=?, updated_at=?
                WHERE id=?
            """, (final, content_hash,
                  seal["receipt_id"], seal["verify_url"],
                  ts, session_id))

        logger.info(
            f"[PAGE] PUBLISHED: {session_id} | "
            f"receipt={seal['receipt_id']} | type={row['doc_type']}"
        )

        return jsonify({
            "status":          "published",
            "session_id":      session_id,
            "stage":           "W6",
            "doc_type":        row["doc_type"],
            "doc_label":       DOC_TYPES.get(row["doc_type"], row["doc_type"]),
            "title":           row["title"],
            "isp_id":          row["isp_id"],
            "render_url":      row["render_url"],
            "render_hash":     row["render_hash"],
            "ledger_receipt":  seal["receipt_id"],
            "content_hash":    content_hash,
            "verify_url":      seal["verify_url"],
            "qr_payload":      f"WINDI:{seal['receipt_id']}|{content_hash[:16]}",
            "ledger_status":   seal["ledger_status"],
            "published_at":    ts,
            "render_lock":     "FULFILLED — aparência aprovada, conteúdo selado",
            "message": f"{DOC_TYPES.get(row['doc_type'], 'Documento')} selado. "
                       "RENDER_LOCK + I11 IRREMEDIÁVEL. "
                       "AI processes. Human decides. WINDI guarantees."
        }), 200

    except Exception as e:
        logger.error(f"bridge_publish error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


@page_bridge_bp.route("/status", methods=["GET"])
def bridge_status():
    """Estado completo da sessão — inclui render_status e lock state."""
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "detail": "session_id obrigatório"}), 400

    try:
        with get_db() as db:
            row = db.execute("""
                SELECT id, wallet_id, doc_type, title, emitter, isp_id,
                       render_status, render_url, render_hash,
                       render_approved, render_approved_at,
                       status, stage, human_approved,
                       ledger_receipt, verify_url, content_hash,
                       created_at, updated_at
                FROM page_sessions WHERE id=?
            """, (session_id,)).fetchone()

            if not row:
                return jsonify({"status": "error", "detail": "Sessão não encontrada"}), 404

            rev_count = db.execute(
                "SELECT COUNT(*) FROM page_revisions WHERE session_id=?",
                (session_id,)
            ).fetchone()[0]

            render_count = db.execute(
                "SELECT COUNT(*) FROM page_renders WHERE session_id=?",
                (session_id,)
            ).fetchone()[0]

        return jsonify({
            "status":       "ok",
            "session_id":   row["id"],
            "doc_type":     row["doc_type"],
            "doc_label":    DOC_TYPES.get(row["doc_type"], row["doc_type"]),
            "title":        row["title"],
            "emitter":      row["emitter"],
            "isp_id":       row["isp_id"],
            "stage":        row["stage"],
            "session_status": row["status"],
            "render": {
                "status":          row["render_status"],
                "description":     RENDER_STATUS.get(row["render_status"], ""),
                "url":             row["render_url"],
                "hash":            row["render_hash"],
                "approved":        bool(row["render_approved"]),
                "approved_at":     row["render_approved_at"],
                "render_attempts": render_count,
                "locked":          row["render_status"] == "LOCKED",
                "publish_blocked": row["render_status"] != "APPROVED",
            },
            "human_approved": bool(row["human_approved"]),
            "revisions":      rev_count,
            "ledger_receipt": row["ledger_receipt"],
            "verify_url":     row["verify_url"],
            "content_hash":   row["content_hash"],
            "created_at":     row["created_at"],
            "updated_at":     row["updated_at"],
            "invariants": {
                "RENDER_LOCK": "ENFORCED — aparência aprovada obrigatória antes de W6",
                "I9":          "ENFORCED — human_approved=true obrigatório",
                "I11":         "ENFORCED — Ledger IRREMEDIÁVEL após W6"
            },
            "stage_map": {
                "W1": "Pedido recebido",
                "W2": "Campos estruturados",
                "W3": "Render gerado",
                "W4": "Revisão visual",
                "W5": "Aguarda aprovação",
                "W6": "Selado no Ledger"
            },
            "supported_doc_types": DOC_TYPES
        }), 200

    except Exception as e:
        logger.error(f"bridge_status error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500
