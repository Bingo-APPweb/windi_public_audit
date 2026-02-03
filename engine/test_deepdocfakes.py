#!/usr/bin/env python3
"""
WINDI DeepDOCFakes — Test Suite
==================================
7 tests covering all critical paths:

  TEST 1: HIGH generates record and validates          → PASS/FAIL
  TEST 2: MEDIUM generates record with identity gov    → PASS/FAIL
  TEST 3: LOW does not persist (metadata-only)         → PASS/FAIL
  TEST 4: Altered payload → TAMPERED                   → PASS/FAIL
  TEST 5: Unknown submission → UNKNOWN                 → PASS/FAIL
  TEST 6: Hash-based verification works                → PASS/FAIL
  TEST 7: Resilience scores are correctly ordered       → PASS/FAIL

Run: python3 test_deepdocfakes.py
"""

import sys
import os
import json
import shutil
import tempfile

# Use temp directory for test storage
TEST_DIR = tempfile.mkdtemp(prefix="windi_test_")
os.environ["WINDI_PROVENANCE_DIR"] = TEST_DIR

# Now import (after setting env)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deepdocfakes.structural_hash import compute_structural_hash, CANONICAL_VERSION
from deepdocfakes.provenance_engine import build_provenance_record, persist_provenance_record, load_provenance_record
from deepdocfakes.verify_engine import verify_by_submission_id, verify_by_hash, VerificationStatus
from deepdocfakes.deepfake_risk import compute_resilience_score, resilience_rating, resilience_factors
from deepdocfakes.pdf_metadata_embed import build_pdf_metadata, verify_pdf_provenance
from deepdocfakes.registry_provenance import registry_stats, registry_integrity_check


def _header(name):
    print(f"\n{'─' * 50}")
    print(f"  {name}")
    print(f"{'─' * 50}")


def _result(test_name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status}  {test_name}")
    if detail:
        print(f"         {detail}")
    return passed


# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

results = []

# ─── TEST 1: HIGH generates record and validates ─────────────
_header("TEST 1: HIGH generates record → VALID")

record_high = build_provenance_record(
    submission_id="TEST-HIGH-001",
    governance_level="HIGH",
    policy_version="2.2.0",
    config_hash="abc123def456",
    isp_profile="bafin",
    organization="BaFin",
    metadata={"document_type": "aufsichtliche_mitteilung", "four_eyes": True},
    identity_governance={"license_status": "model_only", "identity_controlled": True},
    content="Aufsichtliche Mitteilung zur KI-Risikobewertung nach DORA...",
)

# Persist
path = persist_provenance_record(record_high)
results.append(_result(
    "HIGH record persisted",
    path is not None and os.path.exists(path),
    f"Path: {path}"
))

# Verify
verify_result = verify_by_submission_id(
    "TEST-HIGH-001",
    record_high["decision_payload"]
)
results.append(_result(
    "HIGH record verified as VALID",
    verify_result["status"] == VerificationStatus.VALID,
    f"Status: {verify_result['status']}, Checks: {verify_result.get('checks_summary', '')}"
))

# Resilience score
score = record_high["deepfake_resilience"]["score"]
results.append(_result(
    "HIGH resilience score ≥ 85 (MAXIMUM)",
    score >= 85,
    f"Score: {score}/100 — {record_high['deepfake_resilience']['rating']}"
))


# ─── TEST 2: MEDIUM with identity governance ─────────────────
_header("TEST 2: MEDIUM generates record with identity governance")

record_med = build_provenance_record(
    submission_id="TEST-MED-001",
    governance_level="MEDIUM",
    policy_version="2.2.0",
    config_hash="med789ghi012",
    isp_profile="bundesregierung",
    organization="Bundesregierung (Model)",
    metadata={"document_type": "pressemitteilung", "disclaimer": True},
    identity_governance={"license_status": "model_only", "identity_controlled": True},
)

path_med = persist_provenance_record(record_med)
results.append(_result(
    "MEDIUM record persisted",
    path_med is not None,
    f"Path: {path_med}"
))

# Check identity governance is in the record
has_identity = bool(record_med.get("identity_governance", {}).get("license_status"))
results.append(_result(
    "MEDIUM record includes identity governance",
    has_identity,
    f"License: {record_med.get('identity_governance', {}).get('license_status')}"
))


# ─── TEST 3: LOW does NOT persist ────────────────────────────
_header("TEST 3: LOW does not persist (metadata-only)")

