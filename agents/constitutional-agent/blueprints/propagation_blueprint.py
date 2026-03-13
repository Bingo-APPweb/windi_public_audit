"""
W-PROV-002 — Propagation Index
WINDI Publishing House · Kempten, Bavaria · 2026-03-13

Observatório da circulação soberana de artefatos WINDI.
"O sistema observa artefatos, nunca pessoas." (C-PROV-001)

Endpoints:
  POST /propagation/event           — Registrar evento de propagação
  GET  /propagation/artifact/{id}   — Stats de um artefato
  GET  /propagation/network         — Mapa global de circulação
  GET  /propagation/feed            — Feed recente de eventos
  GET  /propagation/health          — Health check
  GET  /propagation/dashboard       — Observatory UI

Invariantes:
  C-PROV-001: Sistema observa artefatos, nunca pessoas
  C-PROV-002: Fingerprints são anônimos — sem dados pessoais
  C-PROV-003: Crawlers externos são opt-in e cirúrgicos
"""

from flask import Blueprint, request, jsonify, Response
import sqlite3
import hashlib
import json
import time
import os
from datetime import datetime, timezone
from typing import Optional
import urllib.request

# ═══════════════════════════════════════════════════════════════════════════════
# Blueprint Setup
# ═══════════════════════════════════════════════════════════════════════════════

propagation_bp = Blueprint('propagation', __name__, url_prefix='/propagation')

DB_PATH = os.environ.get('PROPAGATION_DB', '/opt/windi/data/propagation_index.db')
LEDGER_API = os.environ.get('LEDGER_API', 'http://localhost:8101')

# ═══════════════════════════════════════════════════════════════════════════════
# Database Schema
# ═══════════════════════════════════════════════════════════════════════════════

SCHEMA = """
CREATE TABLE IF NOT EXISTS propagation_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ledger_anchor   TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    source_type     TEXT NOT NULL,
    origin_domain   TEXT,
    country_hint    TEXT,
    verify_node     TEXT,
    client_fp       TEXT,
    timestamp       INTEGER NOT NULL,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS artifact_stats (
    ledger_anchor       TEXT PRIMARY KEY,
    total_verifications INTEGER DEFAULT 0,
    unique_domains      INTEGER DEFAULT 0,
    unique_countries    INTEGER DEFAULT 0,
    first_seen          TEXT,
    last_seen           TEXT,
    last_updated        TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS invariant_seals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    invariant_id    TEXT NOT NULL,
    ledger_receipt  TEXT NOT NULL,
    sealed_at       TEXT NOT NULL,
    hash            TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ledger ON propagation_events(ledger_anchor);
CREATE INDEX IF NOT EXISTS idx_domain ON propagation_events(origin_domain);
CREATE INDEX IF NOT EXISTS idx_ts ON propagation_events(timestamp);
"""

