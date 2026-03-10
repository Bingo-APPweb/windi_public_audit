"""
W-VIRTUE-001 — Virtue Score Layer
WINDI Agent Corps | Sandbox Core :8091

Sistema de reputação verificável para operadores WINDI.

Responsabilidades:
  1. Registrar operadores com níveis (seed → master → elder)
  2. Rastrear decisões e trabalhos selados
  3. Calcular Virtue Score baseado em histórico verificável
  4. Aplicar penalidades e promoções
  5. Integrar com Forensic Ledger para auditoria

Níveis:
  - seed:   Operador iniciante (0-10 decisões verificadas)
  - master: Operador experiente (10-50 decisões, taxa >80%)
  - elder:  Operador sênior (50+ decisões, pode votar em governança)

Princípio:
  "Reputação não se declara. Se constrói com evidência."
"""

from flask import Blueprint, request, jsonify
import sqlite3
import hashlib
import json
import time
import datetime
import urllib.request
import os
import statistics

# ─── Blueprint ───────────────────────────────────────────────────────────────

virtue_bp = Blueprint("w_virtue_001", __name__, url_prefix="/virtue")

# ─── Config ──────────────────────────────────────────────────────────────────

DB_PATH    = os.environ.get("VIRTUE_DB_PATH", "/opt/windi/data/virtue_score.db")
LEDGER_URL = os.environ.get("LEDGER_URL", "http://127.0.0.1:8101")

# Thresholds para promoção
SEED_TO_MASTER_DECISIONS = 10
MASTER_TO_ELDER_DECISIONS = 50
MIN_SUCCESS_RATE = 0.80

