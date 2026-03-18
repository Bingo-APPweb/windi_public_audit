"""
WINDI WALLET — Provisioning Module v1.0.0
=========================================
Converte leads aprovados em identidades soberanas.
Integra com: Governance API (:8080), Forensic Ledger (:8094), Lead Admin.

Three Dragons Protocol: AI processes. Human decides. WINDI guarantees.

Endpoints:
    POST /api/wallet/provision     — Criar wallet a partir de lead aprovado
    GET  /api/wallet/me            — Obter wallet(s) do humano autenticado
    POST /api/wallet/context/freeze — Congelar contexto institucional
    GET  /api/wallet/health        — Health check do módulo

Custódia: Modelo A (servidor) para MVP, preparado para migração ao Modelo B (cliente).

(c) 2026 WINDI Publishing House — Kempten, Bavaria
"""

import os
import json
import hashlib
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Dependências opcionais (graceful fallback) ─────────────────────────────
try:
    from nacl.signing import SigningKey  # PyNaCl para Ed25519
    HAS_NACL = True
except ImportError:
    HAS_NACL = False

try:
    import uuid_utils  # UUIDv7
    def make_uuid7() -> str:
        return str(uuid_utils.uuid7())
    HAS_UUID7 = True
except ImportError:
    import uuid
    def make_uuid7() -> str:
        """Fallback: UUID4 quando uuid_utils não disponível."""
        return str(uuid.uuid4())
    HAS_UUID7 = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── Configuração ───────────────────────────────────────────────────────────

WALLET_DB_PATH = os.environ.get(
    "WALLET_DB_PATH",
    "/opt/windi/data/wallet.db"
)

FORENSIC_API_URL = os.environ.get(
    "FORENSIC_API_URL",
    "http://localhost:8094"
)

FORENSIC_FALLBACK_DIR = os.environ.get(
    "FORENSIC_FALLBACK_DIR",
    "/opt/windi/backups/forensic_pending"
)

LOG_PATH = os.environ.get(
    "WALLET_LOG_PATH",
    "/opt/windi/logs/wallet.log"
)

# ─── Logging ────────────────────────────────────────────────────────────────

logger = logging.getLogger("windi.wallet")
logger.setLevel(logging.INFO)

_log_dir = Path(LOG_PATH).parent
_log_dir.mkdir(parents=True, exist_ok=True)

_fh = logging.FileHandler(LOG_PATH)
_fh.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
))
logger.addHandler(_fh)


# ============================================================================
# SQLite WALLET DB (MVP — migração para PostgreSQL planejada)
# ============================================================================
# NOTA: Para MVP usamos SQLite (como os demais serviços WINDI).
# O DDL PostgreSQL (001_wallet_schema.sql) é o alvo de produção.
# As tabelas SQLite espelham a estrutura PG com adaptações mínimas.
# ============================================================================

