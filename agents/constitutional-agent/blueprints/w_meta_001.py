"""
W-META-001 — Meta-Governance Layer
WINDI Agent Corps | Sandbox Core :8091

O único árbitro que não pode ser comprado: o Ledger.

Responsabilidades:
  1. Auditar Elders — ninguém fica acima da infraestrutura
  2. Detectar anomalias estatísticas em qualquer nível
  3. Quorum constitucional para decisões de governança
  4. Selar toda ação meta no Forensic Ledger (imutável)
  5. Emitir Meta-Receipts públicos verificáveis

Princípio central:
  "O Ledger audita os Elders."
  "O Human Dragon é o único admin — mas suas ações também geram receipts."
  "I9 protege contra concentração humana tanto quanto contra escalada de IA."

Invariante protegida: I9 (Proibição de Escalada de Autonomia)
Meta-Invariante: NINGUÉM está acima do Ledger.
"""

from flask import Blueprint, request, jsonify
import sqlite3
import hashlib
import json
import time
import datetime
import urllib.request
import os

# ─── Blueprint ───────────────────────────────────────────────────────────────

meta_bp = Blueprint("w_meta_001", __name__, url_prefix="/meta")

# ─── Config ──────────────────────────────────────────────────────────────────

DB_PATH    = os.environ.get("META_DB_PATH", "/opt/windi/data/meta_governance.db")
VIRTUE_DB  = os.environ.get("VIRTUE_DB_PATH", "/opt/windi/agents/constitutional-agent/virtue_score.db")
LEDGER_URL = os.environ.get("LEDGER_URL", "http://127.0.0.1:8101")

# Human Dragon é o único titular da chave admin.
# Mas mesmo suas ações geram receipt público — ninguém escapa.
ADMIN_KEY  = os.environ.get("META_ADMIN_KEY", "")

# Quorum mínimo para decisão de governança
ELDER_QUORUM_MIN = int(os.environ.get("ELDER_QUORUM_MIN", "3"))

