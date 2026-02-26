#!/usr/bin/env python3
"""
WINDI Communiqué Engine — Multimedia Extension v1.0
=====================================================
Extends the Communiqué Engine (:8105) with multimedia support.

New endpoints:
  POST /api/communique/multimedia    — Create multimedia communiqué
  GET  /communique/{id}/evidence     — Evidence gallery page
  GET  /communique/{id}/evidence/verify — Verify evidence package
  GET  /communique/{id}/evidence/manifest — Get manifest.json

Integration:
  Import into existing communique_engine.py:
    from communique_multimedia import register_multimedia_handlers

Deploy:
  cp communique_multimedia.py /opt/windi/communique/
  # Then import in main engine

Part of WINDI Communiqué Multimedia Infrastructure.
"The evidence speaks. The hash proves. The Ledger remembers."
"""

import os
import json
import hashlib
import zipfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Import validator (same directory)
try:
    from evidence_validator import validate_manifest, validate_bundle
except ImportError:
    validate_manifest = None
    validate_bundle = None

# ─── CONFIGURATION ───────────────────────────────────────────────────────


# ─── DB BUNDLE HASH FALLBACK ─────────────────────────────────
def _get_db_bundle_hash(com_id):
    """Fetch bundle_hash from DB — manifest can't contain its own zip hash."""
    try:
        import sqlite3
        db_path = "/opt/windi/communique/data/communiques.db"
        conn = sqlite3.connect(db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        cur = conn.execute("SELECT bundle_hash FROM communiques WHERE id=?", (com_id,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row and row[0] else None
    except Exception:
        return None

EVIDENCE_DIR = "/opt/windi/communique/packages"
LEDGER_URL = "http://127.0.0.1:8101"

IMPACT_COLORS = {
    "LOW": "#27AE60",
    "MEDIUM": "#F39C12",
    "HIGH": "#E74C3C",
    "CRITICAL": "#8E44AD",
}

STATUS_CLASSES = {
    "PUBLISHED": "status-verified",
    "DRAFT": "status-archived",
    "REVOKED": "status-revoked",
    "PENDING": "status-archived",
}


# ─── HELPER FUNCTIONS ────────────────────────────────────────────────────

def load_evidence_manifest(com_id):
    """Load manifest.json from the evidence package for a communiqué."""
    # Try to find the .jmpg file
    packages_dir = Path(EVIDENCE_DIR)
    if not packages_dir.exists():
        return None

    # Search by communiqué ID in manifest
    for jmpg_path in packages_dir.glob("*.jmpg"):
        try:
            with zipfile.ZipFile(jmpg_path, "r") as zf:
                manifest = json.loads(zf.read("manifest.json"))
                if manifest.get("communique", {}).get("id") == com_id:
                    return manifest, jmpg_path
        except (zipfile.BadZipFile, json.JSONDecodeError, KeyError):
            continue

    return None, None


def verify_evidence_package(com_id):
    """Verify the evidence package for a communiqué."""
    manifest, jmpg_path = load_evidence_manifest(com_id)

    if manifest is None:
        return {
            "communique_id": com_id,
            "has_evidence": False,
            "error": "No evidence package found"
        }

    result = {
        "communique_id": com_id,
        "has_evidence": True,
        "evidence_id": manifest.get("evidence_id"),
        "bundle_path": str(jmpg_path),
        "total_files": manifest.get("evidence", {}).get("total_files", 0),
        "total_bytes": manifest.get("evidence", {}).get("total_bytes", 0),
        "content_hash": manifest.get("hashes", {}).get("content_hash"),
        "bundle_hash": manifest.get("hashes", {}).get("bundle_hash") or _get_db_bundle_hash(com_id),
    }

    # Validate with schema validator if available
    if validate_bundle and jmpg_path:
        validation = validate_bundle(jmpg_path)
        result["schema_valid"] = validation.valid
        result["schema_errors"] = len(validation.errors)
        result["schema_warnings"] = len(validation.warnings)
        result["invariant_violations"] = len(validation.invariant_violations)
    else:
        # Manual verification
        try:
            with zipfile.ZipFile(jmpg_path, "r") as zf:
                file_hashes = []
                files_ok = True

                for fentry in manifest.get("evidence", {}).get("files", []):
                    fpath = f"evidence/{fentry['filename']}"
                    try:
                        data = zf.read(fpath)
                        computed = hashlib.sha256(data).hexdigest()
                        expected = fentry.get("sha256", "")

                        if "..." not in expected and computed != expected:
                            files_ok = False
                        file_hashes.append(computed)
                    except KeyError:
                        files_ok = False

                # Verify content hash chain
                combined = "".join(file_hashes)
                computed_content = hashlib.sha256(combined.encode("utf-8")).hexdigest()
                expected_content = manifest.get("hashes", {}).get("content_hash", "")

                content_match = "..." in expected_content or computed_content == expected_content

                result["files_verified"] = files_ok
                result["content_hash_match"] = content_match
                result["computed_content_hash"] = computed_content

        except Exception as e:
            result["error"] = str(e)
            result["files_verified"] = False
            result["content_hash_match"] = False

    result["verification_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return result


def register_to_ledger(manifest):
    """Register evidence package hashes in the Forensic Ledger (:8101)."""
    payload = {
        "doc_type": "COMMUNIQUE_MULTIMEDIA",
        "content_hash": manifest.get("hashes", {}).get("content_hash"),
        "bundle_hash": manifest.get("hashes", {}).get("bundle_hash") or _get_db_bundle_hash(com_id),
        "impact_level": manifest.get("governance", {}).get("impact_level", "HIGH"),
        "category": manifest.get("communique", {}).get("category", "INCIDENT"),
        "metadata": {
            "evidence_id": manifest.get("evidence_id"),
            "communique_id": manifest.get("communique", {}).get("id"),
            "total_files": manifest.get("evidence", {}).get("total_files", 0),
        }
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{LEDGER_URL}/api/receipts",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "registered": False}


# ─── HTML GENERATORS ─────────────────────────────────────────────────────

def generate_evidence_gallery_html(com_id, manifest):
    """Generate the evidence gallery HTML page for a multimedia communiqué."""

    files = manifest.get("evidence", {}).get("files", [])
    evidence_id = manifest.get("evidence_id", "")

    # Build evidence cards
    evidence_cards = ""
    for f in files:
        ftype = f.get("type", "")
        fid = f.get("id", "")
        caption_de = f.get("caption", {}).get("de", "")
        caption_en = f.get("caption", {}).get("en", "")
        caption_pt = f.get("caption", {}).get("pt", "")
        sha = f.get("sha256", "")[:24]
        source = f.get("source", "unknown")
        captured = f.get("captured_at", "")

        if ftype == "image":
            dims = f.get("dimensions", "unknown")
            fbytes = f.get("bytes", 0)
            size_str = f"{fbytes / 1024:.0f} KB" if fbytes < 1024*1024 else f"{fbytes / (1024*1024):.1f} MB"
            icon = "🖼️"
            meta = f"{dims} · {f.get('mime_type', 'image/png').split('/')[-1].upper()} · {size_str}"
        elif ftype == "video":
            dur = f.get("duration_seconds")
            dur_str = f"{dur // 60}:{dur % 60:02d}" if dur else "??:??"
            icon = "🎬"
            meta = f"{dur_str} · {f.get('mime_type', 'video/mp4').split('/')[-1].upper()}"
        elif ftype == "document":
            icon = "📄"
            meta = f"PDF · {f.get('bytes', 0) / 1024:.0f} KB"
        else:
            icon = "🔊"
            meta = f"{f.get('mime_type', 'audio')}"

        # Source badge color
        source_colors = {
            "operator": "#3498DB",
            "sentinel": "#C9A84C",
            "audit": "#9B59B6",
            "system": "#27AE60",
            "external": "#E67E22"
        }
        src_color = source_colors.get(source, "#666")

        evidence_cards += f"""
    <div class="evidence-card">
      <div class="ev-header">
        <span class="ev-icon">{icon}</span>
        <span class="ev-id" style="color:var(--gold);">[{fid}]</span>
        <span class="ev-meta">{meta}</span>
        <span class="ev-source" style="background:{src_color}22;color:{src_color};border:1px solid {src_color}44;">
          {source}
        </span>
      </div>
      <div class="ev-placeholder" data-type="{ftype}">
        <span>{icon} {fid}</span>
        <small data-de>Evidenz im Paket · Nicht eingebettet</small>
        <small data-en>Evidence in package · Not embedded</small>
        <small data-pt>Evidência no pacote · Não incorporada</small>
      </div>
      <div class="ev-caption">
        <span data-de>{caption_de}</span>
        <span data-en>{caption_en}</span>
        <span data-pt>{caption_pt}</span>
      </div>
      <div class="ev-hash">
        SHA-256: {sha}… · {captured[:10] if captured else ''}
      </div>
    </div>
"""

    total_files = manifest.get("evidence", {}).get("total_files", 0)
    total_bytes = manifest.get("evidence", {}).get("total_bytes", 0)
    size_str = f"{total_bytes / 1024:.0f} KB" if total_bytes < 1024*1024 else f"{total_bytes / (1024*1024):.1f} MB"
    content_hash = manifest.get("hashes", {}).get("content_hash", "")[:24]
    _bh = manifest.get("hashes", {}).get("bundle_hash") or _get_db_bundle_hash(com_id)
    bundle_hash = _bh[:24] if _bh else "pending"

    html = f"""<!DOCTYPE html>
<html lang="de" data-theme="dark" data-lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{com_id} — Evidence Gallery</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --gold: #C9A84C; --gold-dim: #8B7535;
  --noir-bg: #0D0D0D; --noir-surface: #1A1A1A; --noir-card: #222222;
  --noir-border: #333333; --noir-text: #E8E8E8; --noir-muted: #999999;
  --klar-bg: #FAFAF8; --klar-surface: #FFFFFF; --klar-card: #F5F5F0;
  --klar-border: #E0E0D8; --klar-text: #1A1A1A; --klar-muted: #666666;
}}
[data-theme="dark"] {{
  --bg: var(--noir-bg); --surface: var(--noir-surface); --card: var(--noir-card);
  --border: var(--noir-border); --text: var(--noir-text); --muted: var(--noir-muted);
}}
[data-theme="light"] {{
  --bg: var(--klar-bg); --surface: var(--klar-surface); --card: var(--klar-card);
  --border: var(--klar-border); --text: var(--klar-text); --muted: var(--klar-muted);
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Outfit', sans-serif; background: var(--bg); color: var(--text); line-height: 1.7; }}
.container {{ max-width: 800px; margin: 0 auto; padding: 24px 20px; }}
.header {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 0; border-bottom: 2px solid var(--gold); margin-bottom: 24px;
  flex-wrap: wrap; gap: 8px;
}}
.header-brand {{ display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--text); }}
.header-logo {{
  width: 40px; height: 40px; background: var(--gold); color: var(--noir-bg);
  display: flex; align-items: center; justify-content: center;
  font-family: 'Bricolage Grotesque', serif; font-weight: 700; font-size: 20px; border-radius: 4px;
}}
.header-title {{ font-family: 'Bricolage Grotesque', serif; font-weight: 700; font-size: 18px; }}
.header-subtitle {{ font-size: 11px; color: var(--muted); letter-spacing: 2px; text-transform: uppercase; }}
.controls {{ display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }}
.controls button {{
  background: var(--card); color: var(--text); border: 1px solid var(--border);
  padding: 6px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
}}
.controls button:hover {{ border-color: var(--gold); }}

/* Evidence header section */
.ev-section-header {{
  border: 1px solid var(--gold); border-radius: 8px; padding: 16px 20px;
  margin-bottom: 24px; background: linear-gradient(135deg, rgba(201,168,76,0.08), transparent);
}}
.ev-section-title {{
  font-family: 'Bricolage Grotesque', serif; font-weight: 700; font-size: 20px;
  margin-bottom: 8px;
}}
.ev-stats {{
  display: flex; gap: 16px; flex-wrap: wrap;
  font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--muted);
}}
.ev-stat {{ display: flex; align-items: center; gap: 6px; }}

/* Evidence cards */
.evidence-card {{
  border: 1px solid var(--border); border-radius: 8px; padding: 16px;
  margin-bottom: 16px; background: var(--card); transition: border-color 0.2s;
}}
.evidence-card:hover {{ border-color: var(--gold); }}
.ev-header {{
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  margin-bottom: 12px; font-family: 'JetBrains Mono', monospace; font-size: 12px;
}}
.ev-icon {{ font-size: 18px; }}
.ev-id {{ font-weight: 600; }}
.ev-meta {{ color: var(--muted); }}
.ev-source {{
  padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 1px;
}}
.ev-placeholder {{
  background: var(--surface); border: 1px dashed var(--border);
  border-radius: 6px; padding: 32px 16px; text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  margin-bottom: 12px; color: var(--muted);
}}
.ev-placeholder span {{ font-size: 20px; }}
.ev-placeholder small {{ font-size: 11px; }}
.ev-caption {{ font-size: 14px; margin-bottom: 8px; }}
.ev-hash {{
  font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--muted);
}}

/* Package block */
.package-block {{
  border: 1px solid var(--gold); border-radius: 8px; padding: 20px;
  margin-top: 24px; font-family: 'JetBrains Mono', monospace;
  background: linear-gradient(135deg, rgba(201,168,76,0.05), transparent);
}}
.package-grid {{
  display: grid; grid-template-columns: auto 1fr; gap: 8px 16px; font-size: 13px;
}}
.package-label {{ color: var(--muted); }}
.package-value {{ word-break: break-all; }}

/* Actions */
.actions {{ display: flex; gap: 12px; margin: 24px 0; flex-wrap: wrap; }}
.action-btn {{
  display: inline-flex; align-items: center; gap: 6px; padding: 10px 20px;
  background: var(--card); color: var(--text); border: 1px solid var(--border);
  border-radius: 6px; text-decoration: none; font-size: 13px; transition: all 0.2s;
}}
.action-btn:hover {{ border-color: var(--gold); color: var(--gold); }}
.action-btn.primary {{ background: var(--gold); color: var(--noir-bg); border-color: var(--gold); font-weight: 600; }}

.footer {{
  margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border);
  text-align: center; font-size: 12px; color: var(--muted);
}}
.footer .principle {{ color: var(--gold); font-style: italic; margin-top: 4px; }}

[data-lang="de"] [data-en], [data-lang="de"] [data-pt] {{ display: none; }}
[data-lang="en"] [data-de], [data-lang="en"] [data-pt] {{ display: none; }}
[data-lang="pt"] [data-de], [data-lang="pt"] [data-en] {{ display: none; }}

@media (max-width: 600px) {{
  .ev-section-title {{ font-size: 18px; }}
  .ev-stats {{ flex-direction: column; gap: 6px; }}
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <a href="/communique/{com_id}" class="header-brand">
      <div class="header-logo">W</div>
      <div>
        <div class="header-title">EVIDENCE GALLERY</div>
        <div class="header-subtitle">{com_id}</div>
      </div>
    </a>
    <div class="controls">
      <a href="/communique/{com_id}" style="color:var(--muted);text-decoration:none;font-size:13px;">
        <span data-de>← Communiqué</span>
        <span data-en>← Communiqué</span>
        <span data-pt>← Communiqué</span>
      </a>
      <button onclick="setLang('de')">DE</button>
      <button onclick="setLang('en')">EN</button>
      <button onclick="setLang('pt')">PT</button>
      <button onclick="toggleTheme()">◐</button>
    </div>
  </div>

  <div class="ev-section-header">
    <div class="ev-section-title">
      📎 <span data-de>Beweismaterial</span><span data-en>Evidence Material</span><span data-pt>Material de Evidência</span>
    </div>
    <div class="ev-stats">
      <div class="ev-stat">📦 {evidence_id}</div>
      <div class="ev-stat">📁 {total_files}
        <span data-de>Dateien</span><span data-en>files</span><span data-pt>arquivos</span>
      </div>
      <div class="ev-stat">💾 {size_str}</div>
      <div class="ev-stat">🔗 content: {content_hash}…</div>
    </div>
  </div>

  {evidence_cards}

  <div class="package-block">
    <div style="font-family:'Bricolage Grotesque',serif;font-weight:700;font-size:14px;color:var(--gold);margin-bottom:12px;letter-spacing:2px;">
      📦 <span data-de>BEWEISPAKET</span><span data-en>EVIDENCE PACKAGE</span><span data-pt>PACOTE DE EVIDÊNCIA</span>
    </div>
    <div class="package-grid">
      <span class="package-label">Bundle:</span>
      <span class="package-value" style="color:var(--gold);">{evidence_id}.jmpg</span>
      <span class="package-label">content_hash:</span>
      <span class="package-value" style="font-size:11px;">{manifest.get('hashes', {}).get('content_hash', 'N/A')}</span>
      <span class="package-label">bundle_hash:</span>
      <span class="package-value" style="font-size:11px;">{manifest.get('hashes', {}).get('bundle_hash') or _get_db_bundle_hash(com_id) or 'pending'}</span>
      <span class="package-label">Schema:</span>
      <span class="package-value">{manifest.get('$schema', 'N/A')}</span>
    </div>
  </div>

  <div class="actions">
    <a href="/communique/{com_id}/evidence/verify" class="action-btn primary">
      🔍 <span data-de>Paket verifizieren</span><span data-en>Verify Package</span><span data-pt>Verificar Pacote</span>
    </a>
    <a href="/communique/{com_id}/evidence/manifest" class="action-btn">
      📋 manifest.json
    </a>
    <a href="/communique/{com_id}" class="action-btn">
      ← <span data-de>Communiqué</span><span data-en>Communiqué</span><span data-pt>Communiqué</span>
    </a>
  </div>

  <div class="footer">
    <div>WINDI Publishing House · Kempten, Bavaria</div>
    <div class="principle">"The evidence speaks. The hash proves. The Ledger remembers."</div>
  </div>
</div>

<script>
function toggleTheme() {{
  const html = document.documentElement;
  html.dataset.theme = html.dataset.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('windi-theme', html.dataset.theme);
}}
function setLang(lang) {{
  document.documentElement.dataset.lang = lang;
  localStorage.setItem('windi-lang', lang);
}}
(function() {{
  const t = localStorage.getItem('windi-theme');
  const l = localStorage.getItem('windi-lang');
  if (t) document.documentElement.dataset.theme = t;
  if (l) document.documentElement.dataset.lang = l;
}})();
</script>
</body></html>"""

    return html


# ─── HANDLER REGISTRATION ───────────────────────────────────────────────

def register_multimedia_handlers(handler_class):
    """
    Register multimedia handlers on the Communiqué Engine HTTP handler.

    Usage in communique_engine.py:
        from communique_multimedia import register_multimedia_handlers
        register_multimedia_handlers(CommuniqueHandler)

    This adds route handling for:
        GET /communique/{id}/evidence
        GET /communique/{id}/evidence/verify
        GET /communique/{id}/evidence/manifest
    """

    original_do_GET = handler_class.do_GET

    def extended_do_GET(self):
        path = self.path.rstrip("/")

        # Evidence gallery page
        if "/evidence" in path and path.endswith("/evidence"):
            com_id = path.split("/communique/")[1].split("/evidence")[0]
            manifest, _ = load_evidence_manifest(com_id)

            if manifest is None:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "No evidence package found",
                    "communique_id": com_id
                }).encode())
                return

            html = generate_evidence_gallery_html(com_id, manifest)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # Evidence verification
        if "/evidence/verify" in path:
            com_id = path.split("/communique/")[1].split("/evidence")[0]
            result = verify_evidence_package(com_id)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode())
            return

        # Evidence manifest
        if "/evidence/manifest" in path:
            com_id = path.split("/communique/")[1].split("/evidence")[0]
            manifest, _ = load_evidence_manifest(com_id)

            if manifest is None:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"))
            return

        # Fall through to original handler
        original_do_GET(self)

    handler_class.do_GET = extended_do_GET
    return handler_class


# ─── STANDALONE TEST ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    print(f"\n  🐉 WINDI Communiqué Multimedia Extension v1.0")
    print(f"  ──────────────────────────────────────────────\n")

    if len(sys.argv) > 1:
        com_id = sys.argv[1]
        print(f"  Testing evidence verification for: {com_id}")
        result = verify_evidence_package(com_id)
        print(json.dumps(result, indent=2))
    else:
        print("  Endpoints:")
        print("    GET /communique/{id}/evidence          — Gallery page")
        print("    GET /communique/{id}/evidence/verify    — Verify package")
        print("    GET /communique/{id}/evidence/manifest  — Get manifest")
        print()
        print("  Integration:")
        print("    from communique_multimedia import register_multimedia_handlers")
        print("    register_multimedia_handlers(CommuniqueHandler)")
        print()
        print("  Deploy:")
        print("    scp communique_multimedia.py windi@87.106.29.233:/opt/windi/communique/")
        print()