# ─── Database ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_virtue_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        -- Operadores registrados
        CREATE TABLE IF NOT EXISTS operators (
            wallet_id           TEXT PRIMARY KEY,
            did_short           TEXT,
            display_name        TEXT,
            level               TEXT DEFAULT 'seed',
            registered_at       INTEGER,
            last_activity       INTEGER,
            suspended           INTEGER DEFAULT 0,
            suspension_reason   TEXT,
            total_decisions     INTEGER DEFAULT 0,
            confirmed_decisions INTEGER DEFAULT 0,
            virtue_score        REAL DEFAULT 0.0,
            ledger_receipt      TEXT
        );

        -- Decisões/trabalhos registrados
        CREATE TABLE IF NOT EXISTS decisions (
            id              TEXT PRIMARY KEY,
            wallet_id       TEXT NOT NULL,
            case_id         TEXT,
            decision_type   TEXT NOT NULL,
            jurisdiction    TEXT DEFAULT 'local',
            client_id       TEXT,
            description     TEXT,
            outcome         TEXT,
            reliability     TEXT DEFAULT 'self_declared',
            sealed_at       INTEGER,
            ledger_receipt  TEXT,
            FOREIGN KEY (wallet_id) REFERENCES operators(wallet_id)
        );

        -- Histórico de mudanças de nível
        CREATE TABLE IF NOT EXISTS level_changes (
            id              TEXT PRIMARY KEY,
            wallet_id       TEXT NOT NULL,
            old_level       TEXT,
            new_level       TEXT,
            reason          TEXT,
            changed_at      INTEGER,
            ledger_receipt  TEXT
        );

        -- Penalidades aplicadas
        CREATE TABLE IF NOT EXISTS penalties (
            id              TEXT PRIMARY KEY,
            wallet_id       TEXT NOT NULL,
            penalty_type    TEXT NOT NULL,
            severity        TEXT NOT NULL,
            reason          TEXT,
            applied_at      INTEGER,
            expires_at      INTEGER,
            ledger_receipt  TEXT
        );

        -- Confirmações de clientes (Modelo B)
        CREATE TABLE IF NOT EXISTS client_confirmations (
            id              TEXT PRIMARY KEY,
            decision_id     TEXT NOT NULL,
            client_id       TEXT NOT NULL,
            confirmed       INTEGER DEFAULT 0,
            confirmed_at    INTEGER,
            ip_hash         TEXT,
            ledger_receipt  TEXT,
            FOREIGN KEY (decision_id) REFERENCES decisions(id)
        );

        CREATE INDEX IF NOT EXISTS idx_op_level ON operators(level);
        CREATE INDEX IF NOT EXISTS idx_dec_wallet ON decisions(wallet_id);
        CREATE INDEX IF NOT EXISTS idx_dec_sealed ON decisions(sealed_at);
    """)
    conn.commit()
    conn.close()
    print(f"[W-VIRTUE-001] DB inicializado: {DB_PATH}")

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _gen_id(prefix: str, payload: str) -> str:
    h = hashlib.sha256(f"{prefix}:{payload}:{time.time()}".encode()).hexdigest()[:16]
    return f"{prefix}-{h}"

def _seal_ledger(receipt_id: str, payload: dict) -> str:
    try:
        content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        body = json.dumps({
            "id": receipt_id,
            "actor": payload.get("actor", "W-VIRTUE-001"),
            "app": "W-VIRTUE-001",
            "doc_name": f"Virtue:{payload.get('event_type','event')}",
            "doc_type": "doc",
            "governance_level": "MEDIUM",
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
        print(f"[W-VIRTUE-001] Ledger seal failed: {e}")
        return receipt_id

def _calculate_virtue_score(wallet_id: str) -> dict:
    """
    Calcula Virtue Score baseado em:
    - Total de decisões
    - Taxa de confirmação (audited_confirmed vs total)
    - Diversidade de jurisdições
    - Penalidades ativas
    - Tempo de atividade
    """
    conn = get_db()
    c = conn.cursor()

    # Dados básicos
    c.execute("SELECT * FROM operators WHERE wallet_id=?", (wallet_id,))
    op = c.fetchone()
    if not op:
        conn.close()
        return {"score": 0, "breakdown": {}}

    # Contagem de decisões
    c.execute("SELECT COUNT(*) as total FROM decisions WHERE wallet_id=?", (wallet_id,))
    total = c.fetchone()["total"]

    c.execute("""
        SELECT COUNT(*) as confirmed FROM decisions
        WHERE wallet_id=? AND reliability='audited_confirmed'
    """, (wallet_id,))
    confirmed = c.fetchone()["confirmed"]

    # Jurisdições únicas
    c.execute("""
        SELECT COUNT(DISTINCT jurisdiction) as jurisdictions
        FROM decisions WHERE wallet_id=?
    """, (wallet_id,))
    jurisdictions = c.fetchone()["jurisdictions"]

    # Penalidades ativas
    now = int(time.time())
    c.execute("""
        SELECT COUNT(*) as active FROM penalties
        WHERE wallet_id=? AND (expires_at IS NULL OR expires_at > ?)
    """, (wallet_id, now))
    active_penalties = c.fetchone()["active"]

    conn.close()

    # Cálculo do score (0-100)
    base_score = 0

    # Componente 1: Volume (max 30 pontos)
    volume_score = min(30, total * 0.6)

    # Componente 2: Taxa de confirmação (max 40 pontos)
    if total > 0:
        confirmation_rate = confirmed / total
        confirmation_score = confirmation_rate * 40
    else:
        confirmation_rate = 0
        confirmation_score = 0

    # Componente 3: Diversidade jurisdicional (max 15 pontos)
    jurisdiction_score = min(15, jurisdictions * 5)

    # Componente 4: Senioridade (max 15 pontos)
    registered_at = op["registered_at"] or now
    days_active = (now - registered_at) / 86400
    seniority_score = min(15, days_active * 0.1)

    # Penalidades reduzem score
    penalty_reduction = active_penalties * 10

    total_score = max(0, volume_score + confirmation_score + jurisdiction_score + seniority_score - penalty_reduction)
    total_score = min(100, total_score)

    return {
        "score": round(total_score, 2),
        "breakdown": {
            "volume": round(volume_score, 2),
            "confirmation": round(confirmation_score, 2),
            "jurisdiction": round(jurisdiction_score, 2),
            "seniority": round(seniority_score, 2),
            "penalties": -penalty_reduction
        },
        "stats": {
            "total_decisions": total,
            "confirmed_decisions": confirmed,
            "confirmation_rate": round(confirmation_rate * 100, 1) if total > 0 else 0,
            "jurisdictions": jurisdictions,
            "days_active": round(days_active, 1),
            "active_penalties": active_penalties
        }
    }

def _check_promotion(wallet_id: str) -> dict:
    """Verifica se operador é elegível para promoção."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM operators WHERE wallet_id=?", (wallet_id,))
    op = c.fetchone()
    if not op:
        conn.close()
        return {"eligible": False, "reason": "Operador não encontrado"}

    if op["suspended"]:
        conn.close()
        return {"eligible": False, "reason": "Operador suspenso"}

    current_level = op["level"]
    total = op["total_decisions"]
    confirmed = op["confirmed_decisions"]

    conn.close()

    rate = confirmed / total if total > 0 else 0

    if current_level == "seed":
        if total >= SEED_TO_MASTER_DECISIONS and rate >= MIN_SUCCESS_RATE:
            return {"eligible": True, "next_level": "master", "reason": f"{total} decisões, {rate:.0%} confirmadas"}
        return {"eligible": False, "reason": f"Precisa {SEED_TO_MASTER_DECISIONS} decisões com {MIN_SUCCESS_RATE:.0%} taxa"}

    if current_level == "master":
        if total >= MASTER_TO_ELDER_DECISIONS and rate >= MIN_SUCCESS_RATE:
            return {"eligible": True, "next_level": "elder", "reason": f"{total} decisões, {rate:.0%} confirmadas"}
        return {"eligible": False, "reason": f"Precisa {MASTER_TO_ELDER_DECISIONS} decisões com {MIN_SUCCESS_RATE:.0%} taxa"}

    return {"eligible": False, "reason": "Já é Elder — nível máximo"}