# ─── Database ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_virtue_db():
    if not os.path.exists(VIRTUE_DB):
        return None
    conn = sqlite3.connect(VIRTUE_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_meta_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        -- Investigações abertas contra qualquer operador (incluindo Elders)
        CREATE TABLE IF NOT EXISTS investigations (
            id              TEXT PRIMARY KEY,
            target_wallet   TEXT NOT NULL,
            target_level    TEXT,
            reason          TEXT NOT NULL,
            evidence_hashes TEXT,
            opened_by       TEXT NOT NULL,
            opened_at       INTEGER,
            status          TEXT DEFAULT 'open',
            ruling          TEXT,
            ruled_at        INTEGER,
            ruled_by        TEXT,
            ledger_receipt  TEXT
        );

        -- Propostas de governança (exigem quorum de Elders)
        CREATE TABLE IF NOT EXISTS governance_proposals (
            id              TEXT PRIMARY KEY,
            proposer_wallet TEXT NOT NULL,
            action_type     TEXT NOT NULL,
            payload         TEXT NOT NULL,
            justification   TEXT,
            status          TEXT DEFAULT 'pending',
            votes_for       TEXT DEFAULT '[]',
            votes_against   TEXT DEFAULT '[]',
            quorum_required INTEGER,
            opened_at       INTEGER,
            decided_at      INTEGER,
            ledger_receipt  TEXT
        );

        -- Registro de ações administrativas (Human Dragon)
        CREATE TABLE IF NOT EXISTS admin_actions (
            id              TEXT PRIMARY KEY,
            action          TEXT NOT NULL,
            actor           TEXT NOT NULL,
            payload         TEXT,
            authorized_at   INTEGER,
            ledger_receipt  TEXT NOT NULL
        );

        -- Anomalias detectadas automaticamente
        CREATE TABLE IF NOT EXISTS anomalies (
            id              TEXT PRIMARY KEY,
            wallet_id       TEXT NOT NULL,
            anomaly_type    TEXT NOT NULL,
            severity        TEXT NOT NULL,
            description     TEXT,
            detected_at     INTEGER,
            auto_action     TEXT,
            ledger_receipt  TEXT
        );

        -- Meta-Receipts públicos
        CREATE TABLE IF NOT EXISTS meta_receipts (
            id              TEXT PRIMARY KEY,
            event_type      TEXT NOT NULL,
            subject_wallet  TEXT,
            payload_hash    TEXT NOT NULL,
            issued_at       INTEGER,
            ledger_receipt  TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_inv_target   ON investigations(target_wallet);
        CREATE INDEX IF NOT EXISTS idx_prop_status  ON governance_proposals(status);
        CREATE INDEX IF NOT EXISTS idx_anom_wallet  ON anomalies(wallet_id);
    """)
    conn.commit()
    conn.close()
    print(f"[W-META-001] DB inicializado: {DB_PATH}")

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _gen_id(prefix: str, payload: str) -> str:
    h = hashlib.sha256(f"{prefix}:{payload}:{time.time()}".encode()).hexdigest()[:16]
    return f"{prefix}-{h}"

def _hash_payload(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()

def _seal_ledger(receipt_id: str, payload: dict) -> str:
    try:
        content_hash = _hash_payload(payload)
        body = json.dumps({
            "id": receipt_id,
            "actor": payload.get("actor", "W-META-001"),
            "app": "W-META-001",
            "doc_name": f"MetaGov:{payload.get('event_type','event')}",
            "doc_type": "doc",
            "governance_level": "HIGH",
            "content_hash": content_hash,
            "sge_score": 1.0
        }).encode()
        req = urllib.request.Request(
            f"{LEDGER_URL}/api/receipts",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return receipt_id
    except Exception as e:
        print(f"[W-META-001] Ledger seal failed: {e}")
        return receipt_id

def _issue_meta_receipt(conn, event_type: str, subject_wallet: str, payload: dict, ledger_receipt: str):
    receipt_id = _gen_id("MR", f"{event_type}:{subject_wallet}")
    payload_hash = _hash_payload(payload)
    c = conn.cursor()
    c.execute("""
        INSERT INTO meta_receipts (id, event_type, subject_wallet, payload_hash, issued_at, ledger_receipt)
        VALUES (?,?,?,?,?,?)
    """, (receipt_id, event_type, subject_wallet, payload_hash, int(time.time()), ledger_receipt))
    return receipt_id

def _get_operator_level(wallet_id: str):
    vdb = get_virtue_db()
    if not vdb:
        return None
    c = vdb.cursor()
    c.execute("SELECT level FROM operators WHERE wallet_id=?", (wallet_id,))
    row = c.fetchone()
    vdb.close()
    return row["level"] if row else None

def _get_all_elders():
    vdb = get_virtue_db()
    if not vdb:
        return []
    c = vdb.cursor()
    c.execute("SELECT wallet_id FROM operators WHERE level='elder' AND suspended=0")
    rows = c.fetchall()
    vdb.close()
    return [r["wallet_id"] for r in rows]

# ─── Anomaly Detection ───────────────────────────────────────────────────────

def _detect_anomalies(wallet_id: str):
    vdb = get_virtue_db()
    if not vdb:
        return []

    anomalies = []
    c = vdb.cursor()
    now = int(time.time())
    window_30d = now - (30 * 86400)

    # 1. Muitos casos com mesmo cliente (possível circular confirmation)
    try:
        c.execute("""
            SELECT case_id, COUNT(*) as cnt FROM decisions
            WHERE wallet_id=? AND sealed_at > ?
            GROUP BY case_id HAVING cnt > 5
        """, (wallet_id, window_30d))
        repeated = c.fetchall()
        if repeated:
            anomalies.append({
                "type": "repeated_case_id",
                "severity": "high",
                "description": f"{len(repeated)} case_id(s) aparecem +5x em 30 dias — possível loop de confirmação circular",
            })
    except:
        pass

    # 2. Taxa de sucesso suspeita (>95% audited_confirmed)
    try:
        c.execute("SELECT COUNT(*) as total FROM decisions WHERE wallet_id=?", (wallet_id,))
        total = c.fetchone()["total"]
        if total >= 10:
            c.execute("""
                SELECT COUNT(*) as cnt FROM decisions
                WHERE wallet_id=? AND reliability='audited_confirmed'
            """, (wallet_id,))
            confirmed = c.fetchone()["cnt"]
            rate = confirmed / total
            if rate > 0.95:
                anomalies.append({
                    "type": "unrealistic_success_rate",
                    "severity": "medium",
                    "description": f"Taxa audited_confirmed = {rate:.0%} ({confirmed}/{total}) — acima de limiar estatístico esperado",
                })
    except:
        pass

    # 3. Velocidade de crescimento anormal
    try:
        c.execute("""
            SELECT COUNT(*) as cnt FROM decisions
            WHERE wallet_id=? AND sealed_at > ?
        """, (wallet_id, now - 7 * 86400))
        weekly = c.fetchone()["cnt"]
        if weekly > 50:
            anomalies.append({
                "type": "velocity_spike",
                "severity": "high",
                "description": f"{weekly} decisões em 7 dias — volume anormal para um único operador",
            })
    except:
        pass

    vdb.close()
    return anomalies

# ─── Endpoints ───────────────────────────────────────────────────────────────

@meta_bp.route("/health", methods=["GET"])
def health():
    try:
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    virtue_ok = os.path.exists(VIRTUE_DB)

    return jsonify({
        "agent": "W-META-001",
        "version": "1.0.0",
        "status": "healthy" if db_ok else "degraded",
        "db": "ok" if db_ok else "error",
        "virtue_db_connected": virtue_ok,
        "principle": "O Ledger audita os Elders.",
        "endpoints": [
            "POST /meta/investigations/open",
            "POST /meta/investigations/rule",
            "POST /meta/proposals/submit",
            "POST /meta/proposals/vote",
            "POST /meta/admin/action",
            "GET  /meta/scan/{wallet_id}",
            "GET  /meta/receipts/public",
            "GET  /meta/status",
        ]
    })


@meta_bp.route("/status", methods=["GET"])
def meta_status():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as cnt FROM investigations WHERE status='open'")
    open_inv = c.fetchone()["cnt"]

    c.execute("SELECT COUNT(*) as cnt FROM investigations WHERE ruling='guilty'")
    guilty = c.fetchone()["cnt"]

    c.execute("SELECT COUNT(*) as cnt FROM governance_proposals WHERE status='pending'")
    open_props = c.fetchone()["cnt"]

    c.execute("SELECT COUNT(*) as cnt FROM anomalies WHERE severity IN ('high','critical')")
    critical_anom = c.fetchone()["cnt"]

    c.execute("SELECT COUNT(*) as cnt FROM admin_actions")
    admin_count = c.fetchone()["cnt"]

    conn.close()

    elders = _get_all_elders()

    return jsonify({
        "layer": "W-META-001",
        "principle": "O Ledger audita os Elders. Ninguém está acima.",
        "meta_invariant": "NENHUM humano ou IA controla o Ledger. É append-only.",
        "i9_status": "PROTECTED",
        "stats": {
            "open_investigations": open_inv,
            "guilty_rulings": guilty,
            "pending_proposals": open_props,
            "critical_anomalies": critical_anom,
            "admin_actions_logged": admin_count,
            "active_elders": len(elders),
            "quorum_threshold": max(ELDER_QUORUM_MIN, len(elders) // 2 + 1),
        },
        "protection_layers": [
            "Ledger append-only — nenhuma ação se apaga",
            "Admin actions → receipt público obrigatório",
            "Elder rulings → quorum obrigatório",
            "Anomaly scanner automático",
            "Meta-Receipts públicos — auditoria aberta",
        ],
    })


@meta_bp.route("/investigations/open", methods=["POST"])
def open_investigation():
    body = request.get_json() or {}
    target_wallet = body.get("target_wallet")
    reason = body.get("reason")
    evidence_hashes = body.get("evidence_hashes", [])
    opened_by = body.get("opened_by")

    if not all([target_wallet, reason, opened_by]):
        return jsonify({"ok": False, "error": "Campos obrigatórios: target_wallet, reason, opened_by"}), 400

    opener_level = _get_operator_level(opened_by)
    if opener_level not in ("elder",) and opened_by != "ADMIN":
        return jsonify({"ok": False, "error": "Apenas Elders ou admin podem abrir investigações"}), 403

    target_level = _get_operator_level(target_wallet)

    conn = get_db()
    c = conn.cursor()

    inv_id = _gen_id("INV", f"{target_wallet}:{opened_by}")
    now = int(time.time())

    c.execute("""
        INSERT INTO investigations
        (id, target_wallet, target_level, reason, evidence_hashes, opened_by, opened_at)
        VALUES (?,?,?,?,?,?,?)
    """, (inv_id, target_wallet, target_level, reason,
          json.dumps(evidence_hashes), opened_by, now))

    receipt_id = f"WINDI-INV-OPEN-{inv_id}"
    _seal_ledger(receipt_id, {
        "event_type": "investigation_opened",
        "actor": opened_by,
        "target": target_wallet,
        "target_level": target_level,
        "reason": reason,
        "inv_id": inv_id,
    })

    c.execute("UPDATE investigations SET ledger_receipt=? WHERE id=?", (receipt_id, inv_id))
    _issue_meta_receipt(conn, "investigation_opened", target_wallet,
                        {"inv_id": inv_id, "reason": reason}, receipt_id)
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "investigation_id": inv_id,
        "target": target_wallet,
        "target_level": target_level,
        "status": "open",
        "ledger_receipt": receipt_id,
        "message": "Investigação selada no Ledger. Pública e imutável.",
    })


@meta_bp.route("/investigations/rule", methods=["POST"])
def issue_ruling():
    body = request.get_json() or {}
    investigation_id = body.get("investigation_id")
    ruling = body.get("ruling")
    ruled_by = body.get("ruled_by")
    justification = body.get("justification", "")
    admin_key = body.get("admin_key")

    if not all([investigation_id, ruling, ruled_by]):
        return jsonify({"ok": False, "error": "Campos obrigatórios: investigation_id, ruling, ruled_by"}), 400

    if ruling not in ("guilty", "cleared", "inconclusive"):
        return jsonify({"ok": False, "error": "ruling deve ser: guilty|cleared|inconclusive"}), 400

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM investigations WHERE id=?", (investigation_id,))
    inv = c.fetchone()
    if not inv:
        conn.close()
        return jsonify({"ok": False, "error": "Investigação não encontrada"}), 404
    if inv["status"] == "ruled":
        conn.close()
        return jsonify({"ok": False, "error": "Investigação já tem ruling"}), 400

    # Ruling guilty sobre Elder exige admin_key
    if inv["target_level"] == "elder" and ruling == "guilty":
        if not admin_key or admin_key != ADMIN_KEY:
            conn.close()
            return jsonify({"ok": False, "error": "Ruling guilty sobre Elder exige chave admin do Human Dragon"}), 403

    now = int(time.time())
    c.execute("""
        UPDATE investigations
        SET status='ruled', ruling=?, ruled_at=?, ruled_by=?
        WHERE id=?
    """, (ruling, now, ruled_by, investigation_id))

    # Aplicar consequência se guilty
    consequence = None
    if ruling == "guilty":
        vdb = get_virtue_db()
        if vdb:
            vc = vdb.cursor()
            target_level = inv["target_level"]
            if target_level == "seed":
                vc.execute("UPDATE operators SET suspended=1, suspension_reason=? WHERE wallet_id=?",
                           (f"Meta-Governance ruling: {justification}", inv["target_wallet"]))
                consequence = "suspended"
            elif target_level == "master":
                vc.execute("UPDATE operators SET level='seed' WHERE wallet_id=?", (inv["target_wallet"],))
                consequence = "downgraded_to_seed"
            elif target_level == "elder":
                vc.execute("UPDATE operators SET suspended=1, suspension_reason=? WHERE wallet_id=?",
                           (f"ELDER RULING — Meta-Governance: {justification}", inv["target_wallet"]))
                consequence = "elder_suspended"
            vdb.commit()
            vdb.close()

    receipt_id = f"WINDI-INV-RULING-{investigation_id}"
    _seal_ledger(receipt_id, {
        "event_type": "investigation_ruling",
        "actor": ruled_by,
        "investigation_id": investigation_id,
        "target": inv["target_wallet"],
        "target_level": inv["target_level"],
        "ruling": ruling,
        "consequence": consequence,
        "justification": justification,
    })

    c.execute("UPDATE investigations SET ledger_receipt=? WHERE id=?", (receipt_id, investigation_id))
    _issue_meta_receipt(conn, "investigation_ruling", inv["target_wallet"],
                        {"ruling": ruling, "consequence": consequence}, receipt_id)
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "investigation_id": investigation_id,
        "ruling": ruling,
        "consequence": consequence,
        "ledger_receipt": receipt_id,
        "public": True,
        "message": "Ruling selado. Imutável. Qualquer um pode verificar.",
    })


@meta_bp.route("/proposals/submit", methods=["POST"])
def submit_proposal():
    body = request.get_json() or {}
    proposer_wallet = body.get("proposer_wallet")
    action_type = body.get("action_type")
    payload = body.get("payload", {})
    justification = body.get("justification", "")

    if not all([proposer_wallet, action_type]):
        return jsonify({"ok": False, "error": "Campos obrigatórios: proposer_wallet, action_type"}), 400

    proposer_level = _get_operator_level(proposer_wallet)
    if proposer_level != "elder":
        return jsonify({"ok": False, "error": "Apenas Elders podem propor mudanças de governança"}), 403

    elders = _get_all_elders()
    quorum = max(ELDER_QUORUM_MIN, len(elders) // 2 + 1)

    conn = get_db()
    c = conn.cursor()

    prop_id = _gen_id("PROP", f"{proposer_wallet}:{action_type}")
    now = int(time.time())

    c.execute("""
        INSERT INTO governance_proposals
        (id, proposer_wallet, action_type, payload, justification, quorum_required, opened_at)
        VALUES (?,?,?,?,?,?,?)
    """, (prop_id, proposer_wallet, action_type,
          json.dumps(payload), justification, quorum, now))

    receipt_id = f"WINDI-PROP-{prop_id}"
    _seal_ledger(receipt_id, {
        "event_type": "governance_proposal",
        "actor": proposer_wallet,
        "action_type": action_type,
        "quorum_required": quorum,
        "total_elders": len(elders),
        "prop_id": prop_id,
    })

    c.execute("UPDATE governance_proposals SET ledger_receipt=? WHERE id=?", (receipt_id, prop_id))
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "proposal_id": prop_id,
        "action_type": action_type,
        "quorum_required": quorum,
        "total_elders": len(elders),
        "status": "pending",
        "ledger_receipt": receipt_id,
        "message": f"Proposta aberta. Necessita {quorum} votos de {len(elders)} Elders.",
    })


@meta_bp.route("/proposals/vote", methods=["POST"])
def vote_on_proposal():
    body = request.get_json() or {}
    proposal_id = body.get("proposal_id")
    voter_wallet = body.get("voter_wallet")
    vote = body.get("vote")

    if not all([proposal_id, voter_wallet, vote]):
        return jsonify({"ok": False, "error": "Campos obrigatórios: proposal_id, voter_wallet, vote"}), 400

    if vote not in ("for", "against"):
        return jsonify({"ok": False, "error": "vote deve ser: for|against"}), 400

    voter_level = _get_operator_level(voter_wallet)
    if voter_level != "elder":
        return jsonify({"ok": False, "error": "Apenas Elders votam"}), 403

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM governance_proposals WHERE id=?", (proposal_id,))
    prop = c.fetchone()
    if not prop or prop["status"] != "pending":
        conn.close()
        return jsonify({"ok": False, "error": "Proposta não encontrada ou não está pendente"}), 404

    votes_for = json.loads(prop["votes_for"])
    votes_against = json.loads(prop["votes_against"])

    if voter_wallet in votes_for or voter_wallet in votes_against:
        conn.close()
        return jsonify({"ok": False, "error": "Elder já votou nesta proposta"}), 400

    if vote == "for":
        votes_for.append(voter_wallet)
    else:
        votes_against.append(voter_wallet)

    new_status = "pending"
    if len(votes_for) >= prop["quorum_required"]:
        new_status = "approved"
    elif len(votes_against) >= prop["quorum_required"]:
        new_status = "rejected"

    now = int(time.time())
    c.execute("""
        UPDATE governance_proposals
        SET votes_for=?, votes_against=?, status=?,
            decided_at=CASE WHEN ? != 'pending' THEN ? ELSE decided_at END
        WHERE id=?
    """, (json.dumps(votes_for), json.dumps(votes_against),
          new_status, new_status, now, proposal_id))

    receipt_id = f"WINDI-VOTE-{proposal_id}-{voter_wallet[:8]}"
    _seal_ledger(receipt_id, {
        "event_type": "governance_vote",
        "actor": voter_wallet,
        "proposal_id": proposal_id,
        "vote": vote,
        "tally_for": len(votes_for),
        "tally_against": len(votes_against),
        "new_status": new_status,
    })

    _issue_meta_receipt(conn, "governance_vote", voter_wallet,
                        {"proposal_id": proposal_id, "vote": vote, "status": new_status},
                        receipt_id)
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "proposal_id": proposal_id,
        "vote_registered": vote,
        "tally": {"for": len(votes_for), "against": len(votes_against)},
        "quorum_required": prop["quorum_required"],
        "status": new_status,
        "ledger_receipt": receipt_id,
    })


@meta_bp.route("/admin/action", methods=["POST"])
def admin_action():
    """
    Qualquer ação admin gera receipt público obrigatório.
    Ninguém está acima da infraestrutura.
    """
    body = request.get_json() or {}
    action = body.get("action")
    actor = body.get("actor")
    payload = body.get("payload", {})
    admin_key = body.get("admin_key")

    if not all([action, actor, admin_key]):
        return jsonify({"ok": False, "error": "Campos obrigatórios: action, actor, admin_key"}), 400

    if admin_key != ADMIN_KEY:
        return jsonify({"ok": False, "error": "Chave admin inválida"}), 403

    conn = get_db()
    c = conn.cursor()

    action_id = _gen_id("ADM", f"{actor}:{action}")
    now = int(time.time())

    receipt_id = f"WINDI-ADMIN-{action_id}"
    _seal_ledger(receipt_id, {
        "event_type": "admin_action",
        "actor": actor,
        "action": action,
        "payload": payload,
        "timestamp": datetime.datetime.utcfromtimestamp(now).isoformat(),
    })

    c.execute("""
        INSERT INTO admin_actions (id, action, actor, payload, authorized_at, ledger_receipt)
        VALUES (?,?,?,?,?,?)
    """, (action_id, action, actor, json.dumps(payload), now, receipt_id))

    _issue_meta_receipt(conn, "admin_action", actor,
                        {"action": action}, receipt_id)
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "action_id": action_id,
        "ledger_receipt": receipt_id,
        "public": True,
        "message": "Ação administrativa selada publicamente. Imutável. I9 respeitado.",
    })


@meta_bp.route("/scan/<wallet_id>", methods=["GET"])
def scan_operator(wallet_id):
    anomalies = _detect_anomalies(wallet_id)
    operator_level = _get_operator_level(wallet_id)

    conn = get_db()
    c = conn.cursor()
    now = int(time.time())

    auto_actions = []
    for a in anomalies:
        anom_id = _gen_id("ANOM", f"{wallet_id}:{a['type']}")
        auto_action = "none"

        if a["severity"] in ("high", "critical"):
            auto_action = "investigation_flagged"

        c.execute("""
            INSERT OR IGNORE INTO anomalies
            (id, wallet_id, anomaly_type, severity, description, detected_at, auto_action)
            VALUES (?,?,?,?,?,?,?)
        """, (anom_id, wallet_id, a["type"], a["severity"], a["description"], now, auto_action))

        auto_actions.append({"anomaly": a["type"], "action": auto_action})

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "wallet_id": wallet_id,
        "operator_level": operator_level,
        "anomalies_found": len(anomalies),
        "anomalies": anomalies,
        "auto_actions": auto_actions,
        "recommendation": "open_investigation" if any(
            a["severity"] in ("high", "critical") for a in anomalies
        ) else "monitor",
        "scanned_at": datetime.datetime.utcnow().isoformat(),
    })


@meta_bp.route("/receipts/public", methods=["GET"])
def public_receipts():
    limit = request.args.get("limit", 20, type=int)
    event_type = request.args.get("event_type")

    conn = get_db()
    c = conn.cursor()
    if event_type:
        c.execute("""
            SELECT * FROM meta_receipts WHERE event_type=?
            ORDER BY issued_at DESC LIMIT ?
        """, (event_type, limit))
    else:
        c.execute("SELECT * FROM meta_receipts ORDER BY issued_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    return jsonify({
        "ok": True,
        "total": len(rows),
        "receipts": rows,
        "note": "Todos os eventos de meta-governança são públicos por design.",
    })
