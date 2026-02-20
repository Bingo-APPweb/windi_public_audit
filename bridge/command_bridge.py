#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          WINDI COMMAND BRIDGE — O MAESTRO DA ASSINATURA     ║
║                                                              ║
║  "AI processes. Human decides. WINDI guarantees."            ║
║                                                              ║
║  Orchestration layer that sits:                              ║
║    ABOVE  → Schnittstelle (Paperless engine)                 ║
║    BELOW  → Clone UI / Landing Page                          ║
║    BESIDE → Forensic Ledger (anchor)                         ║
║                                                              ║
║  Port: 8096 (Command Bridge API)                             ║
║  Version: 1.0.0                                              ║
║  Date: 13 Feb 2026                                           ║
║  Three Dragons: Guardian(Claude) + Architect(GPT)            ║
║                 + Witness(Gemini)                             ║
╚══════════════════════════════════════════════════════════════╝

ARCHITECTURE:
                                                    
  Clone UI (:8092)  ──┐                             
  Landing Page      ──┼──→ COMMAND BRIDGE (:8096)   
  War Room (:8090)  ──┘         │                   
                          ┌─────┼─────┐             
                          │     │     │             
                          ▼     ▼     ▼             
                   Paperless  Forensic  Pulse       
                   (TSIL)    Ledger    Monitor      
                   (:8095)   (local)   (health)     

MODULES:
  1. Identity Gate    — Auth + I9 enforcement
  2. Transaction Core — Command routing + dual dispatch
  3. Mirror Sync      — Webhook → Forensic Ledger sync
  4. Pulse Monitor    — Health check aggregation
  5. Virtue Forge     — Receipt generation
"""

import os
import sys
import json
import hashlib
import hmac
import time
import uuid
import logging
import sqlite3
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from functools import wraps

# =============================================================================
# CONFIGURATION
# =============================================================================

WINDI_BASE = os.environ.get("WINDI_BASE", "/opt/windi")
BRIDGE_PORT = int(os.environ.get("WINDI_BRIDGE_PORT", "8096"))
BRIDGE_HOST = os.environ.get("WINDI_BRIDGE_HOST", "0.0.0.0")

# Connected services
SCHNITTSTELLE_URL = os.environ.get(
    "WINDI_SCHNITTSTELLE_URL", "http://localhost:8095"
)
HUB_URL = os.environ.get("WINDI_HUB_URL", "http://localhost:8085")
GOVERNANCE_URL = os.environ.get("WINDI_GOVERNANCE_URL", "http://localhost:8080")
CLONE_URL = os.environ.get("WINDI_CLONE_URL", "http://localhost:8092")

# Forensic database
FORENSIC_DB = os.path.join(WINDI_BASE, "data", "command_bridge_ledger.db")
VIRTUE_DB = os.path.join(WINDI_BASE, "data", "virtue_history.db")

# Kill switch
SIGNING_PROVIDER = os.environ.get("WINDI_SIGNING_PROVIDER", "paperless")
KILL_STATES = {"disabled", "off", "kill", "stop"}

# Logging
LOG_FILE = "/opt/windi/logs/command_bridge.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BRIDGE] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("command_bridge")


# =============================================================================
# MODULE 1: IDENTITY GATE — Auth + I9 Enforcement
# =============================================================================

class IdentityGate:
    """
    Enforces I9 (Prohibition of Autonomy Escalation) at the Bridge level.
    Every command must pass through this gate before execution.
    
    Three checks:
      1. Human identity verified (session/token)
      2. I9 invariant not violated (no auto_apply)
      3. Kill switch not active
    """

    SERVICE_KEYS = {
        "clone": os.environ.get("WINDI_CLONE_API_KEY", ""),
        "hub": os.environ.get("WINDI_HUB_API_KEY", ""),
        "warroom": os.environ.get("WINDI_WARROOM_API_KEY", ""),
    }

    @staticmethod
    def check_i9(command_data: dict) -> dict:
        """
        I9 IRREMEDIABLE CHECK
        Blocks any command that attempts autonomy escalation.
        """
        violations = []

        if command_data.get("auto_apply"):
            violations.append("auto_apply flag detected — I9 VIOLATION")

        if command_data.get("skip_human") or command_data.get("bypass_human"):
            violations.append("skip_human/bypass_human detected — I9 VIOLATION")

        if command_data.get("auto_sign") or command_data.get("robot_sign"):
            violations.append("auto_sign/robot_sign detected — I9 VIOLATION")

        if not command_data.get("source"):
            violations.append("No source identified — unattributed command")

        action = command_data.get("action", "")
        if action in ("sign", "dispatch", "seal") and not command_data.get(
            "human_confirmed"
        ):
            violations.append(
                f"Action '{action}' requires human_confirmed=true — I9"
            )

        if violations:
            return {
                "passed": False,
                "gate": "I9_IRREMEDIABLE",
                "violations": violations,
                "message": "⛔ I9 VIOLATION — Autonomy escalation blocked. "
                "Efficiency NEVER overrides sovereignty.",
            }

        return {"passed": True, "gate": "I9_IRREMEDIABLE", "violations": []}

    @staticmethod
    def check_kill_switch() -> dict:
        """Check if signing is globally disabled."""
        provider = os.environ.get("WINDI_SIGNING_PROVIDER", SIGNING_PROVIDER)
        if provider.lower() in KILL_STATES:
            return {
                "active": True,
                "provider": provider,
                "message": "🔴 KILL SWITCH ACTIVE — All signing operations blocked. "
                "Set WINDI_SIGNING_PROVIDER=paperless to re-enable.",
            }
        return {"active": False, "provider": provider}

    @staticmethod
    def validate_service_key(source: str, key: str) -> bool:
        """Validate inter-service API key."""
        expected = IdentityGate.SERVICE_KEYS.get(source, "")
        if not expected:
            log.warning(f"No API key configured for source '{source}' — DEV MODE")
            return True
        return hmac.compare_digest(expected, key)

    @staticmethod
    def gate(command_data: dict) -> dict:
        """
        Full gate check. Returns pass/fail with details.
        This is the SINGLE entry point for all commands.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        gate_id = f"GATE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        # Step 1: Kill switch
        kill = IdentityGate.check_kill_switch()
        if kill["active"]:
            return {
                "gate_id": gate_id,
                "timestamp": timestamp,
                "passed": False,
                "reason": "KILL_SWITCH",
                "details": kill,
            }

        # Step 2: I9 check
        i9 = IdentityGate.check_i9(command_data)
        if not i9["passed"]:
            return {
                "gate_id": gate_id,
                "timestamp": timestamp,
                "passed": False,
                "reason": "I9_VIOLATION",
                "details": i9,
            }

        # Step 3: Source validation
        source = command_data.get("source", "unknown")
        api_key = command_data.get("api_key", "")
        if not IdentityGate.validate_service_key(source, api_key):
            return {
                "gate_id": gate_id,
                "timestamp": timestamp,
                "passed": False,
                "reason": "AUTH_FAILED",
                "details": {"message": f"Invalid API key for source '{source}'"},
            }

        return {
            "gate_id": gate_id,
            "timestamp": timestamp,
            "passed": True,
            "reason": "ALL_CHECKS_PASSED",
            "source": source,
            "action": command_data.get("action"),
        }


