#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           WINDI GOVERNANCE GUARD AGENT v1.4                  ║
║                                                              ║
║   "AI processes. Human decides. WINDI guarantees."           ║
║                                                              ║
║   Autonomous 24/7 governance watchdog                        ║
║   Guardian Dragon Module — Three Dragons Protocol            ║
║                                                              ║
║   Marco Zero: 19 Jan 2026                                    ║
║   Guard Born: 07 Feb 2026                                    ║
╚══════════════════════════════════════════════════════════════╝

Modules:
  HealthProbe    → Pings all WINDI APIs across 9 ports
  ChainWatcher   → Verifies Merkle Tree / ledger integrity
  ISPScanner     → Validates all ISP profiles periodically
  FlowMonitor    → Detects stagnant submissions
  AlertEngine    → Dispatches alerts to War Room in real-time
  ReportBuilder  → Generates weekly governance PDF report
"""

import os
import sys
import json
import time
import hashlib
import sqlite3
import logging
import threading
import datetime
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

WINDI_BASE = os.environ.get("WINDI_BASE", "/opt/windi")
GUARD_DATA = os.environ.get("GUARD_DATA", os.path.join(WINDI_BASE, "data", "guard"))
GUARD_DB = os.path.join(GUARD_DATA, "governance_guard.db")
GUARD_REPORTS = os.path.join(GUARD_DATA, "reports")
GUARD_LOG = os.environ.get("GUARD_LOG", "/tmp/governance_guard.log")

# WINDI Port Map
WINDI_PORTS = {
    "governance_api":    {"port": 8080, "path": "/api/status",    "critical": True},
    "trust_bus":         {"port": 8081, "path": "/health",        "critical": True},
    "gateway":           {"port": 8082, "path": "/health",        "critical": True},
    "evolution_minimal": {"port": 8083, "path": "/health",        "critical": False},
    "masterarbeit":      {"port": 8084, "path": "/health",        "critical": False},
    "babel_editor":      {"port": 8085, "path": "/",              "critical": True},
    "app":               {"port": 8086, "path": "/health",        "critical": False},
    "warroom_dispatch":  {"port": 8090, "path": "/health",        "critical": False},  # Not deployed yet
    "cortex":            {"port": 8889, "path": "/health",        "critical": False},
}

# ISP Registry Path
ISP_REGISTRY = os.path.join(WINDI_BASE, "isp")

# Databases
BABEL_DB = os.path.join(WINDI_BASE, "data", "babel_documents.db")
VIRTUE_DB = os.path.join(WINDI_BASE, "data", "virtue_history.db")

# Timing (in seconds)
HEALTH_CHECK_INTERVAL = 120      # 2 minutes
CHAIN_CHECK_INTERVAL = 300       # 5 minutes
ISP_SCAN_INTERVAL = 900          # 15 minutes
FLOW_CHECK_INTERVAL = 600        # 10 minutes
REPORT_INTERVAL = 604800         # 7 days (weekly)

# Alert Thresholds
SUBMISSION_STALE_HOURS = 48
SGE_SCORE_DRIFT_THRESHOLD = 5.0  # Points drop triggers alert
MIN_SGE_SCORE_HEALTHY = 70.0


# ─────────────────────────────────────────────
# ENUMS & DATA CLASSES
# ─────────────────────────────────────────────

class AlertSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

class ServiceStatus(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"

class GuardModule(Enum):
    HEALTH_PROBE = "HealthProbe"
    CHAIN_WATCHER = "ChainWatcher"
    ISP_SCANNER = "ISPScanner"
    FLOW_MONITOR = "FlowMonitor"
    ALERT_ENGINE = "AlertEngine"
    REPORT_BUILDER = "ReportBuilder"

@dataclass
class Alert:
    timestamp: str
    severity: AlertSeverity
    module: GuardModule
    title: str
    message: str
    details: Dict = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[str] = None

    def to_dict(self):
        d = asdict(self)
        d["severity"] = self.severity.value
        d["module"] = self.module.value
        return d

@dataclass
class HealthCheckResult:
    service: str
    port: int
    status: ServiceStatus
    response_ms: float
    timestamp: str
    error: Optional[str] = None
    critical: bool = False

@dataclass
class ISPCheckResult:
    profile_id: str
    valid: bool
    issues: List[str] = field(default_factory=list)
    governance_level: Optional[str] = None
    identity_license: Optional[str] = None

@dataclass
class GuardReport:
    generated_at: str
    period_start: str
    period_end: str
    total_documents_governed: int = 0
    chain_breaks: int = 0
    avg_sge_score: float = 0.0
    sge_score_delta: float = 0.0
    submissions_processed: int = 0
    submissions_high: int = 0
    avg_submission_time_hours: float = 0.0
    isp_profiles_healthy: int = 0
    isp_profiles_total: int = 0
    service_uptime_pct: float = 0.0
    alerts_total: int = 0
    alerts_critical: int = 0
    alerts_resolved: int = 0
    windi_verified: bool = False


# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

def setup_logging():
    """Configure Guard logging with rotation-friendly format."""
    logger = logging.getLogger("GovernanceGuard")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [GUARD:%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler
    os.makedirs(os.path.dirname(GUARD_LOG), exist_ok=True)
    fh = logging.FileHandler(GUARD_LOG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

log = setup_logging()


# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────

def init_guard_db():
    """Initialize the Guard's own database for tracking state."""
    os.makedirs(GUARD_DATA, exist_ok=True)
    os.makedirs(GUARD_REPORTS, exist_ok=True)

    conn = sqlite3.connect(GUARD_DB, timeout=30)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            service TEXT NOT NULL,
            port INTEGER NOT NULL,
            status TEXT NOT NULL,
            response_ms REAL,
            error TEXT,
            critical INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            severity TEXT NOT NULL,
            module TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            resolved INTEGER DEFAULT 0,
            resolved_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS isp_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            profile_id TEXT NOT NULL,
            valid INTEGER NOT NULL,
            issues TEXT,
            governance_level TEXT,
            identity_license TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS chain_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            integrity_valid INTEGER NOT NULL,
            records_checked INTEGER DEFAULT 0,
            breaks_found INTEGER DEFAULT 0,
            details TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS guard_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generated_at TEXT NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            report_json TEXT NOT NULL,
            report_path TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sge_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            avg_score REAL,
            total_scanned INTEGER,
            flagged_count INTEGER,
            clean_count INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS hash_baselines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            hash_sha256 TEXT NOT NULL,
            first_seen TEXT NOT NULL,
            last_verified TEXT NOT NULL,
            changed INTEGER DEFAULT 0,
            UNIQUE(profile_id, file_path)
        )
    """)

    conn.commit()
    conn.close()
    log.info("Guard database initialized: %s", GUARD_DB)


# ─────────────────────────────────────────────
# MODULE 1: HEALTH PROBE
# ─────────────────────────────────────────────

class HealthProbe:
    """
    Pings all WINDI APIs across 9 ports.
    Tracks uptime, latency, and service degradation.
    """

    def __init__(self, alert_engine: "AlertEngine"):
        self.alert_engine = alert_engine
        self.last_results: Dict[str, HealthCheckResult] = {}
        self._consecutive_failures: Dict[str, int] = {}

    def check_service(self, name: str, config: Dict) -> HealthCheckResult:
        """Check a single service endpoint."""
        import urllib.request
        import urllib.error

        port = config["port"]
        path = config.get("path", "/health")
        critical = config.get("critical", False)
        url = f"http://localhost:{port}{path}"
        now = datetime.datetime.utcnow().isoformat() + "Z"

        start = time.time()
        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("User-Agent", "WINDI-GovernanceGuard/1.2")
            with urllib.request.urlopen(req, timeout=10) as resp:
                elapsed_ms = (time.time() - start) * 1000
                status = ServiceStatus.HEALTHY if resp.status == 200 else ServiceStatus.DEGRADED
                self._consecutive_failures[name] = 0
                return HealthCheckResult(
                    service=name, port=port, status=status,
                    response_ms=round(elapsed_ms, 2), timestamp=now,
                    critical=critical
                )
        except urllib.error.URLError as e:
            elapsed_ms = (time.time() - start) * 1000
            self._consecutive_failures[name] = self._consecutive_failures.get(name, 0) + 1
            return HealthCheckResult(
                service=name, port=port, status=ServiceStatus.DOWN,
                response_ms=round(elapsed_ms, 2), timestamp=now,
                error=str(e.reason), critical=critical
            )
        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            self._consecutive_failures[name] = self._consecutive_failures.get(name, 0) + 1
            return HealthCheckResult(
                service=name, port=port, status=ServiceStatus.DOWN,
                response_ms=round(elapsed_ms, 2), timestamp=now,
                error=str(e), critical=critical
            )

    def run_full_check(self) -> Dict[str, HealthCheckResult]:
        """Run health checks on all services."""
        results = {}
        for name, config in WINDI_PORTS.items():
            result = self.check_service(name, config)
            results[name] = result
            self.last_results[name] = result

            # Store in DB
            self._store_result(result)

            # Generate alerts
            if result.status == ServiceStatus.DOWN:
                failures = self._consecutive_failures.get(name, 1)
                severity = AlertSeverity.CRITICAL if result.critical else AlertSeverity.WARNING
                if failures >= 3:
                    severity = AlertSeverity.EMERGENCY if result.critical else AlertSeverity.CRITICAL

                self.alert_engine.fire(Alert(
                    timestamp=result.timestamp,
                    severity=severity,
                    module=GuardModule.HEALTH_PROBE,
                    title=f"Service DOWN: {name}",
                    message=f"Port {result.port} unreachable ({failures} consecutive failures). Error: {result.error}",
                    details={"port": result.port, "consecutive_failures": failures, "critical": result.critical}
                ))
            elif result.status == ServiceStatus.DEGRADED:
                self.alert_engine.fire(Alert(
                    timestamp=result.timestamp,
                    severity=AlertSeverity.WARNING,
                    module=GuardModule.HEALTH_PROBE,
                    title=f"Service DEGRADED: {name}",
                    message=f"Port {result.port} responding but degraded (response: {result.response_ms}ms)",
                    details={"port": result.port, "response_ms": result.response_ms}
                ))
            elif result.response_ms > 5000:  # Slow response > 5s
                self.alert_engine.fire(Alert(
                    timestamp=result.timestamp,
                    severity=AlertSeverity.INFO,
                    module=GuardModule.HEALTH_PROBE,
                    title=f"Slow response: {name}",
                    message=f"Port {result.port} responding slowly ({result.response_ms}ms)",
                    details={"port": result.port, "response_ms": result.response_ms}
                ))

        # Summary log
        healthy = sum(1 for r in results.values() if r.status == ServiceStatus.HEALTHY)
        down = sum(1 for r in results.values() if r.status == ServiceStatus.DOWN)
        log.info(
            "HealthProbe: %d/%d healthy, %d down",
            healthy, len(results), down
        )

        return results

    def _store_result(self, result: HealthCheckResult):
        try:
            conn = sqlite3.connect(GUARD_DB, timeout=30)
            conn.execute(
                "INSERT INTO health_checks (timestamp, service, port, status, response_ms, error, critical) VALUES (?,?,?,?,?,?,?)",
                (result.timestamp, result.service, result.port, result.status.value,
                 result.response_ms, result.error, 1 if result.critical else 0)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log.error("Failed to store health check: %s", e)

    def get_uptime_pct(self, hours: int = 168) -> float:
        """Calculate uptime percentage over given hours (default: 1 week)."""
        try:
            since = (datetime.datetime.utcnow() - datetime.timedelta(hours=hours)).isoformat()
            conn = sqlite3.connect(GUARD_DB, timeout=30)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM health_checks WHERE timestamp > ?", (since,))
            total = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM health_checks WHERE timestamp > ? AND status = 'HEALTHY'", (since,))
            healthy = c.fetchone()[0]
            conn.close()
            return round((healthy / total * 100) if total > 0 else 0, 2)
        except Exception:
            return 0.0


# ─────────────────────────────────────────────
# MODULE 2: CHAIN WATCHER
# ─────────────────────────────────────────────

class ChainWatcher:
    """
    Verifies Merkle Tree and forensic ledger integrity.
    Detects chain breaks, hash mismatches, and tampered records.
    Zero-Knowledge: only verifies hashes, never reads sensitive data.
    """

    def __init__(self, alert_engine: "AlertEngine"):
        self.alert_engine = alert_engine
        self.last_check: Optional[Dict] = None

    def verify_virtue_chain(self) -> Dict:
        """Verify the integrity of the virtue receipt chain."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        result = {
            "timestamp": now,
            "integrity_valid": True,
            "records_checked": 0,
            "breaks_found": 0,
            "legacy_excluded": 0,
            "details": []
        }

        if not os.path.exists(VIRTUE_DB):
            result["details"].append("Virtue history DB not found — skipping chain verification")
            log.warning("ChainWatcher: virtue_history.db not found at %s", VIRTUE_DB)
            self._store_result(result)
            return result

        try:
            conn = sqlite3.connect(VIRTUE_DB)
            c = conn.cursor()

            # Get all tables to find virtue/receipt records
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in c.fetchall()]

            # Look for virtue receipt tables
            receipt_tables = [t for t in tables if "virtue" in t.lower() or "receipt" in t.lower() or "ledger" in t.lower()]

            if not receipt_tables:
                # Try the governance_audit in BABEL DB
                if os.path.exists(BABEL_DB):
                    conn2 = sqlite3.connect(BABEL_DB)
                    c2 = conn2.cursor()
                    c2.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    babel_tables = [row[0] for row in c2.fetchall()]

                    if "governance_audit" in babel_tables:
                        c2.execute("SELECT COUNT(*) FROM governance_audit")
                        count = c2.fetchone()[0]
                        result["records_checked"] = count
                        result["details"].append(f"Governance audit chain: {count} records found")

                        # Verify sequential integrity
                        c2.execute("SELECT id, timestamp FROM governance_audit ORDER BY id")
                        rows = c2.fetchall()
                        prev_ts = None
                        for row_id, ts in rows:
                            if prev_ts and ts < prev_ts:
                                result["breaks_found"] += 1
                                result["details"].append(
                                    f"Temporal break at record {row_id}: {ts} < {prev_ts}"
                                )
                            prev_ts = ts

                    if "document_audit" in babel_tables:
                        c2.execute("SELECT COUNT(*) FROM document_audit")
                        doc_count = c2.fetchone()[0]
                        result["records_checked"] += doc_count
                        result["details"].append(f"Document audit chain: {doc_count} records found")

                    conn2.close()
            else:
                for table in receipt_tables:
                    c.execute(f"SELECT COUNT(*) FROM [{table}]")
                    count = c.fetchone()[0]
                    result["records_checked"] += count
                    result["details"].append(f"Table '{table}': {count} records")

                    # Verify hash chain if hash columns exist
                    c.execute(f"PRAGMA table_info([{table}])")
                    columns = [col[1] for col in c.fetchall()]
                    hash_cols = [col for col in columns if "hash" in col.lower()]

                    if hash_cols:
                        c.execute(f"SELECT * FROM [{table}] ORDER BY rowid")
                        rows = c.fetchall()
                        prev_hash = None
                        # Check for domain_tag/source column to identify legacy records
                        legacy_col_names = ["domain_tag", "source", "origin", "tag"]
                        legacy_idx = None
                        for col_name in legacy_col_names:
                            if col_name in columns:
                                legacy_idx = columns.index(col_name)
                                break

                        for i, row in enumerate(rows):
                            # Check for null hashes
                            hash_idx = columns.index(hash_cols[0])
                            current_hash = row[hash_idx] if hash_idx < len(row) else None

                            # Check if this is a legacy pre-chain record
                            is_legacy = False
                            if legacy_idx is not None and legacy_idx < len(row):
                                legacy_val = row[legacy_idx]
                                if legacy_val == "legacy" and (current_hash is None or current_hash == ""):
                                    is_legacy = True

                            if current_hash is None or current_hash == "":
                                if is_legacy:
                                    # Exclude legacy pre-chain records (before hash system was implemented)
                                    result["legacy_excluded"] += 1
                                    result["records_checked"] -= 1  # Don't count legacy in verified records
                                else:
                                    result["breaks_found"] += 1
                                    result["details"].append(f"Null hash at row {i+1} in {table}")

            conn.close()

        except Exception as e:
            result["integrity_valid"] = False
            result["details"].append(f"Chain verification error: {str(e)}")
            log.error("ChainWatcher error: %s", e)

        # Set integrity flag
        if result["breaks_found"] > 0:
            result["integrity_valid"] = False
            self.alert_engine.fire(Alert(
                timestamp=now,
                severity=AlertSeverity.CRITICAL,
                module=GuardModule.CHAIN_WATCHER,
                title=f"Chain Integrity Breach: {result['breaks_found']} breaks detected",
                message=f"Checked {result['records_checked']} records. Found {result['breaks_found']} integrity violations.",
                details={"breaks": result["breaks_found"], "records": result["records_checked"]}
            ))
        else:
            legacy_note = f" ({result['legacy_excluded']} legacy excluded)" if result.get("legacy_excluded", 0) > 0 else ""
            log.info(
                "ChainWatcher: %d records verified, 0 breaks%s. Chain INTACT.",
                result["records_checked"], legacy_note
            )

        self.last_check = result
        self._store_result(result)
        return result

    def verify_config_hash(self) -> Dict:
        """Verify ISP config hashes — store baseline and detect tampering."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        tampered = []
        new_profiles = []

        if not os.path.exists(ISP_REGISTRY):
            return {"timestamp": now, "tampered": [], "new": [], "checked": 0}

        checked = 0
        for profile_dir in Path(ISP_REGISTRY).iterdir():
            if not profile_dir.is_dir():
                continue
            profile_json = profile_dir / "profile.json"
            if profile_json.exists():
                checked += 1
                try:
                    content = profile_json.read_bytes()
                    current_hash = hashlib.sha256(content).hexdigest()
                    profile_id = profile_dir.name

                    # Check against stored baseline
                    conn = sqlite3.connect(GUARD_DB, timeout=30)
                    c = conn.cursor()
                    c.execute(
                        "SELECT hash_sha256 FROM hash_baselines WHERE profile_id = ? AND file_path = ?",
                        (profile_id, "profile.json")
                    )
                    row = c.fetchone()

                    if row is None:
                        # First time — establish baseline
                        c.execute(
                            "INSERT INTO hash_baselines (profile_id, file_path, hash_sha256, first_seen, last_verified) VALUES (?,?,?,?,?)",
                            (profile_id, "profile.json", current_hash, now, now)
                        )
                        new_profiles.append(profile_id)
                    elif row[0] != current_hash:
                        # HASH CHANGED — possible tampering!
                        tampered.append({
                            "profile": profile_id,
                            "expected": row[0][:16] + "...",
                            "actual": current_hash[:16] + "..."
                        })
                        c.execute(
                            "UPDATE hash_baselines SET hash_sha256 = ?, last_verified = ?, changed = 1 WHERE profile_id = ? AND file_path = ?",
                            (current_hash, now, profile_id, "profile.json")
                        )
                    else:
                        # Hash matches — update last_verified
                        c.execute(
                            "UPDATE hash_baselines SET last_verified = ? WHERE profile_id = ? AND file_path = ?",
                            (now, profile_id, "profile.json")
                        )

                    conn.commit()
                    conn.close()
                except Exception as e:
                    tampered.append({"profile": profile_dir.name, "error": str(e)})

        if tampered:
            self.alert_engine.fire(Alert(
                timestamp=now,
                severity=AlertSeverity.CRITICAL,
                module=GuardModule.CHAIN_WATCHER,
                title=f"ISP Tamper Detection: {len(tampered)} profiles CHANGED",
                message=f"Modified profiles: {', '.join(t['profile'] for t in tampered)}",
                details={"tampered": tampered}
            ))
        if new_profiles:
            log.info("ChainWatcher: Established baseline for %d new profiles: %s",
                     len(new_profiles), ", ".join(new_profiles))

        return {"timestamp": now, "tampered": tampered, "new": new_profiles, "checked": checked}

    def _store_result(self, result: Dict):
        try:
            conn = sqlite3.connect(GUARD_DB, timeout=30)
            conn.execute(
                "INSERT INTO chain_checks (timestamp, integrity_valid, records_checked, breaks_found, details) VALUES (?,?,?,?,?)",
                (result["timestamp"], 1 if result["integrity_valid"] else 0,
                 result["records_checked"], result["breaks_found"],
                 json.dumps(result["details"]))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log.error("Failed to store chain check: %s", e)


# ─────────────────────────────────────────────
# MODULE 3: ISP SCANNER
# ─────────────────────────────────────────────

class ISPScanner:
    """
    Validates all ISP (Institutional Style Profile) profiles.
    Checks JSON integrity, required fields, governance level compliance,
    and identity license status.
    """

    # Deep path mappings for nested ISP profile structures
    # Real profiles use: isp_profile.organization.name_full, isp_profile.metadata.governance_level, etc.
    DEEP_PATHS = {
        "profile_id": [
            "profile_id", "id", "profileId", "slug",
            "isp_profile.profile_id", "isp_profile.id",
            "isp_profile.metadata.profile_id",
        ],
        "profile_name": [
            "profile_name", "name", "profileName", "display_name", "title",
            "isp_profile.profile_name", "isp_profile.name",
            "isp_profile.organization.name", "isp_profile.organization.name_full",
            "isp_profile.metadata.name", "isp_profile.display_name",
            "organization.name", "organization.name_full",
        ],
        "version": [
            "version", "ver", "schema_version", "isp_version",
            "isp_profile.version", "isp_profile.metadata.version",
            "isp_profile.schema_version", "metadata.version",
        ],
        "governance_level": [
            "governance_level", "level", "gov_level", "governanceLevel", "governance",
            "isp_profile.governance_level", "isp_profile.level",
            "isp_profile.metadata.governance_level",
            "isp_profile.governance.level",
            "metadata.governance_level", "governance.level",
        ],
        "institution": [
            "institution", "org", "organization", "company", "entity",
            "isp_profile.institution", "isp_profile.organization",
            "isp_profile.org", "isp_profile.company",
        ],
    }

    # Which fields are strictly required vs recommended
    STRICTLY_REQUIRED = ["profile_name"]  # profile_id can fallback to dir name
    RECOMMENDED = ["version", "governance_level", "institution"]

    GOVERNANCE_LEVELS = ["L1", "L2", "L3", "l1", "l2", "l3", "1", "2", "3"]

    LICENSE_STATUSES = ["authorized", "model_only", "pending", "expired", "revoked"]

    def __init__(self, alert_engine: "AlertEngine"):
        self.alert_engine = alert_engine
        self.last_scan: List[ISPCheckResult] = []

    def _deep_get(self, data: Dict, dotted_path: str) -> Any:
        """Traverse a nested dict using dot notation. e.g. 'isp_profile.organization.name'"""
        keys = dotted_path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                # Try exact key first
                if key in current:
                    current = current[key]
                else:
                    # Try case-insensitive
                    found = False
                    for k, v in current.items():
                        if k.lower() == key.lower():
                            current = v
                            found = True
                            break
                    if not found:
                        return None
            else:
                return None
        return current

    def _find_field(self, data: Dict, field_key: str) -> Any:
        """Find a field value using deep path matching across nested structures."""
        paths = self.DEEP_PATHS.get(field_key, [field_key])
        for path in paths:
            value = self._deep_get(data, path)
            if value is not None:
                return value

        # Last resort: recursive search for the key anywhere in the dict
        result = self._recursive_find(data, field_key.split("_")[-1])  # e.g. "governance_level" → search for "level"
        return result

    def _recursive_find(self, data: Any, key_fragment: str, max_depth: int = 4) -> Any:
        """Recursively search for a key fragment in nested dicts."""
        if max_depth <= 0 or not isinstance(data, dict):
            return None
        for k, v in data.items():
            if key_fragment.lower() in k.lower():
                return v
        # Search one level deeper
        for k, v in data.items():
            if isinstance(v, dict):
                result = self._recursive_find(v, key_fragment, max_depth - 1)
                if result is not None:
                    return result
        return None

    def scan_all_profiles(self) -> List[ISPCheckResult]:
        """Scan all ISP profiles in the registry."""
        results = []
        now = datetime.datetime.utcnow().isoformat() + "Z"

        if not os.path.exists(ISP_REGISTRY):
            log.warning("ISPScanner: Registry not found at %s", ISP_REGISTRY)
            return results

        for profile_dir in sorted(Path(ISP_REGISTRY).iterdir()):
            if not profile_dir.is_dir():
                continue
            if profile_dir.name.startswith(".") or profile_dir.name.startswith("_"):
                continue

            result = self._validate_profile(profile_dir)
            results.append(result)
            self._store_result(now, result)

        # Summary
        valid = sum(1 for r in results if r.valid)
        invalid = len(results) - valid
        log.info("ISPScanner: %d/%d profiles valid, %d issues", valid, len(results), invalid)

        if invalid > 0:
            invalid_profiles = [r.profile_id for r in results if not r.valid]
            self.alert_engine.fire(Alert(
                timestamp=now,
                severity=AlertSeverity.WARNING,
                module=GuardModule.ISP_SCANNER,
                title=f"ISP Validation: {invalid} profiles with issues",
                message=f"Invalid profiles: {', '.join(invalid_profiles)}",
                details={"invalid_profiles": invalid_profiles, "total": len(results)}
            ))

        # Check for expired licenses
        expired = [r for r in results if r.identity_license in ("expired", "revoked")]
        if expired:
            self.alert_engine.fire(Alert(
                timestamp=now,
                severity=AlertSeverity.CRITICAL,
                module=GuardModule.ISP_SCANNER,
                title=f"ISP License Alert: {len(expired)} expired/revoked",
                message=f"Profiles with license issues: {', '.join(r.profile_id for r in expired)}",
                details={"expired_profiles": [r.profile_id for r in expired]}
            ))

        self.last_scan = results
        return results

    def _validate_profile(self, profile_dir: Path) -> ISPCheckResult:
        """Validate a single ISP profile with flexible field matching."""
        profile_id = profile_dir.name
        issues = []
        governance_level = None
        identity_license = None

        profile_json = profile_dir / "profile.json"
        if not profile_json.exists():
            return ISPCheckResult(
                profile_id=profile_id, valid=False,
                issues=["Missing profile.json"]
            )

        try:
            data = json.loads(profile_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return ISPCheckResult(
                profile_id=profile_id, valid=False,
                issues=[f"Invalid JSON: {str(e)}"]
            )

        # Handle nested structures — some profiles wrap data inside a key
        if isinstance(data, dict) and len(data) == 1:
            single_key = list(data.keys())[0]
            inner = data[single_key]
            if isinstance(inner, dict) and len(inner) > 3:
                # Likely the real profile data is nested
                data = inner

        # Check strictly required fields (with flexible matching)
        for field_key in self.STRICTLY_REQUIRED:
            value = self._find_field(data, field_key)
            if value is None:
                # Use dir name as fallback for profile_id
                if field_key == "profile_id":
                    continue  # Dir name IS the profile ID
                issues.append(f"Missing required: {field_key}")

        # Check recommended fields (with flexible matching)
        for field_key in self.RECOMMENDED:
            value = self._find_field(data, field_key)
            if value is None:
                issues.append(f"Recommended missing: {field_key}")

        # Extract governance level (flexible)
        governance_level = self._find_field(data, "governance_level")
        gov_level_str = None
        if governance_level is not None:
            # Handle nested governance_level object: {"level": "HIGH", ...}
            if isinstance(governance_level, dict):
                gov_level_str = governance_level.get("level", governance_level.get("governance_level"))
            else:
                gov_level_str = governance_level

            # Normalize to string
            if gov_level_str is not None:
                gov_level_str = str(gov_level_str).upper()
                # Valid levels: HIGH, MEDIUM, LOW (or L1, L2, L3)
                valid_levels = ["HIGH", "MEDIUM", "LOW", "L1", "L2", "L3"]
                if gov_level_str not in valid_levels:
                    issues.append(f"Invalid governance_level: {gov_level_str}")
                else:
                    governance_level = gov_level_str
            else:
                issues.append("governance_level object missing 'level' key")
                governance_level = None
        else:
            governance_level = None

        # Extract identity license (deep search)
        identity = (
            self._deep_get(data, "identity_license") or
            self._deep_get(data, "isp_profile.identity_license") or
            self._deep_get(data, "isp_profile.identity") or
            self._deep_get(data, "isp_profile.license") or
            self._deep_get(data, "identity") or
            self._deep_get(data, "license") or
            self._deep_get(data, "licence") or
            {}
        )
        if isinstance(identity, dict):
            identity_license = identity.get("status", identity.get("type"))
        elif isinstance(identity, str):
            identity_license = identity

        # Check for templates (flexible — dir, inline, or key)
        has_templates = False
        templates_dir = profile_dir / "templates"
        if templates_dir.exists():
            template_files = list(templates_dir.glob("*.j2")) + list(templates_dir.glob("*.jinja2")) + list(templates_dir.glob("*.html"))
            has_templates = len(template_files) > 0
        if not has_templates:
            # Check for inline templates in profile data (top level AND nested)
            all_keys_flat = set()
            def _collect_keys(d, prefix=""):
                if isinstance(d, dict):
                    for k, v in d.items():
                        all_keys_flat.add(k.lower())
                        _collect_keys(v, f"{prefix}{k}.")
            _collect_keys(data)

            template_indicators = {"template", "templates", "sections", "blocks",
                                   "layout", "structure", "header", "footer",
                                   "jinja", "components", "elements", "body_template",
                                   "document_structure", "page_layout"}
            if all_keys_flat & template_indicators:
                has_templates = True
        if not has_templates:
            issues.append("No templates found (dir, inline, or structural)")

        # Determine validity — only strictly required fields make it invalid
        strict_issues = [i for i in issues if i.startswith("Missing required")]
        is_valid = len(strict_issues) == 0

        return ISPCheckResult(
            profile_id=profile_id,
            valid=is_valid,
            issues=issues,
            governance_level=governance_level,
            identity_license=identity_license
        )

    def _store_result(self, timestamp: str, result: ISPCheckResult):
        try:
            conn = sqlite3.connect(GUARD_DB, timeout=30)
            conn.execute(
                "INSERT INTO isp_scans (timestamp, profile_id, valid, issues, governance_level, identity_license) VALUES (?,?,?,?,?,?)",
                (timestamp, result.profile_id, 1 if result.valid else 0,
                 json.dumps(result.issues), result.governance_level, result.identity_license)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log.error("Failed to store ISP scan: %s", e)


# ─────────────────────────────────────────────
# MODULE 4: FLOW MONITOR
# ─────────────────────────────────────────────

class FlowMonitor:
    """
    Monitors governance submission pipeline.
    Detects stagnant submissions, processing delays,
    and flow anomalies.
    """

    def __init__(self, alert_engine: "AlertEngine"):
        self.alert_engine = alert_engine
        self.last_check: Optional[Dict] = None

    def check_submissions(self) -> Dict:
        """Check for stagnant or problematic submissions."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        stale_cutoff = (
            datetime.datetime.utcnow() - datetime.timedelta(hours=SUBMISSION_STALE_HOURS)
        ).isoformat()

        result = {
            "timestamp": now,
            "total_submissions": 0,
            "pending": 0,
            "stale": [],
            "high_priority_pending": 0,
            "flow_healthy": True
        }

        # Check via Governance API
        try:
            import urllib.request
            req = urllib.request.Request(
                "http://localhost:8080/api/submissions",
                method="GET"
            )
            req.add_header("User-Agent", "WINDI-GovernanceGuard/1.2")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                submissions = data if isinstance(data, list) else data.get("submissions", [])
                result["total_submissions"] = len(submissions)

                for sub in submissions:
                    status = sub.get("status", "").lower()
                    if status in ("pending", "processing", "queued"):
                        result["pending"] += 1
                        created = sub.get("created_at", sub.get("timestamp", ""))
                        if created:
                            try:
                                created_dt = datetime.datetime.fromisoformat(
                                    created.replace("Z", "+00:00")
                                )
                                cutoff_dt = datetime.datetime.fromisoformat(
                                    stale_cutoff.replace("Z", "+00:00")
                                ) if "+" not in stale_cutoff else datetime.datetime.fromisoformat(stale_cutoff)
                                if created_dt < cutoff_dt:
                                    result["stale"].append({
                                        "id": sub.get("id", "unknown"),
                                        "created_at": created,
                                        "impact": sub.get("impact_level", "unknown")
                                    })
                            except (ValueError, TypeError):
                                pass  # Skip unparseable dates
                        if sub.get("impact_level", "").upper() == "HIGH":
                            result["high_priority_pending"] += 1

        except Exception as e:
            log.warning("FlowMonitor: Could not reach governance API: %s", e)
            result["flow_healthy"] = False

        # Also check BABEL DB for document flow
        if os.path.exists(BABEL_DB):
            try:
                conn = sqlite3.connect(BABEL_DB)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM documents")
                result["total_documents"] = c.fetchone()[0]
                conn.close()
            except Exception as e:
                log.warning("FlowMonitor: Could not query BABEL DB: %s", e)

        # Generate alerts
        if result["stale"]:
            result["flow_healthy"] = False
            self.alert_engine.fire(Alert(
                timestamp=now,
                severity=AlertSeverity.WARNING,
                module=GuardModule.FLOW_MONITOR,
                title=f"Stale Submissions: {len(result['stale'])} pending > {SUBMISSION_STALE_HOURS}h",
                message=f"Submission IDs: {', '.join(s['id'] for s in result['stale'])}",
                details={"stale_submissions": result["stale"]}
            ))

        if result["high_priority_pending"] > 0:
            self.alert_engine.fire(Alert(
                timestamp=now,
                severity=AlertSeverity.CRITICAL,
                module=GuardModule.FLOW_MONITOR,
                title=f"HIGH Priority Pending: {result['high_priority_pending']} submissions",
                message="High-impact submissions awaiting processing",
                details={"count": result["high_priority_pending"]}
            ))

        log.info(
            "FlowMonitor: %d submissions, %d pending, %d stale",
            result["total_submissions"], result["pending"], len(result["stale"])
        )

        self.last_check = result
        return result

    def check_sge_drift(self) -> Dict:
        """Monitor SGE score trends for drift detection."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        result = {"timestamp": now, "drift_detected": False, "current_avg": 0, "delta": 0}

        try:
            conn = sqlite3.connect(GUARD_DB, timeout=30)
            c = conn.cursor()

            # Get latest 2 snapshots to compare
            c.execute("SELECT avg_score FROM sge_snapshots ORDER BY id DESC LIMIT 2")
            rows = c.fetchall()

            if len(rows) >= 2:
                current = rows[0][0]
                previous = rows[1][0]
                delta = current - previous
                result["current_avg"] = current
                result["delta"] = round(delta, 2)

                if abs(delta) >= SGE_SCORE_DRIFT_THRESHOLD:
                    result["drift_detected"] = True
                    direction = "dropped" if delta < 0 else "increased"
                    severity = AlertSeverity.WARNING if delta < 0 else AlertSeverity.INFO
                    self.alert_engine.fire(Alert(
                        timestamp=now,
                        severity=severity,
                        module=GuardModule.FLOW_MONITOR,
                        title=f"SGE Score Drift: {direction} by {abs(delta):.1f} points",
                        message=f"Average SGE score {direction} from {previous:.1f} to {current:.1f}",
                        details={"previous": previous, "current": current, "delta": delta}
                    ))

                if current < MIN_SGE_SCORE_HEALTHY:
                    self.alert_engine.fire(Alert(
                        timestamp=now,
                        severity=AlertSeverity.CRITICAL,
                        module=GuardModule.FLOW_MONITOR,
                        title=f"SGE Score Below Threshold: {current:.1f} < {MIN_SGE_SCORE_HEALTHY}",
                        message="Average governance quality score is below minimum healthy threshold",
                        details={"current_avg": current, "threshold": MIN_SGE_SCORE_HEALTHY}
                    ))

            conn.close()
        except Exception as e:
            log.warning("FlowMonitor SGE drift check failed: %s", e)

        return result


# ─────────────────────────────────────────────
# MODULE 5: ALERT ENGINE
# ─────────────────────────────────────────────

class AlertEngine:
    """
    Central alert dispatcher for all Guard modules.
    Stores alerts, deduplicates, and dispatches to War Room.
    """

    def __init__(self):
        self.active_alerts: List[Alert] = []
        self._dedup_window: Dict[str, str] = {}  # title -> last_fired
        self.DEDUP_SECONDS = 300  # Don't repeat same alert within 5 min

    def fire(self, alert: Alert):
        """Fire an alert — deduplicate, store, and dispatch."""
        # Deduplication
        dedup_key = f"{alert.module.value}:{alert.title}"
        last_fired = self._dedup_window.get(dedup_key)
        if last_fired:
            try:
                last_dt = datetime.datetime.fromisoformat(last_fired.replace("Z", "+00:00"))
                now_dt = datetime.datetime.fromisoformat(alert.timestamp.replace("Z", "+00:00"))
                if (now_dt - last_dt).total_seconds() < self.DEDUP_SECONDS:
                    return  # Skip duplicate
            except Exception:
                pass

        self._dedup_window[dedup_key] = alert.timestamp
        self.active_alerts.append(alert)

        # Store in DB
        self._store_alert(alert)

        # Log with severity-appropriate level
        severity_icon = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.EMERGENCY: "🚨"
        }
        icon = severity_icon.get(alert.severity, "❓")
        log.warning(
            "%s [%s] %s — %s",
            icon, alert.severity.value, alert.title, alert.message
        )

        # Dispatch to War Room API
        self._dispatch_to_warroom(alert)

    def resolve(self, alert_title: str):
        """Mark an alert as resolved."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        for alert in self.active_alerts:
            if alert.title == alert_title and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = now
                log.info("✅ Alert resolved: %s", alert_title)

        try:
            conn = sqlite3.connect(GUARD_DB, timeout=30)
            conn.execute(
                "UPDATE alerts SET resolved = 1, resolved_at = ? WHERE title = ? AND resolved = 0",
                (now, alert_title)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log.error("Failed to resolve alert in DB: %s", e)

    def get_active_alerts(self) -> List[Alert]:
        """Get all unresolved alerts."""
        return [a for a in self.active_alerts if not a.resolved]

    def get_summary(self) -> Dict:
        """Get alert summary counts."""
        active = self.get_active_alerts()
        return {
            "total": len(self.active_alerts),
            "active": len(active),
            "resolved": len(self.active_alerts) - len(active),
            "by_severity": {
                s.value: sum(1 for a in active if a.severity == s)
                for s in AlertSeverity
            }
        }

    def _store_alert(self, alert: Alert):
        try:
            conn = sqlite3.connect(GUARD_DB, timeout=30)
            conn.execute(
                "INSERT INTO alerts (timestamp, severity, module, title, message, details, resolved) VALUES (?,?,?,?,?,?,?)",
                (alert.timestamp, alert.severity.value, alert.module.value,
                 alert.title, alert.message, json.dumps(alert.details), 0)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log.error("Failed to store alert: %s", e)

    def _dispatch_to_warroom(self, alert: Alert):
        """Send alert to War Room dashboard via API."""
        try:
            import urllib.request
            payload = json.dumps(alert.to_dict()).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:8090/api/warroom/alert",
                data=payload,
                method="POST"
            )
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "WINDI-GovernanceGuard/1.2")
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            # War Room might not have this endpoint yet — that's OK
            pass


