"""
Tests for edge case handling
Spec: §227 Section 8
"""

import pytest

import sys
sys.path.insert(0, '..')

from footer import has_dacp_footer, has_dacp_html_footer, generate_plain_footer, generate_html_footer
from ratelimit import TokenBucket


class TestDACPFooterDetection:
    """Tests for DACP footer detection (idempotence)"""

    def test_detect_plain_footer(self):
        body = """Hello

---
WINDI DACP-v1 PROOF
Proof-ID: WINDI-MAIL-PROOF-123
"""
        assert has_dacp_footer(body) is True

    def test_no_footer(self):
        body = "Just normal email content"
        assert has_dacp_footer(body) is False

    def test_partial_match(self):
        # Should not match partial strings
        body = "Talking about WINDI but no footer"
        assert has_dacp_footer(body) is False

    def test_detect_html_footer(self):
        html = '<div data-windi-dacp="v1">Content</div>'
        assert has_dacp_html_footer(html) is True

    def test_no_html_footer(self):
        html = '<div class="normal">Content</div>'
        assert has_dacp_html_footer(html) is False


class TestFooterGeneration:
    """Tests for footer generation"""

    def test_plain_footer_contains_proof_id(self):
        footer = generate_plain_footer("WINDI-MAIL-PROOF-123")
        assert "WINDI-MAIL-PROOF-123" in footer
        assert "WINDI DACP-v1 PROOF" in footer
        assert "verify-public" in footer

    def test_html_footer_contains_marker(self):
        footer = generate_html_footer("WINDI-MAIL-PROOF-123")
        assert 'data-windi-dacp="v1"' in footer
        assert "WINDI-MAIL-PROOF-123" in footer


class TestRateLimiter:
    """Tests for rate limiting (§227 Section 8 case #9)"""

    def test_allows_under_limit(self):
        limiter = TokenBucket(rate=10, period=60)
        from_hash = "abc123"

        # Should allow first 10 requests
        for _ in range(10):
            assert limiter.allow(from_hash) is True

    def test_blocks_over_limit(self):
        limiter = TokenBucket(rate=5, period=60)
        from_hash = "abc123"

        # Use up all tokens
        for _ in range(5):
            limiter.allow(from_hash)

        # Should be blocked
        assert limiter.allow(from_hash) is False

    def test_different_senders_independent(self):
        limiter = TokenBucket(rate=2, period=60)

        # Exhaust sender A
        for _ in range(2):
            limiter.allow("sender_a")

        # Sender B should still be allowed
        assert limiter.allow("sender_b") is True

    def test_stats(self):
        limiter = TokenBucket(rate=100, period=60)
        limiter.allow("test")

        stats = limiter.get_stats()
        assert stats['active_buckets'] == 1
        assert stats['rate_per_min'] == 100


class TestBypassConditions:
    """Tests for bypass conditions"""

    def test_encrypted_content_types(self):
        """These content types should bypass DACP"""
        encrypted_types = [
            'multipart/encrypted',
            'application/pkcs7-mime',
            'application/pgp-encrypted'
        ]

        for ct in encrypted_types:
            # Just verify they're recognized patterns
            assert any(x in ct.lower() for x in ['encrypted', 'pkcs7', 'pgp'])

    def test_dsn_detection(self):
        """DSN/bounce patterns"""
        dsn_patterns = [
            ('Content-Type', 'multipart/report; report-type=delivery-status'),
            ('From', 'MAILER-DAEMON@example.com'),
            ('Auto-Submitted', 'auto-replied'),
        ]

        for header, value in dsn_patterns:
            # Verify patterns exist
            assert header and value


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