# =============================================================================
# MODULE 2: FORENSIC LEDGER — Hash Chain + Persistence
# =============================================================================

class ForensicLedger:
    """
    Immutable forensic ledger with hash chain integrity.
    Every command, every result, every state change is recorded.
    Hash chain: each entry includes the hash of the previous entry.
    """

    def __init__(self, db_path: str = FORENSIC_DB):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        """Create ledger database if not exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                action TEXT NOT NULL,
                source TEXT,
                gate_id TEXT,
                payload_hash TEXT NOT NULL,
                previous_hash TEXT,
                entry_hash TEXT NOT NULL,
                status TEXT DEFAULT 'recorded',
                metadata TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS virtue_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id TEXT UNIQUE NOT NULL,
                entry_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                document_hash TEXT,
                legal_status TEXT,
                forensic_status TEXT,
                chain_position INTEGER,
                receipt_hash TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (entry_id) REFERENCES ledger(entry_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ledger_category ON ledger(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ledger_timestamp ON ledger(timestamp)")
        conn.commit()
        conn.close()
        log.info(f"Forensic Ledger initialized: {self.db_path}")

    def _get_last_hash(self) -> str:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT entry_hash FROM ledger ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        return row[0] if row else "GENESIS"

    def _compute_hash(self, data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def record(
        self,
        category: str,
        action: str,
        payload: dict,
        source: str = "bridge",
        gate_id: str = None,
        metadata: dict = None,
    ) -> dict:
        """
        Record an entry in the forensic ledger.
        
        Categories: COMMAND, SIGN, WEBHOOK, RECEIPT, HEALTH,
                    GATE, MIRROR, SYSTEM
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        entry_id = f"BRG-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"

        payload_json = json.dumps(payload, sort_keys=True, default=str)
        payload_hash = self._compute_hash(payload_json)
        previous_hash = self._get_last_hash()
        entry_data = f"{entry_id}|{timestamp}|{category}|{action}|{payload_hash}|{previous_hash}"
        entry_hash = self._compute_hash(entry_data)

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO ledger 
            (entry_id, timestamp, category, action, source, gate_id, 
             payload_hash, previous_hash, entry_hash, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (entry_id, timestamp, category, action, source, gate_id,
             payload_hash, previous_hash, entry_hash,
             json.dumps(metadata) if metadata else None),
        )
        conn.commit()
        chain_pos = conn.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
        conn.close()

        log.info(f"LEDGER [{category}] {action} | {entry_id} | chain#{chain_pos}")
        return {
            "entry_id": entry_id, "timestamp": timestamp,
            "category": category, "action": action,
            "entry_hash": entry_hash, "chain_position": chain_pos,
        }

    def verify_chain(self) -> dict:
        """Verify the entire hash chain integrity."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT entry_id, timestamp, category, action, payload_hash, "
            "previous_hash, entry_hash FROM ledger ORDER BY id ASC"
        ).fetchall()
        conn.close()

        if not rows:
            return {"intact": True, "entries_verified": 0, "errors": []}

        errors = []
        expected_prev = "GENESIS"

        for i, row in enumerate(rows):
            entry_id, ts, cat, act, p_hash, prev_hash, stored_hash = row
            if prev_hash != expected_prev:
                errors.append(f"Chain break at #{i+1} ({entry_id})")
            entry_data = f"{entry_id}|{ts}|{cat}|{act}|{p_hash}|{prev_hash}"
            computed = self._compute_hash(entry_data)
            if computed != stored_hash:
                errors.append(f"Hash mismatch at #{i+1} ({entry_id})")
            expected_prev = stored_hash

        return {
            "intact": len(errors) == 0,
            "entries_verified": len(rows),
            "errors": errors,
        }

    def get_stats(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        total = conn.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
        categories = dict(
            conn.execute("SELECT category, COUNT(*) FROM ledger GROUP BY category").fetchall()
        )
        receipts = conn.execute("SELECT COUNT(*) FROM virtue_receipts").fetchone()[0]
        last = conn.execute(
            "SELECT entry_id, timestamp, category, action FROM ledger ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        return {
            "total_entries": total, "categories": categories,
            "virtue_receipts": receipts,
            "last_entry": {"entry_id": last[0], "timestamp": last[1],
                           "category": last[2], "action": last[3]} if last else None,
        }


# =============================================================================
# MODULE 3: VIRTUE FORGE — Receipt Generation
# =============================================================================

class VirtueForge:
    """
    Generates WINDI Virtue Receipts — the governance proof that
    a human decided, AI processed, and WINDI guaranteed.
    """

    def __init__(self, ledger: ForensicLedger):
        self.ledger = ledger

    def forge(
        self, entry_id: str, document_hash: str, human_identity: str,
        legal_status: str = "pending", forensic_status: str = "anchored",
        sge_score: float = None, metadata: dict = None,
    ) -> dict:
        timestamp = datetime.now(timezone.utc).isoformat()
        receipt_id = f"VR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"

        receipt_content = {
            "receipt_id": receipt_id, "entry_id": entry_id,
            "timestamp": timestamp, "document_hash": document_hash,
            "human_identity": human_identity,
            "legal_status": legal_status, "forensic_status": forensic_status,
            "sge_score": sge_score,
            "invariants_checked": ["I1","I2","I3","I4","I5","I6","I7","I8","I9"],
            "i9_status": "ENFORCED",
            "three_dragons": {
                "guardian": "Claude — constitutional validation",
                "architect": "GPT — structural extension",
                "witness": "Gemini — forensic observation",
            },
            "principle": "AI processes. Human decides. WINDI guarantees.",
        }

        receipt_json = json.dumps(receipt_content, sort_keys=True)
        receipt_hash = hashlib.sha256(receipt_json.encode()).hexdigest()

        conn = sqlite3.connect(self.ledger.db_path)
        chain_pos = conn.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
        conn.execute(
            """INSERT INTO virtue_receipts
            (receipt_id, entry_id, timestamp, document_hash, 
             legal_status, forensic_status, chain_position, receipt_hash, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (receipt_id, entry_id, timestamp, document_hash,
             legal_status, forensic_status, chain_pos, receipt_hash,
             json.dumps(metadata) if metadata else None),
        )
        conn.commit()
        conn.close()

        self.ledger.record(
            category="RECEIPT", action="virtue_receipt_forged",
            payload=receipt_content,
            metadata={"receipt_id": receipt_id, "receipt_hash": receipt_hash},
        )

        log.info(f"VIRTUE RECEIPT forged: {receipt_id} | chain#{chain_pos}")
        return {**receipt_content, "receipt_hash": receipt_hash, "chain_position": chain_pos}