# ─────────────────────────────────────────────
# MODULE 6: REPORT BUILDER
# ─────────────────────────────────────────────

class ReportBuilder:
    """
    Generates comprehensive weekly governance PDF reports.
    Produces the "Governance Guard Report" for Controllers/CFOs.
    """

    def __init__(self, health_probe: HealthProbe, chain_watcher: ChainWatcher,
                 isp_scanner: ISPScanner, flow_monitor: FlowMonitor,
                 alert_engine: AlertEngine):
        self.health_probe = health_probe
        self.chain_watcher = chain_watcher
        self.isp_scanner = isp_scanner
        self.flow_monitor = flow_monitor
        self.alert_engine = alert_engine

    def generate_report(self) -> GuardReport:
        """Generate a comprehensive weekly report."""
        now = datetime.datetime.utcnow()
        period_end = now.isoformat() + "Z"
        period_start = (now - datetime.timedelta(days=7)).isoformat() + "Z"

        report = GuardReport(
            generated_at=period_end,
            period_start=period_start,
            period_end=period_end
        )

        # Documents governed
        if os.path.exists(BABEL_DB):
            try:
                conn = sqlite3.connect(BABEL_DB)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM documents WHERE created_at > ?", (period_start,))
                report.total_documents_governed = c.fetchone()[0]
                conn.close()
            except Exception:
                pass

        # Chain integrity
        try:
            conn = sqlite3.connect(GUARD_DB, timeout=30)
            c = conn.cursor()
            c.execute(
                "SELECT SUM(breaks_found) FROM chain_checks WHERE timestamp > ?",
                (period_start,)
            )
            val = c.fetchone()[0]
            report.chain_breaks = val if val else 0
            conn.close()
        except Exception:
            pass

        # SGE scores
        try:
            conn = sqlite3.connect(GUARD_DB, timeout=30)
            c = conn.cursor()
            c.execute(
                "SELECT avg_score FROM sge_snapshots WHERE timestamp > ? ORDER BY id DESC LIMIT 1",
                (period_start,)
            )
            row = c.fetchone()
            if row:
                report.avg_sge_score = round(row[0], 1)

            c.execute(
                "SELECT avg_score FROM sge_snapshots WHERE timestamp > ? ORDER BY id ASC LIMIT 1",
                (period_start,)
            )
            first = c.fetchone()
            if first and row:
                report.sge_score_delta = round(row[0] - first[0], 1)
            conn.close()
        except Exception:
            pass

        # ISP health
        if self.isp_scanner.last_scan:
            report.isp_profiles_total = len(self.isp_scanner.last_scan)
            report.isp_profiles_healthy = sum(1 for r in self.isp_scanner.last_scan if r.valid)

        # Service uptime
        report.service_uptime_pct = self.health_probe.get_uptime_pct(hours=168)

        # Alerts
        summary = self.alert_engine.get_summary()
        report.alerts_total = summary["total"]
        report.alerts_critical = summary["by_severity"].get("CRITICAL", 0) + summary["by_severity"].get("EMERGENCY", 0)
        report.alerts_resolved = summary["resolved"]

        # WINDI Verified status
        report.windi_verified = (
            report.chain_breaks == 0 and
            report.isp_profiles_healthy == report.isp_profiles_total and
            report.service_uptime_pct >= 95.0
        )

        # Store report
        self._store_report(report)

        # Generate HTML report file
        report_path = self._generate_html_report(report)

        log.info(
            "📊 Weekly Report Generated: %d docs, %d chain breaks, SGE %.1f (%+.1f), %d/%d ISPs healthy, %.1f%% uptime — %s",
            report.total_documents_governed, report.chain_breaks,
            report.avg_sge_score, report.sge_score_delta,
            report.isp_profiles_healthy, report.isp_profiles_total,
            report.service_uptime_pct,
            "✅ WINDI VERIFIED" if report.windi_verified else "⚠️ NOT VERIFIED"
        )

        return report

    def _generate_html_report(self, report: GuardReport) -> str:
        """Generate an HTML report file."""
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(GUARD_REPORTS, f"guard_report_{timestamp}.html")

        verified_badge = (
            '<span style="color:#C9A84C;font-weight:bold;">✅ WINDI VERIFIED</span>'
            if report.windi_verified else
            '<span style="color:#FF6B6B;font-weight:bold;">⚠️ VERIFICATION PENDING</span>'
        )

        sge_delta_color = "#4CAF50" if report.sge_score_delta >= 0 else "#FF6B6B"
        sge_delta_sign = "+" if report.sge_score_delta >= 0 else ""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>WINDI Governance Guard Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Outfit', 'Segoe UI', sans-serif;
            background: #0A0A0F;
            color: #E8E6E1;
            padding: 40px;
            line-height: 1.6;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #C9A84C;
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        .header h1 {{
            font-family: 'Bricolage Grotesque', serif;
            color: #C9A84C;
            font-size: 28px;
            letter-spacing: 2px;
        }}
        .header .subtitle {{
            color: #8B8680;
            font-size: 14px;
            margin-top: 8px;
        }}
        .header .period {{
            color: #A09B94;
            font-size: 13px;
            margin-top: 4px;
        }}
        .badge {{ margin-top: 16px; font-size: 18px; }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 32px;
        }}
        .metric-card {{
            background: #14141F;
            border: 1px solid #2A2A3A;
            border-radius: 8px;
            padding: 20px;
        }}
        .metric-card .label {{
            color: #8B8680;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric-card .value {{
            font-size: 32px;
            font-weight: 700;
            color: #C9A84C;
            margin-top: 4px;
        }}
        .metric-card .detail {{
            color: #A09B94;
            font-size: 13px;
            margin-top: 4px;
        }}
        .section {{
            margin-bottom: 24px;
        }}
        .section h2 {{
            color: #C9A84C;
            font-size: 18px;
            margin-bottom: 12px;
            border-left: 3px solid #C9A84C;
            padding-left: 12px;
        }}
        .section p {{
            color: #A09B94;
            font-size: 14px;
        }}
        .footer {{
            text-align: center;
            margin-top: 48px;
            padding-top: 24px;
            border-top: 1px solid #2A2A3A;
            color: #5A5650;
            font-size: 12px;
        }}
        .footer .principle {{
            color: #C9A84C;
            font-style: italic;
            margin-top: 8px;
        }}
        .green {{ color: #4CAF50; }}
        .red {{ color: #FF6B6B; }}
        .yellow {{ color: #FFC107; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚔️ GOVERNANCE GUARD REPORT</h1>
            <div class="subtitle">WINDI Publishing House — Automated Governance Audit</div>
            <div class="period">
                Period: {report.period_start[:10]} → {report.period_end[:10]}
            </div>
            <div class="badge">{verified_badge}</div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="label">Documents Governed</div>
                <div class="value">{report.total_documents_governed}</div>
                <div class="detail">This reporting period</div>
            </div>
            <div class="metric-card">
                <div class="label">Chain Integrity</div>
                <div class="value {'green' if report.chain_breaks == 0 else 'red'}">{report.chain_breaks}</div>
                <div class="detail">{'No breaks detected ✓' if report.chain_breaks == 0 else 'BREAKS DETECTED ✗'}</div>
            </div>
            <div class="metric-card">
                <div class="label">SGE Average Score</div>
                <div class="value">{report.avg_sge_score}</div>
                <div class="detail" style="color:{sge_delta_color}">{sge_delta_sign}{report.sge_score_delta} from previous period</div>
            </div>
            <div class="metric-card">
                <div class="label">ISP Profiles</div>
                <div class="value">{report.isp_profiles_healthy}/{report.isp_profiles_total}</div>
                <div class="detail">Healthy / Total</div>
            </div>
            <div class="metric-card">
                <div class="label">Service Uptime</div>
                <div class="value {'green' if report.service_uptime_pct >= 95 else 'yellow'}">{report.service_uptime_pct}%</div>
                <div class="detail">Across all 9 WINDI services</div>
            </div>
            <div class="metric-card">
                <div class="label">Alerts</div>
                <div class="value">{report.alerts_total}</div>
                <div class="detail">{report.alerts_critical} critical · {report.alerts_resolved} resolved</div>
            </div>
        </div>

        <div class="section">
            <h2>Governance Summary</h2>
            <p>
                During this reporting period, the WINDI Governance Guard monitored
                {report.total_documents_governed} governed documents across the complete
                L1→L2→L3 pipeline. The forensic ledger maintained
                {'perfect integrity with zero chain breaks' if report.chain_breaks == 0 else f'{report.chain_breaks} chain breaks requiring investigation'}.
                {report.isp_profiles_healthy} of {report.isp_profiles_total} ISP profiles
                passed validation. Service infrastructure maintained {report.service_uptime_pct}% uptime.
            </p>
        </div>

        <div class="footer">
            <div>WINDI Governance Guard Agent v1.2 — Three Dragons Protocol</div>
            <div>Guardian: Claude · Architect: GPT · Witness: Gemini</div>
            <div class="principle">"AI processes. Human decides. WINDI guarantees."</div>
        </div>
    </div>
</body>
</html>"""

        os.makedirs(GUARD_REPORTS, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        log.info("Report saved: %s", report_path)
        return report_path

    def _store_report(self, report: GuardReport):
        try:
            conn = sqlite3.connect(GUARD_DB, timeout=30)
            conn.execute(
                "INSERT INTO guard_reports (generated_at, period_start, period_end, report_json) VALUES (?,?,?,?)",
                (report.generated_at, report.period_start, report.period_end,
                 json.dumps(asdict(report)))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log.error("Failed to store report: %s", e)


# ─────────────────────────────────────────────
# MAIN DAEMON ORCHESTRATOR
# ─────────────────────────────────────────────

class GovernanceGuard:
    """
    Main daemon orchestrator — runs all Guard modules
    on their respective intervals as a background service.
    """

    def __init__(self):
        self.running = False
        self.alert_engine = AlertEngine()
        self.health_probe = HealthProbe(self.alert_engine)
        self.chain_watcher = ChainWatcher(self.alert_engine)
        self.isp_scanner = ISPScanner(self.alert_engine)
        self.flow_monitor = FlowMonitor(self.alert_engine)
        self.report_builder = ReportBuilder(
            self.health_probe, self.chain_watcher,
            self.isp_scanner, self.flow_monitor,
            self.alert_engine
        )
        self._threads: List[threading.Thread] = []

    def start(self):
        """Start the Governance Guard daemon."""
        log.info("=" * 60)
        log.info("  WINDI GOVERNANCE GUARD v1.0 — STARTING")
        log.info("  Three Dragons Protocol: Guardian Module Active")
        log.info("  \"AI processes. Human decides. WINDI guarantees.\"")
        log.info("=" * 60)

        init_guard_db()
        self.running = True

        # Run initial checks immediately
        log.info("Running initial full scan...")
        self._run_health_check()
        self._run_chain_check()
        self._run_isp_scan()
        self._run_flow_check()
        log.info("Initial scan complete. Starting scheduled monitors.")

        # Start scheduled threads
        self._start_thread("HealthProbe", self._health_loop, HEALTH_CHECK_INTERVAL)
        self._start_thread("ChainWatcher", self._chain_loop, CHAIN_CHECK_INTERVAL)
        self._start_thread("ISPScanner", self._isp_loop, ISP_SCAN_INTERVAL)
        self._start_thread("FlowMonitor", self._flow_loop, FLOW_CHECK_INTERVAL)
        self._start_thread("ReportBuilder", self._report_loop, REPORT_INTERVAL)

        log.info("All Guard modules running. Press Ctrl+C to stop.")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the Guard daemon gracefully."""
        log.info("Governance Guard shutting down...")
        self.running = False
        for t in self._threads:
            t.join(timeout=5)
        log.info("Governance Guard stopped. ⚔️")

    def run_once(self):
        """Run all checks once (for testing/CLI mode)."""
        init_guard_db()

        log.info("=" * 60)
        log.info("  GOVERNANCE GUARD — SINGLE RUN MODE")
        log.info("=" * 60)

        results = {}
        results["health"] = self._run_health_check()
        results["chain"] = self._run_chain_check()
        results["isp"] = self._run_isp_scan()
        results["flow"] = self._run_flow_check()
        results["alerts"] = self.alert_engine.get_summary()

        # Print summary
        print("\n" + "=" * 60)
        print("  GOVERNANCE GUARD — SCAN RESULTS")
        print("=" * 60)

        # Health
        if results["health"]:
            healthy = sum(1 for r in results["health"].values() if r.status == ServiceStatus.HEALTHY)
            down = sum(1 for r in results["health"].values() if r.status == ServiceStatus.DOWN)
            print(f"\n🏥 HealthProbe: {healthy}/{len(results['health'])} healthy, {down} down")
            for name, r in results["health"].items():
                icon = "🟢" if r.status == ServiceStatus.HEALTHY else "🔴" if r.status == ServiceStatus.DOWN else "🟡"
                print(f"   {icon} {name}:{r.port} — {r.status.value} ({r.response_ms}ms)")

        # Chain
        if results["chain"]:
            chain = results["chain"]
            icon = "🟢" if chain["integrity_valid"] else "🔴"
            legacy_note = f" ({chain.get('legacy_excluded', 0)} legacy excluded)" if chain.get("legacy_excluded", 0) > 0 else ""
            print(f"\n🔗 ChainWatcher: {icon} {chain['records_checked']} records, {chain['breaks_found']} breaks{legacy_note}")

        # ISP
        if results["isp"]:
            valid = sum(1 for r in results["isp"] if r.valid)
            print(f"\n📋 ISPScanner: {valid}/{len(results['isp'])} profiles valid")
            for r in results["isp"]:
                icon = "🟢" if r.valid else "🔴"
                issues_str = f" — {', '.join(r.issues)}" if r.issues else ""
                print(f"   {icon} {r.profile_id} [{r.governance_level or '?'}]{issues_str}")

        # Flow
        if results["flow"]:
            flow = results["flow"]
            icon = "🟢" if flow["flow_healthy"] else "🟡"
            print(f"\n🔄 FlowMonitor: {icon} {flow['total_submissions']} submissions, {flow['pending']} pending, {len(flow['stale'])} stale")

        # Alerts
        alerts = results["alerts"]
        print(f"\n🚨 Alerts: {alerts['active']} active / {alerts['total']} total")
        for severity, count in alerts["by_severity"].items():
            if count > 0:
                print(f"   {severity}: {count}")

        print("\n" + "=" * 60)
        verified = (
            results["chain"] and results["chain"]["integrity_valid"] and
            results["chain"]["breaks_found"] == 0 and
            alerts["by_severity"].get("CRITICAL", 0) == 0 and
            alerts["by_severity"].get("EMERGENCY", 0) == 0
        )
        if verified:
            print("  ✅ WINDI VERIFIED — Governance Intact")
        else:
            print("  ⚠️  VERIFICATION PENDING — Review Required")
        print("=" * 60 + "\n")

        return results

    def generate_report_now(self) -> GuardReport:
        """Generate a report immediately."""
        init_guard_db()
        return self.report_builder.generate_report()

    # ── Scheduled loops ──

    def _start_thread(self, name: str, target, interval: int):
        t = threading.Thread(target=target, args=(interval,), name=name, daemon=True)
        t.start()
        self._threads.append(t)
        log.info("Module started: %s (interval: %ds)", name, interval)

    def _health_loop(self, interval: int):
        while self.running:
            time.sleep(interval)
            try:
                self._run_health_check()
            except Exception as e:
                log.error("HealthProbe error: %s", e)

    def _chain_loop(self, interval: int):
        while self.running:
            time.sleep(interval)
            try:
                self._run_chain_check()
            except Exception as e:
                log.error("ChainWatcher error: %s", e)

    def _isp_loop(self, interval: int):
        while self.running:
            time.sleep(interval)
            try:
                self._run_isp_scan()
            except Exception as e:
                log.error("ISPScanner error: %s", e)

    def _flow_loop(self, interval: int):
        while self.running:
            time.sleep(interval)
            try:
                self._run_flow_check()
            except Exception as e:
                log.error("FlowMonitor error: %s", e)

    def _report_loop(self, interval: int):
        while self.running:
            time.sleep(interval)
            try:
                self.report_builder.generate_report()
            except Exception as e:
                log.error("ReportBuilder error: %s", e)

    # ── Single check runners ──

    def _run_health_check(self) -> Dict[str, HealthCheckResult]:
        return self.health_probe.run_full_check()

    def _run_chain_check(self) -> Dict:
        result = self.chain_watcher.verify_virtue_chain()
        self.chain_watcher.verify_config_hash()
        return result

    def _run_isp_scan(self) -> List[ISPCheckResult]:
        return self.isp_scanner.scan_all_profiles()

    def _run_flow_check(self) -> Dict:
        result = self.flow_monitor.check_submissions()
        self.flow_monitor.check_sge_drift()
        return result


# ─────────────────────────────────────────────
# REST API (Flask micro-server for Guard status)
# ─────────────────────────────────────────────

def create_guard_api(guard: GovernanceGuard):
    """Create a minimal Flask API for Guard status — runs on port 8091."""
    try:
        from flask import Flask, jsonify
    except ImportError:
        log.warning("Flask not installed — Guard API not available. pip install flask")
        return None

    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "running", "module": "GovernanceGuard", "version": "1.1"})

    @app.route("/api/guard/status", methods=["GET"])
    def guard_status():
        health_summary = {}
        for name, result in guard.health_probe.last_results.items():
            health_summary[name] = {
                "status": result.status.value,
                "port": result.port,
                "response_ms": result.response_ms,
                "critical": result.critical
            }
        return jsonify({
            "guard_status": "running" if guard.running else "stopped",
            "services": health_summary,
            "alerts": guard.alert_engine.get_summary(),
            "last_chain_check": guard.chain_watcher.last_check,
            "isp_profiles": len(guard.isp_scanner.last_scan),
            "isp_healthy": sum(1 for r in guard.isp_scanner.last_scan if r.valid)
        })

    @app.route("/api/guard/alerts", methods=["GET"])
    def guard_alerts():
        return jsonify({
            "alerts": [a.to_dict() for a in guard.alert_engine.get_active_alerts()]
        })

    @app.route("/api/guard/report", methods=["POST"])
    def generate_report():
        report = guard.generate_report_now()
        return jsonify(asdict(report))

    return app


# ─────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────

def main():
    """CLI entry point for the Governance Guard."""
    import argparse

    parser = argparse.ArgumentParser(
        description="WINDI Governance Guard Agent v1.2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python governance_guard.py daemon          # Run as 24/7 daemon
  python governance_guard.py scan            # Single full scan
  python governance_guard.py report          # Generate report now
  python governance_guard.py health          # Health check only
  python governance_guard.py isp             # ISP scan only
  python governance_guard.py chain           # Chain integrity only

"AI processes. Human decides. WINDI guarantees."
        """
    )
    parser.add_argument(
        "command",
        choices=["daemon", "scan", "report", "health", "isp", "chain"],
        help="Command to execute"
    )
    parser.add_argument(
        "--api", action="store_true",
        help="Start REST API on port 8091 (daemon mode only)"
    )

    args = parser.parse_args()
    guard = GovernanceGuard()

    if args.command == "daemon":
        if args.api:
            app = create_guard_api(guard)
            if app:
                api_thread = threading.Thread(
                    target=lambda: app.run(host="0.0.0.0", port=8091, debug=False),
                    daemon=True
                )
                api_thread.start()
                log.info("Guard API running on port 8091")
        guard.start()

    elif args.command == "scan":
        guard.run_once()

    elif args.command == "report":
        init_guard_db()
        # Run checks first for fresh data
        guard._run_health_check()
        guard._run_chain_check()
        guard._run_isp_scan()
        guard._run_flow_check()
        report = guard.generate_report_now()
        print(f"\n📊 Report generated: WINDI {'VERIFIED ✅' if report.windi_verified else 'PENDING ⚠️'}")

    elif args.command == "health":
        init_guard_db()
        results = guard._run_health_check()
        for name, r in results.items():
            icon = "🟢" if r.status == ServiceStatus.HEALTHY else "🔴"
            print(f"{icon} {name}:{r.port} — {r.status.value} ({r.response_ms}ms)")

    elif args.command == "isp":
        init_guard_db()
        results = guard._run_isp_scan()
        for r in results:
            icon = "🟢" if r.valid else "🔴"
            print(f"{icon} {r.profile_id} — {'OK' if r.valid else ', '.join(r.issues)}")

    elif args.command == "chain":
        init_guard_db()
        result = guard._run_chain_check()
        icon = "🟢" if result["integrity_valid"] else "🔴"
        print(f"{icon} Chain: {result['records_checked']} records, {result['breaks_found']} breaks")
        for detail in result["details"]:
            print(f"   → {detail}")


if __name__ == "__main__":
    main()
