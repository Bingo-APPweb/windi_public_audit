# ═══════════════════════════════════════════════════════════════════════════════
#  shadow_audit.py — VERA Anti-Backdoor Visibility Layer
#  §204.2 · Liga IA+H · Human Dragon · 25 Abril 2026
#
#  "O backdoor não se manifesta no frontdoor."
#
#  Este módulo NÃO adiciona arquitectura.
#  Apenas OBSERVA e REGISTA o que já acontece.
# ═══════════════════════════════════════════════════════════════════════════════

import json
import hashlib
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# ─── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SHADOW] %(message)s")
log = logging.getLogger("vera.shadow")

# ─── PATHS ───────────────────────────────────────────────────────────────────
SHADOW_DB = Path("/opt/windi/data/shadow_audit.db")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. SHADOW CLASSIFICATION LOG
#    "Cada request precisa registrar: foi classificado como E1/E4/HIGH, por quê"
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ClassificationRecord:
    """Registo invisível de cada decisão de classificação."""
    timestamp: str
    request_hash: str           # SHA-256 dos primeiros 200 chars do input
    input_preview: str          # Primeiros 100 chars (para debug)
    classification: str         # E1_TRIVIAL, E4_NON_PHO, HIGH_GOVERNANCE
    classification_reason: str  # Keywords matched, context_id present, etc.
    routing_path: str           # Mistral, Llama, Claude+GPT4
    pillars_injected: int       # Quantos pilares foram usados
    history_used: int           # Quantas mensagens de histórico
    consensus_required: bool
    consensus_achieved: bool
    models_consulted: List[str]
    divergence_score: float
    latency_ms: int
    officer_did: Optional[str]
    # Post-hoc flags
    suspicious: bool = False
    suspicious_reason: Optional[str] = None


def init_shadow_db():
    """Inicializa a base de dados de auditoria sombra."""
    SHADOW_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SHADOW_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS classification_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            request_hash TEXT NOT NULL,
            input_preview TEXT,
            classification TEXT NOT NULL,
            classification_reason TEXT,
            routing_path TEXT,
            pillars_injected INTEGER,
            history_used INTEGER,
            consensus_required INTEGER,
            consensus_achieved INTEGER,
            models_consulted TEXT,
            divergence_score REAL,
            latency_ms INTEGER,
            officer_did TEXT,
            suspicious INTEGER DEFAULT 0,
            suspicious_reason TEXT,
            UNIQUE(request_hash, timestamp)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backdoor_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT,
            request_hash TEXT,
            metadata TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_class ON classification_log(classification)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_suspicious ON classification_log(suspicious)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts ON backdoor_alerts(alert_type, severity)")
    conn.commit()
    conn.close()
    log.info("Shadow audit DB initialized")


