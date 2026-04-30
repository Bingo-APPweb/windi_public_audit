"""
Tests for canonical hash module
Spec: §227 Section 7
"""

import pytest
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import sys
sys.path.insert(0, '..')

from canonical import (
    canonical_hash,
    hash_field,
    _extract_addr,
    _extract_addrs,
    _strip_dacp_footer
)


class TestExtractAddr:
    """Tests for email address extraction"""

    def test_simple_email(self):
        assert _extract_addr("test@example.com") == "test@example.com"

    def test_name_and_email(self):
        assert _extract_addr("John Doe <john@example.com>") == "john@example.com"

    def test_uppercase(self):
        assert _extract_addr("TEST@EXAMPLE.COM") == "test@example.com"

    def test_none(self):
        assert _extract_addr(None) == ""

    def test_empty(self):
        assert _extract_addr("") == ""


class TestExtractAddrs:
    """Tests for multiple address extraction"""

    def test_single(self):
        assert _extract_addrs(["test@example.com"]) == ["test@example.com"]

    def test_multiple(self):
        result = _extract_addrs(["a@x.com, b@y.com"])
        assert "a@x.com" in result
        assert "b@y.com" in result

    def test_with_names(self):
        result = _extract_addrs(["Alice <a@x.com>", "Bob <b@y.com>"])
        assert result == ["a@x.com", "b@y.com"]


class TestStripDACPFooter:
    """Tests for DACP footer stripping"""

    def test_strip_plain_footer(self):
        body = """Hello World

---
WINDI DACP-v1 PROOF
Proof-ID: WINDI-MAIL-PROOF-123
Verify: https://example.com
"""
        result = _strip_dacp_footer(body)
        assert "WINDI DACP-v1 PROOF" not in result
        assert "Hello World" in result

    def test_strip_html_footer(self):
        html = """<p>Hello</p>
<div data-windi-dacp="v1" style="margin:10px">Footer content</div>
<p>After</p>"""
        result = _strip_dacp_footer(html)
        assert 'data-windi-dacp="v1"' not in result
        assert "<p>Hello</p>" in result

    def test_no_footer(self):
        body = "Just normal text"
        result = _strip_dacp_footer(body)
        assert result == body


class TestCanonicalHash:
    """Tests for canonical hash computation"""

    def test_simple_email(self):
        msg = MIMEText("Hello World")
        msg['From'] = "sender@example.com"
        msg['To'] = "recipient@example.com"
        msg['Subject'] = "Test"
        msg['Date'] = "Thu, 30 Apr 2026 12:00:00 +0000"

        hash1 = canonical_hash(msg)
        hash2 = canonical_hash(msg)

        # Should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex

    def test_crlf_normalization(self):
        """CRLF and LF should produce same hash"""
        msg1 = MIMEText("Hello\r\nWorld")
        msg1['From'] = "a@x.com"
        msg1['To'] = "b@y.com"
        msg1['Subject'] = "Test"
        msg1['Date'] = "Thu, 30 Apr 2026 12:00:00 +0000"

        msg2 = MIMEText("Hello\nWorld")
        msg2['From'] = "a@x.com"
        msg2['To'] = "b@y.com"
        msg2['Subject'] = "Test"
        msg2['Date'] = "Thu, 30 Apr 2026 12:00:00 +0000"

        assert canonical_hash(msg1) == canonical_hash(msg2)

    def test_to_order_normalized(self):
        """To addresses should be sorted for deterministic hash"""
        msg1 = MIMEText("Hello")
        msg1['From'] = "sender@x.com"
        msg1['To'] = "a@x.com, b@y.com"
        msg1['Subject'] = "Test"
        msg1['Date'] = "Thu, 30 Apr 2026 12:00:00 +0000"

        msg2 = MIMEText("Hello")
        msg2['From'] = "sender@x.com"
        msg2['To'] = "b@y.com, a@x.com"  # Different order
        msg2['Subject'] = "Test"
        msg2['Date'] = "Thu, 30 Apr 2026 12:00:00 +0000"

        assert canonical_hash(msg1) == canonical_hash(msg2)


class TestHashField:
    """Tests for field hashing (GDPR compliance)"""

    def test_deterministic(self):
        assert hash_field("test@example.com") == hash_field("test@example.com")

    def test_case_insensitive(self):
        assert hash_field("TEST@EXAMPLE.COM") == hash_field("test@example.com")

    def test_whitespace_stripped(self):
        assert hash_field("  test@example.com  ") == hash_field("test@example.com")

    def test_different_inputs(self):
        assert hash_field("a@x.com") != hash_field("b@y.com")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