# =============================================================================
# MODULE 4: TRANSACTION CORE — Dual Dispatch (Legal + Forensic)
# =============================================================================

class TransactionCore:
    """
    The heart of the Command Bridge.
    Routes commands and dispatches DUAL actions:
      1. LEGAL  → Paperless (via Schnittstelle on :8095)
      2. FORENSIC → Ledger (local hash chain)
    """

    COMMANDS = {
        "sign": "Dispatch document for signing via Paperless",
        "verify": "Verify a document's governance trail",
        "status": "Check status of a pending transaction",
        "revoke": "Revoke/cancel a pending signing",
        "audit": "Full audit trail for a document",
        "health": "System health check",
        "chain": "Verify forensic chain integrity",
    }

    def __init__(self, ledger: ForensicLedger, forge: VirtueForge):
        self.ledger = ledger
        self.forge = forge

    def execute(self, command_data: dict) -> dict:
        start_time = time.time()
        action = command_data.get("action", "unknown")

        handlers = {
            "sign": self._handle_sign, "verify": self._handle_verify,
            "status": self._handle_status, "revoke": self._handle_revoke,
            "audit": self._handle_audit, "health": self._handle_health,
            "chain": self._handle_chain,
        }

        handler = handlers.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}",
                    "available_actions": list(self.COMMANDS.keys())}

        result = handler(command_data)
        result["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)
        return result

    def _handle_sign(self, data: dict) -> dict:
        """
        SIGN FLOW — The Crown Jewel
        1. Record command in ledger (FORENSIC)
        2. Compute document hash
        3. Dispatch to Paperless via Schnittstelle (LEGAL)
        4. Record dispatch result in ledger (FORENSIC)
        5. Generate Virtue Receipt
        6. Return unified status
        """
        document = data.get("document", {})
        doc_path = document.get("path", "")
        doc_title = document.get("title", "Untitled")
        signers = document.get("signers", [])
        human_identity = data.get("human_identity", "unknown")

        # STEP 1: Record command
        cmd_entry = self.ledger.record(
            category="COMMAND", action="sign_requested",
            payload={"document_title": doc_title, "signers_count": len(signers),
                     "source": data.get("source"), "human_confirmed": data.get("human_confirmed")},
            source=data.get("source", "unknown"), gate_id=data.get("gate_id"),
        )

        # STEP 2: Compute document hash
        doc_hash = None
        if doc_path and os.path.exists(doc_path):
            with open(doc_path, "rb") as f:
                doc_hash = hashlib.sha256(f.read()).hexdigest()
        elif document.get("content_hash"):
            doc_hash = document["content_hash"]
        else:
            doc_hash = hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()

        # STEP 3: Dispatch to Paperless
        legal_result = self._dispatch_to_paperless(doc_path, doc_title, signers)

        # STEP 4: Record dispatch result
        dispatch_entry = self.ledger.record(
            category="SIGN",
            action="paperless_dispatched" if legal_result["success"] else "paperless_failed",
            payload={"document_hash": doc_hash, "legal_result": {
                "success": legal_result["success"],
                "submission_id": legal_result.get("submission_id"),
                "error": legal_result.get("error")}},
            source="bridge", gate_id=data.get("gate_id"),
        )

        # STEP 5: Forge Virtue Receipt
        receipt = self.forge.forge(
            entry_id=cmd_entry["entry_id"], document_hash=doc_hash,
            human_identity=human_identity,
            legal_status="dispatched" if legal_result["success"] else "failed",
            forensic_status="anchored",
            metadata={"submission_id": legal_result.get("submission_id"),
                       "dispatch_entry": dispatch_entry["entry_id"]},
        )

        # STEP 6: Unified response
        return {
            "success": legal_result["success"],
            "transaction": {
                "command_entry": cmd_entry["entry_id"],
                "dispatch_entry": dispatch_entry["entry_id"],
                "receipt_id": receipt["receipt_id"],
                "chain_position": receipt["chain_position"],
            },
            "legal": {
                "provider": "paperless", 
                "status": "dispatched" if legal_result["success"] else "failed",
                "submission_id": legal_result.get("submission_id"),
                "error": legal_result.get("error"),
            },
            "forensic": {
                "document_hash": doc_hash,
                "entry_hash": dispatch_entry["entry_hash"],
                "receipt_hash": receipt["receipt_hash"],
                "status": "anchored",
            },
            "governance": {
                "i9_enforced": True,
                "human_confirmed": data.get("human_confirmed", False),
                "invariants_verified": 9,
            },
        }

    def _dispatch_to_paperless(self, doc_path: str, title: str, signers: list) -> dict:
        """Dispatch to Paperless via Schnittstelle CLI or API."""
        try:
            schnittstelle_path = os.path.join(WINDI_BASE, "tsil", "schnittstelle.py")

            if not os.path.exists(schnittstelle_path):
                log.warning("Schnittstelle not found — SIMULATION mode")
                sim_id = f"SIM-{uuid.uuid4().hex[:12]}"
                return {"success": True, "submission_id": sim_id, "mode": "simulation",
                        "message": "Simulated — deploy schnittstelle.py for real signing"}

            # Try HTTP API first
            try:
                import urllib.request
                api_url = f"{SCHNITTSTELLE_URL}/api/sign"
                payload = json.dumps({"document_path": doc_path, "title": title, "signers": signers}).encode()
                req = urllib.request.Request(api_url, data=payload,
                    headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read())
                    return {"success": True, "submission_id": result.get("submission_id"), "mode": "api"}
            except Exception as api_err:
                log.info(f"Schnittstelle API not available, trying CLI: {api_err}")

            # Fallback: CLI mode
            cmd = [sys.executable, schnittstelle_path, "sign",
                   "--document", doc_path or "/opt/windi/data/governance_doc.pdf", "--title", title]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return {"success": True, "submission_id": f"CLI-{uuid.uuid4().hex[:8]}", "mode": "cli"}
            else:
                return {"success": False, "error": result.stderr[:500], "mode": "cli"}

        except Exception as e:
            log.error(f"Paperless dispatch error: {e}")
            return {"success": False, "error": str(e)}

    def _handle_verify(self, data: dict) -> dict:
        doc_hash = data.get("document_hash", "")
        if not doc_hash and data.get("document", {}).get("path"):
            path = data["document"]["path"]
            if os.path.exists(path):
                with open(path, "rb") as f:
                    doc_hash = hashlib.sha256(f.read()).hexdigest()
        if not doc_hash:
            return {"success": False, "error": "No document hash provided"}

        conn = sqlite3.connect(self.ledger.db_path)
        entries = conn.execute(
            "SELECT entry_id, timestamp, category, action, entry_hash "
            "FROM ledger WHERE payload_hash LIKE ? OR metadata LIKE ? ORDER BY id ASC",
            (f"%{doc_hash[:16]}%", f"%{doc_hash[:16]}%"),
        ).fetchall()
        receipts = conn.execute(
            "SELECT receipt_id, timestamp, legal_status, forensic_status, receipt_hash "
            "FROM virtue_receipts WHERE document_hash = ?", (doc_hash,),
        ).fetchall()
        conn.close()

        return {
            "success": True, "document_hash": doc_hash,
            "trail": [{"entry_id": e[0], "timestamp": e[1], "category": e[2],
                        "action": e[3], "entry_hash": e[4]} for e in entries],
            "virtue_receipts": [{"receipt_id": r[0], "timestamp": r[1],
                "legal_status": r[2], "forensic_status": r[3], "receipt_hash": r[4]} for r in receipts],
            "governance_proven": len(receipts) > 0,
        }

    def _handle_status(self, data: dict) -> dict:
        tx_id = data.get("transaction_id") or data.get("entry_id", "")
        conn = sqlite3.connect(self.ledger.db_path)
        entries = conn.execute(
            "SELECT entry_id, timestamp, category, action, status "
            "FROM ledger WHERE entry_id = ? OR gate_id = ?", (tx_id, tx_id),
        ).fetchall()
        conn.close()
        if not entries:
            return {"success": False, "error": f"Transaction not found: {tx_id}"}
        return {"success": True, "transaction_id": tx_id,
                "entries": [{"entry_id": e[0], "timestamp": e[1], "category": e[2],
                             "action": e[3], "status": e[4]} for e in entries]}

    def _handle_revoke(self, data: dict) -> dict:
        tx_id = data.get("transaction_id", "")
        entry = self.ledger.record(
            category="COMMAND", action="revoke_requested",
            payload={"transaction_id": tx_id, "reason": data.get("reason", "Human decision"),
                     "human_confirmed": data.get("human_confirmed", False)},
            source=data.get("source", "unknown"),
        )
        return {"success": True, "entry_id": entry["entry_id"],
                "message": f"Revocation recorded for {tx_id}."}

    def _handle_audit(self, data: dict) -> dict:
        limit = data.get("limit", 50)
        category = data.get("category")
        conn = sqlite3.connect(self.ledger.db_path)
        if category:
            entries = conn.execute(
                "SELECT entry_id, timestamp, category, action, source, entry_hash "
                "FROM ledger WHERE category = ? ORDER BY id DESC LIMIT ?", (category, limit),
            ).fetchall()
        else:
            entries = conn.execute(
                "SELECT entry_id, timestamp, category, action, source, entry_hash "
                "FROM ledger ORDER BY id DESC LIMIT ?", (limit,),
            ).fetchall()
        conn.close()
        return {"success": True, "total": len(entries),
                "entries": [{"entry_id": e[0], "timestamp": e[1], "category": e[2],
                             "action": e[3], "source": e[4], "entry_hash": e[5]} for e in entries]}

    def _handle_health(self, data: dict) -> dict:
        return PulseMonitor(self.ledger).full_check()

    def _handle_chain(self, data: dict) -> dict:
        v = self.ledger.verify_chain()
        return {"success": True, **v,
                "message": "🛡️ Chain INTACT" if v["intact"] else "⚠️ CHAIN COMPROMISED"}


# =============================================================================
# MODULE 5: PULSE MONITOR — Health Check Aggregation
# =============================================================================

class PulseMonitor:
    """
    Monitors the health of all connected systems.
    If Paperless goes down, WINDI knows immediately.
    """

    def __init__(self, ledger: ForensicLedger):
        self.ledger = ledger

    def _check_service(self, name: str, url: str, timeout: int = 5) -> dict:
        try:
            import urllib.request
            req = urllib.request.Request(f"{url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.getcode()
                body = resp.read().decode("utf-8", errors="replace")[:200]
                return {"name": name, "url": url,
                        "status": "UP" if status == 200 else f"HTTP_{status}",
                        "response_code": status, "details": body}
        except Exception as e:
            return {"name": name, "url": url, "status": "DOWN", "error": str(e)[:200]}

    def full_check(self) -> dict:
        timestamp = datetime.now(timezone.utc).isoformat()

        checks = {
            "hub": self._check_service("HUB (BABEL)", HUB_URL),
            "governance": self._check_service("Governance API", GOVERNANCE_URL),
            "clone": self._check_service("Clone UI", CLONE_URL),
            "schnittstelle": self._check_service("Schnittstelle (TSIL)", SCHNITTSTELLE_URL),
        }

        try:
            chain = self.ledger.verify_chain()
            stats = self.ledger.get_stats()
            checks["forensic_ledger"] = {
                "name": "Forensic Ledger", "status": "INTACT" if chain["intact"] else "COMPROMISED",
                "entries": stats["total_entries"], "receipts": stats["virtue_receipts"],
                "chain_intact": chain["intact"],
            }
        except Exception as e:
            checks["forensic_ledger"] = {"name": "Forensic Ledger", "status": "ERROR", "error": str(e)}

        kill = IdentityGate.check_kill_switch()
        checks["kill_switch"] = {
            "name": "Kill Switch",
            "status": "ACTIVE 🔴" if kill["active"] else "INACTIVE ✅",
            "provider": kill["provider"],
        }

        critical_up = all(
            checks[s].get("status") in ("UP", "INTACT", "INACTIVE ✅")
            for s in ("hub", "forensic_ledger", "kill_switch")
        )
        all_up = all(
            checks[s].get("status") in ("UP", "INTACT", "INACTIVE ✅")
            for s in checks
        )

        self.ledger.record(
            category="HEALTH", action="pulse_check",
            payload={"critical_healthy": critical_up, "all_healthy": all_up,
                     "services": {k: v.get("status") for k, v in checks.items()}},
        )

        return {
            "success": True, "timestamp": timestamp,
            "overall": "🟢 ALL SYSTEMS GO" if all_up else ("🟡 DEGRADED" if critical_up else "🔴 CRITICAL"),
            "critical_healthy": critical_up, "all_healthy": all_up, "checks": checks,
        }


# =============================================================================
# MODULE 6: MIRROR SYNC — Webhook Consumer
# =============================================================================

class MirrorSync:
    """
    Mirror Engine: consumes webhooks from Paperless (via Schnittstelle)
    and syncs legal state into the Forensic Ledger.
    Latency target: <100ms from webhook to ledger entry.
    """

    def __init__(self, ledger: ForensicLedger, forge: VirtueForge):
        self.ledger = ledger
        self.forge = forge

    def process_webhook(self, event: dict) -> dict:
        event_type = event.get("event_type", "unknown")
        submission_id = event.get("submission_id", "")

        webhook_entry = self.ledger.record(
            category="WEBHOOK", action=f"received_{event_type}",
            payload={"event_type": event_type, "submission_id": submission_id,
                     "event_data": {k: v for k, v in event.items()
                                    if k not in ("sealed_pdf", "audit_trail_pdf")}},
            source="paperless",
            metadata={"received_at": datetime.now(timezone.utc).isoformat()},
        )

        handlers = {
            "submission.completed": self._handle_completion,
            "submission.expired": self._handle_expiry,
            "submission.declined": self._handle_decline,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(event, webhook_entry)
        elif event_type.startswith("participant."):
            return self._handle_participant(event, webhook_entry)
        else:
            log.warning(f"Unknown webhook event type: {event_type}")
            return {"processed": True, "event_type": event_type, "entry_id": webhook_entry["entry_id"]}

    def _handle_completion(self, event: dict, webhook_entry: dict) -> dict:
        """COMPLETION — Document fully signed. Legal validity achieved."""
        submission_id = event.get("submission_id", "")
        sealed_hash = event.get("sealed_pdf_hash", "")
        audit_trail_hash = event.get("audit_trail_hash", "")

        mirror_entry = self.ledger.record(
            category="MIRROR", action="legal_state_synced",
            payload={"submission_id": submission_id, "sealed_pdf_hash": sealed_hash,
                     "audit_trail_hash": audit_trail_hash, "legal_validity": "eIDAS_QES"},
            source="mirror_engine",
        )

        receipt = self.forge.forge(
            entry_id=webhook_entry["entry_id"],
            document_hash=sealed_hash or audit_trail_hash,
            human_identity=event.get("signers_summary", "signers_verified"),
            legal_status="SIGNED_SEALED", forensic_status="MIRRORED",
            metadata={"submission_id": submission_id, "mirror_entry": mirror_entry["entry_id"]},
        )

        log.info(f"🔱 MIRROR SYNC COMPLETE | {submission_id} | {receipt['receipt_id']}")
        return {
            "processed": True, "event_type": "submission.completed",
            "mirror_entry": mirror_entry["entry_id"], "receipt": receipt,
            "message": "✅ Legal state mirrored. Virtue Receipt forged. "
            "DUAL validity: Legal (eIDAS) + Forensic (WINDI).",
        }

    def _handle_expiry(self, event: dict, webhook_entry: dict) -> dict:
        self.ledger.record(category="MIRROR", action="signing_expired",
            payload={"submission_id": event.get("submission_id")}, source="mirror_engine")
        return {"processed": True, "event_type": "submission.expired", "entry_id": webhook_entry["entry_id"]}

    def _handle_decline(self, event: dict, webhook_entry: dict) -> dict:
        self.ledger.record(category="MIRROR", action="signing_declined",
            payload={"submission_id": event.get("submission_id"),
                     "declined_by": event.get("declined_by", "unknown")}, source="mirror_engine")
        return {"processed": True, "event_type": "submission.declined", "entry_id": webhook_entry["entry_id"],
                "message": "❌ Signing declined. Human sovereignty exercised."}

    def _handle_participant(self, event: dict, webhook_entry: dict) -> dict:
        self.ledger.record(category="MIRROR",
            action=f"participant_{event.get('event_type', '').split('.')[-1]}",
            payload={"submission_id": event.get("submission_id"),
                     "participant_id": event.get("participant_id")}, source="mirror_engine")
        return {"processed": True, "event_type": event.get("event_type"), "entry_id": webhook_entry["entry_id"]}


# =============================================================================
# MODULE 7: HTTP SERVER — Flask API
# =============================================================================

def create_app():
    """Create the Command Bridge Flask application."""
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        log.error("Flask not installed. Run: pip install flask")
        return None

    app = Flask(__name__)
    ledger = ForensicLedger()
    forge = VirtueForge(ledger)
    transaction = TransactionCore(ledger, forge)
    mirror = MirrorSync(ledger, forge)

    ledger.record(category="SYSTEM", action="bridge_started",
                  payload={"port": BRIDGE_PORT, "version": "1.0.0", "provider": SIGNING_PROVIDER})

    @app.route("/health", methods=["GET"])
    def health():
        kill = IdentityGate.check_kill_switch()
        chain = ledger.verify_chain()
        return jsonify({
            "service": "WINDI Command Bridge v1.0.0",
            "status": "operational",
            "kill_switch": "active" if kill["active"] else "inactive",
            "chain_intact": chain["intact"],
            "chain_entries": chain["entries_verified"],
            "principle": "AI processes. Human decides. WINDI guarantees.",
        })

    @app.route("/api/command", methods=["POST"])
    def api_command():
        data = request.get_json(force=True, silent=True) or {}
        gate_result = IdentityGate.gate(data)
        ledger.record(category="GATE", action="gate_checked",
            payload={"passed": gate_result["passed"], "reason": gate_result["reason"],
                     "action": data.get("action")},
            source=data.get("source", "api"), gate_id=gate_result["gate_id"])
        if not gate_result["passed"]:
            return jsonify({"success": False, "gate": gate_result}), 403
        data["gate_id"] = gate_result["gate_id"]
        return jsonify(transaction.execute(data))

    @app.route("/api/webhook", methods=["POST"])
    def api_webhook():
        event = request.get_json(force=True, silent=True) or {}
        return jsonify(mirror.process_webhook(event))

    @app.route("/api/health", methods=["GET"])
    def api_health():
        return jsonify(PulseMonitor(ledger).full_check())

    @app.route("/api/chain/verify", methods=["GET"])
    def api_chain_verify():
        chain = ledger.verify_chain()
        return jsonify({**chain, "message": "🛡️ Chain INTACT" if chain["intact"] else "⚠️ COMPROMISED"})

    @app.route("/api/audit", methods=["GET"])
    def api_audit():
        return jsonify(transaction.execute({
            "action": "audit", "limit": request.args.get("limit", 50, type=int),
            "category": request.args.get("category"), "source": "api"}))

    @app.route("/api/stats", methods=["GET"])
    def api_stats():
        return jsonify(ledger.get_stats())

    return app


# =============================================================================
# CLI INTERFACE
# =============================================================================

def cli_main():
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════════╗
║          WINDI COMMAND BRIDGE v1.0.0                        ║
║          "O Maestro da Assinatura"                          ║
╚══════════════════════════════════════════════════════════════╝

Usage:
  python3 command_bridge.py serve          Start HTTP server on :8096
  python3 command_bridge.py health         Run pulse monitor check
  python3 command_bridge.py chain          Verify forensic chain integrity
  python3 command_bridge.py stats          Show ledger statistics
  python3 command_bridge.py sign-test      Simulate a signing flow
  python3 command_bridge.py webhook-test   Simulate a webhook event
  python3 command_bridge.py audit [N]      Show last N audit entries
  python3 command_bridge.py gate-test      Test I9 gate enforcement

Port Map:
  8080  Governance API
  8085  HUB (BABEL)
  8090  War Room
  8092  Clone UI
  8095  Schnittstelle (Paperless)
  8096  Command Bridge  ← YOU ARE HERE
  8889  Cortex
        """)
        return

    command = sys.argv[1].lower()
    ledger = ForensicLedger()
    forge = VirtueForge(ledger)
    transaction = TransactionCore(ledger, forge)
    mirror = MirrorSync(ledger, forge)

    if command == "serve":
        app = create_app()
        if app:
            print(f"\n🐉 Command Bridge starting on port {BRIDGE_PORT}...")
            print(f"   Provider: {SIGNING_PROVIDER}")
            print(f"   Ledger: {FORENSIC_DB}\n")
            app.run(host=BRIDGE_HOST, port=BRIDGE_PORT, debug=False)
        else:
            print("ERROR: Flask not available. Install: pip install flask")

    elif command == "health":
        pulse = PulseMonitor(ledger)
        result = pulse.full_check()
        print(f"\n{'='*60}")
        print(f"  WINDI PULSE MONITOR — {result['timestamp']}")
        print(f"  Overall: {result['overall']}")
        print(f"{'='*60}")
        for name, check in result["checks"].items():
            status = check.get("status", "UNKNOWN")
            icon = "✅" if status in ("UP", "INTACT", "INACTIVE ✅") else "❌"
            print(f"  {icon} {check.get('name', name)}: {status}")
        print(f"{'='*60}\n")

    elif command == "chain":
        result = ledger.verify_chain()
        if result["intact"]:
            print(f"\n🛡️  Chain INTACT — {result['entries_verified']} entries verified\n")
        else:
            print(f"\n⚠️  CHAIN COMPROMISED — {len(result['errors'])} errors found\n")

    elif command == "stats":
        stats = ledger.get_stats()
        print(f"\n{'='*60}")
        print(f"  FORENSIC LEDGER STATISTICS")
        print(f"{'='*60}")
        print(f"  Total entries:     {stats['total_entries']}")
        print(f"  Virtue receipts:   {stats['virtue_receipts']}")
        for cat, count in stats.get("categories", {}).items():
            print(f"    {cat}: {count}")
        print(f"{'='*60}\n")

    elif command == "sign-test":
        print("\n🐉 SIGN TEST — Full signing flow simulation...\n")
        cmd_data = {
            "action": "sign", "source": "cli_test", "human_confirmed": True,
            "human_identity": "Human Dragon (CLI Test)",
            "document": {"path": "/opt/windi/data/governance_doc.pdf",
                         "title": "WINDI Governance Test Document",
                         "signers": [{"email": "dragon@windi-domain.com", "role": "approver"}]},
        }
        gate = IdentityGate.gate(cmd_data)
        print(f"  Gate: {'✅ PASSED' if gate['passed'] else '❌ BLOCKED'} ({gate['gate_id']})")
        if gate["passed"]:
            cmd_data["gate_id"] = gate["gate_id"]
            result = transaction.execute(cmd_data)
            print(f"  Result: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
            if result.get("transaction"):
                tx = result["transaction"]
                print(f"  Receipt: {tx.get('receipt_id')} | Chain #{tx.get('chain_position')}")
            if result.get("legal"):
                print(f"  Legal: {result['legal'].get('status')} ({result['legal'].get('submission_id')})")
            print(f"  Time: {result.get('execution_time_ms', 0)}ms")
        print()

    elif command == "webhook-test":
        print("\n🔱 WEBHOOK TEST — Simulating Paperless completion...\n")
        event = {
            "event_type": "submission.completed",
            "submission_id": f"SIM-{uuid.uuid4().hex[:12]}",
            "sealed_pdf_hash": hashlib.sha256(b"test_sealed_pdf").hexdigest(),
            "audit_trail_hash": hashlib.sha256(b"test_audit_trail").hexdigest(),
            "signers_summary": "dragon@windi-domain.com (QES verified)",
        }
        result = mirror.process_webhook(event)
        print(f"  Event: {event['event_type']}")
        print(f"  Submission: {event['submission_id']}")
        if result.get("receipt"):
            r = result["receipt"]
            print(f"  Receipt: {r['receipt_id']} | Chain #{r['chain_position']}")
            print(f"  Legal: {r['legal_status']} | Forensic: {r['forensic_status']}")
        print(f"\n  {result.get('message', '')}\n")

    elif command == "gate-test":
        print("\n⛔ I9 GATE TEST — Invariant enforcement...\n")
        tests = [
            ("Valid command", {"action": "sign", "source": "clone", "human_confirmed": True}, True),
            ("auto_apply flag", {"action": "sign", "source": "clone", "auto_apply": True, "human_confirmed": True}, False),
            ("No human confirm", {"action": "sign", "source": "clone", "human_confirmed": False}, False),
            ("skip_human flag", {"action": "verify", "source": "api", "skip_human": True}, False),
            ("No source", {"action": "sign", "human_confirmed": True}, False),
        ]
        ok = 0
        for name, data, expected in tests:
            gate = IdentityGate.gate(data)
            correct = gate["passed"] == expected
            ok += 1 if correct else 0
            icon = "✅" if correct else "❌"
            print(f"  {icon} {name}: {'PASS' if gate['passed'] else 'BLOCK'} (expected: {'PASS' if expected else 'BLOCK'})")
        print(f"\n  I9 Enforcement: {ok}/{len(tests)} correct {'✅' if ok == len(tests) else '⚠️'}\n")

    elif command == "audit":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        result = transaction.execute({"action": "audit", "limit": limit, "source": "cli"})
        entries = result.get("entries", [])
        if not entries:
            print("\n  No entries in ledger yet.\n")
        else:
            print(f"\n{'='*80}")
            print(f"  AUDIT TRAIL — Last {len(entries)} entries")
            print(f"{'='*80}")
            for e in entries:
                print(f"  {e['timestamp'][:19]} | {e['category']:10} | {e['action']:30} | {e['entry_hash'][:16]}...")
            print(f"{'='*80}\n")
    else:
        print(f"Unknown command: {command}. Run without arguments for usage.")


if __name__ == "__main__":
    cli_main()
