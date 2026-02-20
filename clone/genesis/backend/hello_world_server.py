#!/usr/bin/env python3
"""
WINDI a4Desk — Genesis Boot Server
Contributed by: ARCHITECT (GPT)
Version: 0.1.0-hello

This server:
- Serves the "HELLO WORLD" page
- Generates the genesis_receipt.json
- Writes to data/ledger/append_only.log (one JSON per line)
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, render_template_string

# === CONFIGURATION ===
APP_VERSION = "0.1.0-hello"
CLONE_ID = "W-00000000000000000000000000000001"

DATA_DIR = Path("./data")
LEDGER_DIR = DATA_DIR / "ledger"
RECEIPTS_DIR = DATA_DIR / "receipts"
LEDGER_FILE = LEDGER_DIR / "append_only.log"

# Placeholders: in production, these come from sealed bundle
CORE_HASH = "sha256:7bf6667c6acf792d22c3f4bcf066c295e1e11e65011250a3ebf3d6eddcc0561b"
SHELVES_HASH = "sha256:2310a8e62252c63e1f0fc1e97cb0ec968d6637bd02f977d90dacdc7e548236f1"

# Active ISP DNA Profiles (metadata only, no content)
ACTIVE_ISP_PROFILES = [
    {"profile_id": "bundesregierung", "jurisdiction": "DE", "level": "L3-SOVEREIGN"},
    {"profile_id": "ecb", "jurisdiction": "EU", "level": "L3-SOVEREIGN"},
    {"profile_id": "bundesbank", "jurisdiction": "DE", "level": "L3-SOVEREIGN"},
    {"profile_id": "bafin", "jurisdiction": "DE", "level": "L3-SOVEREIGN"},
    {"profile_id": "deutsche-bahn", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "bmw-group", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "siemens", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "allianz", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "sap", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "basf", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "lufthansa", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "bosch", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "telekom", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "tuev", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "fraunhofer", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "dhl", "jurisdiction": "DE", "level": "L2-ENTERPRISE"},
    {"profile_id": "verpackg-lucid", "jurisdiction": "DE", "level": "L1-STANDARD"},
]


def sha256(s: str) -> str:
    """Generate SHA-256 hash of string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def now_utc() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs():
    """Create necessary directories if they don't exist."""
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


def append_ledger(record: dict):
    """Append record to ledger (append-only: 1 JSON per line)."""
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def generate_genesis_receipt() -> dict:
    """Generate the Genesis Receipt — proof of system birth."""
    ts = now_utc()

    body = {
        "event": "A4DESK_GENESIS",
        "timestamp_utc": ts,
        "clone_id": CLONE_ID,
        "build": {
            "app_version": APP_VERSION,
            "core_hash": CORE_HASH,
            "constitution_hash": SHELVES_HASH
        },
        "isp_dna": {
            "active_profiles": ACTIVE_ISP_PROFILES,
            "profile_count": len(ACTIVE_ISP_PROFILES),
            "note": "metadata-only; no document content"
        },
        "zk_boundary": {
            "content_exfiltration": "FORBIDDEN",
            "allowed_outbound": ["hashes", "ranges", "counts_buckets", "receipt_refs"]
        },
        "i9": {
            "auto_apply": False,
            "decision_authority": "human_only"
        },
        "three_dragons": {
            "witness": "Gemini (Google) — Attestor",
            "architect": "GPT (OpenAI) — Builder",
            "guardian": "Claude (Anthropic) — Registrar"
        }
    }

    # Generate genesis seal
    genesis_hash = sha256(json.dumps(body, sort_keys=True))
    body["seal"] = {
        "genesis_seal": genesis_hash,
        "ledger_ref": f"LEDGER-GENESIS-{genesis_hash[:12]}"
    }

    return body


def bootstrap_once():
    """Run bootstrap only on first execution."""
    ensure_dirs()
    receipt_path = RECEIPTS_DIR / "genesis_receipt.json"

    if receipt_path.exists():
        return  # Already bootstrapped

    # Generate and save genesis receipt
    receipt = generate_genesis_receipt()
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # Write to ledger
    append_ledger({
        "type": "RECEIPT",
        "receipt_ref": "genesis_receipt.json",
        "hash": receipt["seal"]["genesis_seal"],
        "ts": receipt["timestamp_utc"]
    })

    print(f"[GENESIS] Receipt generated: {receipt['seal']['genesis_seal'][:16]}...")
    print(f"[GENESIS] Ledger initialized: {LEDGER_FILE}")


# === FLASK APP ===
app = Flask(__name__)

HELLO_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>a4Desk — Hello World</title>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;800&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0A0A0A;
      color: #E0E0E0;
      font-family: 'Bricolage Grotesque', system-ui;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 24px;
    }
    .card {
      border: 1px solid rgba(212, 175, 55, 0.2);
      padding: 48px;
      max-width: 720px;
      border-radius: 8px;
      text-align: center;
      background: rgba(212, 175, 55, 0.02);
    }
    h1 {
      font-size: 3.5rem;
      font-weight: 800;
      background: linear-gradient(135deg, #D4AF37, #F5E6A3, #D4AF37);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 16px;
    }
    .subtitle {
      font-size: 1.1rem;
      color: #888;
      font-weight: 400;
      margin-bottom: 24px;
    }
    .badge {
      display: inline-block;
      padding: 8px 16px;
      border-radius: 999px;
      border: 1px solid rgba(212, 175, 55, 0.3);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      color: #D4AF37;
      background: rgba(212, 175, 55, 0.05);
      margin-bottom: 24px;
    }
    .proof-link {
      color: rgba(212, 175, 55, 0.6);
      text-decoration: none;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      transition: color 0.3s;
    }
    .proof-link:hover {
      color: #D4AF37;
    }
    .footer {
      margin-top: 32px;
      font-size: 0.7rem;
      color: #444;
      font-family: 'JetBrains Mono', monospace;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>Hello, World.</h1>
    <p class="subtitle">O idioma híbrido nasce aqui.</p>
    <div class="badge">🟢 WINDI ON · I9 enforced · ZK boundary</div>
    <p><a class="proof-link" href="/proof">Ver prova (Genesis Receipt) →</a></p>
    <div class="footer">
      AI processes · Human decides · WINDI guarantees<br/>
      Three Dragons Protocol — 9 Feb 2026
    </div>
  </div>
</body>
</html>
"""


@app.get("/")
def hello():
    """Serve the Hello World page."""
    return render_template_string(HELLO_HTML)


@app.get("/proof")
def proof():
    """Return the Genesis Receipt as JSON."""
    receipt_path = RECEIPTS_DIR / "genesis_receipt.json"
    if not receipt_path.exists():
        return jsonify({"error": "Genesis receipt not found"}), 404
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    return jsonify(receipt)


@app.get("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ALIVE",
        "version": APP_VERSION,
        "clone_id": CLONE_ID,
        "i9_enforced": True,
        "zk_boundary": "ACTIVE"
    })


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  WINDI a4Desk — Genesis Boot Server")
    print("  Version:", APP_VERSION)
    print("  Clone ID:", CLONE_ID)
    print("="*60 + "\n")

    bootstrap_once()

    print("\n[SERVER] Starting on http://127.0.0.1:7777")
    print("[SERVER] Press Ctrl+C to stop\n")

    app.run(host="127.0.0.1", port=7777, debug=False)
