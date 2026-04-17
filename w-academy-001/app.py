#!/usr/bin/env python3
"""
W-ACADEMY-001 — WINDI Institute Ausbildungsplattform
=====================================================
Professionelles Kursmanagement mit Ledger-Integration

Port: 8180
Invariants: I9, I11, I14

Kernfunktionen:
- Kursverwaltung (Programme, Module, Lektionen)
- Teilnehmerverwaltung mit DID-Integration
- Ausbilder-Zertifizierung
- Prüfungsnachweis im Ledger
- Fortschrittsverfolgung
- Zertifikatsgenerierung mit SHA-256 Seal

Liga IA+H · Kempten, Bavaria · 2026
"""

import sqlite3
import hashlib
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string
from functools import wraps

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PORT = 8180
VERSION = "1.0.0"
DB_PATH = Path("/opt/windi/w-academy-001/data/academy.db")
LEDGER_URL = "http://localhost:8101"

# Ensure data directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# DATABASE SCHEMA
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Initialize the academy database with full schema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ─── PROGRAMME (Kursprogramme) ───
    c.execute('''
        CREATE TABLE IF NOT EXISTS programme (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name_de TEXT NOT NULL,
            name_en TEXT,
            name_pt TEXT,
            description_de TEXT,
            description_en TEXT,
            tier TEXT DEFAULT 'STANDARD',
            duration_hours INTEGER,
            price_private REAL,
            price_corporate REAL,
            prerequisites TEXT,
            target_audience TEXT,
            certification_type TEXT DEFAULT 'TEILNAHME',
            status TEXT DEFAULT 'DRAFT',
            created_at TEXT,
            updated_at TEXT,
            created_by TEXT
        )
    ''')

    # ─── MODULE (Kursmodule) ───
    c.execute('''
        CREATE TABLE IF NOT EXISTS module (
            id TEXT PRIMARY KEY,
            programme_id TEXT NOT NULL,
            code TEXT NOT NULL,
            name_de TEXT NOT NULL,
            name_en TEXT,
            order_index INTEGER DEFAULT 0,
            duration_minutes INTEGER,
            learning_objectives TEXT,
            content_summary TEXT,
            assessment_type TEXT,
            passing_score INTEGER DEFAULT 70,
            status TEXT DEFAULT 'ACTIVE',
            created_at TEXT,
            FOREIGN KEY (programme_id) REFERENCES programme(id)
        )
    ''')

    # ─── LEKTION (Einzelne Lektionen) ───
    c.execute('''
        CREATE TABLE IF NOT EXISTS lektion (
            id TEXT PRIMARY KEY,
            module_id TEXT NOT NULL,
            code TEXT NOT NULL,
            title_de TEXT NOT NULL,
            title_en TEXT,
            order_index INTEGER DEFAULT 0,
            content_type TEXT DEFAULT 'THEORY',
            content_url TEXT,
            duration_minutes INTEGER,
            requires_action BOOLEAN DEFAULT 0,
            action_type TEXT,
            created_at TEXT,
            FOREIGN KEY (module_id) REFERENCES module(id)
        )
    ''')

    # ─── AUSBILDER (Zertifizierte Trainer) ───
    c.execute('''
        CREATE TABLE IF NOT EXISTS ausbilder (
            id TEXT PRIMARY KEY,
            did TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            company TEXT,
            bio_de TEXT,
            bio_en TEXT,
            specializations TEXT,
            certification_level TEXT DEFAULT 'KANDIDAT',
            certification_date TEXT,
            certification_receipt_id TEXT,
            programmes_authorized TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    # ─── TEILNEHMER (Kursteilnehmer) ───
    c.execute('''
        CREATE TABLE IF NOT EXISTS teilnehmer (
            id TEXT PRIMARY KEY,
            did TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            company TEXT,
            position TEXT,
            industry TEXT,
            registration_date TEXT,
            status TEXT DEFAULT 'ACTIVE',
            notes TEXT
        )
    ''')

    # ─── ENROLLMENT (Kursanmeldungen) ───
    c.execute('''
        CREATE TABLE IF NOT EXISTS enrollment (
            id TEXT PRIMARY KEY,
            teilnehmer_id TEXT NOT NULL,
            programme_id TEXT NOT NULL,
            ausbilder_id TEXT,
            cohort_code TEXT,
            enrollment_date TEXT,
            start_date TEXT,
            expected_end_date TEXT,
            actual_end_date TEXT,
            status TEXT DEFAULT 'ENROLLED',
            payment_status TEXT DEFAULT 'PENDING',
            payment_amount REAL,
            invoice_id TEXT,
            notes TEXT,
            FOREIGN KEY (teilnehmer_id) REFERENCES teilnehmer(id),
            FOREIGN KEY (programme_id) REFERENCES programme(id),
            FOREIGN KEY (ausbilder_id) REFERENCES ausbilder(id)
        )
    ''')

    # ─── FORTSCHRITT (Lernfortschritt) ───
    c.execute('''
        CREATE TABLE IF NOT EXISTS fortschritt (
            id TEXT PRIMARY KEY,
            enrollment_id TEXT NOT NULL,
            lektion_id TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            time_spent_seconds INTEGER DEFAULT 0,
            status TEXT DEFAULT 'NOT_STARTED',
            action_completed BOOLEAN DEFAULT 0,
            action_receipt_id TEXT,
            notes TEXT,
            FOREIGN KEY (enrollment_id) REFERENCES enrollment(id),
            FOREIGN KEY (lektion_id) REFERENCES lektion(id)
        )
    ''')

    # ─── ASSESSMENT (Prüfungen/Bewertungen) ───
    c.execute('''
        CREATE TABLE IF NOT EXISTS assessment (
            id TEXT PRIMARY KEY,
            enrollment_id TEXT NOT NULL,
            module_id TEXT NOT NULL,
            assessment_type TEXT NOT NULL,
            score INTEGER,
            max_score INTEGER DEFAULT 100,
            passed BOOLEAN,
            attempt_number INTEGER DEFAULT 1,
            started_at TEXT,
            completed_at TEXT,
            answers_json TEXT,
            feedback TEXT,
            graded_by TEXT,
            receipt_id TEXT,
            FOREIGN KEY (enrollment_id) REFERENCES enrollment(id),
            FOREIGN KEY (module_id) REFERENCES module(id)
        )
    ''')

    # ─── ZERTIFIKAT (Ausgestellte Zertifikate) ───
    c.execute('''
        CREATE TABLE IF NOT EXISTS zertifikat (
            id TEXT PRIMARY KEY,
            enrollment_id TEXT NOT NULL,
            teilnehmer_did TEXT NOT NULL,
            programme_id TEXT NOT NULL,
            certificate_type TEXT NOT NULL,
            certificate_code TEXT UNIQUE NOT NULL,
            issued_date TEXT NOT NULL,
            valid_until TEXT,
            issuer_did TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            receipt_id TEXT NOT NULL,
            verify_url TEXT,
            pdf_path TEXT,
            status TEXT DEFAULT 'ACTIVE',
            FOREIGN KEY (enrollment_id) REFERENCES enrollment(id),
            FOREIGN KEY (programme_id) REFERENCES programme(id)
        )
    ''')

    # ─── KOHORTE (Kursgruppen) ───
    c.execute('''
        CREATE TABLE IF NOT EXISTS kohorte (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            programme_id TEXT NOT NULL,
            ausbilder_id TEXT NOT NULL,
            name TEXT,
            start_date TEXT,
            end_date TEXT,
            max_participants INTEGER DEFAULT 15,
            current_participants INTEGER DEFAULT 0,
            location TEXT,
            format TEXT DEFAULT 'HYBRID',
            status TEXT DEFAULT 'PLANNED',
            notes TEXT,
            FOREIGN KEY (programme_id) REFERENCES programme(id),
            FOREIGN KEY (ausbilder_id) REFERENCES ausbilder(id)
        )
    ''')

    # ─── AKTION_LOG (Handlungsprotokoll für PHO) ───
    c.execute('''
        CREATE TABLE IF NOT EXISTS aktion_log (
            id TEXT PRIMARY KEY,
            teilnehmer_did TEXT NOT NULL,
            action_type TEXT NOT NULL,
            action_context TEXT,
            decision_made TEXT,
            reasoning TEXT,
            timestamp TEXT NOT NULL,
            content_hash TEXT,
            receipt_id TEXT,
            sealed BOOLEAN DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✓ Database initialized: {DB_PATH}")

# Initialize on import
init_db()

# ═══════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════════════════════════

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_id(prefix="WA"):
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    rand = hashlib.sha256(f"{ts}{datetime.now().microsecond}".encode()).hexdigest()[:6].upper()
    return f"{prefix}-{ts}-{rand}"

# ═══════════════════════════════════════════════════════════════
# LEDGER INTEGRATION (I11)
# ═══════════════════════════════════════════════════════════════

def seal_to_ledger(doc_name, doc_type, content, actor_did, governance_level="MEDIUM"):
    """Seal academy action to Forensic Ledger."""
    content_hash = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()

    receipt = {
        "receipt_id": generate_id("WINDI-ACAD"),
        "actor": actor_did,
        "app": "w-academy-001",
        "doc_name": doc_name,
        "doc_type": doc_type,
        "governance_level": governance_level,
        "content_hash": f"sha256:{content_hash}",
        "invariants": ["I9", "I11"],
        "stage": "C6",
        "sealed_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        r = requests.post(f"{LEDGER_URL}/api/receipts", json=receipt, timeout=5)
        if r.status_code in [200, 201]:
            return receipt["receipt_id"], content_hash
    except:
        pass
    return None, content_hash

# ═══════════════════════════════════════════════════════════════
# I9 GATE
# ═══════════════════════════════════════════════════════════════

def require_i9(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        data = request.get_json() or {}
        actor_did = data.get("actor_did") or request.args.get("actor_did")
        if not actor_did or not actor_did.startswith("did:windi:"):
            return jsonify({"error": "I9_VIOLATION", "message": "Valid DID required"}), 403
        return f(*args, **kwargs)
    return decorated

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS — HEALTH
# ═══════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    conn = get_db()
    stats = {
        "programme": conn.execute("SELECT COUNT(*) FROM programme").fetchone()[0],
        "ausbilder": conn.execute("SELECT COUNT(*) FROM ausbilder").fetchone()[0],
        "teilnehmer": conn.execute("SELECT COUNT(*) FROM teilnehmer").fetchone()[0],
        "enrollments": conn.execute("SELECT COUNT(*) FROM enrollment").fetchone()[0],
        "zertifikate": conn.execute("SELECT COUNT(*) FROM zertifikat").fetchone()[0],
    }
    conn.close()

    return jsonify({
        "service": "W-ACADEMY-001",
        "version": VERSION,
        "port": PORT,
        "status": "ONLINE",
        "database": str(DB_PATH),
        "statistics": stats,
        "invariants": ["I9", "I11", "I14"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS — PROGRAMME
# ═══════════════════════════════════════════════════════════════

@app.route("/api/programme", methods=["GET"])
def list_programme():
    """List all training programmes."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM programme ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify({"programme": [dict(r) for r in rows], "count": len(rows)})

@app.route("/api/programme/<programme_id>", methods=["GET"])
def get_programme(programme_id):
    """Get programme with modules."""
    conn = get_db()
    prog = conn.execute("SELECT * FROM programme WHERE id = ? OR code = ?", (programme_id, programme_id)).fetchone()
    if not prog:
        conn.close()
        return jsonify({"error": "Programme not found"}), 404

    modules = conn.execute(
        "SELECT * FROM module WHERE programme_id = ? ORDER BY order_index",
        (prog["id"],)
    ).fetchall()

    conn.close()

    result = dict(prog)
    result["modules"] = [dict(m) for m in modules]
    return jsonify(result)

@app.route("/api/programme", methods=["POST"])
@require_i9
def create_programme():
    """Create a new training programme."""
    data = request.get_json()
    actor_did = data.get("actor_did")

    prog_id = generate_id("PROG")
    now = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    conn.execute('''
        INSERT INTO programme (id, code, name_de, name_en, name_pt, description_de,
            description_en, tier, duration_hours, price_private, price_corporate,
            prerequisites, target_audience, certification_type, status, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        prog_id, data.get("code"), data.get("name_de"), data.get("name_en"),
        data.get("name_pt"), data.get("description_de"), data.get("description_en"),
        data.get("tier", "STANDARD"), data.get("duration_hours"),
        data.get("price_private"), data.get("price_corporate"),
        data.get("prerequisites"), data.get("target_audience"),
        data.get("certification_type", "TEILNAHME"), "DRAFT", now, actor_did
    ))
    conn.commit()
    conn.close()

    # Seal to Ledger
    receipt_id, _ = seal_to_ledger(
        f"Programme Created: {data.get('name_de')}",
        "programme-created",
        {"programme_id": prog_id, "code": data.get("code")},
        actor_did
    )

    return jsonify({
        "status": "CREATED",
        "programme_id": prog_id,
        "receipt_id": receipt_id
    }), 201

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS — AUSBILDER (Trainers)
# ═══════════════════════════════════════════════════════════════

@app.route("/api/ausbilder", methods=["GET"])
def list_ausbilder():
    """List all certified trainers."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM ausbilder ORDER BY certification_level DESC, name").fetchall()
    conn.close()
    return jsonify({"ausbilder": [dict(r) for r in rows], "count": len(rows)})

@app.route("/api/ausbilder", methods=["POST"])
@require_i9
def register_ausbilder():
    """Register a new trainer candidate."""
    data = request.get_json()
    actor_did = data.get("actor_did")

    aus_id = generate_id("AUS")
    now = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    conn.execute('''
        INSERT INTO ausbilder (id, did, name, email, phone, company, bio_de, bio_en,
            specializations, certification_level, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        aus_id, data.get("did"), data.get("name"), data.get("email"),
        data.get("phone"), data.get("company"), data.get("bio_de"),
        data.get("bio_en"), json.dumps(data.get("specializations", [])),
        "KANDIDAT", "PENDING", now
    ))
    conn.commit()
    conn.close()

    return jsonify({"status": "REGISTERED", "ausbilder_id": aus_id}), 201

@app.route("/api/ausbilder/<ausbilder_id>/certify", methods=["POST"])
@require_i9
def certify_ausbilder(ausbilder_id):
    """Certify a trainer (Gründungsausbilder, etc.)."""
    data = request.get_json()
    actor_did = data.get("actor_did")
    cert_level = data.get("certification_level", "GRÜNDUNGSAUSBILDER")

    conn = get_db()
    aus = conn.execute("SELECT * FROM ausbilder WHERE id = ?", (ausbilder_id,)).fetchone()
    if not aus:
        conn.close()
        return jsonify({"error": "Ausbilder not found"}), 404

    now = datetime.now(timezone.utc).isoformat()

    # Seal certification to Ledger
    receipt_id, content_hash = seal_to_ledger(
        f"Ausbilder Zertifizierung: {aus['name']}",
        "ausbilder-certification",
        {
            "ausbilder_id": ausbilder_id,
            "ausbilder_did": aus["did"],
            "certification_level": cert_level,
            "certified_by": actor_did
        },
        actor_did,
        "HIGH"
    )

    conn.execute('''
        UPDATE ausbilder SET
            certification_level = ?,
            certification_date = ?,
            certification_receipt_id = ?,
            status = 'CERTIFIED',
            updated_at = ?
        WHERE id = ?
    ''', (cert_level, now, receipt_id, now, ausbilder_id))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "CERTIFIED",
        "ausbilder_id": ausbilder_id,
        "certification_level": cert_level,
        "receipt_id": receipt_id,
        "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}"
    })

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS — TEILNEHMER (Participants)
# ═══════════════════════════════════════════════════════════════

@app.route("/api/teilnehmer", methods=["GET"])
def list_teilnehmer():
    """List all participants."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM teilnehmer ORDER BY registration_date DESC").fetchall()
    conn.close()
    return jsonify({"teilnehmer": [dict(r) for r in rows], "count": len(rows)})

@app.route("/api/teilnehmer", methods=["POST"])
def register_teilnehmer():
    """Register a new participant."""
    data = request.get_json()

    teil_id = generate_id("TEIL")
    now = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    conn.execute('''
        INSERT INTO teilnehmer (id, did, name, email, company, position, industry, registration_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        teil_id, data.get("did"), data.get("name"), data.get("email"),
        data.get("company"), data.get("position"), data.get("industry"),
        now, "ACTIVE"
    ))
    conn.commit()
    conn.close()

    return jsonify({"status": "REGISTERED", "teilnehmer_id": teil_id}), 201

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS — ENROLLMENT
# ═══════════════════════════════════════════════════════════════

@app.route("/api/enrollment", methods=["POST"])
@require_i9
def create_enrollment():
    """Enroll a participant in a programme."""
    data = request.get_json()
    actor_did = data.get("actor_did")

    enroll_id = generate_id("ENR")
    now = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    conn.execute('''
        INSERT INTO enrollment (id, teilnehmer_id, programme_id, ausbilder_id, cohort_code,
            enrollment_date, start_date, expected_end_date, status, payment_status, payment_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        enroll_id, data.get("teilnehmer_id"), data.get("programme_id"),
        data.get("ausbilder_id"), data.get("cohort_code"), now,
        data.get("start_date"), data.get("expected_end_date"),
        "ENROLLED", data.get("payment_status", "PENDING"), data.get("payment_amount")
    ))
    conn.commit()
    conn.close()

    # Seal enrollment
    receipt_id, _ = seal_to_ledger(
        f"Enrollment: {data.get('teilnehmer_id')} → {data.get('programme_id')}",
        "enrollment-created",
        {"enrollment_id": enroll_id},
        actor_did
    )

    return jsonify({
        "status": "ENROLLED",
        "enrollment_id": enroll_id,
        "receipt_id": receipt_id
    }), 201

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS — ZERTIFIKAT (Certificates)
# ═══════════════════════════════════════════════════════════════

@app.route("/api/zertifikat/issue", methods=["POST"])
@require_i9
def issue_certificate():
    """Issue a certificate upon programme completion."""
    data = request.get_json()
    actor_did = data.get("actor_did")
    enrollment_id = data.get("enrollment_id")

    conn = get_db()

    # Get enrollment details
    enroll = conn.execute('''
        SELECT e.*, t.did as teilnehmer_did, t.name as teilnehmer_name, p.name_de as programme_name
        FROM enrollment e
        JOIN teilnehmer t ON e.teilnehmer_id = t.id
        JOIN programme p ON e.programme_id = p.id
        WHERE e.id = ?
    ''', (enrollment_id,)).fetchone()

    if not enroll:
        conn.close()
        return jsonify({"error": "Enrollment not found"}), 404

    now = datetime.now(timezone.utc).isoformat()
    cert_id = generate_id("CERT")
    cert_code = f"WINDI-CERT-{datetime.now().strftime('%Y%m%d')}-{hashlib.sha256(enrollment_id.encode()).hexdigest()[:8].upper()}"

    # Create certificate content for hashing
    cert_content = {
        "certificate_id": cert_id,
        "certificate_code": cert_code,
        "teilnehmer_did": enroll["teilnehmer_did"],
        "teilnehmer_name": enroll["teilnehmer_name"],
        "programme_id": enroll["programme_id"],
        "programme_name": enroll["programme_name"],
        "issued_date": now,
        "issuer_did": actor_did
    }

    # Seal to Ledger
    receipt_id, content_hash = seal_to_ledger(
        f"Zertifikat: {enroll['teilnehmer_name']} - {enroll['programme_name']}",
        "certificate-issued",
        cert_content,
        actor_did,
        "HIGH"
    )

    verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"

    # Store certificate
    conn.execute('''
        INSERT INTO zertifikat (id, enrollment_id, teilnehmer_did, programme_id,
            certificate_type, certificate_code, issued_date, issuer_did,
            content_hash, receipt_id, verify_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        cert_id, enrollment_id, enroll["teilnehmer_did"], enroll["programme_id"],
        data.get("certificate_type", "TEILNAHME"), cert_code, now, actor_did,
        content_hash, receipt_id, verify_url, "ACTIVE"
    ))

    # Update enrollment status
    conn.execute("UPDATE enrollment SET status = 'COMPLETED', actual_end_date = ? WHERE id = ?", (now, enrollment_id))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "ISSUED",
        "certificate_id": cert_id,
        "certificate_code": cert_code,
        "receipt_id": receipt_id,
        "content_hash": f"sha256:{content_hash}",
        "verify_url": verify_url,
        "teilnehmer": enroll["teilnehmer_name"],
        "programme": enroll["programme_name"]
    })

@app.route("/api/zertifikat/verify/<cert_code>", methods=["GET"])
def verify_certificate(cert_code):
    """Verify a certificate by code."""
    conn = get_db()
    cert = conn.execute('''
        SELECT z.*, t.name as teilnehmer_name, p.name_de as programme_name
        FROM zertifikat z
        JOIN teilnehmer t ON z.teilnehmer_did = t.did
        JOIN programme p ON z.programme_id = p.id
        WHERE z.certificate_code = ?
    ''', (cert_code,)).fetchone()
    conn.close()

    if not cert:
        return jsonify({"verified": False, "error": "Certificate not found"}), 404

    return jsonify({
        "verified": True,
        "certificate_code": cert["certificate_code"],
        "teilnehmer": cert["teilnehmer_name"],
        "programme": cert["programme_name"],
        "issued_date": cert["issued_date"],
        "content_hash": cert["content_hash"],
        "receipt_id": cert["receipt_id"],
        "verify_url": cert["verify_url"],
        "status": cert["status"]
    })

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS — PHO AKTION (Proof of Human Oversight)
# ═══════════════════════════════════════════════════════════════

@app.route("/api/aktion/log", methods=["POST"])
@require_i9
def log_pho_action():
    """Log a PHO action (decision made during training)."""
    data = request.get_json()
    actor_did = data.get("actor_did")

    action_id = generate_id("PHO")
    now = datetime.now(timezone.utc).isoformat()

    action_content = {
        "action_type": data.get("action_type"),
        "action_context": data.get("action_context"),
        "decision_made": data.get("decision_made"),
        "reasoning": data.get("reasoning"),
        "teilnehmer_did": actor_did
    }

    content_hash = hashlib.sha256(json.dumps(action_content, sort_keys=True).encode()).hexdigest()

    # Seal to Ledger
    receipt_id, _ = seal_to_ledger(
        f"PHO Action: {data.get('action_type')}",
        "pho-action",
        action_content,
        actor_did
    )

    conn = get_db()
    conn.execute('''
        INSERT INTO aktion_log (id, teilnehmer_did, action_type, action_context,
            decision_made, reasoning, timestamp, content_hash, receipt_id, sealed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        action_id, actor_did, data.get("action_type"), data.get("action_context"),
        data.get("decision_made"), data.get("reasoning"), now, content_hash,
        receipt_id, 1
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "SEALED",
        "action_id": action_id,
        "receipt_id": receipt_id,
        "content_hash": f"sha256:{content_hash}",
        "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}"
    })

@app.route("/api/aktion/history/<teilnehmer_did>", methods=["GET"])
def get_action_history(teilnehmer_did):
    """Get PHO action history for a participant."""
    conn = get_db()
    actions = conn.execute(
        "SELECT * FROM aktion_log WHERE teilnehmer_did = ? ORDER BY timestamp DESC",
        (teilnehmer_did,)
    ).fetchall()
    conn.close()

    return jsonify({
        "teilnehmer_did": teilnehmer_did,
        "actions": [dict(a) for a in actions],
        "count": len(actions)
    })

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS — STATISTICS
# ═══════════════════════════════════════════════════════════════

@app.route("/api/curriculum/<programme_id>", methods=["GET"])
def get_curriculum(programme_id):
    """Get full curriculum structure for a programme."""
    conn = get_db()

    # Get programme
    programme = conn.execute("SELECT * FROM programme WHERE id = ?", (programme_id,)).fetchone()
    if not programme:
        conn.close()
        return jsonify({"error": "Programme not found"}), 404

    # Get modules with lessons
    modules = conn.execute(
        "SELECT * FROM module WHERE programme_id = ? ORDER BY order_index",
        (programme_id,)
    ).fetchall()

    result = {
        "programme": dict(programme),
        "modules": []
    }

    for mod in modules:
        lessons = conn.execute(
            "SELECT * FROM lektion WHERE module_id = ? ORDER BY order_index",
            (mod["id"],)
        ).fetchall()

        module_data = dict(mod)
        module_data["lessons"] = [dict(l) for l in lessons]
        result["modules"].append(module_data)

    conn.close()
    return jsonify(result)

@app.route("/api/stats", methods=["GET"])
def get_statistics():
    """Get academy-wide statistics."""
    conn = get_db()

    stats = {
        "programme": {
            "total": conn.execute("SELECT COUNT(*) FROM programme").fetchone()[0],
            "active": conn.execute("SELECT COUNT(*) FROM programme WHERE status = 'ACTIVE'").fetchone()[0],
        },
        "ausbilder": {
            "total": conn.execute("SELECT COUNT(*) FROM ausbilder").fetchone()[0],
            "certified": conn.execute("SELECT COUNT(*) FROM ausbilder WHERE status = 'CERTIFIED'").fetchone()[0],
            "by_level": {}
        },
        "teilnehmer": {
            "total": conn.execute("SELECT COUNT(*) FROM teilnehmer").fetchone()[0],
            "active": conn.execute("SELECT COUNT(*) FROM teilnehmer WHERE status = 'ACTIVE'").fetchone()[0],
        },
        "enrollments": {
            "total": conn.execute("SELECT COUNT(*) FROM enrollment").fetchone()[0],
            "completed": conn.execute("SELECT COUNT(*) FROM enrollment WHERE status = 'COMPLETED'").fetchone()[0],
            "in_progress": conn.execute("SELECT COUNT(*) FROM enrollment WHERE status = 'ENROLLED'").fetchone()[0],
        },
        "zertifikate": {
            "total": conn.execute("SELECT COUNT(*) FROM zertifikat").fetchone()[0],
            "active": conn.execute("SELECT COUNT(*) FROM zertifikat WHERE status = 'ACTIVE'").fetchone()[0],
        },
        "pho_actions": {
            "total": conn.execute("SELECT COUNT(*) FROM aktion_log").fetchone()[0],
            "sealed": conn.execute("SELECT COUNT(*) FROM aktion_log WHERE sealed = 1").fetchone()[0],
        }
    }

    # Ausbilder by level
    levels = conn.execute(
        "SELECT certification_level, COUNT(*) as count FROM ausbilder GROUP BY certification_level"
    ).fetchall()
    for level in levels:
        stats["ausbilder"]["by_level"][level["certification_level"]] = level["count"]

    conn.close()

    return jsonify({
        "statistics": stats,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# ═══════════════════════════════════════════════════════════════
# STATIC PAGES
# ═══════════════════════════════════════════════════════════════

@app.route("/gruendungsausbilder")
@app.route("/gruendungsausbilder/")
def gruendungsausbilder():
    """WPH-AUS-004 — Gründungsausbilder Landing Page."""
    static_path = Path("/opt/windi/w-academy-001/static/gruendungsausbilder.html")
    if static_path.exists():
        return static_path.read_text()
    return "Page not found", 404

# ═══════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def dashboard():
    template_path = Path("/opt/windi/w-academy-001/templates/dashboard.html")
    if template_path.exists():
        return template_path.read_text()
    return render_template_string(DASHBOARD_HTML)

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="de" data-theme="noir">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>W-ACADEMY-001 — WINDI Institute</title>
    <style>
        :root {
            --bg: #0A0A10;
            --bg-card: #12121A;
            --gold: #C9A84C;
            --text: #E8E6E1;
            --text-dim: #9A9890;
            --border: #1A1A24;
            --green: #4ADE80;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 2rem;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { color: var(--gold); margin-bottom: 0.5rem; }
        .subtitle { color: var(--text-dim); margin-bottom: 2rem; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
        }
        .stat-value { font-size: 2.5rem; font-weight: 700; color: var(--gold); }
        .stat-label { color: var(--text-dim); font-size: 0.85rem; text-transform: uppercase; }
        .section { margin-bottom: 2rem; }
        .section-title { color: var(--gold); font-size: 0.9rem; text-transform: uppercase; margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }
        .endpoint-list { list-style: none; }
        .endpoint-list li { padding: 0.75rem 0; border-bottom: 1px solid var(--border); display: flex; gap: 1rem; align-items: center; }
        .method { background: var(--gold); color: var(--bg); padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600; min-width: 50px; text-align: center; }
        .method.get { background: #60A5FA; }
        .method.post { background: #4ADE80; }
        .path { font-family: monospace; color: var(--text); }
        .desc { color: var(--text-dim); font-size: 0.85rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>W-ACADEMY-001</h1>
        <p class="subtitle">WINDI Institute · Ausbildungsplattform · Kempten, Bavaria</p>

        <div class="stats-grid" id="stats"></div>

        <div class="section">
            <h2 class="section-title">API Endpoints</h2>
            <ul class="endpoint-list">
                <li><span class="method get">GET</span><span class="path">/health</span><span class="desc">Service health</span></li>
                <li><span class="method get">GET</span><span class="path">/api/programme</span><span class="desc">List programmes</span></li>
                <li><span class="method post">POST</span><span class="path">/api/programme</span><span class="desc">Create programme</span></li>
                <li><span class="method get">GET</span><span class="path">/api/ausbilder</span><span class="desc">List trainers</span></li>
                <li><span class="method post">POST</span><span class="path">/api/ausbilder</span><span class="desc">Register trainer</span></li>
                <li><span class="method post">POST</span><span class="path">/api/ausbilder/:id/certify</span><span class="desc">Certify trainer</span></li>
                <li><span class="method get">GET</span><span class="path">/api/teilnehmer</span><span class="desc">List participants</span></li>
                <li><span class="method post">POST</span><span class="path">/api/enrollment</span><span class="desc">Enroll participant</span></li>
                <li><span class="method post">POST</span><span class="path">/api/zertifikat/issue</span><span class="desc">Issue certificate</span></li>
                <li><span class="method get">GET</span><span class="path">/api/zertifikat/verify/:code</span><span class="desc">Verify certificate</span></li>
                <li><span class="method post">POST</span><span class="path">/api/aktion/log</span><span class="desc">Log PHO action</span></li>
                <li><span class="method get">GET</span><span class="path">/api/stats</span><span class="desc">Statistics</span></li>
            </ul>
        </div>
    </div>

    <script>
        async function loadStats() {
            const r = await fetch('/api/stats');
            const data = await r.json();
            const s = data.statistics;
            document.getElementById('stats').innerHTML = `
                <div class="stat-card"><div class="stat-value">${s.programme.total}</div><div class="stat-label">Programme</div></div>
                <div class="stat-card"><div class="stat-value">${s.ausbilder.certified}</div><div class="stat-label">Ausbilder</div></div>
                <div class="stat-card"><div class="stat-value">${s.teilnehmer.total}</div><div class="stat-label">Teilnehmer</div></div>
                <div class="stat-card"><div class="stat-value">${s.zertifikate.total}</div><div class="stat-label">Zertifikate</div></div>
                <div class="stat-card"><div class="stat-value">${s.pho_actions.sealed}</div><div class="stat-label">PHO Actions</div></div>
            `;
        }
        loadStats();
    </script>
</body>
</html>
'''

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║   W-ACADEMY-001 — WINDI Institute Ausbildungsplattform       ║
║   Port: {PORT}                                                 ║
║   Database: {DB_PATH}                              ║
║   Invariants: I9, I11, I14                                   ║
║   "Wissen vermitteln. Entscheidungen beweisen."              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host="0.0.0.0", port=PORT, debug=False)