@contextmanager
def shadow_db():
    conn = sqlite3.connect(str(SHADOW_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def log_classification(record: ClassificationRecord):
    """Regista uma classificação para auditoria posterior."""
    try:
        with shadow_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO classification_log
                (timestamp, request_hash, input_preview, classification, classification_reason,
                 routing_path, pillars_injected, history_used, consensus_required, consensus_achieved,
                 models_consulted, divergence_score, latency_ms, officer_did, suspicious, suspicious_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.timestamp, record.request_hash, record.input_preview,
                record.classification, record.classification_reason, record.routing_path,
                record.pillars_injected, record.history_used,
                1 if record.consensus_required else 0,
                1 if record.consensus_achieved else 0,
                json.dumps(record.models_consulted),
                record.divergence_score, record.latency_ms, record.officer_did,
                1 if record.suspicious else 0, record.suspicious_reason
            ))
        log.info(f"Classification logged: {record.classification} | {record.request_hash[:8]}")
    except Exception as e:
        log.error(f"Failed to log classification: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. BACKDOOR DETECTION RULES
#    "Detectar erro silencioso"
# ═══════════════════════════════════════════════════════════════════════════════

BACKDOOR_RULES = {
    # Rule 1: HIGH keywords classified as LOW
    "BD-001": {
        "name": "HIGH_AS_LOW",
        "description": "Input com keywords HIGH foi classificado como LOW_TRIVIAL",
        "severity": "CRITICAL",
        "check": lambda r: (
            r.classification == "LOW_TRIVIAL" and
            any(kw in r.input_preview.lower() for kw in
                ["gdpr", "eu ai act", "artigo", "artikel", "legal", "compliance", "parecer"])
        )
    },
    # Rule 2: Consensus required but not achieved
    "BD-002": {
        "name": "CONSENSUS_BYPASS",
        "description": "Consensus era obrigatório mas não foi atingido",
        "severity": "HIGH",
        "check": lambda r: r.consensus_required and not r.consensus_achieved
    },
    # Rule 3: HIGH divergence in HIGH governance
    "BD-003": {
        "name": "HIGH_DIVERGENCE",
        "description": "Divergência acima do threshold em decisão HIGH",
        "severity": "HIGH",
        "check": lambda r: (
            r.classification == "HIGH_GOVERNANCE" and
            r.divergence_score > 0.25
        )
    },
    # Rule 4: Single model for HIGH decision
    "BD-004": {
        "name": "SINGLE_MODEL_HIGH",
        "description": "Decisão HIGH com apenas 1 modelo (sem triangulação)",
        "severity": "CRITICAL",
        "check": lambda r: (
            r.classification == "HIGH_GOVERNANCE" and
            len(r.models_consulted) < 2
        )
    },
    # Rule 5: Action keywords in trivial classification
    "BD-005": {
        "name": "ACTION_IN_TRIVIAL",
        "description": "Keywords de acção em classificação trivial",
        "severity": "HIGH",
        "check": lambda r: (
            r.classification in ["LOW_TRIVIAL", "E1_TRIVIAL"] and
            any(kw in r.input_preview.lower() for kw in
                ["execute", "delete", "remove", "apagar", "eliminar", "löschen", "executar"])
        )
    },
    # Rule 6: Unusual latency (too fast for complexity)
    "BD-006": {
        "name": "SUSPICIOUS_LATENCY",
        "description": "Latência muito baixa para decisão HIGH (possível cache indevido)",
        "severity": "MEDIUM",
        "check": lambda r: (
            r.classification == "HIGH_GOVERNANCE" and
            r.latency_ms < 500  # Muito rápido para HIGH
        )
    },
}


def detect_backdoors(record: ClassificationRecord) -> List[Dict[str, Any]]:
    """Executa todas as regras de detecção de backdoor."""
    alerts = []
    for rule_id, rule in BACKDOOR_RULES.items():
        try:
            if rule["check"](record):
                alert = {
                    "rule_id": rule_id,
                    "name": rule["name"],
                    "severity": rule["severity"],
                    "description": rule["description"],
                    "request_hash": record.request_hash,
                    "input_preview": record.input_preview,
                    "classification": record.classification,
                }
                alerts.append(alert)
                log.warning(f"BACKDOOR DETECTED: {rule_id} | {rule['name']} | {record.request_hash[:8]}")
        except Exception as e:
            log.error(f"Error checking rule {rule_id}: {e}")
    return alerts


def save_backdoor_alert(alert: Dict[str, Any]):
    """Persiste alerta de backdoor na DB."""
    try:
        with shadow_db() as conn:
            conn.execute("""
                INSERT INTO backdoor_alerts (timestamp, alert_type, severity, description, request_hash, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(timezone.utc).isoformat(),
                alert["name"],
                alert["severity"],
                alert["description"],
                alert["request_hash"],
                json.dumps(alert)
            ))
    except Exception as e:
        log.error(f"Failed to save backdoor alert: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SHADOW AUDIT ENTRY POINT
#    "Invisível para o utilizador, visível para auditoria"
# ═══════════════════════════════════════════════════════════════════════════════

def shadow_audit(
    input_text: str,
    classification: str,
    classification_reason: str,
    routing_path: str,
    pillars_injected: int,
    history_used: int,
    consensus_required: bool,
    consensus_achieved: bool,
    models_consulted: List[str],
    divergence_score: float,
    latency_ms: int,
    officer_did: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Entry point para auditoria sombra.
    Chamado após cada request processado pela VERA.
    Retorna lista de alertas de backdoor detectados.
    """
    # Build record
    request_hash = hashlib.sha256(input_text[:200].encode()).hexdigest()[:16]

    record = ClassificationRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        request_hash=request_hash,
        input_preview=input_text[:100],
        classification=classification,
        classification_reason=classification_reason,
        routing_path=routing_path,
        pillars_injected=pillars_injected,
        history_used=history_used,
        consensus_required=consensus_required,
        consensus_achieved=consensus_achieved,
        models_consulted=models_consulted,
        divergence_score=divergence_score,
        latency_ms=latency_ms,
        officer_did=officer_did,
    )

    # Detect backdoors
    alerts = detect_backdoors(record)

    # Mark as suspicious if any alerts
    if alerts:
        record.suspicious = True
        record.suspicious_reason = ", ".join([a["rule_id"] for a in alerts])
        for alert in alerts:
            save_backdoor_alert(alert)

    # Log classification
    log_classification(record)

    return alerts


# ═══════════════════════════════════════════════════════════════════════════════
# 4. AUDIT REPORTS
#    "Visibilidade sobre comportamento real"
# ═══════════════════════════════════════════════════════════════════════════════

def get_classification_stats(hours: int = 24) -> Dict[str, Any]:
    """Estatísticas de classificação das últimas N horas."""
    try:
        with shadow_db() as conn:
            # Total counts by classification
            rows = conn.execute("""
                SELECT classification, COUNT(*) as count
                FROM classification_log
                WHERE timestamp > datetime('now', ?)
                GROUP BY classification
            """, (f'-{hours} hours',)).fetchall()

            by_class = {r["classification"]: r["count"] for r in rows}

            # Suspicious count
            suspicious = conn.execute("""
                SELECT COUNT(*) FROM classification_log
                WHERE suspicious = 1 AND timestamp > datetime('now', ?)
            """, (f'-{hours} hours',)).fetchone()[0]

            # Alert counts by severity
            alerts = conn.execute("""
                SELECT severity, COUNT(*) as count
                FROM backdoor_alerts
                WHERE timestamp > datetime('now', ?)
                GROUP BY severity
            """, (f'-{hours} hours',)).fetchall()

            alerts_by_severity = {r["severity"]: r["count"] for r in alerts}

            return {
                "period_hours": hours,
                "total_classifications": sum(by_class.values()),
                "by_classification": by_class,
                "suspicious_count": suspicious,
                "alerts_by_severity": alerts_by_severity,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        log.error(f"Error getting stats: {e}")
        return {"error": str(e)}


def get_recent_alerts(limit: int = 20) -> List[Dict[str, Any]]:
    """Últimos N alertas de backdoor."""
    try:
        with shadow_db() as conn:
            rows = conn.execute("""
                SELECT * FROM backdoor_alerts
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        log.error(f"Error getting alerts: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# 5. INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

# Auto-init on import
try:
    init_shadow_db()
except Exception as e:
    log.error(f"Failed to initialize shadow DB: {e}")