# ─── Endpoints ───────────────────────────────────────────────────────────────

@virtue_bp.route("/health", methods=["GET"])
def health():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM operators")
        op_count = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM decisions")
        dec_count = c.fetchone()["cnt"]
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False
        op_count = 0
        dec_count = 0

    return jsonify({
        "agent": "W-VIRTUE-001",
        "version": "1.0.0",
        "status": "healthy" if db_ok else "degraded",
        "db": "ok" if db_ok else "error",
        "stats": {
            "operators": op_count,
            "decisions": dec_count
        },
        "principle": "Reputação não se declara. Se constrói com evidência.",
        "endpoints": [
            "POST /virtue/operators/register",
            "GET  /virtue/operators/{wallet_id}",
            "GET  /virtue/operators",
            "POST /virtue/decisions/record",
            "POST /virtue/decisions/confirm",
            "GET  /virtue/score/{wallet_id}",
            "POST /virtue/promote/{wallet_id}",
            "POST /virtue/penalize/{wallet_id}",
            "GET  /virtue/leaderboard",
        ]
    })


@virtue_bp.route("/operators/register", methods=["POST"])
def register_operator():
    body = request.get_json() or {}
    wallet_id = body.get("wallet_id")
    did_short = body.get("did_short", "")
    display_name = body.get("display_name", "")

    if not wallet_id:
        return jsonify({"ok": False, "error": "wallet_id obrigatório"}), 400

    conn = get_db()
    c = conn.cursor()

    # Verificar se já existe
    c.execute("SELECT wallet_id FROM operators WHERE wallet_id=?", (wallet_id,))
    if c.fetchone():
        conn.close()
        return jsonify({"ok": False, "error": "Operador já registrado"}), 400

    now = int(time.time())
    c.execute("""
        INSERT INTO operators (wallet_id, did_short, display_name, level, registered_at, last_activity)
        VALUES (?,?,?,?,?,?)
    """, (wallet_id, did_short, display_name, "seed", now, now))

    receipt_id = f"WINDI-VIRTUE-REG-{wallet_id[:8].upper()}"
    _seal_ledger(receipt_id, {
        "event_type": "operator_registered",
        "actor": wallet_id,
        "wallet_id": wallet_id,
        "level": "seed",
        "timestamp": datetime.datetime.utcfromtimestamp(now).isoformat()
    })

    c.execute("UPDATE operators SET ledger_receipt=? WHERE wallet_id=?", (receipt_id, wallet_id))
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "wallet_id": wallet_id,
        "level": "seed",
        "ledger_receipt": receipt_id,
        "message": "Operador registrado como Seed. Construa sua reputação."
    })


