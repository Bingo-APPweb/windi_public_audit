#!/usr/bin/env python3
"""
JMPG Trigger Builder — P1 Sovereign Spec Implementation
WINDI Publishing House — 27 Feb 2026

Builds sovereign .jmpg trigger binaries per JMPG-SPEC-P1-v1.0

Binary Layout:
┌──────────────────────────────────────────────────┐
│ MAGIC      4B   0x4A4D5047 ("JMPG")             │
│ VERSION    2B   0x0100 (v1.0)                    │
│ FLAGS      2B   bitfield                          │
│ CODEC_ID   1B   0x01=H264, 0x02=AV1, 0x03=VP9   │
│ DURATION   4B   milliseconds (uint32 LE)          │
│ DID_HASH   32B  SHA-256 of creator DID            │
│ MANIFEST_LEN 4B length of compressed manifest     │
│ MANIFEST   var  zlib-compressed JSON               │
│ CONTENT_LEN 4B  length of onboard segment         │
│ CONTENT    var  onboard bytes (max 30s)            │
│ SEAL       32B  SHA-256 of complete package        │
└──────────────────────────────────────────────────┘

"AI processes. Human decides. WINDI guarantees."
"""

import struct
import hashlib
import json
import zlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


class JMPGTriggerBuilder:
    """
    Builds a sovereign .jmpg trigger binary.

    Usage:
        builder = JMPGTriggerBuilder(creator_did_hash)
        builder.set_onboard(video_bytes, duration_ms)
        builder.set_manifest(stream_url, vault_ref, chapters, receipt_id)
        data = builder.build()

        # Save to file
        with open('trigger.jmpg', 'wb') as f:
            f.write(data)
    """

    # Magic bytes: "JMPG" in ASCII
    MAGIC = b'\x4A\x4D\x50\x47'

    # Protocol version 1.0
    VERSION = 0x0100

    # Codec identifiers
    CODEC_H264 = 0x01
    CODEC_AV1 = 0x02
    CODEC_VP9 = 0x03

    # Flag bits
    FLAG_HAS_VIDEO = 0x01
    FLAG_HAS_AUDIO = 0x02
    FLAG_HAS_TEXT = 0x04
    FLAG_HAS_SEAL = 0x08
    FLAG_ENCRYPTED = 0x10
    FLAG_HAS_CHAPTERS = 0x20
    FLAG_PREMIUM = 0x40
    FLAG_RESERVED = 0x80

    # Limits
    MAX_ONBOARD_DURATION_MS = 30000  # 30 seconds
    MAX_ONBOARD_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self, creator_did_hash: str, codec_id: int = 0x01):
        """
        Initialize the JMPG Trigger Builder.

        Args:
            creator_did_hash: 64-character hex string (SHA-256 of creator DID)
            codec_id: Video codec (0x01=H.264, 0x02=AV1, 0x03=VP9)

        Raises:
            AssertionError: If DID hash is not 64 hex characters
        """
        assert len(creator_did_hash) == 64, f"DID hash must be 64 hex chars, got {len(creator_did_hash)}"
        assert all(c in '0123456789abcdefABCDEF' for c in creator_did_hash), "DID hash must be valid hex"

        self.creator_did_hash = creator_did_hash.lower()
        self.codec_id = codec_id
        self.flags = self.FLAG_HAS_SEAL  # Always sealed
        self.duration_ms = 0
        self.onboard_bytes = b''
        self.manifest: Dict[str, Any] = {}
        self._built: Optional[bytes] = None
        self._created_at = datetime.now(timezone.utc)

    def set_onboard(self, video_bytes: bytes, duration_ms: int) -> 'JMPGTriggerBuilder':
        """
        Set the onboard video segment (max 30 seconds).

        Args:
            video_bytes: Raw video data (H.264/AV1/VP9 encoded)
            duration_ms: Duration in milliseconds (max 30000)

        Returns:
            self for method chaining

        Raises:
            AssertionError: If duration exceeds 30s or size exceeds 10MB
        """
        assert duration_ms <= self.MAX_ONBOARD_DURATION_MS, \
            f"Onboard max {self.MAX_ONBOARD_DURATION_MS}ms (30s), got {duration_ms}ms"
        assert len(video_bytes) <= self.MAX_ONBOARD_SIZE, \
            f"Onboard max {self.MAX_ONBOARD_SIZE} bytes, got {len(video_bytes)}"

        self.onboard_bytes = video_bytes
        self.duration_ms = duration_ms
        self._built = None  # Invalidate cache

        if video_bytes:
            self.flags |= self.FLAG_HAS_VIDEO

        return self

    def set_audio(self, has_audio: bool = True) -> 'JMPGTriggerBuilder':
        """Mark that the onboard segment contains audio."""
        if has_audio:
            self.flags |= self.FLAG_HAS_AUDIO
        else:
            self.flags &= ~self.FLAG_HAS_AUDIO
        self._built = None
        return self

    def set_text_layer(self, has_text: bool = True) -> 'JMPGTriggerBuilder':
        """Mark that the content has text/subtitle layer."""
        if has_text:
            self.flags |= self.FLAG_HAS_TEXT
        else:
            self.flags &= ~self.FLAG_HAS_TEXT
        self._built = None
        return self

    def set_encrypted(self, encrypted: bool = True) -> 'JMPGTriggerBuilder':
        """Mark that the manifest is encrypted."""
        if encrypted:
            self.flags |= self.FLAG_ENCRYPTED
        else:
            self.flags &= ~self.FLAG_ENCRYPTED
        self._built = None
        return self

    def set_premium(self, premium: bool = True) -> 'JMPGTriggerBuilder':
        """Mark as premium content (requires subscription)."""
        if premium:
            self.flags |= self.FLAG_PREMIUM
        else:
            self.flags &= ~self.FLAG_PREMIUM
        self._built = None
        return self

    def set_manifest(
        self,
        stream_url: str,
        vault_ref: str,
        chapters: Optional[List[Dict[str, Any]]] = None,
        receipt_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> 'JMPGTriggerBuilder':
        """
        Set the manifest JSON that will be zlib-compressed.

        Args:
            stream_url: URL to the full video stream (on Vault)
            vault_ref: Vault receipt reference
            chapters: List of chapter markers [{title, offset_ms}, ...]
            receipt_id: Ledger receipt ID for governance
            title: Content title
            description: Content description
            thumbnail_url: URL to thumbnail image
            extra: Additional metadata to include

        Returns:
            self for method chaining
        """
        chapters = chapters or []

        if chapters:
            self.flags |= self.FLAG_HAS_CHAPTERS

        self.manifest = {
            "protocol_version": "1.0",
            "creator_did_hash": self.creator_did_hash,
            "stream_url": stream_url,
            "vault_ref": vault_ref,
            "chapters": chapters,
            "onboard_duration_ms": self.duration_ms,
            "governance_receipt_id": receipt_id or "",
            "created_at": self._created_at.isoformat(),
        }

        # Optional fields
        if title:
            self.manifest["title"] = title
        if description:
            self.manifest["description"] = description
        if thumbnail_url:
            self.manifest["thumbnail_url"] = thumbnail_url

        # Merge extra metadata
        if extra:
            self.manifest.update(extra)

        self._built = None
        return self

    def build(self) -> bytes:
        """
        Build the complete JMPG trigger binary.

        Returns:
            Complete binary data ready to save as .jmpg file

        Raises:
            ValueError: If manifest not set
        """
        if not self.manifest:
            raise ValueError("Manifest not set. Call set_manifest() first.")

        # Compress manifest
        manifest_json = json.dumps(
            self.manifest,
            separators=(',', ':'),
            sort_keys=True,
            ensure_ascii=False
        ).encode('utf-8')
        manifest_compressed = zlib.compress(manifest_json, level=9)

        # Build header + body (without seal)
        parts = bytearray()

        # MAGIC (4 bytes)
        parts.extend(self.MAGIC)

        # VERSION (2 bytes, little-endian)
        parts.extend(struct.pack('<H', self.VERSION))

        # FLAGS (2 bytes, little-endian)
        parts.extend(struct.pack('<H', self.flags))

        # CODEC_ID (1 byte)
        parts.extend(struct.pack('B', self.codec_id))

        # DURATION (4 bytes, little-endian)
        parts.extend(struct.pack('<I', self.duration_ms))

        # DID_HASH (32 bytes)
        parts.extend(bytes.fromhex(self.creator_did_hash))

        # MANIFEST_LEN (4 bytes) + MANIFEST (variable)
        parts.extend(struct.pack('<I', len(manifest_compressed)))
        parts.extend(manifest_compressed)

        # CONTENT_LEN (4 bytes) + CONTENT (variable)
        parts.extend(struct.pack('<I', len(self.onboard_bytes)))
        parts.extend(self.onboard_bytes)

        # Calculate SEAL (SHA-256 of everything above)
        seal = hashlib.sha256(bytes(parts)).digest()
        parts.extend(seal)

        self._built = bytes(parts)
        return self._built

    def seal_hex(self) -> str:
        """
        Return the SHA-256 seal as hex string.

        Returns:
            64-character hex string of the seal
        """
        if not self._built:
            self.build()
        return self._built[-32:].hex()

    def package_id(self) -> str:
        """
        Generate canonical package ID.

        Format: JMPG-YYYYMMDD-XXXXXXXX (8 chars of seal)

        Returns:
            Unique package identifier
        """
        seal = self.seal_hex()
        ts = self._created_at.strftime('%Y%m%d')
        return f"JMPG-{ts}-{seal[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Return metadata dict for Ledger registration.

        Returns:
            Dict with all metadata for the JMPG trigger
        """
        if not self._built:
            self.build()

        manifest_json = json.dumps(self.manifest, separators=(',', ':'), sort_keys=True).encode()

        return {
            "package_id": self.package_id(),
            "seal": self.seal_hex(),
            "creator_did_hash": self.creator_did_hash,
            "codec_id": self.codec_id,
            "codec_name": {0x01: "H.264", 0x02: "AV1", 0x03: "VP9"}.get(self.codec_id, "unknown"),
            "duration_ms": self.duration_ms,
            "flags": self.flags,
            "flags_decoded": self._decode_flags(),
            "manifest_size_raw": len(manifest_json),
            "manifest_size_compressed": len(zlib.compress(manifest_json, 9)),
            "content_size": len(self.onboard_bytes),
            "total_size": len(self._built),
            "header_size": 49,  # Fixed header size
            "created_at": self._created_at.isoformat(),
            "manifest": self.manifest,
        }

    def _decode_flags(self) -> List[str]:
        """Decode flags bitfield to list of strings."""
        flags = []
        if self.flags & self.FLAG_HAS_VIDEO:
            flags.append("HAS_VIDEO")
        if self.flags & self.FLAG_HAS_AUDIO:
            flags.append("HAS_AUDIO")
        if self.flags & self.FLAG_HAS_TEXT:
            flags.append("HAS_TEXT")
        if self.flags & self.FLAG_HAS_SEAL:
            flags.append("HAS_SEAL")
        if self.flags & self.FLAG_ENCRYPTED:
            flags.append("ENCRYPTED")
        if self.flags & self.FLAG_HAS_CHAPTERS:
            flags.append("HAS_CHAPTERS")
        if self.flags & self.FLAG_PREMIUM:
            flags.append("PREMIUM")
        return flags


class JMPGTriggerParser:
    """
    Parse and verify a .jmpg trigger binary.

    Usage:
        with open('trigger.jmpg', 'rb') as f:
            data = f.read()

        parser = JMPGTriggerParser(data)
        result = parser.verify()

        if result['valid']:
            print("Seal verified!")
            print(f"Stream URL: {result['manifest']['stream_url']}")
    """

    MAGIC = b'\x4A\x4D\x50\x47'
    MIN_SIZE = 49 + 32  # Header + seal minimum

    def __init__(self, data: bytes):
        """
        Initialize parser with binary data.

        Args:
            data: Complete .jmpg binary data
        """
        self.data = data
        self.valid = False
        self.error: Optional[str] = None
        self.header: Dict[str, Any] = {}
        self.manifest: Dict[str, Any] = {}
        self.content: bytes = b''
        self.seal: str = ''
        self._parse()

    def _parse(self) -> None:
        """Parse the binary data."""
        try:
            if len(self.data) < self.MIN_SIZE:
                self.error = f"Data too short: {len(self.data)} < {self.MIN_SIZE}"
                return

            offset = 0

            # MAGIC (4 bytes)
            magic = self.data[offset:offset + 4]
            if magic != self.MAGIC:
                self.error = f"Invalid magic: {magic.hex()} != {self.MAGIC.hex()}"
                return
            offset += 4

            # VERSION (2 bytes)
            version = struct.unpack_from('<H', self.data, offset)[0]
            offset += 2

            # FLAGS (2 bytes)
            flags = struct.unpack_from('<H', self.data, offset)[0]
            offset += 2

            # CODEC_ID (1 byte)
            codec_id = struct.unpack_from('B', self.data, offset)[0]
            offset += 1

            # DURATION (4 bytes)
            duration_ms = struct.unpack_from('<I', self.data, offset)[0]
            offset += 4

            # DID_HASH (32 bytes)
            did_hash = self.data[offset:offset + 32].hex()
            offset += 32

            # MANIFEST_LEN (4 bytes) + MANIFEST (variable)
            manifest_len = struct.unpack_from('<I', self.data, offset)[0]
            offset += 4

            if offset + manifest_len > len(self.data):
                self.error = f"Manifest length exceeds data: {offset + manifest_len} > {len(self.data)}"
                return

            manifest_compressed = self.data[offset:offset + manifest_len]
            offset += manifest_len

            # CONTENT_LEN (4 bytes) + CONTENT (variable)
            content_len = struct.unpack_from('<I', self.data, offset)[0]
            offset += 4

            if offset + content_len > len(self.data):
                self.error = f"Content length exceeds data: {offset + content_len} > {len(self.data)}"
                return

            self.content = self.data[offset:offset + content_len]
            offset += content_len

            # SEAL (32 bytes)
            if offset + 32 > len(self.data):
                self.error = f"Missing seal: data ends at {len(self.data)}, need {offset + 32}"
                return

            self.seal = self.data[offset:offset + 32].hex()

            # Verify seal
            body = self.data[:offset]
            expected_seal = hashlib.sha256(body).hexdigest()
            self.valid = (expected_seal == self.seal)

            if not self.valid:
                self.error = f"Seal mismatch: {expected_seal[:16]}... != {self.seal[:16]}..."

            # Decompress manifest
            try:
                manifest_json = zlib.decompress(manifest_compressed)
                self.manifest = json.loads(manifest_json)
            except Exception as e:
                self.error = f"Manifest decompression failed: {e}"
                self.manifest = {}

            # Build header info
            self.header = {
                "magic": magic.decode('ascii'),
                "version": f"{version >> 8}.{version & 0xFF}",
                "version_raw": version,
                "flags": flags,
                "flags_decoded": self._decode_flags(flags),
                "codec_id": codec_id,
                "codec_name": {0x01: "H.264", 0x02: "AV1", 0x03: "VP9"}.get(codec_id, "unknown"),
                "duration_ms": duration_ms,
                "duration_s": duration_ms / 1000,
                "creator_did_hash": did_hash,
                "manifest_size": manifest_len,
                "content_size": content_len,
                "seal": self.seal,
                "valid": self.valid,
            }

        except Exception as e:
            self.error = f"Parse error: {e}"
            self.valid = False

    def _decode_flags(self, flags: int) -> List[str]:
        """Decode flags bitfield."""
        result = []
        if flags & 0x01: result.append("HAS_VIDEO")
        if flags & 0x02: result.append("HAS_AUDIO")
        if flags & 0x04: result.append("HAS_TEXT")
        if flags & 0x08: result.append("HAS_SEAL")
        if flags & 0x10: result.append("ENCRYPTED")
        if flags & 0x20: result.append("HAS_CHAPTERS")
        if flags & 0x40: result.append("PREMIUM")
        return result

    def verify(self) -> Dict[str, Any]:
        """
        Return verification result.

        Returns:
            Dict with validation status and all parsed data
        """
        return {
            "valid": self.valid,
            "error": self.error,
            "seal": self.seal,
            "header": self.header,
            "manifest": self.manifest,
            "content_size": len(self.content),
            "total_size": len(self.data),
        }

    def get_stream_url(self) -> Optional[str]:
        """Get the stream URL from manifest."""
        return self.manifest.get("stream_url")

    def get_vault_ref(self) -> Optional[str]:
        """Get the vault reference from manifest."""
        return self.manifest.get("vault_ref")

    def get_receipt_id(self) -> Optional[str]:
        """Get the governance receipt ID from manifest."""
        return self.manifest.get("governance_receipt_id")


def create_did_hash(did: str) -> str:
    """
    Create a SHA-256 hash of a DID string.

    Args:
        did: The DID string (e.g., "did:windi:abc123")

    Returns:
        64-character hex hash
    """
    return hashlib.sha256(did.encode('utf-8')).hexdigest()


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys

    print("=" * 60)
    print("JMPG TRIGGER BUILDER — P1 Sovereign Spec Test")
    print("WINDI Publishing House — 27 Feb 2026")
    print("=" * 60)
    print()

    # Create test DID hash
    test_did = "did:windi:test-creator-001"
    did_hash = create_did_hash(test_did)
    print(f"Test DID: {test_did}")
    print(f"DID Hash: {did_hash}")
    print()

    # Build a test trigger
    builder = JMPGTriggerBuilder(did_hash, JMPGTriggerBuilder.CODEC_H264)

    # Set onboard (fake video data for test)
    fake_video = b'FAKE_H264_VIDEO_DATA_' * 100  # ~2.1KB
    builder.set_onboard(fake_video, 30000)  # 30 seconds
    builder.set_audio(True)
    builder.set_text_layer(True)

    # Set manifest
    builder.set_manifest(
        stream_url="https://vault.windi-media.com/stream/test-001/master.m3u8",
        vault_ref="VR-VAULT-TEST-001",
        chapters=[
            {"title": "Intro", "offset_ms": 0},
            {"title": "Main Content", "offset_ms": 15000},
            {"title": "Outro", "offset_ms": 25000},
        ],
        receipt_id="VR-TRIGGER-TEST-001",
        title="Test Sovereign Video",
        description="A test video demonstrating the JMPG format",
        thumbnail_url="https://vault.windi-media.com/thumb/test-001.webp",
        extra={
            "language": "de",
            "category": "test",
            "tags": ["windi", "sovereign", "test"],
        }
    )

    # Build
    data = builder.build()

    print("=== BUILD RESULT ===")
    print(f"  Package ID:   {builder.package_id()}")
    print(f"  Total Size:   {len(data)} bytes ({len(data)/1024:.2f} KB)")
    print(f"  Seal:         {builder.seal_hex()}")
    print()

    # Show metadata
    meta = builder.to_dict()
    print("=== METADATA ===")
    print(f"  Codec:        {meta['codec_name']} (0x{meta['codec_id']:02X})")
    print(f"  Duration:     {meta['duration_ms']}ms")
    print(f"  Flags:        {', '.join(meta['flags_decoded'])}")
    print(f"  Header Size:  {meta['header_size']} bytes")
    print(f"  Manifest:     {meta['manifest_size_raw']} → {meta['manifest_size_compressed']} bytes (compressed)")
    print(f"  Content:      {meta['content_size']} bytes")
    print()

    # Parse and verify
    print("=== VERIFICATION ===")
    parser = JMPGTriggerParser(data)
    result = parser.verify()

    if result['valid']:
        print("  ✅ SEAL VALID — Integrity verified!")
    else:
        print(f"  ❌ SEAL INVALID — {result['error']}")

    print(f"  Stream URL:   {parser.get_stream_url()}")
    print(f"  Vault Ref:    {parser.get_vault_ref()}")
    print(f"  Receipt ID:   {parser.get_receipt_id()}")
    print()

    # Save test file
    outfile = '/tmp/test-trigger.jmpg'
    with open(outfile, 'wb') as f:
        f.write(data)
    print(f"=== SAVED ===")
    print(f"  File: {outfile}")
    print(f"  Size: {len(data)} bytes")
    print()

    # Binary structure visualization
    print("=== BINARY STRUCTURE ===")
    print(f"  [0x00-0x03]  MAGIC:        {data[0:4].hex()} ('{data[0:4].decode()}')")
    print(f"  [0x04-0x05]  VERSION:      {data[4:6].hex()}")
    print(f"  [0x06-0x07]  FLAGS:        {data[6:8].hex()}")
    print(f"  [0x08]       CODEC_ID:     {data[8]:02x}")
    print(f"  [0x09-0x0C]  DURATION:     {data[9:13].hex()}")
    print(f"  [0x0D-0x2C]  DID_HASH:     {data[13:45].hex()[:16]}...")
    print(f"  [0x2D-0x30]  MANIFEST_LEN: {data[45:49].hex()}")
    print(f"  [...]        MANIFEST:     {meta['manifest_size_compressed']} bytes")
    print(f"  [...]        CONTENT_LEN:  4 bytes")
    print(f"  [...]        CONTENT:      {meta['content_size']} bytes")
    print(f"  [-32:]       SEAL:         {data[-32:].hex()[:16]}...")
    print()

    print("=" * 60)
    print("🐉 JMPG Trigger Builder — Test Complete")
    print("=" * 60)

    sys.exit(0 if result['valid'] else 1)
