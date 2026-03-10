#!/usr/bin/env python3
"""
WINDI Forensic Vault v1.0.0
Port: 8106
Architecture: BaseHTTPRequestHandler + SQLite (read-only from Ledger)
Principle: "AI processes. Human decides. WINDI guarantees."

The Vault is the audit room. The Suite is the workspace.
Separation of Creation and Proof.
"""

import json
import os
import sqlite3
import hashlib
import math
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# === Configuration ===
PORT = int(os.environ.get("VAULT_PORT", 8106))
LEDGER_DB = os.environ.get("LEDGER_DB", "/opt/windi/data/forensic_ledger.sqlite3")
TEMPLATES_DB = os.environ.get("TEMPLATES_DB", "/opt/windi/data/windi_templates.sqlite3")
PAGE_SIZE = int(os.environ.get("PAGE_SIZE", 25))
VERSION = "1.1.0"
SERVICE_NAME = "WINDI Forensic Vault"

# === Database Helper ===
def get_db():
    """Read-only connection to the Forensic Ledger database."""
    conn = sqlite3.connect(f"file:{LEDGER_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

def safe_query(query, params=(), fetchone=False):
    """Execute a read-only query safely."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(query, params)
        if fetchone:
            row = cur.fetchone()
            result = dict(row) if row else None
        else:
            result = [dict(r) for r in cur.fetchall()]
        conn.close()
        return result
    except Exception as e:
        return {"error": str(e)}


# === Template Registry Database ===
def get_templates_db():
    """Read-write connection to the Templates database."""
    import re
    conn = sqlite3.connect(TEMPLATES_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_templates_db():
    """Initialize the templates database."""
    os.makedirs(os.path.dirname(TEMPLATES_DB), exist_ok=True)
    conn = sqlite3.connect(TEMPLATES_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            description     TEXT DEFAULT '',
            category        TEXT DEFAULT 'generic',
            isp             TEXT DEFAULT 'windi',
            lang            TEXT DEFAULT 'all',
            items_json      TEXT NOT NULL,
            html            TEXT DEFAULT '',
            preview         TEXT DEFAULT '',
            governance      TEXT DEFAULT 'MEDIUM',
            shared          INTEGER DEFAULT 1,
            created_by      TEXT DEFAULT 'html-builder',
            ledger_receipt  TEXT DEFAULT '',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print(f"[VAULT] Templates DB initialized: {TEMPLATES_DB}")

# Initialize templates DB on startup
init_templates_db()

def gen_template_id(name):
    """Generate unique template ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    slug = hashlib.md5(name.encode()).hexdigest()[:6].upper()
    return f"TMPL-{ts}-{slug}"


# === HTML Template ===
def vault_html():
    return '''<!DOCTYPE html>
<html lang="de" data-theme="noir">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WINDI Forensic Vault</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔐</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* === WINDI Design System: Noir + Klar === */
:root {
  --font-display: 'Bricolage Grotesque', sans-serif;
  --font-body: 'Outfit', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --radius: 8px;
  --transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

[data-theme="noir"] {
  --bg-primary: #0a0a0c;
  --bg-secondary: #111114;
  --bg-tertiary: #1a1a1f;
  --bg-card: #14141a;
  --border: #2a2a35;
  --border-accent: #c9a84c33;
  --text-primary: #e8e6e1;
  --text-secondary: #8a8890;
  --text-muted: #55545a;
  --gold: #c9a84c;
  --gold-dim: #c9a84c22;
  --gold-glow: #c9a84c15;
  --green: #4ade80;
  --green-dim: #4ade8020;
  --red: #f87171;
  --red-dim: #f8717120;
  --blue: #60a5fa;
  --blue-dim: #60a5fa20;
  --orange: #fb923c;
  --orange-dim: #fb923c20;
  --shadow: 0 4px 24px rgba(0,0,0,0.5);
}

[data-theme="klar"] {
  --bg-primary: #faf9f7;
  --bg-secondary: #f0eeeb;
  --bg-tertiary: #e8e5e0;
  --bg-card: #ffffff;
  --border: #d4d0ca;
  --border-accent: #8b741d33;
  --text-primary: #1a1917;
  --text-secondary: #6b6860;
  --text-muted: #9e9a92;
  --gold: #8b741d;
  --gold-dim: #8b741d15;
  --gold-glow: #8b741d08;
  --green: #16a34a;
  --green-dim: #16a34a15;
  --red: #dc2626;
  --red-dim: #dc262615;
  --blue: #2563eb;
  --blue-dim: #2563eb15;
  --orange: #ea580c;
  --orange-dim: #ea580c15;
  --shadow: 0 4px 24px rgba(0,0,0,0.08);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: var(--font-body);
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  line-height: 1.6;
  transition: background var(--transition), color var(--transition);
}

/* === Header === */
.vault-header {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  padding: 16px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
}

.vault-brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.vault-icon {
  width: 40px;
  height: 40px;
  background: var(--gold-dim);
  border: 1px solid var(--gold);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.vault-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.vault-subtitle {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 300;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-toggle {
  width: 36px;
  height: 36px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all var(--transition);
}

.theme-toggle:hover {
  border-color: var(--gold);
  color: var(--gold);
}

.lang-select {
  font-family: var(--font-mono);
  font-size: 11px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px 10px;
  cursor: pointer;
  outline: none;
}

.lang-select:focus { border-color: var(--gold); }

.back-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: color var(--transition);
}
.back-link:hover { color: var(--gold); }

/* === Stats Bar === */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  padding: 20px 32px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 18px;
  transition: border-color var(--transition);
}

.stat-card:hover { border-color: var(--border-accent); }

.stat-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--gold);
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 2px;
}

/* === Filters === */
.filters-section {
  padding: 16px 32px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  border-bottom: 1px solid var(--border);
}

.search-input {
  flex: 1;
  min-width: 240px;
  font-family: var(--font-mono);
  font-size: 13px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 14px 10px 38px;
  outline: none;
  transition: border-color var(--transition);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%238a8890' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: 12px center;
}

.search-input:focus { border-color: var(--gold); }
.search-input::placeholder { color: var(--text-muted); }

.filter-select {
  font-family: var(--font-body);
  font-size: 13px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 12px;
  cursor: pointer;
  outline: none;
  min-width: 140px;
}

.filter-select:focus { border-color: var(--gold); }

.filter-date {
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 9px 12px;
  outline: none;
}

.filter-date:focus { border-color: var(--gold); }

.btn-filter {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  background: var(--gold);
  color: #0a0a0c;
  border: none;
  border-radius: var(--radius);
  padding: 10px 20px;
  cursor: pointer;
  transition: all var(--transition);
  letter-spacing: 0.02em;
}

.btn-filter:hover { filter: brightness(1.1); transform: translateY(-1px); }

.btn-reset {
  font-family: var(--font-body);
  font-size: 13px;
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 9px 16px;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-reset:hover { border-color: var(--text-secondary); color: var(--text-secondary); }

/* === Table === */
.table-container {
  padding: 0 32px 32px;
  overflow-x: auto;
}

.vault-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
}

.vault-table th {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  text-align: left;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 73px;
  background: var(--bg-primary);
  z-index: 10;
  cursor: pointer;
  user-select: none;
}

.vault-table th:hover { color: var(--gold); }

.vault-table td {
  font-size: 13px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
  transition: background var(--transition);
}

.vault-table tr:hover td { background: var(--gold-glow); }

.hash-cell {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}

.hash-cell:hover { color: var(--gold); }

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.03em;
}

.status-REGISTERED { background: var(--green-dim); color: var(--green); }
.status-SEALED { background: var(--gold-dim); color: var(--gold); }
.status-PUBLISHED { background: var(--blue-dim); color: var(--blue); }
.status-FLAGGED { background: var(--red-dim); color: var(--red); }
.status-PENDING { background: var(--orange-dim); color: var(--orange); }

.type-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.timestamp {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}

.verify-btn {
  font-family: var(--font-mono);
  font-size: 10px;
  background: transparent;
  color: var(--gold);
  border: 1px solid var(--gold);
  border-radius: 4px;
  padding: 3px 10px;
  cursor: pointer;
  transition: all var(--transition);
  white-space: nowrap;
}

.verify-btn:hover {
  background: var(--gold);
  color: #0a0a0c;
}

/* === Pagination === */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  border-top: 1px solid var(--border);
  background: var(--bg-secondary);
}

.page-info {
  font-size: 13px;
  color: var(--text-secondary);
}

.page-info strong {
  color: var(--text-primary);
  font-weight: 600;
}

.page-controls {
  display: flex;
  gap: 6px;
}

.page-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition);
}

.page-btn:hover:not(:disabled) { border-color: var(--gold); color: var(--gold); }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.page-btn.active { background: var(--gold); color: #0a0a0c; border-color: var(--gold); font-weight: 600; }

/* === Detail Modal === */
.modal-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(4px);
  z-index: 1000;
  align-items: center;
  justify-content: center;
}

.modal-overlay.active { display: flex; }

.modal-content {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  width: 90%;
  max-width: 640px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: var(--shadow);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
}

.modal-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition);
}

.modal-close:hover { border-color: var(--red); color: var(--red); }

.modal-body {
  padding: 24px;
}

.detail-row {
  display: flex;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}

.detail-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  width: 140px;
  flex-shrink: 0;
}

.detail-value {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-primary);
  word-break: break-all;
}

.verify-result {
  margin-top: 16px;
  padding: 14px;
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-size: 12px;
  display: none;
}

.verify-pass {
  background: var(--green-dim);
  border: 1px solid var(--green);
  color: var(--green);
}

.verify-fail {
  background: var(--red-dim);
  border: 1px solid var(--red);
  color: var(--red);
}

/* === Empty State === */
.empty-state {
  text-align: center;
  padding: 80px 32px;
  color: var(--text-muted);
}

.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-title { font-family: var(--font-display); font-size: 20px; margin-bottom: 8px; color: var(--text-secondary); }
.empty-text { font-size: 14px; }

/* === Footer === */
.vault-footer {
  text-align: center;
  padding: 24px 32px;
  font-size: 11px;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
  font-family: var(--font-mono);
  letter-spacing: 0.05em;
}

/* === Loading === */
.loading-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(10,10,12,0.4);
  z-index: 500;
  align-items: center;
  justify-content: center;
}

.loading-overlay.active { display: flex; }

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: var(--gold);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* === Export Btn === */
.btn-export {
  font-family: var(--font-mono);
  font-size: 11px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 9px 16px;
  cursor: pointer;
  transition: all var(--transition);
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-export:hover { border-color: var(--gold); color: var(--gold); }

/* === Responsive === */
@media (max-width: 768px) {
  .vault-header { padding: 12px 16px; }
  .stats-bar { padding: 12px 16px; }
  .filters-section { padding: 12px 16px; }
  .table-container { padding: 0 16px 16px; }
  .pagination { padding: 12px 16px; flex-direction: column; gap: 12px; }
  .vault-table th, .vault-table td { padding: 10px 8px; font-size: 12px; }
  .hash-cell { max-width: 100px; }
}
</style>
</head>
<body>

<!-- Loading Overlay -->
<div class="loading-overlay" id="loadingOverlay">
  <div class="loading-spinner"></div>
</div>

<!-- Header -->
<header class="vault-header">
  <div class="vault-brand">
    <div class="vault-icon">🔐</div>
    <div>
      <div class="vault-title">Forensic Vault</div>
      <div class="vault-subtitle" data-i18n="subtitle">Governance Audit Room</div>
    </div>
  </div>
  <div class="header-controls">
    <a href="/desktop/" class="back-link" data-i18n="back">← Desktop</a>
    <select class="lang-select" id="langSelect" onchange="setLang(this.value)">
      <option value="de">DE</option>
      <option value="en" selected>EN</option>
      <option value="pt">PT</option>
    </select>
    <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">◐</button>
  </div>
</header>

<!-- Stats Bar -->
<div class="stats-bar" id="statsBar">
  <div class="stat-card">
    <div class="stat-value" id="totalReceipts">—</div>
    <div class="stat-label" data-i18n="totalSealed">Receipts Sealed</div>
  </div>
  <div class="stat-card">
    <div class="stat-value" id="todayReceipts">—</div>
    <div class="stat-label" data-i18n="today">Today</div>
  </div>
  <div class="stat-card">
    <div class="stat-value" id="docTypes">—</div>
    <div class="stat-label" data-i18n="docTypes">Document Types</div>
  </div>
  <div class="stat-card">
    <div class="stat-value" id="chainStatus">—</div>
    <div class="stat-label" data-i18n="chainIntegrity">Chain Integrity</div>
  </div>
</div>

<!-- Filters -->
<div class="filters-section">
  <input type="text" class="search-input" id="searchInput"
    data-placeholder-de="Receipt-ID, Hash oder Titel suchen..."
    data-placeholder-en="Search receipt ID, hash or title..."
    data-placeholder-pt="Buscar receipt ID, hash ou título..."
    placeholder="Search receipt ID, hash or title...">
  <select class="filter-select" id="filterType">
    <option value="" data-i18n-opt="allTypes">All Types</option>
    <option value="document">Document</option>
    <option value="communique">Communiqué</option>
    <option value="template">Template</option>
    <option value="export">Export</option>
  </select>
  <select class="filter-select" id="filterStatus">
    <option value="" data-i18n-opt="allStatus">All Status</option>
    <option value="REGISTERED">Registered</option>
    <option value="SEALED">Sealed</option>
    <option value="PUBLISHED">Published</option>
    <option value="FLAGGED">Flagged</option>
  </select>
  <input type="date" class="filter-date" id="filterDateFrom" title="From date">
  <input type="date" class="filter-date" id="filterDateTo" title="To date">
  <button class="btn-filter" onclick="applyFilters()" data-i18n="search">Search</button>
  <button class="btn-reset" onclick="resetFilters()" data-i18n="reset">Reset</button>
  <button class="btn-export" onclick="exportCSV()" title="Export CSV">
    <span>↓</span> CSV
  </button>
</div>

<!-- Table -->
<div class="table-container">
  <table class="vault-table" id="vaultTable">
    <thead>
      <tr>
        <th onclick="sortBy('id')" data-i18n="colId">Receipt ID</th>
        <th onclick="sortBy('doc_type')" data-i18n="colType">Type</th>
        <th onclick="sortBy('doc_name')" data-i18n="colTitle">Title</th>
        <th onclick="sortBy('content_hash')" data-i18n="colHash">Content Hash</th>
        <th onclick="sortBy('status')" data-i18n="colStatus">Status</th>
        <th onclick="sortBy('created_at')" data-i18n="colTimestamp">Timestamp</th>
        <th data-i18n="colActions">Actions</th>
      </tr>
    </thead>
    <tbody id="tableBody">
    </tbody>
  </table>

  <!-- Empty State -->
  <div class="empty-state" id="emptyState" style="display:none;">
    <div class="empty-icon">🔍</div>
    <div class="empty-title" data-i18n="noResults">No receipts found</div>
    <div class="empty-text" data-i18n="noResultsText">Adjust your filters or search query</div>
  </div>
</div>

<!-- Pagination -->
<div class="pagination" id="paginationBar">
  <div class="page-info" id="pageInfo"></div>
  <div class="page-controls" id="pageControls"></div>
</div>

<!-- Footer -->
<footer class="vault-footer">
  WINDI Forensic Vault v1.0.0 · Linhagem de Ferro · AI processes. Human decides. WINDI guarantees.
</footer>

<!-- Detail Modal -->
<div class="modal-overlay" id="detailModal" onclick="if(event.target===this)closeModal()">
  <div class="modal-content">
    <div class="modal-header">
      <div class="modal-title" data-i18n="receiptDetail">Receipt Detail</div>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-body" id="modalBody"></div>
  </div>
</div>

<script>
// === State ===
let currentPage = 1;
let totalPages = 1;
let totalCount = 0;
let sortField = 'created_at';
let sortDir = 'desc';
let currentLang = 'en';

// === i18n ===
const translations = {
  de: {
    subtitle: 'Governance-Prüfraum',
    back: '← Desktop',
    totalSealed: 'Receipts versiegelt',
    today: 'Heute',
    docTypes: 'Dokumenttypen',
    chainIntegrity: 'Kettenintegrität',
    search: 'Suchen',
    reset: 'Zurücksetzen',
    noResults: 'Keine Receipts gefunden',
    noResultsText: 'Filter oder Suchbegriff anpassen',
    colId: 'Receipt-ID',
    colType: 'Typ',
    colTitle: 'Titel',
    colHash: 'Content-Hash',
    colStatus: 'Status',
    colTimestamp: 'Zeitstempel',
    colActions: 'Aktionen',
    receiptDetail: 'Receipt-Detail',
    verify: 'Prüfen',
    allTypes: 'Alle Typen',
    allStatus: 'Alle Status',
    showing: 'Zeige',
    of: 'von',
    receipts: 'Receipts',
    copied: 'Kopiert!'
  },
  en: {
    subtitle: 'Governance Audit Room',
    back: '← Desktop',
    totalSealed: 'Receipts Sealed',
    today: 'Today',
    docTypes: 'Document Types',
    chainIntegrity: 'Chain Integrity',
    search: 'Search',
    reset: 'Reset',
    noResults: 'No receipts found',
    noResultsText: 'Adjust your filters or search query',
    colId: 'Receipt ID',
    colType: 'Type',
    colTitle: 'Title',
    colHash: 'Content Hash',
    colStatus: 'Status',
    colTimestamp: 'Timestamp',
    colActions: 'Actions',
    receiptDetail: 'Receipt Detail',
    verify: 'Verify',
    allTypes: 'All Types',
    allStatus: 'All Status',
    showing: 'Showing',
    of: 'of',
    receipts: 'receipts',
    copied: 'Copied!'
  },
  pt: {
    subtitle: 'Sala de Auditoria de Governança',
    back: '← Desktop',
    totalSealed: 'Receipts selados',
    today: 'Hoje',
    docTypes: 'Tipos de documento',
    chainIntegrity: 'Integridade da Cadeia',
    search: 'Buscar',
    reset: 'Limpar',
    noResults: 'Nenhum receipt encontrado',
    noResultsText: 'Ajuste filtros ou busca',
    colId: 'Receipt ID',
    colType: 'Tipo',
    colTitle: 'Título',
    colHash: 'Hash do Conteúdo',
    colStatus: 'Status',
    colTimestamp: 'Timestamp',
    colActions: 'Ações',
    receiptDetail: 'Detalhe do Receipt',
    verify: 'Verificar',
    allTypes: 'Todos os Tipos',
    allStatus: 'Todos os Status',
    showing: 'Mostrando',
    of: 'de',
    receipts: 'receipts',
    copied: 'Copiado!'
  }
};

function t(key) { return (translations[currentLang] || translations.en)[key] || key; }

function setLang(lang) {
  currentLang = lang;
  localStorage.setItem('vault_lang', lang);
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = t(key);
  });
  const si = document.getElementById('searchInput');
  si.placeholder = si.getAttribute(`data-placeholder-${lang}`) || si.getAttribute('data-placeholder-en');
}

// === Theme ===
function toggleTheme() {
  const html = document.documentElement;
  const next = html.getAttribute('data-theme') === 'noir' ? 'klar' : 'noir';
  html.setAttribute('data-theme', next);
  localStorage.setItem('vault_theme', next);
}

// === API ===
const API_BASE = window.location.origin + '/vault/api';

async function fetchReceipts() {
  showLoading(true);
  const params = new URLSearchParams();
  params.set('page', currentPage);
  params.set('per_page', 25);
  params.set('sort', sortField);
  params.set('dir', sortDir);

  const search = document.getElementById('searchInput').value.trim();
  if (search) params.set('q', search);

  const type = document.getElementById('filterType').value;
  if (type) params.set('doc_type', type);

  const status = document.getElementById('filterStatus').value;
  if (status) params.set('status', status);

  const dateFrom = document.getElementById('filterDateFrom').value;
  if (dateFrom) params.set('date_from', dateFrom);

  const dateTo = document.getElementById('filterDateTo').value;
  if (dateTo) params.set('date_to', dateTo);

  try {
    const res = await fetch(`${API_BASE}/receipts?${params}`);
    const data = await res.json();
    renderTable(data);
    renderPagination(data);
  } catch (err) {
    console.error('Fetch error:', err);
    document.getElementById('tableBody').innerHTML =
      `<tr><td colspan="7" style="text-align:center;color:var(--red);padding:40px;">Error loading receipts</td></tr>`;
  }
  showLoading(false);
}

async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    const data = await res.json();
    document.getElementById('totalReceipts').textContent = (data.total || 0).toLocaleString();
    document.getElementById('todayReceipts').textContent = (data.today || 0).toLocaleString();
    document.getElementById('docTypes').textContent = data.doc_types || '—';
    document.getElementById('chainStatus').textContent = data.chain_ok ? '✓ VALID' : '⚠ CHECK';
    document.getElementById('chainStatus').style.color =
      data.chain_ok ? 'var(--green)' : 'var(--red)';
  } catch (err) {
    console.error('Stats error:', err);
  }
}

// === Render ===
function renderTable(data) {
  const tbody = document.getElementById('tableBody');
  const receipts = data.receipts || [];
  totalCount = data.total || 0;
  totalPages = data.total_pages || 1;

  if (receipts.length === 0) {
    tbody.innerHTML = '';
    document.getElementById('emptyState').style.display = 'block';
    document.getElementById('vaultTable').querySelector('thead').style.display = 'none';
    return;
  }

  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('vaultTable').querySelector('thead').style.display = '';

  tbody.innerHTML = receipts.map(r => `
    <tr>
      <td><span class="hash-cell" onclick="copyText('${r.id || ''}')" title="Click to copy">${r.id || '—'}</span></td>
      <td><span class="type-badge">${r.doc_type || 'document'}</span></td>
      <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escHtml(r.title || '')}">${escHtml(r.doc_name || 'Untitled')}</td>
      <td><span class="hash-cell" onclick="copyText('${r.content_hash || ''}')" title="Click to copy">${truncHash(r.content_hash)}</span></td>
      <td><span class="status-badge status-${r.status || 'REGISTERED'}">${r.status || 'REGISTERED'}</span></td>
      <td><span class="timestamp">${fmtDate(r.created_at)}</span></td>
      <td>
        <button class="verify-btn" onclick="showDetail('${r.id || ''}')">${t('verify')}</button>
      </td>
    </tr>
  `).join('');
}

function renderPagination(data) {
  const info = document.getElementById('pageInfo');
  const from = ((currentPage - 1) * 25) + 1;
  const to = Math.min(currentPage * 25, totalCount);
  info.innerHTML = `${t('showing')} <strong>${from}–${to}</strong> ${t('of')} <strong>${totalCount.toLocaleString()}</strong> ${t('receipts')}`;

  const controls = document.getElementById('pageControls');
  let btns = '';

  btns += `<button class="page-btn" onclick="goPage(1)" ${currentPage<=1?'disabled':''}>«</button>`;
  btns += `<button class="page-btn" onclick="goPage(${currentPage-1})" ${currentPage<=1?'disabled':''}>‹</button>`;

  const start = Math.max(1, currentPage - 2);
  const end = Math.min(totalPages, currentPage + 2);
  for (let i = start; i <= end; i++) {
    btns += `<button class="page-btn ${i===currentPage?'active':''}" onclick="goPage(${i})">${i}</button>`;
  }

  btns += `<button class="page-btn" onclick="goPage(${currentPage+1})" ${currentPage>=totalPages?'disabled':''}>›</button>`;
  btns += `<button class="page-btn" onclick="goPage(${totalPages})" ${currentPage>=totalPages?'disabled':''}>»</button>`;

  controls.innerHTML = btns;
}

// === Actions ===
function goPage(p) {
  if (p < 1 || p > totalPages) return;
  currentPage = p;
  fetchReceipts();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function sortBy(field) {
  if (sortField === field) { sortDir = sortDir === 'asc' ? 'desc' : 'asc'; }
  else { sortField = field; sortDir = 'desc'; }
  currentPage = 1;
  fetchReceipts();
}

function applyFilters() {
  currentPage = 1;
  fetchReceipts();
}

function resetFilters() {
  document.getElementById('searchInput').value = '';
  document.getElementById('filterType').value = '';
  document.getElementById('filterStatus').value = '';
  document.getElementById('filterDateFrom').value = '';
  document.getElementById('filterDateTo').value = '';
  sortField = 'created_at';
  sortDir = 'desc';
  currentPage = 1;
  fetchReceipts();
}

async function showDetail(receiptId) {
  if (!receiptId) return;
  try {
    const res = await fetch(`${API_BASE}/receipt/${receiptId}`);
    const r = await res.json();
    if (r.error) { alert(r.error); return; }

    const body = document.getElementById('modalBody');
    body.innerHTML = `
      <div class="detail-row"><div class="detail-label">Receipt ID</div><div class="detail-value">${r.id || '—'}</div></div>
      <div class="detail-row"><div class="detail-label">Type</div><div class="detail-value">${r.doc_type || 'document'}</div></div>
      <div class="detail-row"><div class="detail-label">Title</div><div class="detail-value">${escHtml(r.doc_name || 'Untitled')}</div></div>
      <div class="detail-row"><div class="detail-label">Content Hash</div><div class="detail-value">${r.content_hash || '—'}</div></div>
      <div class="detail-row"><div class="detail-label">Bundle Hash</div><div class="detail-value">${r.bundle_hash || '—'}</div></div>
      <div class="detail-row"><div class="detail-label">Status</div><div class="detail-value"><span class="status-badge status-${r.status || 'REGISTERED'}">${r.status || 'REGISTERED'}</span></div></div>
      <div class="detail-row"><div class="detail-label">Created</div><div class="detail-value">${r.created_at || '—'}</div></div>
      <div class="detail-row"><div class="detail-label">Updated</div><div class="detail-value">${r.created_at || '—'}</div></div>
      ${r.metadata ? `<div class="detail-row"><div class="detail-label">Metadata</div><div class="detail-value" style="font-size:11px;">${escHtml(typeof r.metadata === 'string' ? r.metadata : JSON.stringify(r.metadata, null, 2))}</div></div>` : ''}
      <div id="verifyResult" class="verify-result"></div>
    `;
    document.getElementById('detailModal').classList.add('active');
  } catch (err) {
    alert('Error loading receipt detail');
  }
}

function closeModal() {
  document.getElementById('detailModal').classList.remove('active');
}

async function exportCSV() {
  try {
    const params = new URLSearchParams();
    params.set('format', 'csv');
    params.set('per_page', 10000);
    const search = document.getElementById('searchInput').value.trim();
    if (search) params.set('q', search);
    const type = document.getElementById('filterType').value;
    if (type) params.set('doc_type', type);
    const status = document.getElementById('filterStatus').value;
    if (status) params.set('status', status);

    const res = await fetch(`${API_BASE}/export?${params}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vault_export_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert('Export error');
  }
}

// === Helpers ===
function truncHash(h) { return h ? h.substring(0, 16) + '…' : '—'; }
function escHtml(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function fmtDate(d) {
  if (!d) return '—';
  try { return new Date(d).toLocaleString(currentLang === 'de' ? 'de-DE' : currentLang === 'pt' ? 'pt-BR' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }); }
  catch { return d; }
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => {
    const toast = document.createElement('div');
    toast.textContent = t('copied');
    toast.style.cssText = 'position:fixed;bottom:20px;right:20px;background:var(--gold);color:#0a0a0c;padding:8px 16px;border-radius:6px;font-size:13px;font-family:var(--font-mono);z-index:9999;animation:fadeIn 0.2s;';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 1500);
  });
}

function showLoading(show) {
  document.getElementById('loadingOverlay').classList.toggle('active', show);
}

// === Init ===
document.addEventListener('DOMContentLoaded', () => {
  // Restore preferences
  const savedTheme = localStorage.getItem('vault_theme');
  if (savedTheme) document.documentElement.setAttribute('data-theme', savedTheme);

  const savedLang = localStorage.getItem('vault_lang') || 'en';
  document.getElementById('langSelect').value = savedLang;
  setLang(savedLang);

  // Keyboard shortcut
  document.getElementById('searchInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') applyFilters();
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });

  // Load data
  fetchStats();
  fetchReceipts();
});
</script>
</body>
</html>'''


# === Request Handler ===
class VaultHandler(BaseHTTPRequestHandler):
    """WINDI Forensic Vault HTTP Handler."""

    def log_message(self, format, *args):
        """Structured logging."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"[{timestamp}] VAULT {args[0]}")

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_csv(self, csv_data, filename="export.csv"):
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(csv_data.encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        # Helper to get single param
        def p(key, default=None):
            return params.get(key, [default])[0]

        # === Routes ===
        if path in ("", "/", "/index.html", "/vault"):
            self._send_html(vault_html())

        elif path == "/health":
            try:
                conn = get_db()
                count = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
                conn.close()
                self._send_json({
                    "service": SERVICE_NAME,
                    "version": VERSION,
                    "status": "healthy",
                    "receipts": count,
                    "db": LEDGER_DB,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                self._send_json({"service": SERVICE_NAME, "status": "error", "error": str(e)}, 500)

        elif path == "/api/stats":
            self._handle_stats()

        elif path == "/api/receipts":
            self._handle_receipts(params)

        elif path.startswith("/api/receipt/"):
            id = path.split("/api/receipt/")[1]
            self._handle_receipt_detail(id)

        elif path == "/api/export":
            self._handle_export(params)

        # === Template Registry Routes ===
        elif path == "/api/templates":
            self._handle_templates_list(params)

        elif path == "/api/templates/categories":
            self._handle_template_categories()

        elif path.startswith("/api/templates/"):
            template_id = path.split("/api/templates/")[1]
            self._handle_template_detail(template_id)

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        """Handle POST requests for template creation."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/templates":
            self._handle_template_save()
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_DELETE(self):
        """Handle DELETE requests for template deletion."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/templates/"):
            template_id = path.split("/api/templates/")[1]
            self._handle_template_delete(template_id)
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_stats(self):
        """Return aggregate stats for the dashboard."""
        try:
            conn = get_db()
            cur = conn.cursor()

            total = cur.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]

            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            today = cur.execute(
                "SELECT COUNT(*) FROM receipts WHERE created_at LIKE ?",
                (f"{today_str}%",)
            ).fetchone()[0]

            # Distinct doc types
            types_row = cur.execute(
                "SELECT COUNT(DISTINCT doc_type) FROM receipts WHERE doc_type IS NOT NULL AND doc_type != ''"
            ).fetchone()
            doc_types = types_row[0] if types_row else 0

            # Simple chain integrity check: verify no NULL hashes
            broken = cur.execute(
                "SELECT COUNT(*) FROM receipts WHERE content_hash IS NULL OR content_hash = ''"
            ).fetchone()[0]

            conn.close()

            self._send_json({
                "total": total,
                "today": today,
                "doc_types": doc_types if doc_types > 0 else "—",
                "chain_ok": broken == 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_receipts(self, params):
        """Paginated, filtered, sorted receipt listing."""
        try:
            def p(key, default=None):
                return params.get(key, [default])[0]

            page = int(p("page", 1))
            per_page = min(int(p("per_page", 25)), 100)
            sort = p("sort", "created_at")
            direction = p("dir", "desc").upper()
            if direction not in ("ASC", "DESC"):
                direction = "DESC"

            # Whitelist sort fields
            allowed_sorts = ["id", "doc_type", "doc_name", "content_hash", "status", "created_at"]
            if sort not in allowed_sorts:
                sort = "created_at"

            conditions = []
            values = []

            # Search
            q = p("q")
            if q:
                conditions.append("(id LIKE ? OR content_hash LIKE ? OR doc_name LIKE ? OR bundle_hash LIKE ?)")
                like = f"%{q}%"
                values.extend([like, like, like, like])

            # Type filter
            doc_type = p("doc_type")
            if doc_type:
                conditions.append("doc_type = ?")
                values.append(doc_type)

            # Status filter
            status = p("status")
            if status:
                conditions.append("status = ?")
                values.append(status)

            # Date filters
            date_from = p("date_from")
            if date_from:
                conditions.append("created_at >= ?")
                values.append(f"{date_from}T00:00:00")

            date_to = p("date_to")
            if date_to:
                conditions.append("created_at <= ?")
                values.append(f"{date_to}T23:59:59")

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            conn = get_db()
            cur = conn.cursor()

            # Count
            count_sql = f"SELECT COUNT(*) FROM receipts WHERE {where_clause}"
            total = cur.execute(count_sql, values).fetchone()[0]

            # Fetch page
            offset = (page - 1) * per_page
            data_sql = f"""
                SELECT id, doc_type, doc_name, content_hash, bundle_hash,
                       status, created_at, metadata_json
                FROM receipts
                WHERE {where_clause}
                ORDER BY {sort} {direction}
                LIMIT ? OFFSET ?
            """
            cur.execute(data_sql, values + [per_page, offset])
            receipts = [dict(r) for r in cur.fetchall()]
            conn.close()

            total_pages = max(1, math.ceil(total / per_page))

            self._send_json({
                "receipts": receipts,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "sort": sort,
                "direction": direction
            })
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_receipt_detail(self, id):
        """Get full detail for a single receipt."""
        try:
            result = safe_query(
                "SELECT * FROM receipts WHERE id = ?",
                (id,),
                fetchone=True
            )
            if not result or "error" in (result if isinstance(result, dict) else {}):
                self._send_json({"error": "Receipt not found"}, 404)
            else:
                self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_export(self, params):
        """Export filtered receipts as CSV."""
        try:
            def p(key, default=None):
                return params.get(key, [default])[0]

            conditions = []
            values = []

            q = p("q")
            if q:
                conditions.append("(id LIKE ? OR content_hash LIKE ? OR doc_name LIKE ?)")
                like = f"%{q}%"
                values.extend([like, like, like])

            doc_type = p("doc_type")
            if doc_type:
                conditions.append("doc_type = ?")
                values.append(doc_type)

            status = p("status")
            if status:
                conditions.append("status = ?")
                values.append(status)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            per_page = min(int(p("per_page", 10000)), 50000)

            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                f"""SELECT id, doc_type, doc_name, content_hash, bundle_hash,
                           status, created_at
                    FROM receipts WHERE {where_clause}
                    ORDER BY created_at DESC LIMIT ?""",
                values + [per_page]
            )
            rows = cur.fetchall()
            conn.close()

            # Build CSV
            import io
            output = io.StringIO()
            output.write("id,doc_type,doc_name,content_hash,bundle_hash,status,created_at\n")
            for r in rows:
                row = dict(r)
                line = ",".join([
                    f'"{row.get("id", "")}"',
                    f'"{row.get("doc_type", "")}"',
                    f'"{(row.get("doc_name", "") or "").replace(chr(34), chr(39))}"',
                    f'"{row.get("content_hash", "")}"',
                    f'"{row.get("bundle_hash", "")}"',
                    f'"{row.get("status", "")}"',
                    f'"{row.get("created_at", "")}"'
                ])
                output.write(line + "\n")

            filename = f"vault_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self._send_csv(output.getvalue(), filename)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    # === Template Registry Handlers ===

    def _handle_templates_list(self, params):
        """List templates with optional filters."""
        try:
            def p(key, default=None):
                return params.get(key, [default])[0]

            conn = get_templates_db()
            cur = conn.cursor()

            query = "SELECT * FROM templates WHERE 1=1"
            values = []

            category = p("category")
            if category:
                query += " AND category = ?"
                values.append(category)

            lang = p("lang")
            if lang and lang != "all":
                query += " AND (lang = ? OR lang = 'all')"
                values.append(lang)

            isp = p("isp")
            if isp:
                query += " AND isp = ?"
                values.append(isp)

            shared_only = p("shared_only")
            if shared_only == "true":
                query += " AND shared = 1"

            query += " ORDER BY created_at DESC"

            cur.execute(query, values)
            rows = cur.fetchall()
            conn.close()

            templates = []
            for r in rows:
                t = dict(r)
                t["shared"] = bool(t.get("shared", 0))
                # Don't include full items_json and html in list view
                t.pop("items_json", None)
                t.pop("html", None)
                templates.append(t)

            self._send_json({"templates": templates, "total": len(templates)})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_template_detail(self, template_id):
        """Get full template detail including items."""
        try:
            conn = get_templates_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
            row = cur.fetchone()
            conn.close()

            if not row:
                self._send_json({"error": "Template not found"}, 404)
                return

            t = dict(row)
            t["shared"] = bool(t.get("shared", 0))
            # Parse items_json
            import re
            items_json = t.pop("items_json", "[]")
            try:
                t["items"] = json.loads(items_json)
            except:
                t["items"] = []

            self._send_json(t)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_template_categories(self):
        """List categories with counts."""
        try:
            conn = get_templates_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT category, COUNT(*) as count
                FROM templates GROUP BY category ORDER BY count DESC
            """)
            rows = cur.fetchall()
            conn.close()

            categories = [{"category": r[0], "count": r[1]} for r in rows]
            self._send_json({"categories": categories})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_template_save(self):
        """Save a new template."""
        try:
            import re
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            name = data.get("name", "").strip()
            if not name:
                self._send_json({"error": "Name is required"}, 400)
                return

            tid = gen_template_id(name)
            now = datetime.now(timezone.utc).isoformat()

            items = data.get("items", [])
            html = data.get("html", "")
            # Create text preview (strip HTML tags)
            preview_text = re.sub(r'<[^>]+>', '', html[:200])[:120] if html else ""

            conn = get_templates_db()
            conn.execute("""
                INSERT OR REPLACE INTO templates
                (id, name, description, category, isp, lang, items_json, html,
                 preview, governance, shared, created_by, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                tid,
                name,
                data.get("description", ""),
                data.get("category", "generic"),
                data.get("isp", "windi"),
                data.get("lang", "all"),
                json.dumps(items),
                html,
                preview_text,
                data.get("governance", "MEDIUM"),
                1 if data.get("shared", True) else 0,
                data.get("created_by", "html-builder"),
                now,
                now
            ))
            conn.commit()
            conn.close()

            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "template_id": tid,
                "name": name,
                "created_at": now
            }).encode())

        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_template_delete(self, template_id):
        """Delete a template."""
        try:
            conn = get_templates_db()
            conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))
            conn.commit()
            conn.close()

            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        except Exception as e:
            self._send_json({"error": str(e)}, 500)


# === Main ===
def main():
    print(f"""
╔══════════════════════════════════════════════╗
║  🔐 WINDI Forensic Vault v{VERSION}             ║
║  Port: {PORT}                                  ║
║  DB:   {LEDGER_DB}  ║
║  "AI processes. Human decides."              ║
╚══════════════════════════════════════════════╝
    """)

    # Verify DB exists
    if not os.path.exists(LEDGER_DB):
        print(f"⚠️  WARNING: Ledger DB not found at {LEDGER_DB}")
        print("   The Vault will start but queries will fail until the DB is available.")

    server = HTTPServer(("0.0.0.0", PORT), VaultHandler)
    print(f"[VAULT] Listening on http://0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[VAULT] Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