record_low = build_provenance_record(
    submission_id="TEST-LOW-001",
    governance_level="LOW",
    isp_profile="tuev",
    organization="TÜV",
    metadata={"document_type": "pruefbericht"},
)

path_low = persist_provenance_record(record_low)
results.append(_result(
    "LOW record NOT persisted",
    path_low is None,
    "Correctly returns None for LOW governance"
))

# But record still has structural hash
results.append(_result(
    "LOW record still has structural hash",
    bool(record_low.get("cryptographic_proof", {}).get("structural_hash")),
    f"Hash: {record_low['cryptographic_proof']['structural_hash'][:32]}..."
))


# ─── TEST 4: Altered payload → TAMPERED ──────────────────────
_header("TEST 4: Altered payload → TAMPERED")

# Modify the decision payload (simulate tampering)
tampered_payload = dict(record_high["decision_payload"])
tampered_payload["organization"] = "FAKE-BaFin"

verify_tampered = verify_by_submission_id("TEST-HIGH-001", tampered_payload)
results.append(_result(
    "Tampered payload detected as TAMPERED",
    verify_tampered["status"] == VerificationStatus.TAMPERED,
    f"Status: {verify_tampered['status']}, Reason: {verify_tampered.get('reason', '')}"
))


# ─── TEST 5: Unknown submission → UNKNOWN ────────────────────
_header("TEST 5: Unknown submission → UNKNOWN")

verify_unknown = verify_by_submission_id("NONEXISTENT-999", {})
results.append(_result(
    "Unknown submission returns UNKNOWN",
    verify_unknown["status"] == VerificationStatus.UNKNOWN,
    f"Status: {verify_unknown['status']}, Reason: {verify_unknown.get('reason', '')}"
))


# ─── TEST 6: Hash-based verification ─────────────────────────
_header("TEST 6: Hash-based verification")

# Get hash prefix from HIGH record
hash_prefix = record_high["cryptographic_proof"]["structural_hash"][:16]
verify_hash = verify_by_hash(hash_prefix)
results.append(_result(
    "Hash-based lookup finds record",
    verify_hash["status"] == VerificationStatus.VALID,
    f"Found via prefix: {hash_prefix}..."
))

# Unknown hash
verify_bad_hash = verify_by_hash("0000000000000000")
results.append(_result(
    "Unknown hash returns UNKNOWN",
    verify_bad_hash["status"] == VerificationStatus.UNKNOWN
))


# ─── TEST 7: Resilience scores correctly ordered ─────────────
_header("TEST 7: Resilience scores ordering HIGH > MEDIUM > LOW")

score_high = record_high["deepfake_resilience"]["score"]
score_med = record_med["deepfake_resilience"]["score"]
score_low = record_low["deepfake_resilience"]["score"]

results.append(_result(
    "HIGH > MEDIUM > LOW resilience ordering",
    score_high > score_med > score_low,
    f"HIGH={score_high} > MEDIUM={score_med} > LOW={score_low}"
))


# ─── BONUS: PDF metadata & registry ──────────────────────────
_header("BONUS: PDF metadata & registry integrity")

# PDF metadata
pdf_meta = build_pdf_metadata(record_high)
results.append(_result(
    "PDF metadata generated for HIGH",
    "windi:ProvenanceID" in pdf_meta and "windi:StructuralHash" in pdf_meta,
    f"Fields: {len(pdf_meta)}"
))

# Registry stats
stats = registry_stats()
results.append(_result(
    "Registry stats available",
    stats["total_records"] >= 2,
    f"Total: {stats['total_records']}, Avg resilience: {stats['avg_resilience_score']}"
))

# Registry integrity
integrity = registry_integrity_check()
results.append(_result(
    "Registry integrity check passes",
    integrity["status"] == "HEALTHY",
    f"Checked: {integrity['records_checked']}, Valid: {integrity['records_valid']}"
))


# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════

print("\n" + "═" * 50)
passed = sum(results)
total = len(results)
print(f"  RESULTS: {passed}/{total} passed")

if passed == total:
    print("  STATUS:  ✅ ALL TESTS PASSED")
    print("  🐉 DeepDOCFakes module ready for production")
else:
    failed = total - passed
    print(f"  STATUS:  ❌ {failed} TEST(S) FAILED")

print("═" * 50)

# Cleanup
shutil.rmtree(TEST_DIR, ignore_errors=True)

sys.exit(0 if passed == total else 1)
