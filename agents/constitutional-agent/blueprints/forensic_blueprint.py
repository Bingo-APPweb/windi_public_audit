"""
W-FORENSIC-001 — Forensic Inspector Agent
==========================================
WINDI Publishing House · Kempten, Bavaria · 2026-03-13

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /forensic/* endpoints on :8091.

Philosophy:
  "A prova da prova é também prova."

  O Forensic Inspector não cria documentos.
  Ele inspeciona artefatos .jmpg e valida a cadeia de prova.
  Cada inspecção é ela própria selada no Ledger.

Role:
  W-FORENSIC-001 is LAYER 3 of the Proof Constellation:
    Genesis (creates) -> Propagation (tracks) -> Forensic (validates)

  The Inspector answers:
    - O bundle é válido?
    - A prova está intacta?
    - O Ledger confirma?
    - A cadeia está completa?

Critical Rules:
  - Inspector NEVER modifies bundles
  - Inspector NEVER alters Ledger receipts
  - Inspector ONLY reads + validates + reports
  - Every inspection is sealed (F2)
  - Violation = I9 violation

Forensic Invariants (F1-F5):
  F1 — Immutability:     Inspector does not alter — only reads and validates
  F2 — Self-sealing:     Every inspection generates its own Ledger receipt
  F3 — Reproducibility:  Same bundle -> same result, always
  F4 — Chain Integrity:  Anchor chain must be valid if present
  F5 — Transparency:     Inspection result is public for anyone with bundle

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 1.0.0
Sealed: W-FORENSIC-001
"""

import hashlib
import json
import os
import sqlite3
import tarfile
import zipfile
import io
import gzip
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import urllib.request

from flask import Blueprint, jsonify, request, Response

# API Key authentication (W-KEYS-001)
try:
    from blueprints.api_keys_blueprint import require_api_key
    API_KEYS_AVAILABLE = True
except ImportError:
    API_KEYS_AVAILABLE = False
    def require_api_key(scopes=None):
        def decorator(f):
            return f
        return decorator

__version__ = "1.0.0"
__agent_id__ = "W-FORENSIC-001"
__agent_name__ = "Forensic Inspector"

# ═══════════════════════════════════════════════════════════════════════════════
# Blueprint Setup
# ═══════════════════════════════════════════════════════════════════════════════

forensic_bp = Blueprint('forensic', __name__, url_prefix='/forensic')

# Database path
FORENSIC_DIR = "/opt/windi/forensic"
DB_PATH = os.path.join(FORENSIC_DIR, "forensic.db")

# External services (READ ONLY)
LEDGER_API = os.environ.get('LEDGER_API', 'http://localhost:8101')

# ═══════════════════════════════════════════════════════════════════════════════
# Forensic Invariants (F1-F5)
# ═══════════════════════════════════════════════════════════════════════════════

class ForensicInvariant(Enum):
    """The five forensic invariants that govern all inspector operations."""
    F1 = ("F1", "imutabilidade", "Inspector nao altera — apenas le e valida")
    F2 = ("F2", "auto-selagem", "Toda inspecao gera receipt proprio no Ledger")
    F3 = ("F3", "reproducibilidade", "Mesmo bundle -> mesmo resultado, sempre")
    F4 = ("F4", "integridade_cadeia", "Anchor chain deve ser valida se presente")
    F5 = ("F5", "transparencia", "Resultado de inspecao e publico para quem tem bundle")

    def __init__(self, code: str, name: str, description: str):
        self._code = code
        self._name = name
        self._description = description

    @property
    def code(self) -> str:
        return self._code

    @property
    def invariant_name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description


# ═══════════════════════════════════════════════════════════════════════════════
# Database Schema
# ═══════════════════════════════════════════════════════════════════════════════

