"""
WINDI Agent Security & Forensic Tests
========================================
Tests hash-chained forensic log integrity and security middleware.
"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.forensic_log import ForensicLog, GENESIS_HASH
from core.security import (
    validate_document_hash, validate_doc_type, validate_request_size,
    verify_token, compute_code_hash, RateLimiter,
)


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def ok(self, name):
        self.passed += 1
        print(f"  ✅ {name}")
    
    def fail(self, name, reason=""):
        self.failed += 1
        self.errors.append(f"{name}: {reason}")
        print(f"  ❌ {name} — {reason}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'═' * 50}")
        print(f"  Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"  FAILURES: {self.failed}")
            for e in self.errors:
                print(f"    • {e}")
        else:
            print("  ALL TESTS PASSED ✅")
        print(f"{'═' * 50}")
        return self.failed == 0


def run_tests():
    results = TestResults()
    
    print("🛡 WINDI Agent Security & Forensic Tests")
    print("=" * 50)
    
    # Create temp directory for forensic log tests
    temp_dir = tempfile.mkdtemp(prefix="windi_test_")
    
    try:
        # ═══ FORENSIC LOG TESTS ═══
        print("\n▸ Forensic Log — Hash Chain")
        
        log = ForensicLog(
            log_dir=temp_dir,
            agent_version="1.0.0",
            config_hash="test_config_hash",
        )
        
        # Test: first entry links to genesis
        entry1 = log.append("test_operation_1", {"key": "value1"})
        if entry1.prev_hash == GENESIS_HASH:
            results.ok("Forensic: first entry links to genesis hash")
        else:
            results.fail("Forensic: first entry links to genesis hash")
        
        # Test: second entry links to first
        entry2 = log.append("test_operation_2", {"key": "value2"})
        if entry2.prev_hash == entry1.entry_hash:
            results.ok("Forensic: chain links correctly (entry2 → entry1)")
        else:
            results.fail("Forensic: chain links correctly")
        
        # Test: third entry links to second
        entry3 = log.append("test_operation_3", {"key": "value3"})
        if entry3.prev_hash == entry2.entry_hash:
            results.ok("Forensic: chain links correctly (entry3 → entry2)")
        else:
            results.fail("Forensic: chain links correctly")
        
        # Test: chain verification passes
        report = log.verify_chain()
        if report["valid"] and report["entries_checked"] == 3:
            results.ok("Forensic: chain verification passes (3 entries)")
        else:
            results.fail("Forensic: chain verification passes", str(report))
        
        # Test: hashes are deterministic
        recomputed = entry1.compute_hash()
        if recomputed == entry1.entry_hash:
            results.ok("Forensic: entry hash is deterministic")
        else:
            results.fail("Forensic: entry hash is deterministic")
        
        # Test: sequence is monotonic
        if entry1.sequence < entry2.sequence < entry3.sequence:
            results.ok("Forensic: sequence is monotonically increasing")
        else:
            results.fail("Forensic: sequence is monotonically increasing")
        
        # Test: tamper detection
        print("\n▸ Forensic Log — Tamper Detection")
        
        # Tamper with an entry
        original_hash = entry2.entry_hash
        entry2.detail = {"key": "TAMPERED"}
        tampered_hash = entry2.compute_hash()
        
        if tampered_hash != original_hash:
            results.ok("Forensic: tampering changes hash")
        else:
            results.fail("Forensic: tampering changes hash")
        
        # Restore for further tests
        entry2.detail = {"key": "value2"}
        
        # Test: log written to disk
        log_path = log.get_log_path()
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                lines = f.readlines()
            if len(lines) == 3:
                results.ok("Forensic: all entries persisted to disk")
            else:
                results.fail("Forensic: all entries persisted to disk", f"Found {len(lines)} lines")
        else:
            results.fail("Forensic: log file exists", "File not found")
        
        # ═══ INPUT VALIDATION TESTS ═══
        print("\n▸ Input Validation")
        
        # Valid SHA-256 hash
        valid_hash = "a" * 64
        if validate_document_hash(valid_hash):
            results.ok("Validation: valid SHA-256 accepted")
        else:
            results.fail("Validation: valid SHA-256 accepted")
        
        # Invalid hashes
        if not validate_document_hash("too_short"):
            results.ok("Validation: short hash rejected")
        else:
            results.fail("Validation: short hash rejected")
        
        if not validate_document_hash("g" * 64):  # 'g' is not hex
            results.ok("Validation: non-hex hash rejected")
        else:
            results.fail("Validation: non-hex hash rejected")
        
        # Doc type validation
        if validate_doc_type("CONTRACT"):
            results.ok("Validation: valid doc_type accepted")
        else:
            results.fail("Validation: valid doc_type accepted")
        
        if not validate_doc_type("MALICIOUS_TYPE"):
            results.ok("Validation: invalid doc_type rejected")
        else:
            results.fail("Validation: invalid doc_type rejected")
        
        # Request size
        if validate_request_size(1024):
            results.ok("Validation: normal request size accepted")
        else:
            results.fail("Validation: normal request size accepted")
        
        if not validate_request_size(100 * 1024 * 1024):  # 100MB
            results.ok("Validation: oversized request rejected")
        else:
            results.fail("Validation: oversized request rejected")
        
        # ═══ TOKEN SECURITY TESTS ═══
        print("\n▸ Token Security")
        
        # Correct token
        if verify_token("my_secret_token", "my_secret_token"):
            results.ok("Token: correct token accepted")
        else:
            results.fail("Token: correct token accepted")
        
        # Wrong token
        if not verify_token("wrong_token", "my_secret_token"):
            results.ok("Token: wrong token rejected")
        else:
            results.fail("Token: wrong token rejected")
        
        # Empty token
        if not verify_token("", "my_secret_token"):
            results.ok("Token: empty token rejected")
        else:
            results.fail("Token: empty token rejected")
        
        # None token
        if not verify_token(None, "my_secret_token"):
            results.ok("Token: None token rejected")
        else:
            results.fail("Token: None token rejected")
        
        # ═══ RATE LIMITER TESTS ═══
        print("\n▸ Rate Limiter")
        
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        
        # First 3 requests should pass
        for i in range(3):
            if limiter.is_allowed("test_ip"):
                pass
            else:
                results.fail(f"RateLimiter: request {i+1} allowed")
        results.ok("RateLimiter: first 3 requests allowed")
        
        # 4th request should be blocked
        if not limiter.is_allowed("test_ip"):
            results.ok("RateLimiter: 4th request blocked")
        else:
            results.fail("RateLimiter: 4th request blocked")
        
        # Different IP should be allowed
        if limiter.is_allowed("other_ip"):
            results.ok("RateLimiter: different IP unaffected")
        else:
            results.fail("RateLimiter: different IP unaffected")
        
        # ═══ CODE INTEGRITY TESTS ═══
        print("\n▸ Code Integrity")
        
        agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        code_hash = compute_code_hash(agent_dir)
        
        if len(code_hash) == 64:
            results.ok(f"Code integrity: hash computed ({code_hash[:16]}...)")
        else:
            results.fail("Code integrity: hash computed")
        
        # Hash should be deterministic
        code_hash_2 = compute_code_hash(agent_dir)
        if code_hash == code_hash_2:
            results.ok("Code integrity: hash is deterministic")
        else:
            results.fail("Code integrity: hash is deterministic")
        
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    return results.summary()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
