#!/usr/bin/env python3
"""
RFC-003 Integration Test Suite — Governance Access & Authority Model
WINDI SDK v1.1 | Guardian Certification Tests
9 Sovereignty Tests: Token Validation, RBAC Filtering, Governance Hold
"""

import json
import hashlib
import hmac
import base64
import time
import pytest
from datetime import datetime, timezone

# ============================================================
# MOCK INFRASTRUCTURE (standalone — no external dependencies)
# ============================================================

# Simulated JWT secret for testing
TEST_SECRET = "windi-guardian-test-secret-2026"

# Signal registry per RFC-003 Section 3
SIGNAL_REGISTRY = {
    "S1": {"shelf": "SH-OPER", "code": "ID-DEPT", "name": "Department Code", "min_level": 1},
    "S2": {"shelf": "SH-OPER", "code": "ID-FLOW", "name": "Flow Status", "min_level": 1},
    "S3": {"shelf": "SH-OPER", "code": "ID-TYPE", "name": "Document Type", "min_level": 1},
    "S4": {"shelf": "SH-RISK", "code": "SGE-SCORE", "name": "SGE Risk Score", "min_level": 1},
    "S5": {"shelf": "SH-RISK", "code": "SGE-CAT", "name": "Risk Category", "min_level": 1},
    "S6": {"shelf": "SH-RISK", "code": "SGE-FLAG", "name": "Risk Flags", "min_level": 1},
    "S7": {"shelf": "SH-VALUE", "code": "VAL-RANGE", "name": "Value Range R1-R5", "min_level": 1},
    "S8": {"shelf": "SH-VALUE", "code": "VAL-IMPACT", "name": "Impact Level", "min_level": 2},
    "S9": {"shelf": "SH-TEMPO", "code": "TMP-DEAD", "name": "Deadline", "min_level": 2},
    "S10": {"shelf": "SH-TEMPO", "code": "TMP-FREQ", "name": "Frequency Pattern", "min_level": 2},
    "S11": {"shelf": "SH-DECISION", "code": "DEC-REC", "name": "AI Recommendation", "min_level": 2},
    "S12": {"shelf": "SH-DECISION", "code": "DEC-OVER", "name": "Human Override", "min_level": 2},
    "S13": {"shelf": "SH-DECISION", "code": "DEC-HOLD", "name": "Governance Hold", "min_level": 2},
    "S14": {"shelf": "SH-DECISION", "code": "DEC-KILL", "name": "Kill Switch", "min_level": 2},
    "S15": {"shelf": "SH-IDENTITY", "code": "ID-CONC", "name": "Concealed Identity", "min_level": 3},
    "S16": {"shelf": "SH-FORENSIC", "code": "FOR-CHAIN", "name": "Forensic Chain", "min_level": 3},
    "S17": {"shelf": "SH-FORENSIC", "code": "FOR-LINEAGE", "name": "Decision Lineage", "min_level": 3},
}

# S-Level definitions per RFC-003 Section 2
S_LEVELS = {
    1: {"name": "Tactical", "shelves": ["SH-OPER", "SH-RISK", "SH-VALUE"], "temporal": "7d", "can_hold": False, "can_kill": False},
    2: {"name": "Strategic", "shelves": ["SH-OPER", "SH-RISK", "SH-VALUE", "SH-TEMPO", "SH-DECISION"], "temporal": "90d", "can_hold": True, "can_kill": True},
    3: {"name": "Sovereign", "shelves": ["SH-OPER", "SH-RISK", "SH-VALUE", "SH-TEMPO", "SH-DECISION", "SH-IDENTITY", "SH-FORENSIC"], "temporal": "unlimited", "can_hold": True, "can_kill": True},
}


