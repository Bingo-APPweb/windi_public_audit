"""
W-STATE-CORE-006 — Verify Public
==================================
Endpoint público de verificação de provas WINDI.
Sem autenticação. Só leitura. Determinístico.

Porta: :8109  (BaseHTTPRequestHandler — consistente com stack 001-005)

Endpoints:
  GET  /verify/{ledger_id}              → Consulta Ledger, devolve prova
  POST /verify/anchor                   → Verifica anchor_hash dado pho_id + ledger_id
  GET  /verify/health                   → Health check

Invariante I-State-006:
  "A verificação é pública, imutável e nunca modifica estado.
   Se o Ledger responde, a verdade está lá. WINDI não opina — reporta."
"""

from __future__ import annotations

import hashlib
import http.server
import json
import logging
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("windi.state.006")

# ─── Config ──────────────────────────────────────────────────────────────────

LEDGER_BASE = os.getenv("LEDGER_URL", "http://localhost:8101/api/receipts")
LEDGER_TIMEOUT = 8
PORT = int(os.getenv("PORT", "8109"))
VERSION = "1.0.0"

# Formato canónico do ledger_id
_LEDGER_ID_RE = re.compile(r"^WINDI-[A-Z0-9]+-\d{14}-[A-F0-9]{8}$")
_ANCHOR_HASH_RE = re.compile(r"^[a-f0-9]{64}$")


# ─── Data classes ────────────────────────────────────────────────────────────

@dataclass
class VerifyResult:
    verified: bool
    ledger_id: str
    pho_id: Optional[str]
    anchor_hash: Optional[str]
    anchor_valid: Optional[bool]
    timestamp: str
    ledger_data: Optional[dict]
    error: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None or k in
                ("verified", "ledger_id", "timestamp", "error")}


# ─── Lógica central ──────────────────────────────────────────────────────────

def _recompute_anchor(pho_id: str, ledger_id: str) -> str:
    """Mesmo algoritmo do ledger_anchor.py — SHA-256(pho_id:ledger_id)."""
    raw = f"{pho_id}:{ledger_id}".encode()
    return hashlib.sha256(raw).hexdigest()


def _fetch_from_ledger(ledger_id: str) -> tuple[bool, Optional[dict], Optional[str]]:
    """
    GET /api/receipts/{ledger_id}
    Retorna (found, data_dict, error_str)
    """
    url = f"{LEDGER_BASE}/{ledger_id}"
    try:
        with urllib.request.urlopen(url, timeout=LEDGER_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            return True, data, None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, None, "Receipt não encontrado no Ledger"
        return False, None, f"Ledger HTTP {e.code}"
    except Exception as exc:
        return False, None, f"Ledger inacessível: {exc}"


def verify_by_ledger_id(ledger_id: str) -> VerifyResult:
    """GET /verify/{ledger_id}"""
    ts = datetime.now(timezone.utc).isoformat()

    if not _LEDGER_ID_RE.match(ledger_id):
        return VerifyResult(
            verified=False,
            ledger_id=ledger_id,
            pho_id=None,
            anchor_hash=None,
            anchor_valid=None,
            timestamp=ts,
            ledger_data=None,
            error=f"ledger_id inválido — formato esperado: WINDI-{{APP}}-{{YYYYMMDDHHmmss}}-{{UUID8}}",
        )

    found, data, err = _fetch_from_ledger(ledger_id)

    if not found:
        return VerifyResult(
            verified=False,
            ledger_id=ledger_id,
            pho_id=None,
            anchor_hash=None,
            anchor_valid=None,
            timestamp=ts,
            ledger_data=None,
            error=err,
        )

    return VerifyResult(
        verified=True,
        ledger_id=ledger_id,
        pho_id=data.get("actor"),
        anchor_hash=None,
        anchor_valid=None,
        timestamp=ts,
        ledger_data=data,
    )


def verify_anchor(pho_id: str, ledger_id: str, claimed_hash: str) -> VerifyResult:
    """POST /verify/anchor"""
    ts = datetime.now(timezone.utc).isoformat()

    if not _ANCHOR_HASH_RE.match(claimed_hash):
        return VerifyResult(
            verified=False, ledger_id=ledger_id, pho_id=pho_id,
            anchor_hash=claimed_hash, anchor_valid=False,
            timestamp=ts, ledger_data=None,
            error="anchor_hash inválido — deve ser SHA-256 hex (64 chars)",
        )

    expected = _recompute_anchor(pho_id, ledger_id)
    hash_ok = (expected == claimed_hash)

    if not hash_ok:
        return VerifyResult(
            verified=False, ledger_id=ledger_id, pho_id=pho_id,
            anchor_hash=claimed_hash, anchor_valid=False,
            timestamp=ts, ledger_data=None,
            error="anchor_hash não corresponde ao par (pho_id, ledger_id)",
        )

    found, data, err = _fetch_from_ledger(ledger_id)

    return VerifyResult(
        verified=found and hash_ok,
        ledger_id=ledger_id,
        pho_id=pho_id,
        anchor_hash=claimed_hash,
        anchor_valid=hash_ok,
        timestamp=ts,
        ledger_data=data if found else None,
        error=err if not found else None,
    )


# ─── HTTP Handler ─────────────────────────────────────────────────────────────

class VerifyHandler(http.server.BaseHTTPRequestHandler):

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> Optional[dict]:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def do_GET(self) -> None:
        path = self.path.split("?")[0].rstrip("/")

        if path == "/verify/health":
            self._send_json(200, {
                "status": "ok",
                "service": "W-STATE-CORE-006",
                "version": VERSION,
                "ledger": LEDGER_BASE,
            })
            return

        m = re.match(r"^/verify/([^/]+)$", path)
        if m:
            ledger_id = m.group(1)
            result = verify_by_ledger_id(ledger_id)
            code = 200 if result.verified else (404 if not result.error else 400)
            self._send_json(code, result.to_dict())
            return

        self._send_json(404, {"error": "Endpoint não encontrado"})

    def do_POST(self) -> None:
        path = self.path.rstrip("/")

        if path == "/verify/anchor":
            body = self._read_body()
            if not body:
                self._send_json(400, {"error": "Body JSON obrigatório"})
                return

            pho_id = body.get("pho_id", "")
            ledger_id = body.get("ledger_id", "")
            anchor_hash = body.get("anchor_hash", "")

            if not all([pho_id, ledger_id, anchor_hash]):
                self._send_json(400, {
                    "error": "Campos obrigatórios: pho_id, ledger_id, anchor_hash"
                })
                return

            result = verify_anchor(pho_id, ledger_id, anchor_hash)
            code = 200 if result.verified else 422
            self._send_json(code, result.to_dict())
            return

        self._send_json(404, {"error": "Endpoint não encontrado"})

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt, *args):
        logger.info(fmt, *args)


