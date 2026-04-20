"""
W-SHELF-001 — I14 Epistemic Enforcement Tests
§200 — Test-before-fix discipline (same as §199)

All tests MUST FAIL before implementation.
After implementation, all MUST PASS.

Tests:
1. test_i14_pronoun_without_antecedent — "corrige isto" sem referência → 422
2. test_i14_missing_options — "qual é melhor?" sem opções → hedge explícita
3. test_i14_consensus_split — modelos divergentes → declara split
4. test_i14_ungrounded_assertion — número inventado → gate bloqueia
5. test_i14_trilingual_ambiguity — mesmo vector PT/DE/EN
6. test_i14_declared_limit_receipt — bloco I14 gera receipt

Invariants: I14 (Explicit Failure Principle)
"""
import pytest
import httpx
import json

BASE_URL = "http://localhost:8191"


class TestI14EpistemicEnforcement:
    """
    I14 Runtime Enforcement Test Suite.

    Principle: "Non-simulation of understanding"
    The system must not respond as if it understood when it cannot.
    """

    # ══════════════════════════════════════════════════════════════════
    # TEST 1: Pronoun without antecedent
    # ══════════════════════════════════════════════════════════════════

    def test_i14_pronoun_without_antecedent_pt(self):
        """
        Input: "corrige isto" (no referent)
        Expected: 422 INSUFFICIENT_CONTEXT + epistemic_status=ambiguous
        """
        # Step 1: Create request
        resp = httpx.post(f"{BASE_URL}/shelf/request", json={
            "prompt": "corrige isto",
            "user_id": "test-i14-1"
        })
        assert resp.status_code == 200
        req_id = resp.json()["request_id"]

        # Step 2: Interpret — this SHOULD detect ambiguity
        resp = httpx.post(f"{BASE_URL}/shelf/interpret/{req_id}")
        data = resp.json()

        # Expected: epistemic_sufficient=false OR 422
        # Current behavior: returns 200 with intent=system_question (WRONG)
        assert data.get("interpretation", {}).get("epistemic_sufficient") is False, \
            "I14 VIOLATION: 'corrige isto' should be marked as epistemically insufficient"
        assert data.get("interpretation", {}).get("epistemic_status") == "ambiguous", \
            "I14 VIOLATION: Should detect ambiguous reference"
        assert "isto" in data.get("interpretation", {}).get("ambiguity_markers", []), \
            "I14 VIOLATION: Should identify 'isto' as ambiguous pronoun"

    def test_i14_pronoun_without_antecedent_de(self):
        """
        Input: "korrigiere das" (German, no referent)
        Expected: Same as PT version
        """
        resp = httpx.post(f"{BASE_URL}/shelf/request", json={
            "prompt": "korrigiere das",
            "user_id": "test-i14-1-de"
        })
        assert resp.status_code == 200
        req_id = resp.json()["request_id"]

        resp = httpx.post(f"{BASE_URL}/shelf/interpret/{req_id}")
        data = resp.json()

        assert data.get("interpretation", {}).get("epistemic_sufficient") is False, \
            "I14 VIOLATION: 'korrigiere das' should be marked as epistemically insufficient"

    def test_i14_pronoun_without_antecedent_en(self):
        """
        Input: "fix this" (English, no referent)
        Expected: Same as PT version
        """
        resp = httpx.post(f"{BASE_URL}/shelf/request", json={
            "prompt": "fix this",
            "user_id": "test-i14-1-en"
        })
        assert resp.status_code == 200
        req_id = resp.json()["request_id"]

        resp = httpx.post(f"{BASE_URL}/shelf/interpret/{req_id}")
        data = resp.json()

        assert data.get("interpretation", {}).get("epistemic_sufficient") is False, \
            "I14 VIOLATION: 'fix this' should be marked as epistemically insufficient"

    # ══════════════════════════════════════════════════════════════════
    # TEST 2: Missing options/context
    # ══════════════════════════════════════════════════════════════════

    def test_i14_missing_options(self):
        """
        Input: "qual é a melhor opção?" (no options provided)
        Expected: epistemic_status=insufficient_context + missing_context includes "options"
        """
        resp = httpx.post(f"{BASE_URL}/shelf/request", json={
            "prompt": "qual é a melhor opção?",
            "user_id": "test-i14-2"
        })
        assert resp.status_code == 200
        req_id = resp.json()["request_id"]

        resp = httpx.post(f"{BASE_URL}/shelf/interpret/{req_id}")
        data = resp.json()

        interp = data.get("interpretation", {})
        assert interp.get("epistemic_sufficient") is False, \
            "I14 VIOLATION: 'qual é a melhor?' without options is insufficient"
        assert interp.get("epistemic_status") == "insufficient_context", \
            "I14 VIOLATION: Should be insufficient_context, not ambiguous"
        assert "options" in interp.get("missing_context", []) or \
               "choices" in interp.get("missing_context", []), \
            "I14 VIOLATION: Should identify missing options/choices"

    def test_i14_missing_document(self):
        """
        Input: "analisa este documento" (no document)
        Expected: insufficient_context + missing_context includes "document"
        """
        resp = httpx.post(f"{BASE_URL}/shelf/request", json={
            "prompt": "analisa este documento",
            "user_id": "test-i14-2b"
        })
        assert resp.status_code == 200
        req_id = resp.json()["request_id"]

        resp = httpx.post(f"{BASE_URL}/shelf/interpret/{req_id}")
        data = resp.json()

        interp = data.get("interpretation", {})
        assert interp.get("epistemic_sufficient") is False, \
            "I14 VIOLATION: 'analisa este documento' without document is insufficient"
        assert "document" in str(interp.get("missing_context", [])).lower(), \
            "I14 VIOLATION: Should identify missing document"

    # ══════════════════════════════════════════════════════════════════
    # TEST 3: Consensus split (mock divergent models)
    # ══════════════════════════════════════════════════════════════════

    def test_i14_consensus_split(self):
        """
        When multiple interpretations diverge materially,
        the system must declare split, not hide it.

        This test uses the Codex assist endpoint with conflicting context.
        """
        # Create a request that could have multiple valid interpretations
        resp = httpx.post(f"{BASE_URL}/shelf/request", json={
            "prompt": "devemos usar a opção A ou a opção B? ambas têm méritos",
            "user_id": "test-i14-3"
        })
        assert resp.status_code == 200
        req_id = resp.json()["request_id"]

        resp = httpx.post(f"{BASE_URL}/shelf/interpret/{req_id}")
        data = resp.json()

        # If there's genuine conflict, epistemic_status should reflect it
        interp = data.get("interpretation", {})

        # For now, we check if the system at least recognizes uncertainty
        # Full consensus split detection requires Grove integration
        if "ambas" in "devemos usar a opção A ou a opção B? ambas têm méritos".lower():
            assert interp.get("confidence", 1.0) < 0.8, \
                "I14 VIOLATION: Conflicting options should reduce confidence"

    # ══════════════════════════════════════════════════════════════════
    # TEST 4: Ungrounded assertion gate
    # ══════════════════════════════════════════════════════════════════

    def test_i14_ungrounded_assertion_gate(self):
        """
        The Codex mock should not emit confident assertions
        when the context doesn't support them.

        This tests the assertion gate (Layer 3).
        """
        # First create a valid flow
        resp = httpx.post(f"{BASE_URL}/shelf/request", json={
            "prompt": "quanto custa o serviço X?",  # Asking for specific number
            "user_id": "test-i14-4"
        })
        req_id = resp.json()["request_id"]

        resp = httpx.post(f"{BASE_URL}/shelf/interpret/{req_id}")
        data = resp.json()
        twin_id = data.get("twin_id")

        # Create handshake for Codex assist
        resp = httpx.post(
            f"{BASE_URL}/shelf/handshake",
            params={
                "from_agent": "interpreter",
                "to_agent": "codex",
                "purpose": "price_query",
                "scope": ["analyze"],
                "linked_twin": twin_id
            }
        )
        hs_id = resp.json()["handshake_id"]

        # Accept handshake
        resp = httpx.patch(f"{BASE_URL}/shelf/handshake/{hs_id}/accept")

        # Now call Codex assist
        resp = httpx.post(f"{BASE_URL}/shelf/codex/assist", json={
            "intent": "price_query",
            "agent_role": "witness",
            "context": "User asking about price of service X",
            "linked_twin": twin_id,
            "linked_handshake": hs_id
        })

        codex_result = resp.json()

        # The Codex should NOT invent a price
        # It should mark this as ungrounded if it tries to give a specific number
        assert "ungrounded" in str(codex_result.get("risks", [])).lower() or \
               codex_result.get("confidence_adjustment", 0) <= 0.1, \
            "I14 VIOLATION: Codex should not confidently answer ungrounded price queries"

    # ══════════════════════════════════════════════════════════════════
    # TEST 5: Trilingual ambiguity detection
    # ══════════════════════════════════════════════════════════════════

    def test_i14_trilingual_ambiguity(self):
        """
        Ambiguity detection must work in PT, DE, and EN.

        Test phrase: "do it for me" / "mach das für mich" / "faz isso por mim"
        All contain agency transfer + ambiguous target.
        """
        test_cases = [
            ("faz isso por mim", "pt"),
            ("mach das für mich", "de"),
            ("do it for me", "en"),
        ]

        for prompt, lang in test_cases:
            resp = httpx.post(f"{BASE_URL}/shelf/request", json={
                "prompt": prompt,
                "user_id": f"test-i14-5-{lang}",
                "language": lang
            })
            assert resp.status_code == 200
            req_id = resp.json()["request_id"]

            resp = httpx.post(f"{BASE_URL}/shelf/interpret/{req_id}")
            data = resp.json()

            interp = data.get("interpretation", {})

            # Should detect either agency (I9) or ambiguity (I14) or both
            is_agency = interp.get("requires_human_approval", False)
            is_ambiguous = interp.get("epistemic_sufficient") is False

            assert is_agency or is_ambiguous, \
                f"I14 VIOLATION: '{prompt}' ({lang}) should trigger I9 or I14 detection"

    # ══════════════════════════════════════════════════════════════════
    # TEST 6: Declared limit receipt (Ledger seal)
    # ══════════════════════════════════════════════════════════════════

    def test_i14_declared_limit_receipt(self):
        """
        When I14 blocks, it must generate a Ledger receipt.

        Type: I14_DECLARED_LIMIT
        Fields: input_hash, epistemic_status, missing_context, etc.
        """
        # This test requires the full I14 implementation
        # For now, we verify the endpoint exists and returns proper structure

        resp = httpx.post(f"{BASE_URL}/shelf/request", json={
            "prompt": "isto",  # Maximally ambiguous
            "user_id": "test-i14-6"
        })
        req_id = resp.json()["request_id"]

        resp = httpx.post(f"{BASE_URL}/shelf/interpret/{req_id}")
        data = resp.json()

        # After full implementation, this should include:
        # - i14_block_receipt_id (if blocked)
        # - The receipt should be verifiable at /verify-public/

        interp = data.get("interpretation", {})

        # If epistemic_sufficient is False, there should be a receipt
        if interp.get("epistemic_sufficient") is False:
            assert "i14_block_receipt" in data or "receipt_id" in data, \
                "I14 VIOLATION: Epistemic block should generate Ledger receipt"


