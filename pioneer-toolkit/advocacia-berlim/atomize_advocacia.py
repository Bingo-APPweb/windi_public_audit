#!/usr/bin/env python3
"""
WINDI Pioneer Toolkit — Sector Advocacia Berlin
Atomiza documentos legais com selo forense ZPO-konform.

Uso: python3 atomize_advocacia.py dokument.pdf
Usage: python3 atomize_advocacia.py document.pdf
"""

import requests
import sys
import json
import os
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# KONFIGURATION / CONFIGURATION — Nur diesen Abschnitt bearbeiten
# ══════════════════════════════════════════════════════════════════════════════

API_KEY = os.environ.get("WINDI_API_KEY", "wnd_live_SEU_KEY_AQUI")
BASE    = "https://windi-domain.com"

# ══════════════════════════════════════════════════════════════════════════════


def atomize_dokument(caminho_doc: str) -> dict:
    """
    Atomisiert ein juristisches Dokument.
    Atomizes a legal document.

    Args:
        caminho_doc: Pfad zur Datei / Path to file (pdf, docx, etc.)

    Returns:
        dict mit seed_id, forensic_hash, verify_url, ledger_receipt
    """
    if not os.path.exists(caminho_doc):
        print(f"FEHLER / ERROR: Datei nicht gefunden / File not found: {caminho_doc}")
        sys.exit(1)

    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    print(f"Atomisiere / Atomizing: {caminho_doc}")
    print(f"Zeitstempel / Timestamp: {timestamp} UTC")
    print("Sende an WINDI Forensic Ledger...")
    print()

    with open(caminho_doc, 'rb') as f:
        response = requests.post(
            f"{BASE}/par/atomize",
            headers={"X-WINDI-API-Key": API_KEY},
            files={"frame": f},
            data={
                "schema_type":      "LEGAL",
                "activation_tier":  "NODAL",
                "title":            f"Dokument — {os.path.basename(caminho_doc)}",
                "description":      f"Forensisch versiegelt am {timestamp} UTC",
                "operator_did":     "did:windi:kanzlei-berlin-pioneer",
                "jurisdiction":     "DE",
                "compliance":       "ZPO,eIDAS"
            },
            timeout=30
        )

    if response.status_code != 200:
        print(f"FEHLER / ERROR: API returned {response.status_code}")
        print(response.text)
        sys.exit(1)

    result = response.json()

    print("=" * 60)
    print("DOKUMENT VERSIEGELT / DOCUMENT SEALED")
    print(f"   Seed ID:    {result.get('seed_id', 'N/A')}")
    print(f"   Hash:       {result.get('forensic_hash','N/A')[:40]}...")
    print(f"   Ledger:     {result.get('ledger_receipt', 'N/A')}")
    print(f"   Verify URL: {result.get('verify_url', 'N/A')}")
    print("=" * 60)
    print()
    print("Für das Gerichtsprotokoll / For the court record:")
    print(f"   WINDI Forensic Receipt: {result.get('ledger_receipt', 'N/A')}")
    print(f"   SHA-256: {result.get('forensic_hash', 'N/A')}")
    print()
    print("Öffentlich prüfbar / Publicly verifiable:")
    print(f"   {result.get('verify_url', 'N/A')}")

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso / Usage: python3 atomize_advocacia.py <dokument.pdf>")
        print()
        print("Beispiel / Example:")
        print("  python3 atomize_advocacia.py vertrag.pdf")
        print()
        print("Umgebungsvariable / Environment variable:")
        print("  export WINDI_API_KEY=wnd_live_xxx")
        sys.exit(1)

    doc = sys.argv[1]
    atomize_dokument(doc)
