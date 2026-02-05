# WINDI SDK - Reference Emitter (Python)
# RFC-002: WINDI-SEC-JSON-v1 (HMAC default)
# "Flow is Truth. Content is Sovereign."

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Literal

Alg = Literal["HMAC-SHA256"]
Shelf = Literal["S1", "S2", "S3", "S4", "S5", "S6", "S7"]

EVENTS = {
    "DOC_CREATED",
    "APPROVAL_REQUESTED",
    "APPROVED",
    "REJECTED",
    "APPROVAL_OVERRIDDEN",
    "DEADLINE_EXCEEDED",
    "DEPENDENCY_LINKED",
    "DEPENDENCY_BLOCKING",
    "STATE_TRANSITION",
}

def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

def _sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")

def _hmac_sha256(key: bytes, msg: bytes) -> bytes:
    return hmac.new(key, msg, hashlib.sha256).digest()

@dataclass(frozen=True)
class WindiEmitterConfig:
    client_id: str
    key_id: str
    csalt_b64: str          # 256-bit recommended (32 bytes) base64
    hmac_key_b64: str       # 256-bit recommended base64
    protocol_version: str = "1.0"
    alg: Alg = "HMAC-SHA256"

class Sequence:
    def __init__(self, start: int = 0):
        self._lock = threading.Lock()
        self._seq = start

    def next(self) -> int:
        with self._lock:
            self._seq += 1
            return self._seq

class WindiEmitter:
    def __init__(self, cfg: WindiEmitterConfig):
        self.cfg = cfg
        self.csalt = base64.b64decode(cfg.csalt_b64)
        self.hmac_key = base64.b64decode(cfg.hmac_key_b64)
        self.seq = Sequence()
        self.cid = _b64(_sha256(cfg.client_id.encode("utf-8")))

    def derive_domain_hash(self, domain_id: str) -> str:
        raw = b"WINDI:DOMAIN:v1" + self.csalt + domain_id.encode("utf-8")
        return _b64(_sha256(raw))

    def derive_doc_fingerprint(self, doc_vector_bytes: bytes) -> str:
        raw = b"WINDI:DOC:v1" + self.csalt + doc_vector_bytes
        return _b64(_sha256(raw))

    def sign_packet(self, header: Dict[str, Any], payload: Dict[str, Any]) -> str:
        signing_obj = {"header": header, "payload": payload}
        mac = _hmac_sha256(self.hmac_key, _canonical_json(signing_obj))
        return _b64(mac)

    def emit(
        self,
        shelf: Shelf,
        code: str,
        weight: int,
        domain_id: str,
        doc_vector_bytes: bytes,
        event: str,
        ctx_window: Optional[str] = "5m",
        ctx_flags: int = 0,
        ts_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        if event not in EVENTS:
            raise ValueError(f"Invalid event: {event}")
        if not (0 <= weight <= 100):
            raise ValueError("weight must be 0..100")

        now = ts_ms if ts_ms is not None else int(time.time() * 1000)
        nonce = os.urandom(12)

        header: Dict[str, Any] = {
            "v": self.cfg.protocol_version,
            "alg": self.cfg.alg,
            "cid": self.cid,
            "kid": self.cfg.key_id,
            "ts": now,
            "nonce": _b64(nonce),
            "seq": self.seq.next(),
        }

        payload: Dict[str, Any] = {
            "shelf": shelf,
            "code": code,
            "weight": weight,
            "domain_hash": self.derive_domain_hash(domain_id),
            "doc_fingerprint": self.derive_doc_fingerprint(doc_vector_bytes),
            "event": event,
        }

        if ctx_window is not None:
            payload["ctx"] = {"window": ctx_window, "flags": int(ctx_flags)}

        sig = self.sign_packet(header, payload)
        return {"header": header, "payload": payload, "auth": {"sig": sig}}

def build_doc_vector_bytes(
    doc_type_id: int,
    issuer_role_id: int,
    impact_band_id: int,
    lifecycle_state_id: int,
    local_doc_id_salted: Optional[bytes] = None,
) -> bytes:
    parts = [
        doc_type_id.to_bytes(2, "big", signed=False),
        issuer_role_id.to_bytes(2, "big", signed=False),
        impact_band_id.to_bytes(1, "big", signed=False),
        lifecycle_state_id.to_bytes(1, "big", signed=False),
    ]
    if local_doc_id_salted:
        parts.append(local_doc_id_salted)
    return b"".join(parts)

def salt_local_id(csalt_b64: str, local_id: str) -> bytes:
    csalt = base64.b64decode(csalt_b64)
    return _sha256(b"WINDI:LOCALID:v1" + csalt + local_id.encode("utf-8"))