def run(port: int = PORT) -> None:
    server = http.server.HTTPServer(("", port), VerifyHandler)
    logger.info("W-STATE-CORE-006 Verify Public em :%d", port)
    server.serve_forever()


# ─── Testes ───────────────────────────────────────────────────────────────────

def _run_tests() -> None:
    import unittest.mock as mock

    print("=" * 60)
    print("W-STATE-CORE-006 — Test Suite")
    print("=" * 60)

    GOOD_LEDGER_ID = "WINDI-WINDILAW-20260411120000-AB12CD34"
    GOOD_PHO_ID    = "PHO-WINDILAW-20260411120000-AB12CD34"
    GOOD_HASH      = _recompute_anchor(GOOD_PHO_ID, GOOD_LEDGER_ID)

    LEDGER_RECORD = {
        "id": GOOD_LEDGER_ID,
        "actor": "did:windi:JOBER-MOGELE-CORREA-001",
        "app": "WINDI-LAW",
        "doc_name": "Contrato_006_Test.pdf",
        "doc_type": "CONTRACT",
        "content_hash": "a" * 64,
        "governance_level": "HIGH",
        "sge_score": 0.97,
        "stored": True,
    }

    class _MockResp:
        def __init__(self, data): self._data = json.dumps(data).encode()
        def read(self): return self._data
        def __enter__(self): return self
        def __exit__(self, *_): pass

    print("\n[T1] ledger_id inválido")
    r = verify_by_ledger_id("nao-e-valido")
    assert not r.verified
    assert r.error
    print(f"  OK")

    print("\n[T2] Ledger offline")
    with mock.patch("urllib.request.urlopen",
                    side_effect=ConnectionRefusedError("offline")):
        r = verify_by_ledger_id(GOOD_LEDGER_ID)
    assert not r.verified
    print(f"  OK")

    print("\n[T3] Ledger 404")
    http_404 = urllib.error.HTTPError(url="", code=404, msg="Not Found",
                                      hdrs=None, fp=None)
    with mock.patch("urllib.request.urlopen", side_effect=http_404):
        r = verify_by_ledger_id(GOOD_LEDGER_ID)
    assert not r.verified
    print(f"  OK")

    print("\n[T4] Ledger OK")
    with mock.patch("urllib.request.urlopen",
                    return_value=_MockResp(LEDGER_RECORD)):
        r = verify_by_ledger_id(GOOD_LEDGER_ID)
    assert r.verified
    print(f"  OK")

    print("\n[T5] anchor_hash formato errado")
    r = verify_anchor(GOOD_PHO_ID, GOOD_LEDGER_ID, "hash-curto")
    assert not r.verified
    print(f"  OK")

    print("\n[T6] anchor_hash errado")
    wrong_hash = _recompute_anchor("PHO-OUTRO", GOOD_LEDGER_ID)
    r = verify_anchor(GOOD_PHO_ID, GOOD_LEDGER_ID, wrong_hash)
    assert not r.verified
    print(f"  OK")

    print("\n[T7] anchor correcto + Ledger OK")
    with mock.patch("urllib.request.urlopen",
                    return_value=_MockResp(LEDGER_RECORD)):
        r = verify_anchor(GOOD_PHO_ID, GOOD_LEDGER_ID, GOOD_HASH)
    assert r.verified
    assert r.anchor_valid is True
    print(f"  OK")

    print("\n[T8] anchor correcto + Ledger offline")
    with mock.patch("urllib.request.urlopen",
                    side_effect=ConnectionRefusedError("offline")):
        r = verify_anchor(GOOD_PHO_ID, GOOD_LEDGER_ID, GOOD_HASH)
    assert not r.verified
    assert r.anchor_valid is True
    print(f"  OK")

    print("\n" + "=" * 60)
    print("T1-T8 PASSED")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    if "--serve" in sys.argv:
        run()
    else:
        _run_tests()