SQLITE_SCHEMA = """
-- wallet_human: identidade imutável
CREATE TABLE IF NOT EXISTS wallet_human (
    human_id        TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    created_by      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    display_name    TEXT,
    legal_name      TEXT,
    email           TEXT,
    pubkey_ed25519  TEXT NOT NULL,
    sip_pass_hash   TEXT,
    fingerprint     TEXT NOT NULL UNIQUE,
    lead_id         TEXT,
    meta            TEXT NOT NULL DEFAULT '{}'
);

-- wallet_key_history: rotações de chave (append-only)
CREATE TABLE IF NOT EXISTS wallet_key_history (
    key_event_id    TEXT PRIMARY KEY,
    human_id        TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    pubkey_ed25519  TEXT NOT NULL,
    reason          TEXT,
    ledger_ref      TEXT,
    meta            TEXT NOT NULL DEFAULT '{}'
);

-- org: organizações
CREATE TABLE IF NOT EXISTS org (
    org_id          TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    name            TEXT NOT NULL,
    domain          TEXT,
    brand_dna       TEXT NOT NULL DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'active',
    isp_profile_id  TEXT,
    meta            TEXT NOT NULL DEFAULT '{}'
);

-- wallet_context: contextos operacionais (PF/PJ)
CREATE TABLE IF NOT EXISTS wallet_context (
    context_id      TEXT PRIMARY KEY,
    human_id        TEXT NOT NULL,
    org_id          TEXT,
    context_type    TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'operator',
    authority_scope TEXT NOT NULL DEFAULT '{}',
    governance_level TEXT NOT NULL DEFAULT 'L1',
    isp_profile_id  TEXT,
    policy_version  TEXT,
    state           TEXT NOT NULL DEFAULT 'active',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    frozen_at       TEXT,
    revoked_at      TEXT,
    revoked_reason  TEXT,
    wallet_id       TEXT NOT NULL UNIQUE,
    meta            TEXT NOT NULL DEFAULT '{}'
);

-- wallet_context_history: versionamento (append-only)
CREATE TABLE IF NOT EXISTS wallet_context_history (
    ctx_event_id    TEXT PRIMARY KEY,
    context_id      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    actor           TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    diff            TEXT NOT NULL,
    ledger_ref      TEXT,
    meta            TEXT NOT NULL DEFAULT '{}'
);

-- ledger_link: referências ao Forensic Ledger (append-only)
CREATE TABLE IF NOT EXISTS ledger_link (
    link_id         TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    human_id        TEXT NOT NULL,
    context_id      TEXT,
    ref_type        TEXT NOT NULL,
    ref_id          TEXT NOT NULL,
    ledger_hash     TEXT NOT NULL,
    ledger_entry    TEXT,
    UNIQUE(ref_type, ref_id, ledger_hash)
);

-- trust_score: estado atual de confiança
CREATE TABLE IF NOT EXISTS trust_score (
    context_id      TEXT PRIMARY KEY,
    updated_at      TEXT NOT NULL,
    score           REAL NOT NULL DEFAULT 50.0,
    level           TEXT NOT NULL DEFAULT 'T1',
    signals         TEXT NOT NULL DEFAULT '{"receipts_ok":0,"receipts_total":0,"decisions_made":0,"policy_violations":0,"audits_passed":0,"recovery_events":0}'
);

-- trust_events: sinais de confiança (append-only)
CREATE TABLE IF NOT EXISTS trust_events (
    trust_event_id  TEXT PRIMARY KEY,
    context_id      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    signal_type     TEXT NOT NULL,
    weight          REAL NOT NULL,
    description     TEXT,
    source_ref      TEXT NOT NULL DEFAULT '{}',
    ledger_ref      TEXT
);

-- clone_wallets: commissioned clone agents (Phase 2 Bridge)
CREATE TABLE IF NOT EXISTS clone_wallets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id        TEXT UNIQUE NOT NULL,
    clone_id        TEXT NOT NULL,
    public_key      TEXT NOT NULL,
    fingerprint     TEXT NOT NULL,
    constitutional_hash TEXT NOT NULL,
    genesis_seal    TEXT NOT NULL,
    phase           TEXT DEFAULT 'PHASE_2_COMMISSIONED',
    commissioned_at TEXT NOT NULL,
    commissioned_by TEXT NOT NULL,
    verified        INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db() -> sqlite3.Connection:
    """Conecta ao SQLite do WALLET com Turbo PRAGMAs para alta concorrência."""
    db_path = Path(WALLET_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    # Turbo PRAGMAs - Autarquia Máxima
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-8000")       # 8MB cache
    conn.execute("PRAGMA mmap_size=268435456")    # 256MB mmap
    conn.execute("PRAGMA busy_timeout=5000")      # 5s timeout
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Inicializa tabelas se não existem."""
    conn = get_db()
    conn.executescript(SQLITE_SCHEMA)
    conn.commit()
    conn.close()
    logger.info("WALLET DB initialized at %s", WALLET_DB_PATH)


# ============================================================================
# CRIPTOGRAFIA — Geração de Chaves Ed25519
# ============================================================================

def generate_keypair() -> dict:
    """
    Gera par de chaves Ed25519.
    Modelo A (custódia servidor): chave privada armazenada no servidor.
    Retorna dict com pubkey (base64), privkey_hex (para armazenamento seguro),
    e fingerprint.
    """
    if HAS_NACL:
        signing_key = SigningKey.generate()
        pubkey_bytes = signing_key.verify_key.encode()
        privkey_bytes = signing_key.encode()

        import base64
        pubkey_b64 = base64.b64encode(pubkey_bytes).decode("ascii")
        privkey_hex = privkey_bytes.hex()
    else:
        # Fallback: gerar pseudo-chave para desenvolvimento
        import secrets
        fake_seed = secrets.token_bytes(32)
        pubkey_b64 = hashlib.sha256(fake_seed).hexdigest()[:44]
        privkey_hex = fake_seed.hex()
        logger.warning("PyNaCl not available — using fallback key generation (DEV ONLY)")

    return {
        "pubkey_b64": pubkey_b64,
        "privkey_hex": privkey_hex,
    }


def compute_fingerprint(pubkey: str, human_id: str, created_at: str) -> str:
    """SHA-256 do pubkey + human_id + created_at → identidade curta."""
    raw = f"{pubkey}|{human_id}|{created_at}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ============================================================================
# FORENSIC LEDGER — Registro de eventos
# ============================================================================