def create_virtue_token(s_level, role="controller", org="windi-test", expired=False, tampered=False):
    """Create a Virtue Token JWT-like structure for testing."""
    now = int(time.time())
    payload = {
        "sub": f"user-{role}-{s_level}",
        "org": org,
        "s_level": s_level,
        "role": role,
        "shelves": S_LEVELS[s_level]["shelves"],
        "temporal": S_LEVELS[s_level]["temporal"],
        "can_hold": S_LEVELS[s_level]["can_hold"],
        "can_kill": S_LEVELS[s_level]["can_kill"],
        "iat": now,
        "exp": now - 3600 if expired else now + 3600,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()
    
    secret = TEST_SECRET if not tampered else "wrong-secret-tampered"
    signature = hmac.new(secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    
    return {
        "header": {"alg": "HS256", "typ": "VT"},
        "payload": payload,
        "payload_b64": payload_b64,
        "signature": signature,
    }


def validate_token(token):
    """Validate a Virtue Token signature and expiration."""
    expected_sig = hmac.new(
        TEST_SECRET.encode(), 
        token["payload_b64"].encode(), 
        hashlib.sha256
    ).hexdigest()
    
    if token["signature"] != expected_sig:
        return {"valid": False, "error": "SIGNATURE_INVALID"}
    
    if token["payload"]["exp"] < int(time.time()):
        return {"valid": False, "error": "TOKEN_EXPIRED"}
    
    return {"valid": True, "s_level": token["payload"]["s_level"]}


def filter_signals(token, all_signals):
    """Filter signals based on Virtue Token S-Level (RBAC enforcement)."""
    validation = validate_token(token)
    if not validation["valid"]:
        return {"error": validation["error"], "signals": []}
    
    s_level = validation["s_level"]
    allowed_shelves = set(S_LEVELS[s_level]["shelves"])
    
    filtered = {}
    for sig_id, sig_data in all_signals.items():
        sig_def = SIGNAL_REGISTRY.get(sig_id)
        if sig_def and sig_def["shelf"] in allowed_shelves and sig_def["min_level"] <= s_level:
            filtered[sig_id] = sig_data
    
    return {"error": None, "signals": filtered}


def create_governance_hold(token, reason, signals_snapshot):
    """Create a Governance Hold with Virtue Receipt."""
    validation = validate_token(token)
    if not validation["valid"]:
        return {"error": validation["error"], "hold": None}
    
    if not S_LEVELS[validation["s_level"]]["can_hold"]:
        return {"error": "INSUFFICIENT_AUTHORITY", "hold": None}
    
    now = datetime.now(timezone.utc).isoformat()
    hold_data = {
        "hold_id": f"HOLD-{hashlib.sha256(now.encode()).hexdigest()[:12].upper()}",
        "reason": reason,
        "initiated_by": token["payload"]["sub"],
        "s_level": validation["s_level"],
        "signals_snapshot": signals_snapshot,
        "timestamp": now,
        "status": "ACTIVE",
    }
    
    # Generate Virtue Receipt
    receipt_content = json.dumps(hold_data, sort_keys=True)
    receipt_hash = hashlib.sha256(receipt_content.encode()).hexdigest()
    
    virtue_receipt = {
        "hash": receipt_hash,
        "hold": hold_data,
        "immutable": True,
        "forensic_registered": True,
    }
    
    return {"error": None, "hold": virtue_receipt}


# ============================================================
# TEST SUITE — 9 Sovereignty Tests
# ============================================================

# --- Sample signal data for testing ---
ALL_SIGNALS = {
    "S1": "DEPT-FINANCE",
    "S2": "IN_REVIEW",
    "S3": "CONTRACT",
    "S4": 78.5,
    "S5": "HIGH",
    "S6": ["DUPLICATE_CLAUSE", "VALUE_MISMATCH"],
    "S7": "R4",
    "S8": "CRITICAL",
    "S9": "2026-03-15",
    "S10": "MONTHLY",
    "S11": "REJECT",
    "S12": None,
    "S13": None,
    "S14": False,
    "S15": "CONCEALED-ENTITY-7291",
    "S16": ["HASH-A1B2", "HASH-C3D4", "HASH-E5F6"],
    "S17": {"origin": "SGE-v1.0", "chain": ["detect", "classify", "recommend"]},
}


class TestVirtueTokenValidation:
    """Test 1-3: Token integrity and authentication."""

    def test_01_valid_token_s1(self):
        """TEST 1: Valid S-Level 1 token authenticates successfully."""
        token = create_virtue_token(s_level=1, role="analyst")
        result = validate_token(token)
        assert result["valid"] is True
        assert result["s_level"] == 1

    def test_02_tampered_token_rejected(self):
        """TEST 2: Tampered token rejected with SIGNATURE_INVALID."""
        token = create_virtue_token(s_level=2, tampered=True)
        result = validate_token(token)
        assert result["valid"] is False
        assert result["error"] == "SIGNATURE_INVALID"

    def test_03_expired_token_rejected(self):
        """TEST 3: Expired token rejected with TOKEN_EXPIRED."""
        token = create_virtue_token(s_level=3, expired=True)
        result = validate_token(token)
        assert result["valid"] is False
        assert result["error"] == "TOKEN_EXPIRED"


class TestRBACSignalFiltering:
    """Test 4-6: S-Level signal visibility enforcement."""

    def test_04_s1_tactical_sees_limited_signals(self):
        """TEST 4: S-Level 1 (Tactical) sees only SH-OPER, SH-RISK, SH-VALUE signals."""
        token = create_virtue_token(s_level=1)
        result = filter_signals(token, ALL_SIGNALS)
        assert result["error"] is None
        visible = set(result["signals"].keys())
        # S1 sees: S1-S7 (OPER + RISK + VALUE shelves, min_level=1)
        expected = {"S1", "S2", "S3", "S4", "S5", "S6", "S7"}
        assert visible == expected, f"S1 should see {expected}, got {visible}"

    def test_05_s2_strategic_sees_expanded_signals(self):
        """TEST 5: S-Level 2 (Strategic) sees all 7 shelves including TEMPO + DECISION."""
        token = create_virtue_token(s_level=2)
        result = filter_signals(token, ALL_SIGNALS)
        assert result["error"] is None
        visible = set(result["signals"].keys())
        # S2 sees: S1-S14 (adds TEMPO + DECISION shelves)
        expected = {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12", "S13", "S14"}
        assert visible == expected, f"S2 should see {expected}, got {visible}"

    def test_06_s1_cannot_see_identity_signals(self):
        """TEST 6: S-Level 1 CANNOT see ID-CONC (concealed identity) — sovereignty enforced."""
        token = create_virtue_token(s_level=1)
        result = filter_signals(token, ALL_SIGNALS)
        assert "S15" not in result["signals"], "S1 must NOT see ID-CONC (S15)"
        assert "S16" not in result["signals"], "S1 must NOT see FOR-CHAIN (S16)"
        assert "S17" not in result["signals"], "S1 must NOT see FOR-LINEAGE (S17)"


class TestGovernanceHold:
    """Test 7-9: Governance Hold and Virtue Receipt generation."""

    def test_07_s1_cannot_activate_hold(self):
        """TEST 7: S-Level 1 (Tactical) CANNOT activate Governance Hold."""
        token = create_virtue_token(s_level=1)
        result = create_governance_hold(token, "Test hold", {"S4": 78.5})
        assert result["error"] == "INSUFFICIENT_AUTHORITY"
        assert result["hold"] is None

    def test_08_s2_can_activate_hold(self):
        """TEST 8: S-Level 2 (Strategic) CAN activate Governance Hold with Virtue Receipt."""
        token = create_virtue_token(s_level=2, role="controller")
        result = create_governance_hold(token, "Risk threshold exceeded", {"S4": 78.5, "S5": "HIGH"})
        assert result["error"] is None
        assert result["hold"] is not None
        receipt = result["hold"]
        assert receipt["immutable"] is True
        assert receipt["forensic_registered"] is True
        assert "hash" in receipt
        assert len(receipt["hash"]) == 64  # SHA-256 hex
        assert receipt["hold"]["status"] == "ACTIVE"
        assert receipt["hold"]["reason"] == "Risk threshold exceeded"

    def test_09_s3_sovereign_full_visibility(self):
        """TEST 9: S-Level 3 (Sovereign) sees ALL 17 signals including forensic lineage."""
        token = create_virtue_token(s_level=3, role="sovereign")
        result = filter_signals(token, ALL_SIGNALS)
        assert result["error"] is None
        visible = set(result["signals"].keys())
        expected = set(ALL_SIGNALS.keys())  # All 17 signals
        assert visible == expected, f"S3 should see ALL {len(expected)} signals, got {len(visible)}"
        # Verify forensic data accessible
        assert result["signals"]["S15"] == "CONCEALED-ENTITY-7291"
        assert isinstance(result["signals"]["S17"], dict)
        assert "chain" in result["signals"]["S17"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
