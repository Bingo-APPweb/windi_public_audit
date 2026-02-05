"""
WINDI Dragon Council Integration Test — 8 tests covering full pipeline.
AI processes. Human decides. WINDI guarantees.
"""
import os, sys, json, shutil

TEST_DIR = "/tmp/windi-dc-test"
ENGINE = os.path.dirname(os.path.abspath(__file__))
ISP = os.path.join(os.path.dirname(ENGINE), "isp")
SUBS = os.path.join(TEST_DIR, "submissions")
CFG = os.path.join(ENGINE, "governance_levels.json")

if os.path.exists(TEST_DIR): shutil.rmtree(TEST_DIR)
os.makedirs(SUBS, exist_ok=True)
sys.path.insert(0, ENGINE)

from governance_validator import GovernanceValidator
from submission_id import generate_submission_id
from tamper_evidence import seal_record, verify_record
from submission_registry import SubmissionRegistry
from isp_governance_loader import ISPLoader
from audit_dashboard import AuditDashboard

BIS_META = {
    "reporting_entity": "European Central Bank (Model)",
    "reporting_entity_identifier": "ECB-MODEL-001",
    "reporting_scope": "euro_area",
    "reference_period": "2026-Q1",
    "data_frequency": "quarterly",
    "consolidation_level": "consolidated",
    "statistical_framework": "ESA2010",
    "confidentiality_level": "restricted",
    "data_owner": "DG-Statistics",
    "validation_status": "provisional",
}

passed = failed = 0
def test(name, fn):
    global passed, failed
    try:
        fn(); print(f"  PASS  {name}"); passed += 1
    except Exception as e:
        print(f"  FAIL  {name}\n        {e}"); failed += 1

print("=" * 70)
print("WINDI Dragon Council Integration Test")
print("=" * 70)

loader = ISPLoader(CFG, ISP, SUBS)
loader.load_all()

def t1():
    pkg = loader.generate_document("deutsche-bahn", document_id="DB-001")
    assert pkg["status"] == "APPROVED"
    assert pkg["governance_level"] == "LOW"
    assert "submission_id" not in pkg
test("1. Deutsche Bahn LOW passes without metadata", t1)

def t2():
    try:
        loader.generate_document("bis-style", document_id="FAIL-001")
        assert False, "Should block"
    except ValueError as e:
        assert "required" in str(e).lower() or "BLOCKED" in str(e)
test("2. BIS-Style HIGH blocked without metadata", t2)

def t3():
    pkg = loader.generate_document("bis-style", metadata=BIS_META,
        document_id="BIS-001", policy_version="2.0.0")
    assert pkg["status"] == "APPROVED"
    assert pkg["governance_level"] == "HIGH"
    assert pkg["submission_id"].startswith("REG-")
    assert "integrity_hash" in pkg["audit_record"]
    assert "sealed_at" in pkg["audit_record"]
test("3. BIS-Style HIGH approved with full metadata", t3)

def t4():
    try:
        loader.generate_document("bis-style", metadata=BIS_META,
            governance_level="LOW", document_id="DOWN-001")
        assert False, "Should block downgrade"
    except ValueError as e:
        assert "downgrade" in str(e).lower() or "not allowed" in str(e).lower()
test("4. No-downgrade enforcement", t4)

def t5():
    r = {"test": "data", "value": 42}
    seal_record(r)
    assert "integrity_hash" in r
    ok, _ = verify_record(r)
    assert ok
    r["test"] = "TAMPERED"
    ok, msg = verify_record(r)
    assert not ok and "TAMPER" in msg
test("5. Tamper evidence: seal + verify + detect", t5)

def t6():
    for i in range(3):
        m = dict(BIS_META, reference_period=f"2026-Q{i+1}")
        loader.generate_document("bis-style", metadata=m,
            document_id=f"BATCH-{i}", policy_version="2.0.0")
    reg = SubmissionRegistry(SUBS)
    assert reg.get_stats()["total"] >= 4
    assert len(reg.query(level="HIGH", limit=10)) >= 4
    assert len(reg.query(entity="European Central Bank")) >= 1
test("6. Registry: register + query + stats", t6)

def t7():
    dash = AuditDashboard(SUBS)
    ov = dash.overview()
    assert ov["statistics"]["total"] >= 4
    assert len(ov["recent"]) > 0
    ic = dash.integrity_check()
    assert ic["status"] in ("INTACT", "ATTENTION")
    er = dash.entity_report("European Central Bank")
    assert er["total"] >= 1
test("7. Audit dashboard: overview + integrity + entity", t7)

def t8():
    bad = dict(BIS_META, data_frequency="biweekly")
    try:
        loader.generate_document("bis-style", metadata=bad,
            document_id="BAD-001", policy_version="2.0.0")
        assert False, "Should reject biweekly"
    except ValueError as e:
        assert "biweekly" in str(e) and "Allowed" in str(e)
test("8. Rejects invalid allowed values", t8)

print()
print("=" * 70)
total = passed + failed
print(f"Results: {passed}/{total} passed, {failed} failed")
if failed == 0:
    print()
    print("Dragon Council merge: VALIDATED")
    print()
    print("Sarcofago Draconico  ->  Producao Institucional")
    print("  PoP hash           ->  integrity_hash (tamper_evidence.py)")
    print("  traceId            ->  submission_id  (submission_id.py)")
    print("  contentHash        ->  config_hash    (governance_validator.py)")
    print("  IPFS anchor        ->  registry       (submission_registry.py)")
    print("  Forensic PDF       ->  dashboard      (audit_dashboard.py)")
print()
print("AI processes. Human decides. WINDI guarantees.")
print("=" * 70)