# ══════════════════════════════════════════════════════════════════════
# REGRESSION TESTS (must continue to pass)
# ══════════════════════════════════════════════════════════════════════

class TestI14NoFalsePositives:
    """
    Ensure I14 doesn't over-block clear, valid queries.
    """

    def test_clear_knowledge_request_passes(self):
        """
        Input: "How does the Forensic Ledger work in WINDI?"
        Expected: epistemic_sufficient=true, normal flow
        """
        resp = httpx.post(f"{BASE_URL}/shelf/request", json={
            "prompt": "How does the Forensic Ledger work in WINDI?",
            "user_id": "test-i14-regression-1"
        })
        req_id = resp.json()["request_id"]

        resp = httpx.post(f"{BASE_URL}/shelf/interpret/{req_id}")
        data = resp.json()

        interp = data.get("interpretation", {})

        # This is a clear query with sufficient context
        # It should NOT be blocked by I14
        assert interp.get("epistemic_sufficient", True) is True, \
            "I14 FALSE POSITIVE: Clear knowledge request should not be blocked"
        assert interp.get("intent") == "knowledge_request", \
            "Clear knowledge request should be classified correctly"

    def test_specific_technical_query_passes(self):
        """
        Input: "What is the nginx configuration for port 8191?"
        Expected: epistemic_sufficient=true
        """
        resp = httpx.post(f"{BASE_URL}/shelf/request", json={
            "prompt": "What is the nginx configuration for port 8191?",
            "user_id": "test-i14-regression-2"
        })
        req_id = resp.json()["request_id"]

        resp = httpx.post(f"{BASE_URL}/shelf/interpret/{req_id}")
        data = resp.json()

        interp = data.get("interpretation", {})

        assert interp.get("epistemic_sufficient", True) is True, \
            "I14 FALSE POSITIVE: Specific technical query should not be blocked"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