SCHEMA = """
CREATE TABLE IF NOT EXISTS inspections (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    inspection_id   TEXT UNIQUE NOT NULL,
    bundle_hash     TEXT NOT NULL,
    receipt_id      TEXT,
    format          TEXT,
    generation      INTEGER,
    structure_valid INTEGER,
    proof_valid     INTEGER,
    ledger_valid    INTEGER,
    chain_valid     INTEGER,
    overall_status  TEXT,
    findings        TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chain_audits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    inspection_id   TEXT NOT NULL,
    receipt_id      TEXT NOT NULL,
    depth           INTEGER,
    genesis         TEXT,
    supersedes      TEXT,
    validated       INTEGER,
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id)
);

CREATE INDEX IF NOT EXISTS idx_bundle ON inspections(bundle_hash);
CREATE INDEX IF NOT EXISTS idx_receipt ON inspections(receipt_id);
CREATE INDEX IF NOT EXISTS idx_chain ON chain_audits(receipt_id);
"""

def get_db():
    """Get database connection with schema initialization."""
    os.makedirs(FORENSIC_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def init_forensic_db():
    """Initialize database on blueprint registration."""
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        print(f"[W-FORENSIC-001] DB initialized: {DB_PATH}")
    except Exception as e:
        print(f"[W-FORENSIC-001] DB init error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def generate_inspection_id(bundle_hash: str) -> str:
    """Generate unique inspection ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"WINDI-FORENSIC-{bundle_hash[:8].upper()}-{ts}"

# ═══════════════════════════════════════════════════════════════════════════════
# Bundle Format Detection
# ═══════════════════════════════════════════════════════════════════════════════

class BundleFormat(Enum):
    TARGZ = "tar.gz"
    ZIP = "zip"
    JPEG_APP1 = "jpeg_app1"
    UNKNOWN = "unknown"

def detect_format(content: bytes) -> BundleFormat:
    """Detect .jmpg bundle format from magic bytes."""
    if len(content) < 4:
        return BundleFormat.UNKNOWN

    # gzip magic (1f 8b)
    if content[0] == 0x1f and content[1] == 0x8b:
        return BundleFormat.TARGZ

    # ZIP magic (PK)
    if content[0:2] == b'PK':
        return BundleFormat.ZIP

    # JPEG magic (ff d8)
    if content[0] == 0xFF and content[1] == 0xD8:
        return BundleFormat.JPEG_APP1

    return BundleFormat.UNKNOWN

# ═══════════════════════════════════════════════════════════════════════════════
# Bundle Extraction
# ═══════════════════════════════════════════════════════════════════════════════

def extract_bundle(content: bytes) -> Tuple[Dict[str, Any], BundleFormat, List[str]]:
    """
    Extract contents from .jmpg bundle.
    Returns (blocks_dict, format, findings).
    """
    fmt = detect_format(content)
    blocks = {}
    findings = []

    if fmt == BundleFormat.TARGZ:
        try:
            with tarfile.open(fileobj=io.BytesIO(content), mode='r:gz') as tar:
                for member in tar.getmembers():
                    f = tar.extractfile(member)
                    if f:
                        data = f.read()
                        name = os.path.basename(member.name)
                        if name.endswith('.json'):
                            try:
                                blocks[name] = json.loads(data.decode('utf-8'))
                            except json.JSONDecodeError:
                                blocks[name] = {"_raw": data.decode('utf-8', errors='replace')}
                                findings.append(f"WARN: {name} is not valid JSON")
                        else:
                            blocks[name] = data.decode('utf-8', errors='replace')
        except Exception as e:
            findings.append(f"ERROR: tar.gz extraction failed: {e}")

    elif fmt == BundleFormat.ZIP:
        try:
            with zipfile.ZipFile(io.BytesIO(content), 'r') as z:
                for name in z.namelist():
                    data = z.read(name)
                    basename = os.path.basename(name)
                    if basename.endswith('.json'):
                        try:
                            blocks[basename] = json.loads(data.decode('utf-8'))
                        except json.JSONDecodeError:
                            blocks[basename] = {"_raw": data.decode('utf-8', errors='replace')}
                            findings.append(f"WARN: {basename} is not valid JSON")
                    else:
                        blocks[basename] = data.decode('utf-8', errors='replace')
        except Exception as e:
            findings.append(f"ERROR: ZIP extraction failed: {e}")

    elif fmt == BundleFormat.JPEG_APP1:
        try:
            # Check for APP1 marker after SOI
            if len(content) > 6 and content[2] == 0xFF and content[3] == 0xE1:
                length = (content[4] << 8) | content[5]
                proof_data = content[6:6+length-2].decode('utf-8')
                blocks["P2_proof.json"] = json.loads(proof_data)
                findings.append("INFO: JPEG APP1 format detected")
        except Exception as e:
            findings.append(f"ERROR: JPEG APP1 extraction failed: {e}")

    return blocks, fmt, findings

# ═══════════════════════════════════════════════════════════════════════════════
# Generation Detection
# ═══════════════════════════════════════════════════════════════════════════════

def detect_generation(blocks: Dict[str, Any]) -> int:
    """
    Detect WINDI generation from bundle structure.

    Gen 1-4: P1-P4 only
    Gen 5:   P1-P4 + governance.level
    Gen 6:   P1-P4 + anchor_chain
    Gen 7:   P1-P5 + sector + trust_index
    """
    has_p5 = "P5_sector.json" in blocks

    if has_p5:
        return 7

    p2 = blocks.get("P2_proof.json", {})
    proof = p2.get("windi_proof", p2)

    gov = proof.get("governance", {})
    chain = proof.get("anchor_chain", {})

    if chain.get("depth") is not None:
        return 6

    if gov.get("level"):
        return 5

    return 4  # Pre-governance era

# ═══════════════════════════════════════════════════════════════════════════════
# Validation Functions
# ═══════════════════════════════════════════════════════════════════════════════

def validate_structure(blocks: Dict[str, Any], findings: List[str]) -> bool:
    """Validate bundle structure (P1-P5)."""
    required = ["P1_content.json", "P2_proof.json"]
    optional = ["P3_qr.txt", "P4_metadata.json", "P5_sector.json"]

    valid = True

    for req in required:
        if req not in blocks:
            findings.append(f"FAIL: Required block missing: {req}")
            valid = False
        else:
            findings.append(f"OK: {req} present")

    for opt in optional:
        if opt in blocks:
            findings.append(f"OK: {opt} present")
        else:
            findings.append(f"INFO: {opt} absent (optional)")

    return valid


def validate_proof(blocks: Dict[str, Any], findings: List[str]) -> Tuple[bool, Optional[str]]:
    """Validate proof envelope in P2."""
    p2 = blocks.get("P2_proof.json", {})

    if not p2:
        findings.append("FAIL: P2_proof.json is empty")
        return False, None

    proof = p2.get("windi_proof", p2)

    receipt_id = proof.get("receipt_id")
    if not receipt_id:
        findings.append("FAIL: receipt_id missing in proof")
        return False, None
    findings.append(f"OK: receipt_id = {receipt_id}")

    content_hash = proof.get("content_hash")
    if not content_hash:
        findings.append("WARN: content_hash missing in proof")
    else:
        findings.append(f"OK: content_hash = {content_hash[:16]}...")

    timestamp = proof.get("timestamp_utc")
    if not timestamp:
        findings.append("WARN: timestamp_utc missing in proof")
    else:
        findings.append(f"OK: timestamp_utc = {timestamp}")

    issuer = proof.get("issuer", {})
    if not issuer.get("actor"):
        findings.append("WARN: issuer.actor missing")
    else:
        findings.append(f"OK: issuer.actor = {issuer.get('actor')}")

    gov = proof.get("governance", {})
    if gov.get("level"):
        findings.append(f"OK: governance.level = {gov.get('level')}")

    return True, receipt_id


def validate_ledger(receipt_id: str, findings: List[str]) -> bool:
    """Verify receipt exists in Forensic Ledger."""
    try:
        url = f"{LEDGER_API}/api/receipts/{receipt_id}"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get("ok") and data.get("receipt"):
                findings.append(f"OK: Ledger confirms receipt {receipt_id}")
                rec = data["receipt"]
                if rec.get("status") == "sealed":
                    findings.append("OK: Receipt status = sealed")
                return True
            else:
                findings.append(f"FAIL: Receipt not found in Ledger")
                return False
    except Exception as e:
        findings.append(f"WARN: Ledger verification failed: {e}")
        return False


def validate_chain(blocks: Dict[str, Any], findings: List[str]) -> bool:
    """Validate anchor chain if present."""
    p2 = blocks.get("P2_proof.json", {})
    proof = p2.get("windi_proof", p2)
    chain = proof.get("anchor_chain", {})

    if not chain:
        findings.append("INFO: No anchor_chain (pre-Gen6)")
        return True  # Not required for older generations

    genesis = chain.get("genesis")
    depth = chain.get("depth")
    parent = chain.get("parent")

    if depth == 0:
        if genesis:
            findings.append("WARN: depth=0 but genesis is set (should be null for genesis doc)")
        else:
            findings.append("OK: Genesis document (depth=0, no parent)")
        return True

    if depth > 0:
        if not parent:
            findings.append(f"FAIL: depth={depth} but no parent reference")
            return False
        findings.append(f"OK: Chain depth={depth}, parent={parent}")

        # Optionally verify parent exists in Ledger
        try:
            url = f"{LEDGER_API}/api/receipts/{parent}"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get("ok"):
                    findings.append(f"OK: Parent {parent} confirmed in Ledger")
                else:
                    findings.append(f"WARN: Parent {parent} not found in Ledger")
        except Exception:
            findings.append(f"INFO: Could not verify parent in Ledger")

    return True

# ═══════════════════════════════════════════════════════════════════════════════
# Seal Inspection in Ledger
# ═══════════════════════════════════════════════════════════════════════════════

def seal_inspection(inspection_id: str, result: Dict[str, Any]) -> Optional[str]:
    """Seal inspection report in Forensic Ledger (F2 invariant)."""
    try:
        payload = {
            "id": inspection_id,
            "actor": "W-FORENSIC-001",
            "app": "forensic-inspector",
            "doc_name": f"Forensic Inspection: {result.get('receipt_id', 'unknown')}",
            "doc_type": "doc",
            "governance_level": "HIGH",
            "content_hash": sha256_str(json.dumps(result, sort_keys=True)),
            "sge_score": 95.0,
            "metadata": {
                "bundle_hash": result.get("bundle_hash"),
                "receipt_id": result.get("receipt_id"),
                "overall_status": result.get("overall_status"),
                "generation": result.get("generation"),
                "invariants": ["F1", "F2", "F3", "F4", "F5"]
            }
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{LEDGER_API}/api/receipts",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            response = json.loads(resp.read().decode('utf-8'))
            if response.get("ok"):
                return inspection_id
    except Exception as e:
        print(f"[W-FORENSIC-001] Seal failed: {e}")
    return None

# ═══════════════════════════════════════════════════════════════════════════════
# Core Inspection Logic
# ═══════════════════════════════════════════════════════════════════════════════

def inspect_bundle(content: bytes) -> Dict[str, Any]:
    """
    Full forensic inspection of a .jmpg bundle.
    Returns detailed inspection report.
    """
    bundle_hash = sha256_bytes(content)
    inspection_id = generate_inspection_id(bundle_hash)
    findings = []

    # Extract bundle
    blocks, fmt, extract_findings = extract_bundle(content)
    findings.extend(extract_findings)

    if fmt == BundleFormat.UNKNOWN:
        return {
            "inspection_id": inspection_id,
            "bundle_hash": bundle_hash,
            "format": "unknown",
            "overall_status": "INVALID",
            "findings": ["FAIL: Unknown bundle format"],
            "timestamp": now_iso()
        }

    findings.append(f"OK: Format detected: {fmt.value}")

    # Detect generation
    generation = detect_generation(blocks)
    findings.append(f"OK: Generation: Gen {generation}")

    # Validate structure
    structure_valid = validate_structure(blocks, findings)

    # Validate proof
    proof_valid, receipt_id = validate_proof(blocks, findings)

    # Validate against Ledger
    ledger_valid = False
    if receipt_id:
        ledger_valid = validate_ledger(receipt_id, findings)

    # Validate chain
    chain_valid = validate_chain(blocks, findings)

    # Determine overall status
    if structure_valid and proof_valid and ledger_valid:
        overall_status = "VERIFIED"
    elif structure_valid and proof_valid:
        overall_status = "VALID_UNANCHORED"  # Valid bundle but not in Ledger
    elif structure_valid:
        overall_status = "PARTIAL"
    else:
        overall_status = "INVALID"

    result = {
        "inspection_id": inspection_id,
        "bundle_hash": bundle_hash,
        "bundle_size": len(content),
        "format": fmt.value,
        "generation": generation,
        "receipt_id": receipt_id,
        "structure_valid": structure_valid,
        "proof_valid": proof_valid,
        "ledger_valid": ledger_valid,
        "chain_valid": chain_valid,
        "overall_status": overall_status,
        "findings": findings,
        "invariants_applied": ["F1", "F2", "F3", "F4", "F5"],
        "timestamp": now_iso()
    }

    # Seal inspection in Ledger (F2)
    sealed_id = seal_inspection(inspection_id, result)
    if sealed_id:
        result["sealed"] = True
        result["ledger_receipt"] = sealed_id
        findings.append(f"OK: Inspection sealed as {sealed_id}")
    else:
        result["sealed"] = False
        findings.append("WARN: Inspection could not be sealed")

    # Store in local DB
    try:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO inspections
                (inspection_id, bundle_hash, receipt_id, format, generation,
                 structure_valid, proof_valid, ledger_valid, chain_valid,
                 overall_status, findings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inspection_id, bundle_hash, receipt_id, fmt.value, generation,
                1 if structure_valid else 0,
                1 if proof_valid else 0,
                1 if ledger_valid else 0,
                1 if chain_valid else 0,
                overall_status,
                json.dumps(findings)
            ))
            conn.commit()
    except Exception as e:
        print(f"[W-FORENSIC-001] DB store failed: {e}")

    return result

# ═══════════════════════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@forensic_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as total FROM inspections")
            total = c.fetchone()['total']
            c.execute("SELECT COUNT(*) as verified FROM inspections WHERE overall_status = 'VERIFIED'")
            verified = c.fetchone()['verified']
        db_ok = True
    except Exception:
        db_ok = False
        total = 0
        verified = 0

    return jsonify({
        "status": "GREEN" if db_ok else "YELLOW",
        "agent": __agent_id__,
        "agent_name": __agent_name__,
        "version": __version__,
        "total_inspections": total,
        "verified_bundles": verified,
        "invariants": ["F1", "F2", "F3", "F4", "F5"],
        "db_path": DB_PATH,
        "timestamp": now_iso()
    })


@forensic_bp.route('/inspect', methods=['POST'])
def inspect():
    """
    POST /forensic/inspect

    Inspect a .jmpg bundle.
    Accepts multipart/form-data with 'file' field or raw bytes.

    Returns full inspection report sealed in Ledger (F2).
    """
    content = None

    # Try to get file from form data
    if 'file' in request.files:
        content = request.files['file'].read()
    else:
        # Try raw body
        content = request.get_data()

    if not content or len(content) < 10:
        return jsonify({
            "ok": False,
            "error": "No file provided or file too small",
            "invariants": ["F1", "F3"]
        }), 400

    result = inspect_bundle(content)

    return jsonify({
        "ok": True,
        **result
    })


@forensic_bp.route('/inspect/<inspection_id>', methods=['GET'])
# @require_api_key(scopes=['forensic:read'])  # Public for MVP
def get_inspection(inspection_id: str):
    """
    GET /forensic/inspect/<inspection_id>

    Retrieve a previous inspection by ID.
    """
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM inspections WHERE inspection_id = ?", (inspection_id,))
            row = c.fetchone()

            if not row:
                return jsonify({
                    "ok": False,
                    "error": "Inspection not found"
                }), 404

            return jsonify({
                "ok": True,
                "inspection_id": row['inspection_id'],
                "bundle_hash": row['bundle_hash'],
                "receipt_id": row['receipt_id'],
                "format": row['format'],
                "generation": row['generation'],
                "structure_valid": bool(row['structure_valid']),
                "proof_valid": bool(row['proof_valid']),
                "ledger_valid": bool(row['ledger_valid']),
                "chain_valid": bool(row['chain_valid']),
                "overall_status": row['overall_status'],
                "findings": json.loads(row['findings']) if row['findings'] else [],
                "created_at": row['created_at']
            })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@forensic_bp.route('/history', methods=['GET'])
# @require_api_key(scopes=['forensic:read'])  # Public for MVP
def history():
    """
    GET /forensic/history

    Get recent inspection history.
    Query params: limit (default 20), status (optional filter)
    """
    limit = request.args.get('limit', 20, type=int)
    status_filter = request.args.get('status', None)

    try:
        with get_db() as conn:
            c = conn.cursor()

            if status_filter:
                c.execute("""
                    SELECT inspection_id, bundle_hash, receipt_id, format,
                           generation, overall_status, created_at
                    FROM inspections
                    WHERE overall_status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (status_filter.upper(), limit))
            else:
                c.execute("""
                    SELECT inspection_id, bundle_hash, receipt_id, format,
                           generation, overall_status, created_at
                    FROM inspections
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))

            rows = c.fetchall()

            inspections = [{
                "inspection_id": r['inspection_id'],
                "bundle_hash": r['bundle_hash'][:16] + "...",
                "receipt_id": r['receipt_id'],
                "format": r['format'],
                "generation": r['generation'],
                "overall_status": r['overall_status'],
                "created_at": r['created_at']
            } for r in rows]

            return jsonify({
                "ok": True,
                "count": len(inspections),
                "inspections": inspections,
                "timestamp": now_iso()
            })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@forensic_bp.route('/stats', methods=['GET'])
# @require_api_key(scopes=['forensic:read'])  # Public for MVP
def stats():
    """
    GET /forensic/stats

    Get aggregated inspection statistics.
    """
    try:
        with get_db() as conn:
            c = conn.cursor()

            c.execute("SELECT COUNT(*) as total FROM inspections")
            total = c.fetchone()['total']

            c.execute("""
                SELECT overall_status, COUNT(*) as count
                FROM inspections
                GROUP BY overall_status
            """)
            by_status = {r['overall_status']: r['count'] for r in c.fetchall()}

            c.execute("""
                SELECT generation, COUNT(*) as count
                FROM inspections
                GROUP BY generation
            """)
            by_generation = {f"gen{r['generation']}": r['count'] for r in c.fetchall()}

            c.execute("""
                SELECT format, COUNT(*) as count
                FROM inspections
                GROUP BY format
            """)
            by_format = {r['format']: r['count'] for r in c.fetchall()}

            return jsonify({
                "ok": True,
                "total_inspections": total,
                "by_status": by_status,
                "by_generation": by_generation,
                "by_format": by_format,
                "timestamp": now_iso()
            })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@forensic_bp.route('/verify/<receipt_id>', methods=['GET'])
# @require_api_key(scopes=['forensic:read'])  # Public for MVP
def verify_by_receipt(receipt_id: str):
    """
    GET /forensic/verify/<receipt_id>

    Quick verification: check if a receipt_id has been inspected
    and what the result was.
    """
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT inspection_id, overall_status, ledger_valid, created_at
                FROM inspections
                WHERE receipt_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (receipt_id,))
            row = c.fetchone()

            if row:
                return jsonify({
                    "ok": True,
                    "receipt_id": receipt_id,
                    "inspected": True,
                    "inspection_id": row['inspection_id'],
                    "overall_status": row['overall_status'],
                    "ledger_valid": bool(row['ledger_valid']),
                    "last_inspected": row['created_at']
                })
            else:
                # Not inspected locally, check Ledger directly
                ledger_ok = False
                try:
                    url = f"{LEDGER_API}/api/receipts/{receipt_id}"
                    req = urllib.request.Request(url, method='GET')
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        data = json.loads(resp.read().decode('utf-8'))
                        ledger_ok = data.get("ok", False)
                except Exception:
                    pass

                return jsonify({
                    "ok": True,
                    "receipt_id": receipt_id,
                    "inspected": False,
                    "ledger_exists": ledger_ok,
                    "message": "Bundle not inspected. Submit to /forensic/inspect for full analysis."
                })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


# ═══════════════════════════════════════════════════════════════════════════════
# Initialize on import
# ═══════════════════════════════════════════════════════════════════════════════

init_forensic_db()
