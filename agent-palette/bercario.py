# /opt/windi/dragon-hub/bercario.py
# Berçário — Portão de Nascimento Soberano
# Dragon Hub :8108 · Módulo autónomo
# DNA: ALMA → DID → CÉREBRO → LEDGER → MUNDO
# I9: falha silenciosa nunca bloqueia nascimento
# I11: nascimento → IRREMEDIÁVEL no Ledger
# i18n: PT / DE / EN

import sqlite3
import uuid
import urllib.request
import json
from datetime import datetime, timezone
from pathlib import Path

from i18n_bercario import t, response_i18n, Lang, DEFAULT

# ─── CONFIG ────────────────────────────────────────────────────────
DB_PATH = Path("/opt/windi/agent-palette/wallet_databank.db")
LEDGER  = "http://127.0.0.1:8101"

ESTADOS_VALIDOS = ("nasceu", "semDID", "entrou", "voltou", "saiu")


# ─── DB ────────────────────────────────────────────────────────────
def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA journal_mode=WAL")
    return c


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── PORTÃO PRINCIPAL ──────────────────────────────────────────────
def chegada(
    wallet_id: str | None,
    did: str | None,
    lang: Lang = DEFAULT,
) -> dict:
    """
    Ponto de entrada soberano.
    Detecta estado e encaminha para o fluxo correcto.
    Nunca falha sem resposta — I9 garante graceful fallback.
    """
    try:
        with _conn() as db:
            # Sem wallet → nasce agora
            if not wallet_id:
                return _nascer(db, None, lang)

            row = db.execute(
                "SELECT * FROM wallets WHERE wallet_id = ?",
                (wallet_id,)
            ).fetchone()

            # Wallet desconhecida → nasce com o ID fornecido
            if not row:
                return _nascer(db, wallet_id, lang)

            # Tem wallet, sem DID
            if not row["did"]:
                return _registar_estado(db, wallet_id, "semDID", lang)

            # Calcular ausência
            try:
                last = datetime.fromisoformat(row["last_seen_at"])
                agora_dt = datetime.now(timezone.utc)
                # Garantir que last é aware
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                ausencia_s = (agora_dt - last).total_seconds()
            except Exception:
                ausencia_s = 0

            estado = "entrou" if ausencia_s < 86400 else "voltou"
            return _registar_estado(db, wallet_id, estado, lang)

    except Exception as e:
        # I9: falha nunca bloqueia — retorna erro estruturado
        return {
            "estado": "erro",
            "error": str(e),
            "message": t("err.nascimento_falhou", lang),
            "lang": lang,
        }


# ─── NASCIMENTO ────────────────────────────────────────────────────
def _nascer(
    db: sqlite3.Connection,
    wallet_id: str | None,
    lang: Lang,
) -> dict:
    wid   = wallet_id or f"W-{uuid.uuid4().hex[:12].upper()}"
    agora = _now()
    sid   = str(uuid.uuid4())

    db.execute(
        """
        INSERT INTO wallets
            (wallet_id, born_at, last_seen_at, estado_atual, lang)
        VALUES (?, ?, ?, 'nasceu', ?)
        """,
        (wid, agora, agora, lang),
    )

    db.execute(
        """
        INSERT INTO sessions
            (session_id, wallet_id, estado, started_at)
        VALUES (?, ?, 'nasceu', ?)
        """,
        (sid, wid, agora),
    )

    event_id = f"BIRTH-{wid}-{agora[:10].replace('-', '')}"
    db.execute(
        """
        INSERT INTO birth_events
            (event_id, wallet_id, event_type, sealed_at)
        VALUES (?, ?, 'nascimento', ?)
        """,
        (event_id, wid, agora),
    )

    # Selar no Ledger (I11 — IRREMEDIÁVEL)
    receipt_id = _seal_ledger(wid, event_id, "nascimento")
    if receipt_id:
        db.execute(
            "UPDATE birth_events SET ledger_receipt_id = ? WHERE event_id = ?",
            (receipt_id, event_id),
        )

    db.commit()

    ledger_msg = t(
        "ledger.nascimento_selado" if receipt_id else "ledger.sem_seal",
        lang,
    )

    return response_i18n({
        "estado":         "nasceu",
        "wallet_id":      wid,
        "session_id":     sid,
        "born_at":        agora,
        "ledger_receipt": receipt_id,
        "ledger_msg":     ledger_msg,
        "message":        t("msg.nasceu", lang),
        "ui": {
            "titulo":    t("ui.titulo_bercario", lang),
            "portao":    t("ui.portao", lang),
            "criar_did": t("ui.criar_did", lang),
            "continuar": t("ui.continuar", lang),
        },
    }, lang)