@virtue_bp.route("/operators/<wallet_id>", methods=["GET"])
def get_operator(wallet_id):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM operators WHERE wallet_id=?", (wallet_id,))
    op = c.fetchone()
    if not op:
        conn.close()
        return jsonify({"ok": False, "error": "Operador não encontrado"}), 404

    # Calcular score atual
    score_data = _calculate_virtue_score(wallet_id)
    promotion = _check_promotion(wallet_id)

    conn.close()

    return jsonify({
        "ok": True,
        "operator": {
            "wallet_id": op["wallet_id"],
            "did_short": op["did_short"],
            "display_name": op["display_name"],
            "level": op["level"],
            "registered_at": op["registered_at"],
            "last_activity": op["last_activity"],
            "suspended": bool(op["suspended"]),
            "suspension_reason": op["suspension_reason"],
            "total_decisions": op["total_decisions"],
            "confirmed_decisions": op["confirmed_decisions"],
            "virtue_score": score_data["score"],
            "ledger_receipt": op["ledger_receipt"]
        },
        "score_breakdown": score_data["breakdown"],
        "stats": score_data["stats"],
        "promotion": promotion
    })


@virtue_bp.route("/operators", methods=["GET"])
def list_operators():
    level = request.args.get("level")
    limit = request.args.get("limit", 50, type=int)

    conn = get_db()
    c = conn.cursor()

    if level:
        c.execute("""
            SELECT wallet_id, did_short, display_name, level, virtue_score,
                   total_decisions, suspended, registered_at
            FROM operators WHERE level=? AND suspended=0
            ORDER BY virtue_score DESC LIMIT ?
        """, (level, limit))
    else:
        c.execute("""
            SELECT wallet_id, did_short, display_name, level, virtue_score,
                   total_decisions, suspended, registered_at
            FROM operators WHERE suspended=0
            ORDER BY virtue_score DESC LIMIT ?
        """, (limit,))

    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    return jsonify({
        "ok": True,
        "total": len(rows),
        "operators": rows
    })


