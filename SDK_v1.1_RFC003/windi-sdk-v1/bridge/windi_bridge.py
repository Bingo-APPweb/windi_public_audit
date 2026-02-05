"""
WINDI Bridge API v1.0
RFC-002 Compliant Telemetry Receiver

Validates HMAC-SHA256 signatures, enforces anti-replay (ts + nonce + seq),
decodes Micro-Signals and routes them to the Dashboard aggregator.

"AI processes. Human decides. WINDI guarantees."
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler

# ─── Configuration ───────────────────────────────────────────────

PROTOCOL_VERSION = "1.0"
MAX_TS_DRIFT_MS = 300_000        # 5 minutes max clock drift (production)
MAX_TS_DRIFT_SIMULATION_MS = 365 * 24 * 3600 * 1000  # 1 year (simulation mode)
NONCE_WINDOW_SIZE = 10_000       # remember last 10k nonces per client
SEQ_GRACE = 50                   # allow seq gaps up to 50 (batch reorder)

# Micro-Signal Registry (RFC-001)
SIGNAL_REGISTRY = {
    "ID-CONC": {"shelf": "S1", "name": "Decisional Concentration",    "severity": "high"},
    "ID-CENT": {"shelf": "S1", "name": "Centralization Drift",        "severity": "medium"},
    "IMP-GRAV": {"shelf": "S2", "name": "Energy Gravity",             "severity": "medium"},
    "IMP-SKEW": {"shelf": "S2", "name": "Impact Skew",                "severity": "low"},
    "DOM-FRIC": {"shelf": "S3", "name": "Interdepartmental Friction", "severity": "high"},
    "DOM-LOOP": {"shelf": "S3", "name": "Circular Flow",              "severity": "medium"},
    "GOV-DENS": {"shelf": "S4", "name": "Bureaucratic Density",       "severity": "medium"},
    "GOV-STACK": {"shelf": "S4", "name": "Rule Stacking",             "severity": "high"},
    "DEC-OVR":  {"shelf": "S5", "name": "Override Frequency",         "severity": "high"},
    "DEC-INTU": {"shelf": "S5", "name": "Intuition Bias",             "severity": "medium"},
    "TMP-SPIKE": {"shelf": "S6", "name": "Quarter-End Pulse",         "severity": "high"},
    "TMP-STALL": {"shelf": "S6", "name": "Latency Plateau",           "severity": "medium"},
    "REL-DEPTH": {"shelf": "S7", "name": "Dependency Depth",          "severity": "medium"},
    "REL-NODE":  {"shelf": "S7", "name": "Critical Node",             "severity": "high"},
}

VALID_SHELVES = {"S1", "S2", "S3", "S4", "S5", "S6", "S7"}
VALID_EVENTS = {
    "DOC_CREATED", "APPROVAL_REQUESTED", "APPROVED", "REJECTED",
    "APPROVAL_OVERRIDDEN", "DEADLINE_EXCEEDED", "DEPENDENCY_LINKED",
    "DEPENDENCY_BLOCKING", "STATE_TRANSITION",
}


# ─── Helpers ─────────────────────────────────────────────────────

def _b64d(s: str) -> bytes:
    return base64.b64decode(s)

def _b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")

def _hmac_sha256(key: bytes, msg: bytes) -> bytes:
    return hmac.new(key, msg, hashlib.sha256).digest()


# ─── Anti-Replay State ──────────────────────────────────────────

@dataclass
class ClientState:
    """Per-client anti-replay tracking."""
    last_seq: int = 0
    nonces: deque = field(default_factory=lambda: deque(maxlen=NONCE_WINDOW_SIZE))
    nonce_set: Set[str] = field(default_factory=set)
    lock: threading.Lock = field(default_factory=threading.Lock)
    simulation_mode: bool = False

    def check_and_update(self, seq: int, nonce: str, ts: int) -> Optional[str]:
        """Returns error string or None if valid."""
        now_ms = int(time.time() * 1000)
        max_drift = MAX_TS_DRIFT_SIMULATION_MS if self.simulation_mode else MAX_TS_DRIFT_MS

        # Timestamp drift check
        drift = abs(now_ms - ts)
        if drift > max_drift:
            return f"REPLAY:TS_DRIFT ts={ts} drift={drift}ms max={MAX_TS_DRIFT_MS}ms"

        with self.lock:
            # Nonce uniqueness
            if nonce in self.nonce_set:
                return f"REPLAY:NONCE_REUSE nonce={nonce[:8]}..."

            # Sequence monotonicity (with grace for batch reorder)
            if seq <= self.last_seq - SEQ_GRACE:
                return f"REPLAY:SEQ_REGRESSION seq={seq} last={self.last_seq}"

            # All checks passed — update state
            if seq > self.last_seq:
                self.last_seq = seq

            # Rotate nonce window
            if len(self.nonces) >= NONCE_WINDOW_SIZE:
                evicted = self.nonces[0]
                self.nonce_set.discard(evicted)
            self.nonces.append(nonce)
            self.nonce_set.add(nonce)

            return None


# ─── Signal Aggregator (Dashboard Feed) ─────────────────────────

@dataclass
class DecodedSignal:
    """A validated, decoded signal ready for Dashboard consumption."""
    ts: int
    client_id_hash: str
    shelf: str
    code: str
    signal_name: str
    severity: str
    weight: int
    domain_hash: str
    doc_fingerprint: str
    event: str
    ctx_window: Optional[str] = None
    ctx_flags: int = 0
    seq: int = 0


class SignalAggregator:
    """Thread-safe signal store with shelf-based indexing for dashboards."""

    def __init__(self, max_signals: int = 50_000):
        self._lock = threading.Lock()
        self._signals: deque = deque(maxlen=max_signals)
        self._by_shelf: Dict[str, List[DecodedSignal]] = {s: [] for s in VALID_SHELVES}
        self._stats = {
            "total_received": 0,
            "total_rejected": 0,
            "by_shelf": {s: 0 for s in VALID_SHELVES},
            "by_severity": {"low": 0, "medium": 0, "high": 0, "unknown": 0},
            "by_event": {e: 0 for e in VALID_EVENTS},
            "weight_sum": 0,
            "weight_count": 0,
        }

    def ingest(self, sig: DecodedSignal):
        with self._lock:
            self._signals.append(sig)
            self._by_shelf[sig.shelf].append(sig)
            self._stats["total_received"] += 1
            self._stats["by_shelf"][sig.shelf] += 1
            self._stats["by_severity"][sig.severity] += 1
            self._stats["by_event"][sig.event] += 1
            self._stats["weight_sum"] += sig.weight
            self._stats["weight_count"] += 1

    def reject(self):
        with self._lock:
            self._stats["total_rejected"] += 1

    def get_dashboard_state(self) -> Dict[str, Any]:
        """Snapshot for Dashboard consumption."""
        with self._lock:
            avg_weight = (
                round(self._stats["weight_sum"] / self._stats["weight_count"], 1)
                if self._stats["weight_count"] > 0 else 0
            )

            # Last 20 signals for live feed
            recent = list(self._signals)[-20:]
            recent_dicts = [
                {
                    "ts": s.ts, "shelf": s.shelf, "code": s.code,
                    "signal_name": s.signal_name, "severity": s.severity,
                    "weight": s.weight, "event": s.event,
                }
                for s in recent
            ]

            # Shelf health (avg weight per shelf, higher = more stress)
            shelf_health = {}
            for shelf_id, signals in self._by_shelf.items():
                if signals:
                    shelf_avg = sum(s.weight for s in signals) / len(signals)
                    shelf_health[shelf_id] = {
                        "count": len(signals),
                        "avg_weight": round(shelf_avg, 1),
                        "status": "critical" if shelf_avg > 75 else "warning" if shelf_avg > 50 else "healthy",
                    }
                else:
                    shelf_health[shelf_id] = {"count": 0, "avg_weight": 0, "status": "no_data"}

            # Top 5 hottest signals (highest weight recent)
            hot = sorted(list(self._signals)[-200:], key=lambda s: s.weight, reverse=True)[:5]
            hotspots = [
                {"code": s.code, "signal_name": s.signal_name, "weight": s.weight, "event": s.event}
                for s in hot
            ]

            return {
                "meta": {
                    "snapshot_ts": int(time.time() * 1000),
                    "protocol": PROTOCOL_VERSION,
                },
                "totals": {
                    "received": self._stats["total_received"],
                    "rejected": self._stats["total_rejected"],
                    "avg_weight": avg_weight,
                },
                "by_shelf": self._stats["by_shelf"].copy(),
                "by_severity": self._stats["by_severity"].copy(),
                "by_event": self._stats["by_event"].copy(),
                "shelf_health": shelf_health,
                "hotspots": hotspots,
                "live_feed": recent_dicts,
            }

    def get_shelf_detail(self, shelf: str, limit: int = 50) -> List[Dict]:
        with self._lock:
            signals = self._by_shelf.get(shelf, [])[-limit:]
            return [
                {
                    "ts": s.ts, "code": s.code, "signal_name": s.signal_name,
                    "weight": s.weight, "event": s.event, "severity": s.severity,
                    "domain_hash": s.domain_hash[:12] + "...",
                }
                for s in signals
            ]


# ─── Bridge Core ─────────────────────────────────────────────────

class WindiBridge:
    """
    WINDI Telemetry Bridge v1.0
    Receives signed packets from Edge emitters (a4Desk),
    validates them cryptographically, and feeds decoded signals
    to the Dashboard aggregator.
    """

    def __init__(self, simulation_mode: bool = False):
        self._clients: Dict[str, ClientState] = {}
        self._client_keys: Dict[str, bytes] = {}  # kid -> hmac_key
        self.aggregator = SignalAggregator()
        self._lock = threading.Lock()
        self._simulation_mode = simulation_mode

    def register_client(self, client_id_hash: str, key_id: str, hmac_key_b64: str):
        """Register a client's HMAC key for signature verification."""
        with self._lock:
            self._client_keys[key_id] = base64.b64decode(hmac_key_b64)
            if client_id_hash not in self._clients:
                self._clients[client_id_hash] = ClientState(simulation_mode=self._simulation_mode)

    def validate_and_ingest(self, packet: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Full validation pipeline:
        1. Schema check
        2. HMAC signature verification
        3. Anti-replay (ts + nonce + seq)
        4. Signal decode & ingest
        Returns (success, message)
        """
        try:
            # ── Step 1: Schema validation ──
            header = packet.get("header")
            payload = packet.get("payload")
            auth = packet.get("auth")

            if not all([header, payload, auth]):
                self.aggregator.reject()
                return False, "SCHEMA:MISSING_FIELDS"

            if header.get("v") != PROTOCOL_VERSION:
                self.aggregator.reject()
                return False, f"SCHEMA:VERSION_MISMATCH v={header.get('v')}"

            kid = header.get("kid")
            cid = header.get("cid")
            ts = header.get("ts")
            nonce = header.get("nonce")
            seq = header.get("seq")

            if not all([kid, cid, ts, nonce, seq is not None]):
                self.aggregator.reject()
                return False, "SCHEMA:HEADER_INCOMPLETE"

            shelf = payload.get("shelf")
            code = payload.get("code")
            weight = payload.get("weight")
            event = payload.get("event")

            if shelf not in VALID_SHELVES:
                self.aggregator.reject()
                return False, f"SCHEMA:INVALID_SHELF shelf={shelf}"

            if event not in VALID_EVENTS:
                self.aggregator.reject()
                return False, f"SCHEMA:INVALID_EVENT event={event}"

            if not isinstance(weight, int) or weight < 0 or weight > 100:
                self.aggregator.reject()
                return False, f"SCHEMA:INVALID_WEIGHT weight={weight}"

            # ── Step 2: HMAC Verification ──
            hmac_key = self._client_keys.get(kid)
            if hmac_key is None:
                self.aggregator.reject()
                return False, f"AUTH:UNKNOWN_KEY kid={kid}"

            sig_expected = _hmac_sha256(
                hmac_key,
                _canonical_json({"header": header, "payload": payload})
            )
            sig_received = _b64d(auth["sig"])

            if not hmac.compare_digest(sig_expected, sig_received):
                self.aggregator.reject()
                return False, "AUTH:HMAC_INVALID"

            # ── Step 3: Anti-Replay ──
            with self._lock:
                if cid not in self._clients:
                    self._clients[cid] = ClientState(simulation_mode=self._simulation_mode)
                client_state = self._clients[cid]

            replay_err = client_state.check_and_update(seq, nonce, ts)
            if replay_err:
                self.aggregator.reject()
                return False, replay_err

            # ── Step 4: Decode & Ingest ──
            signal_meta = SIGNAL_REGISTRY.get(code, {})
            signal_name = signal_meta.get("name", f"UNKNOWN:{code}")
            severity = signal_meta.get("severity", "unknown")

            ctx = payload.get("ctx", {})

            decoded = DecodedSignal(
                ts=ts,
                client_id_hash=cid,
                shelf=shelf,
                code=code,
                signal_name=signal_name,
                severity=severity,
                weight=weight,
                domain_hash=payload.get("domain_hash", ""),
                doc_fingerprint=payload.get("doc_fingerprint", ""),
                event=event,
                ctx_window=ctx.get("window"),
                ctx_flags=ctx.get("flags", 0),
                seq=seq,
            )

            self.aggregator.ingest(decoded)
            return True, f"OK shelf={shelf} code={code} w={weight} seq={seq}"

        except Exception as e:
            self.aggregator.reject()
            return False, f"ERROR:{type(e).__name__}:{str(e)}"

    def ingest_batch(self, packets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of telemetry packets."""
        results = {"accepted": 0, "rejected": 0, "errors": []}
        for i, pkt in enumerate(packets):
            ok, msg = self.validate_and_ingest(pkt)
            if ok:
                results["accepted"] += 1
            else:
                results["rejected"] += 1
                results["errors"].append({"index": i, "reason": msg})
        return results


# ─── HTTP Server ─────────────────────────────────────────────────

bridge = WindiBridge()


class BridgeHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for the WINDI Bridge API."""

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json_response(self, data: Any, status=200):
        self._set_headers(status)
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        if self.path == "/api/v1/health":
            self._json_response({
                "status": "operational",
                "protocol": PROTOCOL_VERSION,
                "ts": int(time.time() * 1000),
                "motto": "AI processes. Human decides. WINDI guarantees.",
            })

        elif self.path == "/api/v1/dashboard":
            self._json_response(bridge.aggregator.get_dashboard_state())

        elif self.path.startswith("/api/v1/shelf/"):
            shelf = self.path.split("/")[-1].upper()
            if shelf in VALID_SHELVES:
                self._json_response(bridge.aggregator.get_shelf_detail(shelf))
            else:
                self._json_response({"error": f"Invalid shelf: {shelf}"}, 400)

        elif self.path == "/api/v1/registry":
            self._json_response(SIGNAL_REGISTRY)

        elif self.path == "/":
            self._set_headers(200, "text/html")
            self.wfile.write(b"<h1>WINDI Bridge v1.0</h1><p>Flow is Truth. Content is Sovereign.</p>")

        else:
            self._json_response({"error": "Not found"}, 404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        if self.path == "/api/v1/telemetry":
            try:
                data = json.loads(body)
                ok, msg = bridge.validate_and_ingest(data)
                status = 200 if ok else 400
                self._json_response({"accepted": ok, "message": msg}, status)
            except json.JSONDecodeError:
                self._json_response({"error": "Invalid JSON"}, 400)

        elif self.path == "/api/v1/telemetry/batch":
            try:
                data = json.loads(body)
                packets = data.get("packets", [])
                result = bridge.ingest_batch(packets)
                self._json_response(result)
            except json.JSONDecodeError:
                self._json_response({"error": "Invalid JSON"}, 400)

        elif self.path == "/api/v1/register":
            try:
                data = json.loads(body)
                bridge.register_client(
                    client_id_hash=data["client_id_hash"],
                    key_id=data["key_id"],
                    hmac_key_b64=data["hmac_key_b64"],
                )
                self._json_response({"registered": True, "kid": data["key_id"]})
            except (json.JSONDecodeError, KeyError) as e:
                self._json_response({"error": str(e)}, 400)

        else:
            self._json_response({"error": "Not found"}, 404)

    def log_message(self, format, *args):
        """Suppress default logging for clean output."""
        pass


def run_bridge(host: str = "0.0.0.0", port: int = 8090):
    """Start the WINDI Bridge API server."""
    server = HTTPServer((host, port), BridgeHandler)
    print(f"╔══════════════════════════════════════════════╗")
    print(f"║  WINDI Bridge API v1.0                       ║")
    print(f"║  Listening on {host}:{port}                  ║")
    print(f"║  Flow is Truth. Content is Sovereign.        ║")
    print(f"╚══════════════════════════════════════════════╝")
    print(f"\nEndpoints:")
    print(f"  GET  /api/v1/health        — System health")
    print(f"  GET  /api/v1/dashboard     — Dashboard state")
    print(f"  GET  /api/v1/shelf/{{S1-S7}} — Shelf detail")
    print(f"  GET  /api/v1/registry      — Signal registry")
    print(f"  POST /api/v1/telemetry     — Single packet")
    print(f"  POST /api/v1/telemetry/batch — Batch packets")
    print(f"  POST /api/v1/register      — Register client key")
    server.serve_forever()


if __name__ == "__main__":
    run_bridge()