# ─── REGISTAR ESTADO (entrou / voltou / semDID) ────────────────────
def _registar_estado(
    db: sqlite3.Connection,
    wallet_id: str,
    estado: str,
    lang: Lang,
) -> dict:
    agora = _now()
    sid   = str(uuid.uuid4())

    db.execute(
        """
        UPDATE wallets
        SET estado_atual   = ?,
            last_seen_at   = ?,
            total_sessions = total_sessions + 1,
            lang           = ?
        WHERE wallet_id = ?
        """,
        (estado, agora, lang, wallet_id),
    )

    db.execute(
        """
        INSERT INTO sessions
            (session_id, wallet_id, estado, started_at)
        VALUES (?, ?, ?, ?)
        """,
        (sid, wallet_id, estado, agora),
    )

    db.commit()

    return response_i18n({
        "estado":     estado,
        "wallet_id":  wallet_id,
        "session_id": sid,
        "message":    t(f"msg.{estado}", lang),
        "ui": {
            "estado_sessao": t("ui.estado_sessao", lang),
            "criar_did":     t("ui.criar_did", lang) if estado == "semDID" else None,
            "continuar":     t("ui.continuar", lang),
        },
    }, lang)


# ─── ENCERRAR SESSÃO ───────────────────────────────────────────────
def encerrar_sessao(session_id: str, lang: Lang = DEFAULT) -> dict:
    try:
        with _conn() as db:
            row = db.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()

            if not row:
                return {
                    "error":   t("err.sessao_nao_encontrada", lang),
                    "lang":    lang,
                }

            agora  = _now()
            inicio = datetime.fromisoformat(row["started_at"])
            if inicio.tzinfo is None:
                inicio = inicio.replace(tzinfo=timezone.utc)
            dur = int((datetime.now(timezone.utc) - inicio).total_seconds())

            db.execute(
                """
                UPDATE sessions
                SET ended_at = ?, duration_s = ?, estado = 'saiu'
                WHERE session_id = ?
                """,
                (agora, dur, session_id),
            )
            db.execute(
                "UPDATE wallets SET estado_atual = 'saiu' WHERE wallet_id = ?",
                (row["wallet_id"],),
            )
            db.commit()

        return response_i18n({
            "estado":     "saiu",
            "session_id": session_id,
            "wallet_id":  row["wallet_id"],
            "duration_s": dur,
            "message":    t("msg.saiu", lang),
        }, lang)

    except Exception as e:
        return {"error": str(e), "lang": lang}


# ─── ESTADO ACTUAL ─────────────────────────────────────────────────
def estado_wallet(wallet_id: str, lang: Lang = DEFAULT) -> dict:
    try:
        with _conn() as db:
            row = db.execute(
                "SELECT * FROM wallets WHERE wallet_id = ?",
                (wallet_id,)
            ).fetchone()

            if not row:
                return {
                    "error": t("err.wallet_nao_encontrada", lang),
                    "lang":  lang,
                }

            sessions = db.execute(
                """
                SELECT estado, started_at, ended_at, duration_s
                FROM sessions
                WHERE wallet_id = ?
                ORDER BY started_at DESC
                LIMIT 10
                """,
                (wallet_id,)
            ).fetchall()

        return response_i18n({
            "estado":         row["estado_atual"],
            "wallet_id":      wallet_id,
            "did":            row["did"],
            "tier":           row["tier"],
            "born_at":        row["born_at"],
            "last_seen_at":   row["last_seen_at"],
            "total_sessions": row["total_sessions"],
            "sessions":       [dict(s) for s in sessions],
            "ui": {
                "nascido_em":    t("ui.nascido_em", lang),
                "ultima_sessao": t("ui.ultima_sessao", lang),
                "total_sessoes": t("ui.total_sessoes", lang),
                "historico":     t("ui.historico", lang),
            },
        }, lang)

    except Exception as e:
        return {"error": str(e), "lang": lang}


# ─── SEAL LEDGER (I11) ─────────────────────────────────────────────
def _seal_ledger(
    wallet_id: str,
    event_id:  str,
    event_type: str,
) -> str | None:
    """
    I9: falha silenciosa — nunca bloqueia o nascimento.
    I11: quando bem-sucedido, registo é IRREMEDIÁVEL.
    """
    try:
        receipt_id = f"WINDI-BERCARIO-{event_id[:20]}"
        payload = json.dumps({
            "id":               receipt_id,
            "actor":            "bercario",
            "app":              "dragon-hub",
            "doc_name":         f"nascimento_{wallet_id}",
            "doc_type":         "doc",
            "governance_level": "HIGH",
            "content_hash":     f"sha256:{uuid.uuid4().hex}",
            "sge_score":        1.0,
            "metadata": {
                "wallet_id":   wallet_id,
                "event_type":  event_type,
                "invariants":  ["I9", "I11"],
                "dna":         "ALMA→DID→CÉREBRO→LEDGER→MUNDO",
            },
        }).encode()

        req = urllib.request.Request(
            f"{LEDGER}/api/receipts",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
            return data.get("id") or data.get("receipt_id") or receipt_id

    except Exception:
        return None  # I9: silencioso