@virtue_bp.route("/decisions/record", methods=["POST"])
def record_decision():
    body = request.get_json() or {}
    wallet_id = body.get("wallet_id")
    decision_type = body.get("decision_type")
    case_id = body.get("case_id", "")
    jurisdiction = body.get("jurisdiction", "local")
    client_id = body.get("client_id", "")
    description = body.get("description", "")
    outcome = body.get("outcome", "")

    if not all([wallet_id, decision_type]):
        return jsonify({"ok": False, "error": "wallet_id e decision_type obrigatórios"}), 400

    conn = get_db()
    c = conn.cursor()

    # Verificar operador existe e não está suspenso
    c.execute("SELECT * FROM operators WHERE wallet_id=?", (wallet_id,))
    op = c.fetchone()
    if not op:
        conn.close()
        return jsonify({"ok": False, "error": "Operador não registrado"}), 404
    if op["suspended"]:
        conn.close()
        return jsonify({"ok": False, "error": "Operador suspenso"}), 403

    now = int(time.time())
    dec_id = _gen_id("DEC", f"{wallet_id}:{decision_type}:{now}")

    c.execute("""
        INSERT INTO decisions
        (id, wallet_id, case_id, decision_type, jurisdiction, client_id, description, outcome, sealed_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (dec_id, wallet_id, case_id, decision_type, jurisdiction, client_id, description, outcome, now))

    # Atualizar contador do operador
    c.execute("""
        UPDATE operators
        SET total_decisions = total_decisions + 1, last_activity = ?
        WHERE wallet_id = ?
    """, (now, wallet_id))

    receipt_id = f"WINDI-DEC-{dec_id}"
    _seal_ledger(receipt_id, {
        "event_type": "decision_recorded",
        "actor": wallet_id,
        "decision_id": dec_id,
        "decision_type": decision_type,
        "jurisdiction": jurisdiction,
        "timestamp": datetime.datetime.utcfromtimestamp(now).isoformat()
    })

    c.execute("UPDATE decisions SET ledger_receipt=? WHERE id=?", (receipt_id, dec_id))
    conn.commit()

    # Recalcular score
    score_data = _calculate_virtue_score(wallet_id)
    c.execute("UPDATE operators SET virtue_score=? WHERE wallet_id=?", (score_data["score"], wallet_id))
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "decision_id": dec_id,
        "reliability": "self_declared",
        "ledger_receipt": receipt_id,
        "new_virtue_score": score_data["score"],
        "message": "Decisão registrada. Aguardando confirmação do cliente para upgrade de reliability."
    })


@virtue_bp.route("/decisions/confirm", methods=["POST"])
def confirm_decision():
    """Cliente confirma que decisão/trabalho foi realizado."""
    body = request.get_json() or {}
    decision_id = body.get("decision_id")
    client_id = body.get("client_id")
    ip_hash = body.get("ip_hash", "")

    if not all([decision_id, client_id]):
        return jsonify({"ok": False, "error": "decision_id e client_id obrigatórios"}), 400

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM decisions WHERE id=?", (decision_id,))
    dec = c.fetchone()
    if not dec:
        conn.close()
        return jsonify({"ok": False, "error": "Decisão não encontrada"}), 404

    # Verificar se já confirmada
    if dec["reliability"] == "audited_confirmed":
        conn.close()
        return jsonify({"ok": False, "error": "Decisão já confirmada"}), 400

    now = int(time.time())
    conf_id = _gen_id("CONF", f"{decision_id}:{client_id}")

    # Registrar confirmação
    c.execute("""
        INSERT INTO client_confirmations (id, decision_id, client_id, confirmed, confirmed_at, ip_hash)
        VALUES (?,?,?,1,?,?)
    """, (conf_id, decision_id, client_id, now, ip_hash))

    # Atualizar reliability da decisão
    c.execute("UPDATE decisions SET reliability='audited_confirmed' WHERE id=?", (decision_id,))

    # Atualizar contador do operador
    c.execute("""
        UPDATE operators
        SET confirmed_decisions = confirmed_decisions + 1
        WHERE wallet_id = ?
    """, (dec["wallet_id"],))

    receipt_id = f"WINDI-CONF-{conf_id}"
    _seal_ledger(receipt_id, {
        "event_type": "decision_confirmed",
        "actor": client_id,
        "decision_id": decision_id,
        "operator_wallet": dec["wallet_id"],
        "timestamp": datetime.datetime.utcfromtimestamp(now).isoformat()
    })

    c.execute("UPDATE client_confirmations SET ledger_receipt=? WHERE id=?", (receipt_id, conf_id))
    conn.commit()

    # Recalcular score
    score_data = _calculate_virtue_score(dec["wallet_id"])
    c.execute("UPDATE operators SET virtue_score=? WHERE wallet_id=?", (score_data["score"], dec["wallet_id"]))
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "confirmation_id": conf_id,
        "decision_id": decision_id,
        "new_reliability": "audited_confirmed",
        "ledger_receipt": receipt_id,
        "message": "Confirmação selada. Decisão agora tem reliability máxima."
    })


@virtue_bp.route("/score/<wallet_id>", methods=["GET"])
def get_score(wallet_id):
    score_data = _calculate_virtue_score(wallet_id)
    if score_data["score"] == 0 and not score_data.get("breakdown"):
        return jsonify({"ok": False, "error": "Operador não encontrado"}), 404

    return jsonify({
        "ok": True,
        "wallet_id": wallet_id,
        "virtue_score": score_data["score"],
        "breakdown": score_data["breakdown"],
        "stats": score_data["stats"]
    })


@virtue_bp.route("/promote/<wallet_id>", methods=["POST"])
def promote_operator(wallet_id):
    """Promove operador para próximo nível se elegível."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM operators WHERE wallet_id=?", (wallet_id,))
    op = c.fetchone()
    if not op:
        conn.close()
        return jsonify({"ok": False, "error": "Operador não encontrado"}), 404

    promotion = _check_promotion(wallet_id)
    if not promotion["eligible"]:
        conn.close()
        return jsonify({"ok": False, "error": promotion["reason"]}), 400

    old_level = op["level"]
    new_level = promotion["next_level"]
    now = int(time.time())

    c.execute("UPDATE operators SET level=? WHERE wallet_id=?", (new_level, wallet_id))

    change_id = _gen_id("LVL", f"{wallet_id}:{new_level}")
    c.execute("""
        INSERT INTO level_changes (id, wallet_id, old_level, new_level, reason, changed_at)
        VALUES (?,?,?,?,?,?)
    """, (change_id, wallet_id, old_level, new_level, promotion["reason"], now))

    receipt_id = f"WINDI-PROMO-{change_id}"
    _seal_ledger(receipt_id, {
        "event_type": "operator_promoted",
        "actor": wallet_id,
        "wallet_id": wallet_id,
        "old_level": old_level,
        "new_level": new_level,
        "reason": promotion["reason"],
        "timestamp": datetime.datetime.utcfromtimestamp(now).isoformat()
    })

    c.execute("UPDATE level_changes SET ledger_receipt=? WHERE id=?", (receipt_id, change_id))
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "wallet_id": wallet_id,
        "old_level": old_level,
        "new_level": new_level,
        "ledger_receipt": receipt_id,
        "message": f"Promovido de {old_level} para {new_level}!"
    })