def get_db():
    """Get database connection with schema initialization."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def init_propagation_db():
    """Initialize database on blueprint registration."""
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        print(f"[W-PROV-002] DB initialized: {DB_PATH}")
    except Exception as e:
        print(f"[W-PROV-002] DB init error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def seal_milestone(ledger_anchor: str, milestone: str, metadata: dict):
    """Seal propagation milestone in Forensic Ledger."""
    try:
        receipt_id = f"WINDI-PROP-{ledger_anchor[:16]}-{milestone.upper()}"
        payload = {
            "id": receipt_id,
            "actor": "W-PROV-002",
            "app": "propagation-index",
            "doc_name": f"Propagation Milestone: {milestone}",
            "doc_type": "doc",
            "governance_level": "MEDIUM",
            "content_hash": hashlib.sha256(json.dumps(metadata).encode()).hexdigest(),
            "sge_score": 1.0,
            "metadata": {
                "milestone": milestone,
                "ledger_anchor": ledger_anchor,
                **metadata
            }
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{LEDGER_API}/api/receipts",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            return receipt_id
    except Exception as e:
        print(f"[W-PROV-002] Milestone seal failed: {e}")
        return None

def update_artifact_stats(ledger_anchor: str, domain: str, country: str):
    """Update aggregated stats for an artifact."""
    with get_db() as conn:
        c = conn.cursor()

        # Get current stats
        c.execute("SELECT * FROM artifact_stats WHERE ledger_anchor = ?", (ledger_anchor,))
        row = c.fetchone()

        now = now_iso()

        if not row:
            # First verification — seal milestone
            c.execute("""
                INSERT INTO artifact_stats
                (ledger_anchor, total_verifications, unique_domains, unique_countries, first_seen, last_seen)
                VALUES (?, 1, 1, ?, ?, ?)
            """, (ledger_anchor, 1 if country else 0, now, now))
            seal_milestone(ledger_anchor, "FIRST", {"origin_domain": domain, "country": country})
        else:
            # Count unique domains
            c.execute("""
                SELECT COUNT(DISTINCT origin_domain) as domains,
                       COUNT(DISTINCT country_hint) as countries
                FROM propagation_events WHERE ledger_anchor = ?
            """, (ledger_anchor,))
            counts = c.fetchone()

            new_total = row['total_verifications'] + 1

            # Update stats
            c.execute("""
                UPDATE artifact_stats SET
                    total_verifications = ?,
                    unique_domains = ?,
                    unique_countries = ?,
                    last_seen = ?,
                    last_updated = ?
                WHERE ledger_anchor = ?
            """, (new_total, counts['domains'], counts['countries'], now, now, ledger_anchor))

            # Check for milestones
            if new_total == 10:
                seal_milestone(ledger_anchor, "10TH", {"total": 10})
            elif new_total == 100:
                seal_milestone(ledger_anchor, "100TH", {"total": 100})
            elif new_total == 1000:
                seal_milestone(ledger_anchor, "1000TH", {"total": 1000})

        conn.commit()

# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@propagation_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as events FROM propagation_events")
            events = c.fetchone()['events']
            c.execute("SELECT COUNT(*) as artifacts FROM artifact_stats")
            artifacts = c.fetchone()['artifacts']
        db_ok = True
    except Exception:
        db_ok = False
        events = 0
        artifacts = 0

    return jsonify({
        "status": "GREEN" if db_ok else "YELLOW",
        "agent": "W-PROV-002",
        "version": "1.0.0",
        "db_events": events,
        "db_artifacts": artifacts,
        "invariants": ["C-PROV-001", "C-PROV-002", "C-PROV-003"],
        "timestamp": now_iso()
    })


@propagation_bp.route('/event', methods=['POST'])
def record_event():
    """
    POST /propagation/event
    Record a propagation event from Verify Public or other sources.
    """
    body = request.get_json(silent=True) or {}

    ledger_anchor = body.get('ledger_anchor', '').strip()
    event_type = body.get('event_type', 'VERIFICATION').upper()
    source_type = body.get('source_type', 'web')
    origin_domain = body.get('origin_domain', 'direct')
    country_hint = body.get('country_hint', '')
    verify_node = body.get('verify_node', '')
    client_fp = body.get('client_fp', '')[:8] if body.get('client_fp') else ''  # Max 8 chars (C-PROV-002)
    timestamp = body.get('timestamp', int(time.time()))

    if not ledger_anchor:
        return jsonify({"error": "ledger_anchor required"}), 400

    # Insert event
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO propagation_events
            (ledger_anchor, event_type, source_type, origin_domain, country_hint, verify_node, client_fp, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ledger_anchor, event_type, source_type, origin_domain, country_hint, verify_node, client_fp, timestamp))
        event_id = c.lastrowid
        conn.commit()

    # Update aggregated stats
    update_artifact_stats(ledger_anchor, origin_domain, country_hint)

    return jsonify({
        "status": "recorded",
        "event_id": event_id,
        "ledger_anchor": ledger_anchor
    }), 201


@propagation_bp.route('/artifact/<path:ledger_anchor>', methods=['GET'])
def get_artifact_stats(ledger_anchor: str):
    """
    GET /propagation/artifact/{ledger_anchor}
    Get propagation statistics for a specific artifact.
    """
    with get_db() as conn:
        c = conn.cursor()

        # Get stats
        c.execute("SELECT * FROM artifact_stats WHERE ledger_anchor = ?", (ledger_anchor,))
        stats = c.fetchone()

        if not stats:
            return jsonify({
                "ledger_anchor": ledger_anchor,
                "total_verifications": 0,
                "message": "No propagation events recorded yet"
            }), 404

        # Get top domains
        c.execute("""
            SELECT origin_domain, COUNT(*) as count
            FROM propagation_events
            WHERE ledger_anchor = ?
            GROUP BY origin_domain
            ORDER BY count DESC
            LIMIT 10
        """, (ledger_anchor,))
        top_domains = [{"domain": r['origin_domain'], "count": r['count']} for r in c.fetchall()]

        # Get geography
        c.execute("""
            SELECT country_hint, COUNT(*) as count
            FROM propagation_events
            WHERE ledger_anchor = ? AND country_hint != ''
            GROUP BY country_hint
            ORDER BY count DESC
        """, (ledger_anchor,))
        geography = {r['country_hint']: r['count'] for r in c.fetchall()}

    return jsonify({
        "ledger_anchor": ledger_anchor,
        "total_verifications": stats['total_verifications'],
        "unique_domains": stats['unique_domains'],
        "unique_countries": stats['unique_countries'],
        "first_seen": stats['first_seen'],
        "last_seen": stats['last_seen'],
        "top_domains": top_domains,
        "geography": geography
    })


@propagation_bp.route('/network', methods=['GET'])
def get_network_stats():
    """
    GET /propagation/network
    Get global network propagation statistics.
    """
    days = request.args.get('days', 7, type=int)
    domain_filter = request.args.get('domain', None)

    cutoff = int(time.time()) - (days * 86400)

    with get_db() as conn:
        c = conn.cursor()

        # Base query
        base_where = "WHERE timestamp > ?"
        params = [cutoff]

        if domain_filter:
            base_where += " AND origin_domain = ?"
            params.append(domain_filter)

        # Total events
        c.execute(f"SELECT COUNT(*) as total FROM propagation_events {base_where}", params)
        total_events = c.fetchone()['total']

        # Total artifacts
        c.execute(f"SELECT COUNT(DISTINCT ledger_anchor) as total FROM propagation_events {base_where}", params)
        total_artifacts = c.fetchone()['total']

        # Top artifacts
        c.execute(f"""
            SELECT ledger_anchor, COUNT(*) as verifications,
                   COUNT(DISTINCT origin_domain) as unique_domains
            FROM propagation_events
            {base_where}
            GROUP BY ledger_anchor
            ORDER BY verifications DESC
            LIMIT 20
        """, params)
        top_artifacts = [{
            "ledger_anchor": r['ledger_anchor'],
            "verifications": r['verifications'],
            "unique_domains": r['unique_domains']
        } for r in c.fetchall()]

        # Top domains
        c.execute(f"""
            SELECT origin_domain, COUNT(*) as count
            FROM propagation_events
            {base_where}
            GROUP BY origin_domain
            ORDER BY count DESC
            LIMIT 10
        """, params)
        top_domains = [{"domain": r['origin_domain'], "count": r['count']} for r in c.fetchall()]

        # Geography
        c.execute(f"""
            SELECT country_hint, COUNT(*) as count
            FROM propagation_events
            {base_where} AND country_hint != ''
            GROUP BY country_hint
            ORDER BY count DESC
        """, params)
        geography = {r['country_hint']: r['count'] for r in c.fetchall()}

    return jsonify({
        "period": f"{days}d",
        "total_events": total_events,
        "total_artifacts": total_artifacts,
        "top_artifacts": top_artifacts,
        "top_domains": top_domains,
        "geography": geography
    })


@propagation_bp.route('/feed', methods=['GET'])
def get_feed():
    """
    GET /propagation/feed
    Get recent propagation events feed.
    """
    limit = request.args.get('limit', 20, type=int)
    limit = min(limit, 100)  # Max 100
    ledger_anchor = request.args.get('ledger_anchor', None)

    with get_db() as conn:
        c = conn.cursor()

        if ledger_anchor:
            c.execute("""
                SELECT id, ledger_anchor, event_type, source_type, origin_domain, country_hint, timestamp
                FROM propagation_events
                WHERE ledger_anchor = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (ledger_anchor, limit))
        else:
            c.execute("""
                SELECT id, ledger_anchor, event_type, source_type, origin_domain, country_hint, timestamp
                FROM propagation_events
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        events = [{
            "event_id": r['id'],
            "ledger_anchor": r['ledger_anchor'],
            "event_type": r['event_type'],
            "source_type": r['source_type'],
            "origin_domain": r['origin_domain'],
            "country_hint": r['country_hint'],
            "timestamp": datetime.utcfromtimestamp(r['timestamp']).isoformat() + "Z"
        } for r in c.fetchall()]

        c.execute("SELECT COUNT(*) as total FROM propagation_events")
        total = c.fetchone()['total']

    return jsonify({
        "events": events,
        "total": total
    })


@propagation_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """
    GET /propagation/dashboard
    Observatory dashboard HTML - Complete visualization of artifact circulation.

    C-PROV-001: Sistema observa artefatos, nunca pessoas.
    """
    # Get stats for dashboard
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as total FROM propagation_events")
        total_events = c.fetchone()['total']
        c.execute("SELECT COUNT(*) as total FROM artifact_stats")
        total_artifacts = c.fetchone()['total']
        c.execute("SELECT COUNT(*) as total FROM propagation_events WHERE event_type='VERIFICATION'")
        total_verifications = c.fetchone()['total']
        c.execute("SELECT COUNT(*) as total FROM propagation_events WHERE event_type='SEED'")
        total_seeds = c.fetchone()['total']

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WINDI Propagation Observatory</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --gold: #C9A84C;
            --gold-dim: rgba(201,168,76,0.3);
            --bg-dark: #0a0a0f;
            --bg-card: rgba(255,255,255,0.03);
            --border: rgba(255,255,255,0.08);
            --text: #f0ece0;
            --text-dim: rgba(240,236,224,0.5);
            --green: #00ff96;
            --blue: #4da6ff;
            --purple: #a64dff;
        }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            font-family: 'JetBrains Mono', monospace;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.5;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
            border-bottom: 2px solid var(--gold);
            padding: 24px;
            text-align: center;
            position: relative;
        }}
        .header h1 {{ font-size: 20px; font-weight: 600; color: var(--gold); letter-spacing: 2px; }}
        .header p {{ font-size: 11px; color: var(--text-dim); margin-top: 6px; font-style: italic; }}
        .refresh-indicator {{
            position: absolute;
            top: 12px;
            right: 16px;
            font-size: 10px;
            color: var(--text-dim);
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .refresh-dot {{
            width: 6px;
            height: 6px;
            background: var(--green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}

        /* Stats Grid */
        .stats {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        @media (max-width: 1200px) {{ .stats {{ grid-template-columns: repeat(3, 1fr); }} }}
        @media (max-width: 768px) {{ .stats {{ grid-template-columns: repeat(2, 1fr); }} }}

        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            transition: border-color 0.2s;
        }}
        .stat-card:hover {{ border-color: var(--gold-dim); }}
        .stat-value {{
            font-size: 32px;
            font-weight: 600;
            color: var(--gold);
            font-variant-numeric: tabular-nums;
        }}
        .stat-label {{
            font-size: 10px;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 6px;
        }}
        .stat-card.verification .stat-value {{ color: var(--green); }}
        .stat-card.seed .stat-value {{ color: var(--blue); }}

        /* Two Column Layout */
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        @media (max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}

        .section {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }}
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }}
        .section-title {{
            font-size: 11px;
            font-weight: 600;
            color: var(--gold);
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .section-badge {{
            font-size: 9px;
            background: var(--gold-dim);
            color: var(--gold);
            padding: 3px 8px;
            border-radius: 4px;
        }}

        /* Top Artifacts List */
        .artifact-list {{ list-style: none; }}
        .artifact-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
            font-size: 12px;
        }}
        .artifact-item:last-child {{ border-bottom: none; }}
        .artifact-id {{
            color: var(--green);
            font-weight: 600;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .artifact-count {{
            color: var(--text-dim);
            font-size: 11px;
        }}
        .artifact-count strong {{
            color: var(--gold);
            font-weight: 600;
        }}

        /* Domains List */
        .domain-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
            font-size: 12px;
        }}
        .domain-item:last-child {{ border-bottom: none; }}
        .domain-name {{ color: var(--blue); }}
        .domain-bar {{
            flex: 1;
            margin: 0 12px;
            height: 4px;
            background: var(--border);
            border-radius: 2px;
            overflow: hidden;
        }}
        .domain-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--blue), var(--purple));
            border-radius: 2px;
        }}
        .domain-count {{ color: var(--text-dim); min-width: 40px; text-align: right; }}

        /* Geography */
        .geo-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .geo-tag {{
            background: var(--border);
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 11px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .geo-tag .flag {{ font-size: 14px; }}
        .geo-tag .count {{ color: var(--gold); font-weight: 600; }}

        /* Feed */
        .feed-section {{ margin-bottom: 20px; }}
        #feed {{ max-height: 400px; overflow-y: auto; }}
        .event {{
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
            display: grid;
            grid-template-columns: 60px 1fr 120px 60px;
            gap: 12px;
            align-items: center;
            font-size: 11px;
        }}
        .event:last-child {{ border-bottom: none; }}
        .event-time {{ color: var(--text-dim); }}
        .event-anchor {{
            color: var(--green);
            font-weight: 600;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .event-domain {{ color: var(--text-dim); text-align: right; }}
        .event-type {{
            font-size: 9px;
            padding: 2px 6px;
            border-radius: 3px;
            text-align: center;
        }}
        .event-type.verification {{ background: rgba(0,255,150,0.15); color: var(--green); }}
        .event-type.seed {{ background: rgba(77,166,255,0.15); color: var(--blue); }}

        .empty-state {{
            text-align: center;
            padding: 40px;
            color: var(--text-dim);
            font-size: 12px;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: var(--text-dim);
            font-size: 10px;
            border-top: 1px solid var(--border);
            margin-top: 20px;
        }}
        .dragon {{ font-size: 28px; margin-bottom: 12px; }}
        .invariants {{
            max-width: 600px;
            margin: 16px auto 0;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 8px;
        }}
        .invariant {{
            background: var(--border);
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 9px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>WINDI PROPAGATION OBSERVATORY</h1>
        <p>"Onde estão os seus artefatos soberanos"</p>
        <div class="refresh-indicator">
            <span class="refresh-dot"></span>
            <span id="last-update">Ao vivo</span>
        </div>
    </div>
    <div class="container">
        <!-- Stats Row -->
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="total-artifacts">{total_artifacts}</div>
                <div class="stat-label">Artefatos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-events">{total_events}</div>
                <div class="stat-label">Eventos Totais</div>
            </div>
            <div class="stat-card verification">
                <div class="stat-value" id="total-verifications">{total_verifications}</div>
                <div class="stat-label">Verificações</div>
            </div>
            <div class="stat-card seed">
                <div class="stat-value" id="total-seeds">{total_seeds}</div>
                <div class="stat-label">Seeds</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-domains">-</div>
                <div class="stat-label">Domínios</div>
            </div>
        </div>

        <!-- Two Column: Top Artifacts + Top Domains -->
        <div class="grid-2">
            <div class="section">
                <div class="section-header">
                    <span class="section-title">Top Artefatos</span>
                    <span class="section-badge">Por verificações</span>
                </div>
                <ul class="artifact-list" id="top-artifacts">
                    <li class="empty-state">Carregando...</li>
                </ul>
            </div>
            <div class="section">
                <div class="section-header">
                    <span class="section-title">Top Domínios</span>
                    <span class="section-badge">Origem das verificações</span>
                </div>
                <div id="top-domains-list">
                    <div class="empty-state">Carregando...</div>
                </div>
            </div>
        </div>

        <!-- Geography -->
        <div class="section" style="margin-bottom: 20px;">
            <div class="section-header">
                <span class="section-title">Geografia</span>
                <span class="section-badge">Países alcançados</span>
            </div>
            <div class="geo-grid" id="geography">
                <div class="empty-state" style="width:100%;">Carregando...</div>
            </div>
        </div>

        <!-- Live Feed -->
        <div class="section feed-section">
            <div class="section-header">
                <span class="section-title">Feed em Tempo Real</span>
                <span class="section-badge">Últimos 20 eventos</span>
            </div>
            <div id="feed">
                <div class="empty-state">Carregando...</div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="dragon">🐉</div>
        <p><strong>W-PROV-002</strong> · Propagation Index v1.0.0</p>
        <p style="margin-top:4px;">AI processes. Human decides. WINDI guarantees.</p>
        <div class="invariants">
            <span class="invariant">C-PROV-001: Observa artefatos, nunca pessoas</span>
            <span class="invariant">C-PROV-002: Fingerprints anônimos</span>
            <span class="invariant">C-PROV-003: Crawlers opt-in</span>
        </div>
    </div>

    <script>
        const COUNTRY_FLAGS = {{
            'BR': '🇧🇷', 'DE': '🇩🇪', 'PT': '🇵🇹', 'US': '🇺🇸', 'GB': '🇬🇧',
            'FR': '🇫🇷', 'ES': '🇪🇸', 'IT': '🇮🇹', 'NL': '🇳🇱', 'CH': '🇨🇭',
            'AT': '🇦🇹', 'BE': '🇧🇪', 'JP': '🇯🇵', 'CN': '🇨🇳', 'IN': '🇮🇳',
            'AU': '🇦🇺', 'CA': '🇨🇦', 'MX': '🇲🇽', 'AR': '🇦🇷', 'CL': '🇨🇱'
        }};

        function updateTime() {{
            const now = new Date();
            document.getElementById('last-update').textContent =
                now.toLocaleTimeString('de-DE', {{hour:'2-digit', minute:'2-digit', second:'2-digit'}});
        }}

        async function loadFeed() {{
            try {{
                const res = await fetch('/propagation/feed?limit=20');
                const data = await res.json();
                const feed = document.getElementById('feed');
                if (data.events.length === 0) {{
                    feed.innerHTML = '<div class="empty-state">Nenhum evento registado ainda.</div>';
                    return;
                }}
                feed.innerHTML = data.events.map(e => `
                    <div class="event">
                        <span class="event-time">${{new Date(e.timestamp).toLocaleTimeString('de-DE', {{hour:'2-digit',minute:'2-digit'}})}}</span>
                        <span class="event-anchor">${{e.ledger_anchor}}</span>
                        <span class="event-domain">${{e.origin_domain || 'direct'}}</span>
                        <span class="event-type ${{e.event_type?.toLowerCase() || 'verification'}}">${{e.event_type || 'VERIFY'}}</span>
                    </div>
                `).join('');
                updateTime();
            }} catch(e) {{
                document.getElementById('feed').innerHTML = '<div class="empty-state" style="color:#ff6b6b;">Erro ao carregar feed.</div>';
            }}
        }}

        async function loadNetwork() {{
            try {{
                const res = await fetch('/propagation/network?days=30');
                const data = await res.json();

                // Update domain count
                document.getElementById('total-domains').textContent = data.top_domains?.length || 0;

                // Top Artifacts
                const artifactsList = document.getElementById('top-artifacts');
                if (data.top_artifacts && data.top_artifacts.length > 0) {{
                    artifactsList.innerHTML = data.top_artifacts.slice(0,8).map(a => `
                        <li class="artifact-item">
                            <span class="artifact-id">${{a.ledger_anchor}}</span>
                            <span class="artifact-count"><strong>${{a.verifications}}</strong> verificações</span>
                        </li>
                    `).join('');
                }} else {{
                    artifactsList.innerHTML = '<li class="empty-state">Nenhum artefato ainda.</li>';
                }}

                // Top Domains
                const domainsList = document.getElementById('top-domains-list');
                if (data.top_domains && data.top_domains.length > 0) {{
                    const maxCount = Math.max(...data.top_domains.map(d => d.count));
                    domainsList.innerHTML = data.top_domains.slice(0,8).map(d => `
                        <div class="domain-item">
                            <span class="domain-name">${{d.domain}}</span>
                            <div class="domain-bar">
                                <div class="domain-bar-fill" style="width:${{(d.count/maxCount)*100}}%"></div>
                            </div>
                            <span class="domain-count">${{d.count}}</span>
                        </div>
                    `).join('');
                }} else {{
                    domainsList.innerHTML = '<div class="empty-state">Nenhum domínio ainda.</div>';
                }}

                // Geography
                const geoGrid = document.getElementById('geography');
                const geo = data.geography || {{}};
                const countries = Object.entries(geo).sort((a,b) => b[1] - a[1]);
                if (countries.length > 0) {{
                    geoGrid.innerHTML = countries.map(([code, count]) => `
                        <div class="geo-tag">
                            <span class="flag">${{COUNTRY_FLAGS[code] || '🌍'}}</span>
                            <span>${{code}}</span>
                            <span class="count">${{count}}</span>
                        </div>
                    `).join('');
                }} else {{
                    geoGrid.innerHTML = '<div class="empty-state" style="width:100%;">Nenhum país detectado ainda.</div>';
                }}

            }} catch(e) {{
                console.error('Network load error:', e);
            }}
        }}

        // Initial load
        loadFeed();
        loadNetwork();

        // Auto-refresh every 30 seconds
        setInterval(loadFeed, 30000);
        setInterval(loadNetwork, 60000);
        setInterval(updateTime, 1000);
    </script>
</body>
</html>'''

    return Response(html, mimetype='text/html')