def register_forensic_event(payload: dict) -> Optional[dict]:
    """
    Registra evento no Forensic Ledger (:8094).
    Fallback: salva localmente se Forensic não responde.
    Retorna dict com entry_id e hash, ou None se falhou.
    """
    if not HAS_REQUESTS:
        logger.warning("requests not available — forensic fallback only")
        return _forensic_fallback(payload)

    try:
        resp = requests.post(
            f"{FORENSIC_API_URL}/api/register",
            json=payload,
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            logger.info("Forensic registered: %s → entry %s",
                        payload.get("ref_id"), data.get("entry_id"))
            return data
        else:
            logger.warning("Forensic responded %d — falling back", resp.status_code)
            return _forensic_fallback(payload)
    except Exception as e:
        logger.warning("Forensic unreachable (%s) — falling back", str(e))
        return _forensic_fallback(payload)


def _forensic_fallback(payload: dict) -> dict:
    """Salva evento localmente para sync posterior."""
    fallback_dir = Path(FORENSIC_FALLBACK_DIR)
    fallback_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ref_id = payload.get("ref_id", "unknown")
    filename = f"{now}_{ref_id}.json"

    filepath = fallback_dir / filename
    filepath.write_text(json.dumps(payload, indent=2, default=str))

    # Gerar hash local como substituto
    local_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()

    logger.info("Forensic fallback saved: %s (hash: %s...)", filename, local_hash[:16])

    return {
        "entry_id": f"LOCAL-{now}",
        "hash": local_hash,
        "pending_sync": True,
    }


# ============================================================================
# WALLET ID — Gerador de IDs legíveis
# ============================================================================

def generate_wallet_id(conn: sqlite3.Connection) -> str:
    """Gera WALLET-YYYYMMDD-NNNN sequencial."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"WALLET-{today}-"

    row = conn.execute(
        "SELECT wallet_id FROM wallet_context "
        "WHERE wallet_id LIKE ? ORDER BY wallet_id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()

    if row:
        last_num = int(row["wallet_id"].split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1

    return f"{prefix}{next_num:04d}"


# ============================================================================
# CORE: PROVISIONING
# ============================================================================

def provision_wallet(data: dict) -> dict:
    """
    Converte lead aprovado em WALLET soberano.

    Fluxo:
        1. Validar dados de entrada
        2. Verificar idempotência (lead_id já provisionado?)
        3. Gerar human_id (UUIDv7) + chaves Ed25519
        4. Inserir wallet_human (imutável)
        5. Criar org se PJ e inexistente
        6. Criar wallet_context + trust_score
        7. Registrar WALLET_PROVISIONED no Forensic
        8. Criar ledger_link
        9. Registrar key_created em wallet_key_history
       10. Retornar wallet completo

    Args:
        data: dict com lead_id, email, display_name, kind (PF/PJ),
              org (name, domain), role, approved_by, etc.

    Returns:
        dict com human_id, context_id, wallet_id, pubkey, fingerprint, ledger info.

    Raises:
        ValueError: dados inválidos
        RuntimeError: falha de provisioning
    """
    # ─── 1. Validar ─────────────────────────────────────────────────────────
    lead_id = data.get("lead_id")
    if not lead_id:
        raise ValueError("lead_id is required")

    kind = data.get("kind", "PF").upper()
    if kind not in ("PF", "PJ"):
        raise ValueError("kind must be PF or PJ")

    email = data.get("email", "")
    display_name = data.get("display_name", "")
    approved_by = data.get("approved_by", "system")
    role = data.get("role", "operator")

    now_iso = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    try:
        # ─── 2. Idempotência ────────────────────────────────────────────────
        existing = conn.execute(
            "SELECT wh.human_id, wc.wallet_id FROM wallet_human wh "
            "LEFT JOIN wallet_context wc ON wc.human_id = wh.human_id "
            "WHERE wh.lead_id = ?",
            (lead_id,)
        ).fetchone()

        if existing:
            logger.info("Idempotent: lead %s already provisioned as %s",
                        lead_id, existing["wallet_id"])
            # Retornar dados existentes
            full = conn.execute(
                "SELECT * FROM wallet_human WHERE human_id = ?",
                (existing["human_id"],)
            ).fetchone()
            ctx = conn.execute(
                "SELECT * FROM wallet_context WHERE human_id = ?",
                (existing["human_id"],)
            ).fetchone()
            return {
                "status": "ok",
                "idempotent": True,
                "human_id": existing["human_id"],
                "wallet_id": existing["wallet_id"],
                "context_id": ctx["context_id"] if ctx else None,
                "pubkey": full["pubkey_ed25519"] if full else None,
                "fingerprint": full["fingerprint"] if full else None,
            }

        # ─── 3. Gerar identidade ────────────────────────────────────────────
        human_id = make_uuid7()
        keypair = generate_keypair()
        pubkey = keypair["pubkey_b64"]
        fingerprint = compute_fingerprint(pubkey, human_id, now_iso)

        # ─── 4. Inserir wallet_human ────────────────────────────────────────
        conn.execute(
            """INSERT INTO wallet_human
               (human_id, created_at, created_by, status,
                display_name, email, pubkey_ed25519, fingerprint, lead_id, meta)
               VALUES (?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)""",
            (human_id, now_iso, approved_by,
             display_name, email, pubkey, fingerprint, lead_id,
             json.dumps({"provisioned_from": "governance_api"}))
        )

        # ─── 5. Org (se PJ) ────────────────────────────────────────────────
        org_id = None
        if kind == "PJ":
            org_data = data.get("org", {})
            org_name = org_data.get("name", "")
            org_domain = org_data.get("domain", "")

            if org_domain:
                existing_org = conn.execute(
                    "SELECT org_id FROM org WHERE domain = ?",
                    (org_domain,)
                ).fetchone()

                if existing_org:
                    org_id = existing_org["org_id"]
                else:
                    org_id = make_uuid7()
                    conn.execute(
                        """INSERT INTO org
                           (org_id, created_at, name, domain, brand_dna, status)
                           VALUES (?, ?, ?, ?, '{}', 'active')""",
                        (org_id, now_iso, org_name, org_domain)
                    )
            else:
                org_id = make_uuid7()
                conn.execute(
                    """INSERT INTO org
                       (org_id, created_at, name, domain, brand_dna, status)
                       VALUES (?, ?, ?, NULL, '{}', 'active')""",
                    (org_id, now_iso, org_name)
                )

        # ─── 6. Criar wallet_context + trust_score ──────────────────────────
        context_id = make_uuid7()
        wallet_id = generate_wallet_id(conn)

        conn.execute(
            """INSERT INTO wallet_context
               (context_id, human_id, org_id, context_type, role,
                authority_scope, governance_level, state,
                created_at, updated_at, wallet_id, meta)
               VALUES (?, ?, ?, ?, ?, '{}', 'L1', 'active', ?, ?, ?, '{}')""",
            (context_id, human_id, org_id, kind, role,
             now_iso, now_iso, wallet_id)
        )

        # Trust score inicial
        conn.execute(
            """INSERT INTO trust_score
               (context_id, updated_at, score, level, signals)
               VALUES (?, ?, 50.0, 'T1', ?)""",
            (context_id, now_iso, json.dumps({
                "receipts_ok": 0, "receipts_total": 0,
                "decisions_made": 0, "policy_violations": 0,
                "audits_passed": 0, "recovery_events": 0,
            }))
        )

        # ─── 7. Forensic Ledger ─────────────────────────────────────────────
        forensic_payload = {
            "ref_id": wallet_id,
            "ref_type": "WALLET_PROVISIONED",
            "impact_level": "CRITICAL",
            "risk_level": "R0",
            "actor": {"approved_by": approved_by},
            "subject": {
                "human_id": human_id,
                "context_id": context_id,
                "context_type": kind,
                "org_domain": data.get("org", {}).get("domain", ""),
            },
            "hashes": {
                "pubkey_fingerprint": fingerprint,
            },
            "timestamp": now_iso,
        }

        forensic_result = register_forensic_event(forensic_payload)

        # ─── 8. Ledger link ─────────────────────────────────────────────────
        ledger_hash = (forensic_result or {}).get("hash", "pending")
        ledger_entry = (forensic_result or {}).get("entry_id", "pending")

        conn.execute(
            """INSERT INTO ledger_link
               (link_id, created_at, human_id, context_id,
                ref_type, ref_id, ledger_hash, ledger_entry)
               VALUES (?, ?, ?, ?, 'WALLET_PROVISIONED', ?, ?, ?)""",
            (make_uuid7(), now_iso, human_id, context_id,
             wallet_id, ledger_hash, ledger_entry)
        )

        # ─── 9. Key history ─────────────────────────────────────────────────
        conn.execute(
            """INSERT INTO wallet_key_history
               (key_event_id, human_id, created_at, event_type,
                pubkey_ed25519, reason, ledger_ref)
               VALUES (?, ?, ?, 'key_created', ?, 'initial_provisioning', ?)""",
            (make_uuid7(), human_id, now_iso, pubkey, ledger_hash)
        )

        # ─── 10. Context history (evento inicial) ───────────────────────────
        conn.execute(
            """INSERT INTO wallet_context_history
               (ctx_event_id, context_id, created_at, actor, event_type, diff)
               VALUES (?, ?, ?, ?, 'created', ?)""",
            (make_uuid7(), context_id, now_iso, approved_by,
             json.dumps({"kind": kind, "role": role, "wallet_id": wallet_id}))
        )

        # ─── Commit ─────────────────────────────────────────────────────────
        conn.commit()

        # Armazenar chave privada de forma segura (Modelo A)
        _store_private_key(human_id, keypair["privkey_hex"])

        logger.info(
            "WALLET PROVISIONED: %s | human=%s | kind=%s | lead=%s",
            wallet_id, human_id, kind, lead_id
        )

        # ─── G3 — Lead Admin Hook (fire-and-forget) ────────────────────────
        import requests as _req
        try:
            _req.post(
                "http://127.0.0.1:8096/api/leads/register",
                json={"wallet_id": wallet_id, "email": email,
                      "tier": "PIONEER", "source": "wallet_provision"},
                timeout=2
            )
        except Exception:
            pass  # Hook não bloqueia provision — fire-and-forget

        return {
            "status": "ok",
            "human_id": human_id,
            "context_id": context_id,
            "wallet_id": wallet_id,
            "pubkey": f"ed25519:{pubkey}",
            "fingerprint": fingerprint,
            "trust": {"score": 50.0, "level": "T1"},
            "ledger": {
                "entry_id": ledger_entry,
                "hash": ledger_hash,
                "ref_id": wallet_id,
                "pending_sync": (forensic_result or {}).get("pending_sync", False),
            },
            "next": {
                "a4_builder_url": f"/a4builder?wallet={wallet_id}",
            },
        }

    except Exception as e:
        conn.rollback()
        logger.error("Provisioning failed for lead %s: %s", lead_id, str(e))
        raise RuntimeError(f"Provisioning failed: {str(e)}")
    finally:
        conn.close()


def _store_private_key(human_id: str, privkey_hex: str):
    """
    Armazena chave privada com permissões restritas.
    Modelo A: custódia no servidor.
    PRODUÇÃO: migrar para HSM ou vault.
    """
    keys_dir = Path("/opt/windi/tsil/wallet_keys")
    keys_dir.mkdir(parents=True, exist_ok=True)

    key_file = keys_dir / f"{human_id}.key"
    key_file.write_text(privkey_hex)
    key_file.chmod(0o600)
    logger.info("Private key stored for human %s", human_id)


# ============================================================================
# QUERY: /api/wallet/me
# ============================================================================

def get_wallet_by_email(email: str) -> Optional[dict]:
    """Retorna todos os contextos do humano identificado pelo email."""
    conn = get_db()
    try:
        human = conn.execute(
            "SELECT * FROM wallet_human WHERE email = ? AND status = 'active'",
            (email,)
        ).fetchone()

        if not human:
            return None

        contexts = conn.execute(
            """SELECT wc.*, ts.score AS trust_score, ts.level AS trust_level,
                      ts.signals AS trust_signals,
                      o.name AS org_name, o.domain AS org_domain, o.brand_dna
               FROM wallet_context wc
               LEFT JOIN trust_score ts ON ts.context_id = wc.context_id
               LEFT JOIN org o ON o.org_id = wc.org_id
               WHERE wc.human_id = ? AND wc.state = 'active'
               ORDER BY wc.created_at DESC""",
            (human["human_id"],)
        ).fetchall()

        return {
            "human_id": human["human_id"],
            "display_name": human["display_name"],
            "fingerprint": human["fingerprint"],
            "human_status": human["status"],
            "contexts": [
                {
                    "context_id": c["context_id"],
                    "wallet_id": c["wallet_id"],
                    "context_type": c["context_type"],
                    "role": c["role"],
                    "governance_level": c["governance_level"],
                    "state": c["state"],
                    "trust": {
                        "score": c["trust_score"],
                        "level": c["trust_level"],
                    },
                    "org": {
                        "name": c["org_name"],
                        "domain": c["org_domain"],
                        "brand_dna": json.loads(c["brand_dna"] or "{}"),
                    } if c["org_name"] else None,
                    "render": {
                        "path": "PJ" if c["context_type"] == "PJ" else "PF",
                        "isp_profile_id": c["isp_profile_id"],
                        "builder_url": f"/a4builder?wallet={c['wallet_id']}",
                    },
                }
                for c in contexts
            ],
        }
    finally:
        conn.close()


def get_wallet_by_id(wallet_id: str) -> Optional[dict]:
    """Retorna wallet pelo WALLET-YYYYMMDD-NNNN."""
    conn = get_db()
    try:
        ctx = conn.execute(
            "SELECT * FROM wallet_context WHERE wallet_id = ?",
            (wallet_id,)
        ).fetchone()

        if not ctx:
            return None

        human = conn.execute(
            "SELECT * FROM wallet_human WHERE human_id = ?",
            (ctx["human_id"],)
        ).fetchone()

        trust = conn.execute(
            "SELECT * FROM trust_score WHERE context_id = ?",
            (ctx["context_id"],)
        ).fetchone()

        org = None
        if ctx["org_id"]:
            org_row = conn.execute(
                "SELECT * FROM org WHERE org_id = ?",
                (ctx["org_id"],)
            ).fetchone()
            if org_row:
                org = {
                    "org_id": org_row["org_id"],
                    "name": org_row["name"],
                    "domain": org_row["domain"],
                    "brand_dna": json.loads(org_row["brand_dna"] or "{}"),
                }

        return {
            "human_id": human["human_id"],
            "display_name": human["display_name"],
            "fingerprint": human["fingerprint"],
            "wallet_id": wallet_id,
            "context_type": ctx["context_type"],
            "role": ctx["role"],
            "state": ctx["state"],
            "governance_level": ctx["governance_level"],
            "trust": {
                "score": trust["score"] if trust else 50.0,
                "level": trust["level"] if trust else "T1",
            },
            "org": org,
            "render": {
                "path": "PJ" if ctx["context_type"] == "PJ" else "PF",
                "isp_profile_id": ctx["isp_profile_id"],
            },
        }
    finally:
        conn.close()


# ============================================================================
# FREEZE: Congelar contexto (desligamento)
# ============================================================================

def freeze_context(context_id: str, actor: str, reason: str = "") -> dict:
    """
    Congela um contexto institucional (desligamento).
    - state → frozen
    - Registra no Forensic Ledger
    - Não apaga wallet_human (soberania preservada)
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_db()

    try:
        ctx = conn.execute(
            "SELECT * FROM wallet_context WHERE context_id = ?",
            (context_id,)
        ).fetchone()

        if not ctx:
            raise ValueError(f"Context {context_id} not found")

        if ctx["state"] != "active":
            raise ValueError(f"Context {context_id} is already {ctx['state']}")

        # Atualizar estado
        conn.execute(
            """UPDATE wallet_context
               SET state = 'frozen', frozen_at = ?, updated_at = ?,
                   revoked_reason = ?
               WHERE context_id = ?""",
            (now_iso, now_iso, reason, context_id)
        )

        # Context history (trigger PG faria isso, aqui fazemos manual)
        conn.execute(
            """INSERT INTO wallet_context_history
               (ctx_event_id, context_id, created_at, actor, event_type, diff)
               VALUES (?, ?, ?, ?, 'frozen', ?)""",
            (make_uuid7(), context_id, now_iso, actor,
             json.dumps({"reason": reason, "wallet_id": ctx["wallet_id"]}))
        )

        # Forensic
        forensic_payload = {
            "ref_id": ctx["wallet_id"],
            "ref_type": "CONTEXT_FROZEN",
            "impact_level": "HIGH",
            "risk_level": "R1",
            "actor": {"frozen_by": actor},
            "subject": {
                "human_id": ctx["human_id"],
                "context_id": context_id,
                "reason": reason,
            },
            "timestamp": now_iso,
        }
        forensic_result = register_forensic_event(forensic_payload)

        # Ledger link
        conn.execute(
            """INSERT INTO ledger_link
               (link_id, created_at, human_id, context_id,
                ref_type, ref_id, ledger_hash, ledger_entry)
               VALUES (?, ?, ?, ?, 'CONTEXT_FROZEN', ?, ?, ?)""",
            (make_uuid7(), now_iso, ctx["human_id"], context_id,
             ctx["wallet_id"],
             (forensic_result or {}).get("hash", "pending"),
             (forensic_result or {}).get("entry_id", "pending"))
        )

        conn.commit()

        logger.info("CONTEXT FROZEN: %s | wallet=%s | actor=%s",
                     context_id, ctx["wallet_id"], actor)

        return {
            "status": "ok",
            "context_id": context_id,
            "wallet_id": ctx["wallet_id"],
            "new_state": "frozen",
            "human_sovereignty": "preserved",
        }
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================================
# STATS: Dashboard data
# ============================================================================

def get_wallet_stats() -> dict:
    """Retorna estatísticas para dashboard/Sentinel."""
    conn = get_db()
    try:
        total_humans = conn.execute(
            "SELECT COUNT(*) as c FROM wallet_human"
        ).fetchone()["c"]

        active_contexts = conn.execute(
            "SELECT COUNT(*) as c FROM wallet_context WHERE state = 'active'"
        ).fetchone()["c"]

        frozen_contexts = conn.execute(
            "SELECT COUNT(*) as c FROM wallet_context WHERE state = 'frozen'"
        ).fetchone()["c"]

        total_ledger_links = conn.execute(
            "SELECT COUNT(*) as c FROM ledger_link"
        ).fetchone()["c"]

        avg_trust = conn.execute(
            "SELECT AVG(score) as avg FROM trust_score"
        ).fetchone()["avg"]

        return {
            "total_humans": total_humans,
            "active_contexts": active_contexts,
            "frozen_contexts": frozen_contexts,
            "total_ledger_links": total_ledger_links,
            "avg_trust_score": round(avg_trust or 0, 2),
            "db_path": WALLET_DB_PATH,
            "has_nacl": HAS_NACL,
            "has_uuid7": HAS_UUID7,
        }
    finally:
        conn.close()


# ============================================================================
# TRUST EVENTS: Record trust signals and update score
# ============================================================================

def record_trust_event(data: dict) -> dict:
    """
    Record a trust event and update the trust_score.

    Args:
        data: {
            wallet_id: str,
            event_type: str (e.g., 'receipt_created'),
            signal: int (+1, -1, etc.),
            receipt_id: Optional[str]
        }

    Returns:
        Updated trust_score info
    """
    wallet_id = data.get("wallet_id")
    signal_type = data.get("event_type", "unknown")
    weight = float(data.get("signal", 1))
    receipt_id = data.get("receipt_id")

    if not wallet_id:
        raise ValueError("wallet_id required")

    conn = get_db()
    try:
        # Find context_id for this wallet
        ctx = conn.execute(
            "SELECT context_id FROM wallet_context WHERE wallet_id = ?",
            (wallet_id,)
        ).fetchone()

        if not ctx:
            raise ValueError(f"wallet not found: {wallet_id}")

        context_id = ctx["context_id"]

        # Generate event ID
        event_id = make_uuid7()
        now = datetime.now(timezone.utc).isoformat()

        # Build source_ref JSON
        source_ref = json.dumps({"receipt_id": receipt_id}) if receipt_id else "{}"

        # Insert trust event (append-only) — matches actual schema
        conn.execute(
            """INSERT INTO trust_events
               (trust_event_id, context_id, created_at, signal_type, weight, description, source_ref)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (event_id, context_id, now, signal_type, weight,
             f"Trust signal from {signal_type}", source_ref)
        )

        # Update trust_score
        conn.execute(
            """UPDATE trust_score
               SET score = MIN(100, MAX(0, score + ?)),
                   signals = signals + 1,
                   level = CASE
                       WHEN MIN(100, MAX(0, score + ?)) >= 95 THEN 5
                       WHEN MIN(100, MAX(0, score + ?)) >= 80 THEN 4
                       WHEN MIN(100, MAX(0, score + ?)) >= 65 THEN 3
                       WHEN MIN(100, MAX(0, score + ?)) >= 50 THEN 2
                       ELSE 1
                   END,
                   updated_at = ?
               WHERE context_id = ?""",
            (weight, weight, weight, weight, weight, now, context_id)
        )

        conn.commit()

        # Fetch updated score
        updated = conn.execute(
            "SELECT score, level, signals FROM trust_score WHERE context_id = ?",
            (context_id,)
        ).fetchone()

        return {
            "ok": True,
            "event_id": event_id,
            "wallet_id": wallet_id,
            "trust_score": updated["score"] if updated else 50,
            "trust_level": updated["level"] if updated else 1,
            "trust_signals": updated["signals"] if updated else 0
        }

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ============================================================================
# CLONE WALLET: Registration & Verification (Phase 2 Bridge)
# ============================================================================

def register_clone_wallet(data: dict) -> dict:
    """
    Register a commissioned clone wallet.

    Args:
        data: dict with agent_id, public_key, fingerprint, constitutional_hash,
              genesis_seal, clone_id, commissioned_at, commissioned_by

    Returns:
        dict with status, agent_id, fingerprint

    Raises:
        ValueError: invalid data
    """
    agent_id = data.get("agent_id")
    if not agent_id:
        raise ValueError("agent_id is required")

    # Validate agent_id format: W-[32 hex digits]
    import re
    if not re.match(r"^W-[0-9a-fA-F]{32}$", agent_id):
        raise ValueError(f"Invalid agent_id format: {agent_id}. Expected W-[32 hex digits]")

    fingerprint = data.get("fingerprint", "")
    if not fingerprint:
        raise ValueError("fingerprint is required")

    clone_id = data.get("clone_id", f"CLONE-{agent_id[-8:]}")
    public_key = data.get("public_key", "")
    constitutional_hash = data.get("constitutional_hash", "")
    genesis_seal = data.get("genesis_seal", "")
    phase = data.get("phase", "PHASE_2_COMMISSIONED")
    commissioned_at = data.get("commissioned_at", datetime.now(timezone.utc).isoformat())
    commissioned_by = data.get("commissioned_by", "system")

    conn = get_db()
    try:
        # Check idempotency
        existing = conn.execute(
            "SELECT * FROM clone_wallets WHERE agent_id = ?",
            (agent_id,)
        ).fetchone()

        if existing:
            logger.info("Idempotent: clone %s already registered", agent_id)
            return {
                "status": "registered",
                "idempotent": True,
                "agent_id": agent_id,
                "fingerprint": existing["fingerprint"],
                "phase": existing["phase"],
                "commissioned_at": existing["commissioned_at"],
            }

        # Insert new clone wallet
        conn.execute(
            """INSERT INTO clone_wallets
               (agent_id, clone_id, public_key, fingerprint, constitutional_hash,
                genesis_seal, phase, commissioned_at, commissioned_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (agent_id, clone_id, public_key, fingerprint, constitutional_hash,
             genesis_seal, phase, commissioned_at, commissioned_by)
        )
        conn.commit()

        logger.info("CLONE REGISTERED: %s | fingerprint=%s | phase=%s",
                    agent_id, fingerprint[:32], phase)

        return {
            "status": "registered",
            "agent_id": agent_id,
            "clone_id": clone_id,
            "fingerprint": fingerprint,
            "phase": phase,
            "commissioned_at": commissioned_at,
            "commissioned_by": commissioned_by,
        }
    except Exception as e:
        conn.rollback()
        logger.error("Clone registration failed for %s: %s", agent_id, str(e))
        raise
    finally:
        conn.close()


def verify_clone_wallet(agent_id: str) -> Optional[dict]:
    """
    Verify and return clone wallet data for Tab Wallet display.

    Args:
        agent_id: The clone's agent ID (W-[32 hex digits])

    Returns:
        dict with clone wallet data or None if not found
    """
    conn = get_db()
    try:
        clone = conn.execute(
            "SELECT * FROM clone_wallets WHERE agent_id = ?",
            (agent_id,)
        ).fetchone()

        if not clone:
            return None

        return {
            "agent_id": clone["agent_id"],
            "clone_id": clone["clone_id"],
            "fingerprint": clone["fingerprint"],
            "constitutional_hash": clone["constitutional_hash"],
            "genesis_seal": clone["genesis_seal"],
            "phase": clone["phase"],
            "commissioned_at": clone["commissioned_at"],
            "commissioned_by": clone["commissioned_by"],
            "verified": bool(clone["verified"]),
            "created_at": clone["created_at"],
        }
    finally:
        conn.close()


def get_clone_status() -> dict:
    """
    Get status of all commissioned clones.

    Returns:
        dict with clones list and counts
    """
    conn = get_db()
    try:
        clones = conn.execute(
            """SELECT agent_id, clone_id, fingerprint, phase,
                      commissioned_at, commissioned_by, verified
               FROM clone_wallets ORDER BY created_at DESC"""
        ).fetchall()

        total = len(clones)
        verified_count = sum(1 for c in clones if c["verified"])

        return {
            "total_clones": total,
            "verified_clones": verified_count,
            "pending_verification": total - verified_count,
            "clones": [
                {
                    "agent_id": c["agent_id"],
                    "clone_id": c["clone_id"],
                    "fingerprint": c["fingerprint"],
                    "phase": c["phase"],
                    "commissioned_at": c["commissioned_at"],
                    "commissioned_by": c["commissioned_by"],
                    "verified": bool(c["verified"]),
                }
                for c in clones
            ],
        }
    finally:
        conn.close()


# ============================================================================
# FLASK BLUEPRINT — Para integrar na Governance API (:8080)
# ============================================================================

def create_wallet_blueprint():
    """
    Cria Flask Blueprint com todos os endpoints do WALLET.
    Importar e registrar na Governance API:

        from wallet_provisioning import create_wallet_blueprint
        app.register_blueprint(create_wallet_blueprint())
    """
    from flask import Blueprint, request, jsonify

    bp = Blueprint("wallet", __name__, url_prefix="/api/wallet")

    @bp.before_request
    def ensure_db():
        init_db()

    # ─── POST /api/wallet/provision ──────────────────────────────────────
    @bp.route("/provision", methods=["POST"])
    def endpoint_provision():
        """Provisiona wallet a partir de lead aprovado."""
        data = request.get_json(force=True)
        try:
            result = provision_wallet(data)
            return jsonify(result), 201 if not result.get("idempotent") else 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 500

    # ─── GET /api/wallet/me?email=... ────────────────────────────────────
    @bp.route("/me", methods=["GET"])
    def endpoint_me():
        """Retorna wallet(s) do humano. Query: email ou wallet_id."""
        email = request.args.get("email")
        wallet_id = request.args.get("wallet_id")

        if wallet_id:
            result = get_wallet_by_id(wallet_id)
        elif email:
            result = get_wallet_by_email(email)
        else:
            return jsonify({"error": "email or wallet_id required"}), 400

        if not result:
            return jsonify({"error": "wallet not found"}), 404

        return jsonify(result)

    # ─── POST /api/wallet/context/<id>/freeze ────────────────────────────
    @bp.route("/context/<context_id>/freeze", methods=["POST"])
    def endpoint_freeze(context_id):
        """Congela contexto institucional (desligamento)."""
        data = request.get_json(force=True) if request.data else {}
        actor = data.get("actor", "system")
        reason = data.get("reason", "")

        try:
            result = freeze_context(context_id, actor, reason)
            return jsonify(result)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ─── GET /api/wallet/stats ───────────────────────────────────────────
    @bp.route("/stats", methods=["GET"])
    def endpoint_stats():
        """Estatísticas do sistema WALLET para Sentinel/Dashboard."""
        return jsonify(get_wallet_stats())

    # ─── GET /api/wallet/health ──────────────────────────────────────────
    @bp.route("/health", methods=["GET"])
    def endpoint_health():
        """Health check do módulo WALLET."""
        try:
            stats = get_wallet_stats()
            return jsonify({
                "status": "healthy",
                "module": "WINDI WALLET v1.0.0",
                "protocol": "Three Dragons v1.1 — I9 Active",
                "db": WALLET_DB_PATH,
                "crypto": "Ed25519" if HAS_NACL else "fallback (DEV)",
                "uuid": "v7" if HAS_UUID7 else "v4 (fallback)",
                "humans": stats["total_humans"],
                "contexts_active": stats["active_contexts"],
            })
        except Exception as e:
            return jsonify({
                "status": "degraded",
                "error": str(e),
            }), 503

    return bp


# ============================================================================
# STANDALONE (para teste direto)
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("WINDI WALLET — Provisioning Module v1.0.0")
    print("Three Dragons Protocol: AI processes. Human decides.")
    print("=" * 60)

    # Inicializar DB
    init_db()
    print(f"[OK] DB initialized at {WALLET_DB_PATH}")
    print(f"[{'OK' if HAS_NACL else 'WARN'}] PyNaCl: {HAS_NACL}")
    print(f"[{'OK' if HAS_UUID7 else 'WARN'}] UUIDv7: {HAS_UUID7}")

    # Teste de provisioning
    test_data = {
        "lead_id": "LEAD-TEST-001",
        "email": "test@example.de",
        "display_name": "Test Human",
        "kind": "PF",
        "approved_by": "admin:test",
    }

    print("\n--- Test Provision (PF) ---")
    try:
        result = provision_wallet(test_data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"[ERROR] {e}")

    print("\n--- Test Stats ---")
    print(json.dumps(get_wallet_stats(), indent=2))

    print("\n--- Test Idempotency ---")
    try:
        result2 = provision_wallet(test_data)
        print(f"Idempotent: {result2.get('idempotent')}")
    except Exception as e:
        print(f"[ERROR] {e}")

    print("\nDone. 🐉")