@virtue_bp.route("/penalize/<wallet_id>", methods=["POST"])
def penalize_operator(wallet_id):
    """Aplica penalidade a um operador."""
    body = request.get_json() or {}
    penalty_type = body.get("penalty_type")
    severity = body.get("severity", "low")
    reason = body.get("reason", "")
    duration_days = body.get("duration_days")

    if not penalty_type:
        return jsonify({"ok": False, "error": "penalty_type obrigatório"}), 400

    if severity not in ("low", "medium", "high", "critical"):
        return jsonify({"ok": False, "error": "severity deve ser: low|medium|high|critical"}), 400

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM operators WHERE wallet_id=?", (wallet_id,))
    op = c.fetchone()
    if not op:
        conn.close()
        return jsonify({"ok": False, "error": "Operador não encontrado"}), 404

    now = int(time.time())
    expires_at = now + (duration_days * 86400) if duration_days else None

    pen_id = _gen_id("PEN", f"{wallet_id}:{penalty_type}")
    c.execute("""
        INSERT INTO penalties (id, wallet_id, penalty_type, severity, reason, applied_at, expires_at)
        VALUES (?,?,?,?,?,?,?)
    """, (pen_id, wallet_id, penalty_type, severity, reason, now, expires_at))

    # Suspender se severidade crítica
    if severity == "critical":
        c.execute("UPDATE operators SET suspended=1, suspension_reason=? WHERE wallet_id=?",
                  (reason, wallet_id))

    receipt_id = f"WINDI-PEN-{pen_id}"
    _seal_ledger(receipt_id, {
        "event_type": "penalty_applied",
        "actor": "W-VIRTUE-001",
        "wallet_id": wallet_id,
        "penalty_type": penalty_type,
        "severity": severity,
        "reason": reason,
        "timestamp": datetime.datetime.utcfromtimestamp(now).isoformat()
    })

    c.execute("UPDATE penalties SET ledger_receipt=? WHERE id=?", (receipt_id, pen_id))
    conn.commit()

    # Recalcular score
    score_data = _calculate_virtue_score(wallet_id)
    c.execute("UPDATE operators SET virtue_score=? WHERE wallet_id=?", (score_data["score"], wallet_id))
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "penalty_id": pen_id,
        "wallet_id": wallet_id,
        "penalty_type": penalty_type,
        "severity": severity,
        "suspended": severity == "critical",
        "ledger_receipt": receipt_id,
        "new_virtue_score": score_data["score"]
    })


@virtue_bp.route("/leaderboard", methods=["GET"])
def leaderboard():
    """Top operadores por Virtue Score."""
    limit = request.args.get("limit", 20, type=int)
    level = request.args.get("level")

    conn = get_db()
    c = conn.cursor()

    if level:
        c.execute("""
            SELECT wallet_id, did_short, display_name, level, virtue_score,
                   total_decisions, confirmed_decisions
            FROM operators
            WHERE level=? AND suspended=0
            ORDER BY virtue_score DESC LIMIT ?
        """, (level, limit))
    else:
        c.execute("""
            SELECT wallet_id, did_short, display_name, level, virtue_score,
                   total_decisions, confirmed_decisions
            FROM operators
            WHERE suspended=0
            ORDER BY virtue_score DESC LIMIT ?
        """, (limit,))

    rows = c.fetchall()
    conn.close()

    leaderboard = []
    for i, r in enumerate(rows):
        leaderboard.append({
            "rank": i + 1,
            "wallet_id": r["wallet_id"],
            "did_short": r["did_short"],
            "display_name": r["display_name"],
            "level": r["level"],
            "virtue_score": r["virtue_score"],
            "total_decisions": r["total_decisions"],
            "confirmed_decisions": r["confirmed_decisions"],
            "confirmation_rate": round(r["confirmed_decisions"] / r["total_decisions"] * 100, 1) if r["total_decisions"] > 0 else 0
        })

    return jsonify({
        "ok": True,
        "total": len(leaderboard),
        "leaderboard": leaderboard,
        "principle": "Reputação não se declara. Se constrói com evidência."
    })
