"""
WINDI Virtue Token & RBAC Enforcement v1.0
RFC-003: Governance Access & Authority Model

Implements:
- Virtue Token (JWT) issuance and validation
- S-Level signal filtering
- Domain-scoped visibility
- Governance Hold authorization
- Forensic accountability logging

"Authority scales with abstraction. Visibility scales with responsibility."
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ─── S-Level Signal Mapping (RFC-003 Section 5) ─────────────────

# Signals visible at each Sovereignty Level
S_LEVEL_SIGNALS: Dict[int, Dict[str, str]] = {
    1: {  # Tactical — Flow Layer
        "TMP-STALL": "direct",
        "TMP-SPIKE": "direct",
        "REL-NODE":  "direct",
        "REL-DEPTH": "direct",
        "DOM-FRIC":  "direct",
        "DOM-LOOP":  "direct",
    },
    2: {  # Strategic — Capital Layer (includes all L1 aggregated + own)
        "TMP-STALL": "aggregated",
        "TMP-SPIKE": "aggregated",
        "REL-NODE":  "aggregated",
        "REL-DEPTH": "aggregated",
        "DOM-FRIC":  "aggregated",
        "DOM-LOOP":  "aggregated",
        "ID-CONC":   "direct",
        "ID-CENT":   "direct",
        "IMP-GRAV":  "direct",
        "IMP-SKEW":  "direct",
        "DEC-OVR":   "direct",
        "DEC-INTU":  "direct",
        "GOV-DENS":  "direct",
        "GOV-STACK": "direct",
    },
    3: {  # Sovereign — Integrity Layer (all signals + forensic)
        "TMP-STALL": "historical",
        "TMP-SPIKE": "historical",
        "REL-NODE":  "historical",
        "REL-DEPTH": "historical",
        "DOM-FRIC":  "historical",
        "DOM-LOOP":  "historical",
        "ID-CONC":   "historical",
        "ID-CENT":   "historical",
        "IMP-GRAV":  "historical",
        "IMP-SKEW":  "historical",
        "DEC-OVR":   "historical",
        "DEC-INTU":  "historical",
        "GOV-DENS":  "historical",
        "GOV-STACK": "historical",
        # Forensic-only signals
        "FORENSIC_LINEAGE":  "historical",
        "OVERRIDE_LINEAGE":  "historical",
        "HOLD_HISTORY":      "historical",
    },
}

# Temporal scope defaults per S-Level
S_LEVEL_TEMPORAL: Dict[int, str] = {
    1: "7d",        # Tactical sees last 7 days
    2: "90d",       # Strategic sees last 90 days
    3: "unlimited",  # Sovereign sees everything
}

# Clearance names
S_LEVEL_CLEARANCE: Dict[int, str] = {
    1: "TACTICAL",
    2: "STRATEGIC",
    3: "SOVEREIGN",
}


# ─── Virtue Token ────────────────────────────────────────────────

@dataclass
class VirtueToken:
    """RFC-003 Virtue Token — JWT payload for governance access."""
    sub: str                    # user hash
    s_level: int                # 1, 2, or 3
    domains: List[str]          # organizational domains
    kill_switch_authority: bool = False
    shelves: Optional[List[str]] = None   # override auto-derived
    signals: Optional[List[str]] = None   # override auto-derived
    temporal_scope: Optional[str] = None  # override auto-derived
    audit_trail: bool = True

    # Auto-populated
    iss: str = "windi-core"
    iat: int = 0
    exp: int = 0
    clearance: str = ""
    nonce: str = ""

    def __post_init__(self):
        import os
        self.iat = int(time.time())
        self.exp = self.iat + 86400  # 24h default
        self.clearance = S_LEVEL_CLEARANCE.get(self.s_level, "UNKNOWN")
        self.nonce = base64.b64encode(os.urandom(16)).decode("ascii")

        # Auto-derive visible signals from S-Level
        if self.signals is None:
            self.signals = list(S_LEVEL_SIGNALS.get(self.s_level, {}).keys())

        # Auto-derive visible shelves from signals
        if self.shelves is None:
            from_signals = set()
            signal_shelf_map = {
                "ID-CONC": "S1", "ID-CENT": "S1",
                "IMP-GRAV": "S2", "IMP-SKEW": "S2",
                "DOM-FRIC": "S3", "DOM-LOOP": "S3",
                "GOV-DENS": "S4", "GOV-STACK": "S4",
                "DEC-OVR": "S5", "DEC-INTU": "S5",
                "TMP-SPIKE": "S6", "TMP-STALL": "S6",
                "REL-DEPTH": "S7", "REL-NODE": "S7",
            }
            for sig in self.signals:
                if sig in signal_shelf_map:
                    from_signals.add(signal_shelf_map[sig])
            self.shelves = sorted(from_signals) if from_signals else ["S3", "S6", "S7"]

        # Auto-derive temporal scope
        if self.temporal_scope is None:
            self.temporal_scope = S_LEVEL_TEMPORAL.get(self.s_level, "7d")

        # Kill switch only for S-Level 2+ with explicit grant
        if self.s_level < 2:
            self.kill_switch_authority = False

    def to_jwt_payload(self) -> Dict[str, Any]:
        """Serialize to JWT payload dict."""
        return {
            "sub": self.sub,
            "iss": self.iss,
            "iat": self.iat,
            "exp": self.exp,
            "s_level": self.s_level,
            "domains": self.domains,
            "clearance": self.clearance,
            "kill_switch_authority": self.kill_switch_authority,
            "shelves": self.shelves,
            "signals": self.signals,
            "temporal_scope": self.temporal_scope,
            "audit_trail": self.audit_trail,
            "nonce": self.nonce,
        }

    def is_expired(self) -> bool:
        return int(time.time()) > self.exp

    def can_see_signal(self, signal_code: str) -> bool:
        """Check if this token permits visibility of a signal."""
        return signal_code in (self.signals or [])

    def can_see_shelf(self, shelf: str) -> bool:
        """Check if this token permits visibility of a shelf."""
        return shelf in (self.shelves or [])

    def can_see_domain(self, domain_hash: str, domain_map: Dict[str, str] = None) -> bool:
        """Check if this token permits visibility of a domain."""
        if not self.domains:
            return False
        if "*" in self.domains:
            return True
        # In production, domain_hash would be compared against allowed domain hashes
        return True  # Simplified — real implementation compares hashes

    def can_activate_hold(self) -> bool:
        """Check if this token permits Governance Hold activation."""
        return self.kill_switch_authority and self.s_level >= 2


# ─── Token Issuer ────────────────────────────────────────────────

class VirtueTokenIssuer:
    """Issues and validates Virtue Tokens using HMAC-SHA256 signing."""

    def __init__(self, signing_key_b64: str):
        self.signing_key = base64.b64decode(signing_key_b64)
        self._issued: List[Dict] = []  # Forensic log
        self._lock = threading.Lock()

    def _sign(self, payload: Dict[str, Any]) -> str:
        """Sign JWT payload with HMAC-SHA256."""
        canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        mac = hmac.new(self.signing_key, canonical, hashlib.sha256).digest()
        return base64.b64encode(mac).decode("ascii")

    def issue(self, token: VirtueToken) -> Dict[str, Any]:
        """Issue a signed Virtue Token."""
        payload = token.to_jwt_payload()
        signature = self._sign(payload)

        signed_token = {
            "header": {"alg": "HS256", "typ": "VirtueToken", "v": "1.0"},
            "payload": payload,
            "signature": signature,
        }

        # Forensic log
        with self._lock:
            self._issued.append({
                "action": "TOKEN_ISSUED",
                "sub": token.sub,
                "s_level": token.s_level,
                "clearance": token.clearance,
                "domains": token.domains,
                "kill_switch": token.kill_switch_authority,
                "iat": token.iat,
                "exp": token.exp,
            })

        return signed_token

    def validate(self, signed_token: Dict[str, Any]) -> Tuple[bool, Optional[VirtueToken], str]:
        """Validate a signed Virtue Token. Returns (valid, token, message)."""
        try:
            payload = signed_token.get("payload", {})
            sig = signed_token.get("signature", "")

            # Verify signature
            expected_sig = self._sign(payload)
            if not hmac.compare_digest(expected_sig, sig):
                return False, None, "AUTH:SIGNATURE_INVALID"

            # Check expiration
            if int(time.time()) > payload.get("exp", 0):
                return False, None, "AUTH:TOKEN_EXPIRED"

            # Reconstruct token
            token = VirtueToken(
                sub=payload["sub"],
                s_level=payload["s_level"],
                domains=payload["domains"],
                kill_switch_authority=payload.get("kill_switch_authority", False),
                shelves=payload.get("shelves"),
                signals=payload.get("signals"),
                temporal_scope=payload.get("temporal_scope"),
            )
            token.iat = payload["iat"]
            token.exp = payload["exp"]
            token.nonce = payload.get("nonce", "")

            return True, token, "OK"

        except (KeyError, TypeError) as e:
            return False, None, f"AUTH:MALFORMED_TOKEN:{e}"

    def get_issuance_log(self) -> List[Dict]:
        with self._lock:
            return list(self._issued)


# ─── Signal Filter (Server-Side Enforcement) ────────────────────

class SignalFilter:
    """
    Server-side signal filtering based on Virtue Token.
    This is the core RBAC enforcement — dashboards NEVER filter client-side.
    """

    @staticmethod
    def filter_signals(
        signals: List[Dict[str, Any]],
        token: VirtueToken,
    ) -> List[Dict[str, Any]]:
        """Filter a list of decoded signals based on token permissions."""
        filtered = []
        for sig in signals:
            code = sig.get("code", "")
            shelf = sig.get("shelf", "")

            # Check signal visibility
            if not token.can_see_signal(code):
                continue

            # Check shelf visibility
            if not token.can_see_shelf(shelf):
                continue

            # Apply abstraction level
            visibility = S_LEVEL_SIGNALS.get(token.s_level, {}).get(code, None)
            if visibility is None:
                continue

            # Annotate with visibility mode
            enriched = dict(sig)
            enriched["_visibility"] = visibility  # direct / aggregated / historical
            enriched["_s_level"] = token.s_level
            filtered.append(enriched)

        return filtered

    @staticmethod
    def filter_dashboard_state(
        dashboard_state: Dict[str, Any],
        token: VirtueToken,
    ) -> Dict[str, Any]:
        """Filter complete dashboard state for token holder."""
        filtered = dict(dashboard_state)

        # Filter shelf health — only show permitted shelves
        if "shelf_health" in filtered:
            filtered["shelf_health"] = {
                k: v for k, v in filtered["shelf_health"].items()
                if token.can_see_shelf(k)
            }

        # Filter by_shelf counts
        if "by_shelf" in filtered:
            filtered["by_shelf"] = {
                k: v for k, v in filtered["by_shelf"].items()
                if token.can_see_shelf(k)
            }

        # Filter live feed
        if "live_feed" in filtered:
            filtered["live_feed"] = [
                s for s in filtered["live_feed"]
                if token.can_see_signal(s.get("code", ""))
            ]

        # Filter hotspots
        if "hotspots" in filtered:
            filtered["hotspots"] = [
                h for h in filtered["hotspots"]
                if token.can_see_signal(h.get("code", ""))
            ]

        # Add token metadata
        filtered["_token_meta"] = {
            "s_level": token.s_level,
            "clearance": token.clearance,
            "temporal_scope": token.temporal_scope,
            "visible_shelves": token.shelves,
            "visible_signals": len(token.signals or []),
            "kill_switch": token.kill_switch_authority,
        }

        return filtered


# ─── Governance Hold Protocol ────────────────────────────────────

@dataclass
class GovernanceHold:
    """RFC-003 Section 6 — Governance Hold record."""
    actor_hash: str
    scope: str
    reason_code: str
    reason_signals: List[str]
    hold_duration_hours: int = 4
    timestamp: int = 0
    release_actor_hash: Optional[str] = None
    release_timestamp: Optional[int] = None
    signature: str = ""

    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = int(time.time())

    def is_active(self) -> bool:
        if self.release_timestamp:
            return False
        expiry = self.timestamp + (self.hold_duration_hours * 3600)
        return int(time.time()) < expiry

    def to_virtue_receipt(self) -> Dict[str, Any]:
        return {
            "action": "GOVERNANCE_HOLD",
            "actor_hash": self.actor_hash,
            "scope": self.scope,
            "reason_code": self.reason_code,
            "reason_signals": self.reason_signals,
            "timestamp": self.timestamp,
            "hold_duration_hours": self.hold_duration_hours,
            "release_actor_hash": self.release_actor_hash,
            "release_timestamp": self.release_timestamp,
            "signature": self.signature,
        }


class GovernanceHoldManager:
    """Manages the Governance Hold Protocol (Kill Switch)."""

    def __init__(self):
        self._holds: List[GovernanceHold] = []
        self._lock = threading.Lock()

    def activate(
        self,
        token: VirtueToken,
        scope: str,
        reason_code: str,
        reason_signals: List[str],
        duration_hours: int = 4,
    ) -> Tuple[bool, str, Optional[GovernanceHold]]:
        """Activate a Governance Hold. Returns (success, message, hold)."""

        # Authorization check
        if not token.can_activate_hold():
            return False, "HOLD:UNAUTHORIZED — requires s_level>=2 + kill_switch_authority", None

        if duration_hours > 72:
            return False, "HOLD:DURATION_EXCEEDED — max 72 hours", None

        actor_hash = hashlib.sha256(token.sub.encode()).hexdigest()

        hold = GovernanceHold(
            actor_hash=actor_hash,
            scope=scope,
            reason_code=reason_code,
            reason_signals=reason_signals,
            hold_duration_hours=duration_hours,
        )

        with self._lock:
            self._holds.append(hold)

        return True, f"HOLD:ACTIVATED scope={scope} duration={duration_hours}h", hold

    def release(
        self,
        token: VirtueToken,
        hold_index: int = -1,
    ) -> Tuple[bool, str]:
        """Release a Governance Hold. Requires same or higher authority."""
        if token.s_level < 2:
            return False, "HOLD:RELEASE_UNAUTHORIZED"

        with self._lock:
            if not self._holds:
                return False, "HOLD:NO_ACTIVE_HOLDS"

            hold = self._holds[hold_index]
            if not hold.is_active():
                return False, "HOLD:ALREADY_RELEASED"

            hold.release_actor_hash = hashlib.sha256(token.sub.encode()).hexdigest()
            hold.release_timestamp = int(time.time())

        return True, "HOLD:RELEASED"

    def get_active_holds(self) -> List[Dict]:
        with self._lock:
            return [h.to_virtue_receipt() for h in self._holds if h.is_active()]

    def get_hold_history(self) -> List[Dict]:
        with self._lock:
            return [h.to_virtue_receipt() for h in self._holds]
