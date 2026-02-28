#!/usr/bin/env python3
"""
WINDI JMPG Export Engine v1.0.0
Port: 8103

Creates .jmpg packages (Joint Media Protocol for Governance)
from a4Desk Desktop content.

.jmpg = ZIP containing:
  manifest.json   — package identity + hash chain
  content.json    — editorial blocks (text, headings, lists, etc.)
  receipt.json    — governance receipt from Forensic Ledger
  media/          — embedded images, videos, audio (base64 decoded)

Pipeline:
  Desktop (:8100) → Export Engine (:8103) → Ledger (:8101)
                                           → .jmpg file returned

Principle: "AI processes. Human decides. WINDI guarantees."
"""

import json
import hashlib
import uuid
import os
import io
import zipfile
import base64
import time
import re
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError

# Import JMPG Trigger Builder (P1 Sovereign Spec)
try:
    from jmpg_trigger_builder import JMPGTriggerBuilder, JMPGTriggerParser, create_did_hash
    TRIGGER_AVAILABLE = True
except ImportError:
    TRIGGER_AVAILABLE = False

# ─── CONFIG ──────────────────────────────────────────────────
PORT = 8103
LEDGER_URL = "http://127.0.0.1:8101"
VERSION = "1.0.0"
JMPG_SPEC = "JMPG-1.0"
MEDIA_DIR = "/opt/windi/desktop/export/media_cache"
LOG_FILE = "/opt/windi/logs/jmpg-export.log"
TRIGGERS_DIR = "/opt/windi/export-engine/triggers"  # Binary .jmpg triggers (P1 Sovereign Spec)

# ─── LOGGING ─────────────────────────────────────────────────
def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

# ─── HASH UTILITIES ──────────────────────────────────────────
def sha256_bytes(data: bytes) -> str:
    """SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()

def sha256_str(text: str) -> str:
    """SHA-256 hash of UTF-8 string."""
    return sha256_bytes(text.encode("utf-8"))

def compute_content_hash(content_blocks: list) -> str:
    """
    Deterministic hash of content blocks.
    Serializes with sorted keys, no whitespace for reproducibility.
    """
    canonical = json.dumps(content_blocks, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_str(canonical)

# ─── MANIFEST BUILDER ────────────────────────────────────────
def build_manifest(
    content_hash: str,
    template: str,
    title: str,
    author: str,
    metadata: dict,
    media_count: int,
    receipt_id: str = None
) -> dict:
    """Build the manifest.json for the .jmpg package."""
    now = datetime.now(timezone.utc)
    package_id = f"JMPG-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    manifest = {
        "jmpg_version": JMPG_SPEC,
        "engine_version": VERSION,
        "package_id": package_id,
        "created_at": now.isoformat(),
        "title": title,
        "author": author,
        "template": template,
        "content_hash": content_hash,
        "media_count": media_count,
        "metadata": {
            "doc_type": metadata.get("doc_type", "COMMUNIQUE"),
            "impact_level": metadata.get("impact_level", "MED"),
            "department_code": metadata.get("department_code", "GENERAL"),
            "language": metadata.get("language", "de"),
            "tags": metadata.get("tags", []),
        },
        "governance": {
            "ledger_registered": receipt_id is not None,
            "receipt_id": receipt_id,
            "sge_score": metadata.get("sge_score", None),
            "risk_level": metadata.get("risk_level", "R0"),
        },
        "integrity": {
            "algorithm": "SHA-256",
            "manifest_hash": None,  # filled after all other fields
        }
    }

    # Self-referential integrity: hash everything except manifest_hash
    manifest_copy = json.loads(json.dumps(manifest))
    manifest_copy["integrity"]["manifest_hash"] = "PENDING"
    canonical = json.dumps(manifest_copy, sort_keys=True, separators=(",", ":"))
    manifest["integrity"]["manifest_hash"] = sha256_str(canonical)

    return manifest

# ─── LEDGER INTEGRATION ──────────────────────────────────────
def register_with_ledger(content_hash: str, manifest: dict) -> dict:
    """
    Register the .jmpg hash with Forensic Ledger (:8101).
    Returns receipt dict or None on failure.
    """
    try:
        pkg_id = manifest.get("package_id", "JMPG-UNKNOWN")
        payload = json.dumps({
            "id": pkg_id,
            "actor": manifest.get("author", "WINDI System"),
            "app": "jmpg-export-engine",
            "doc_name": manifest.get("title", "Untitled"),
            "content_hash": content_hash,
            "governance_level": manifest.get("metadata", {}).get("impact_level", "MED"),
            "doc_type": "jmpg",
            "sge_score": manifest.get("governance", {}).get("sge_score", 0.0) or 0.0
        }).encode("utf-8")

        req = Request(
            f"{LEDGER_URL}/api/receipts",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
            log(f"Ledger registration OK: {result.get('id', 'N/A')}")
            return result

    except URLError as e:
        log(f"Ledger registration FAILED: {e}")
        return None
    except Exception as e:
        log(f"Ledger registration ERROR: {e}")
        return None

# ─── MEDIA PROCESSOR ─────────────────────────────────────────
def process_media(media_refs: list) -> list:
    """
    Process media references. Supports:
    - base64 encoded data (inline)
    - file paths (server-side)
    Returns list of (filename, bytes) tuples for the ZIP.
    """
    processed = []
    for i, ref in enumerate(media_refs):
        try:
            if isinstance(ref, dict):
                name = ref.get("filename", f"media_{i:03d}")
                mime = ref.get("mime_type", "application/octet-stream")

                # Determine extension from mime
                ext_map = {
                    "image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
                    "image/webp": ".webp", "image/svg+xml": ".svg",
                    "video/mp4": ".mp4", "audio/mpeg": ".mp3",
                    "application/pdf": ".pdf"
                }
                ext = ext_map.get(mime, "")
                if not name.endswith(ext):
                    name = f"{name}{ext}"

                if "data" in ref:
                    # Base64 encoded data
                    raw = base64.b64decode(ref["data"])
                    processed.append((f"media/{name}", raw))
                    log(f"Media packed: {name} ({len(raw)} bytes)")

                elif "path" in ref:
                    # Server file path
                    fpath = ref["path"]
                    if os.path.exists(fpath):
                        with open(fpath, "rb") as f:
                            raw = f.read()
                        processed.append((f"media/{name}", raw))
                        log(f"Media packed from path: {name} ({len(raw)} bytes)")

        except Exception as e:
            log(f"Media processing error for ref {i}: {e}")

    return processed

# ─── JMPG PACKAGER ────────────────────────────────────────────
def create_jmpg_package(
    title: str,
    author: str,
    template: str,
    content_blocks: list,
    metadata: dict,
    media_refs: list = None
) -> tuple:
    """
    Create a .jmpg package.

    Returns: (zip_bytes, manifest_dict, receipt_dict)
    """
    media_refs = media_refs or []

    # 1. Compute content hash
    content_hash = compute_content_hash(content_blocks)
    log(f"Content hash: {content_hash[:16]}...")

    # 2. Process media
    media_files = process_media(media_refs)

    # 3. Build manifest (without receipt yet)
    manifest = build_manifest(
        content_hash=content_hash,
        template=template,
        title=title,
        author=author,
        metadata=metadata,
        media_count=len(media_files),
        receipt_id=None
    )

    # 4. Register with Forensic Ledger
    receipt = register_with_ledger(content_hash, manifest)
    if receipt:
        manifest["governance"]["ledger_registered"] = True
        manifest["governance"]["receipt_id"] = receipt.get("id", receipt.get("receipt_id"))
        # Rebuild manifest hash with receipt info
        manifest_copy = json.loads(json.dumps(manifest))
        manifest_copy["integrity"]["manifest_hash"] = "PENDING"
        canonical = json.dumps(manifest_copy, sort_keys=True, separators=(",", ":"))
        manifest["integrity"]["manifest_hash"] = sha256_str(canonical)

    # 5. Build receipt.json
    receipt_data = {
        "registered": receipt is not None,
        "receipt_id": manifest["governance"]["receipt_id"],
        "content_hash": content_hash,
        "timestamp": manifest["created_at"],
        "ledger_response": receipt
    }

    # 6. Build content.json
    content_data = {
        "version": JMPG_SPEC,
        "blocks": content_blocks,
        "block_count": len(content_blocks),
        "content_hash": content_hash
    }

    # 7. Generate hash.txt (human-readable integrity file)
    hash_txt = (
        f"WINDI JMPG Integrity Record\n"
        f"{'=' * 40}\n"
        f"Package:      {manifest['package_id']}\n"
        f"Title:        {title}\n"
        f"Author:       {author}\n"
        f"Template:     {template}\n"
        f"Created:      {manifest['created_at']}\n"
        f"Content Hash: {content_hash}\n"
        f"Algorithm:    SHA-256\n"
        f"Blocks:       {len(content_blocks)}\n"
        f"Media:        {len(media_files)}\n"
        f"Ledger ID:    {manifest['governance']['receipt_id'] or 'PENDING'}\n"
        f"{'=' * 40}\n"
        f"Verify at: https://admin.windia4desk.tech/desktop/jmpg/\n"
    )

    # 8. Generate preview text (structured summary for quick inspection)
    preview_lines = []
    for block in content_blocks[:10]:  # first 10 blocks
        btype = block.get("type", "")
        if btype == "heading":
            level = block.get("level", 1)
            preview_lines.append(f"{'#' * level} {block.get('text', '')}")
        elif btype == "paragraph":
            text = block.get("text", "")
            preview_lines.append(text[:200] + ("..." if len(text) > 200 else ""))
        elif btype == "quote":
            preview_lines.append(f"> {block.get('text', '')[:150]}")
        elif btype == "list":
            for item in block.get("items", [])[:5]:
                preview_lines.append(f"  • {item[:100]}")
        elif btype == "divider":
            preview_lines.append("───────────────────")
        elif btype == "image":
            preview_lines.append(f"[Image: {block.get('alt', block.get('filename', 'embedded'))}]")
    if len(content_blocks) > 10:
        preview_lines.append(f"... +{len(content_blocks) - 10} more blocks")
    preview_txt = "\n".join(preview_lines)

    # 9. Package into ZIP (.jmpg)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Core files
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        zf.writestr("content.json", json.dumps(content_data, indent=2, ensure_ascii=False))
        zf.writestr("receipt.json", json.dumps(receipt_data, indent=2, ensure_ascii=False))
        zf.writestr("hash.txt", hash_txt)
        zf.writestr("preview.txt", preview_txt)

        # Media files
        for fname, fdata in media_files:
            zf.writestr(fname, fdata)

    zip_bytes = buf.getvalue()
    package_hash = sha256_bytes(zip_bytes)
    log(f"Package created: {manifest['package_id']} ({len(zip_bytes)} bytes, hash: {package_hash[:16]}...)")

    # ── DUAL-HASH: Seal bundle_hash in Forensic Ledger ──
    # The bundle_hash proves the PACKAGE wasn't tampered.
    # The content_hash (already registered) proves the CONTENT wasn't altered.
    receipt_id = manifest["governance"].get("receipt_id")
    if receipt_id:
        try:
            seal_payload = json.dumps({
                "bundle_hash": package_hash,
                "bundle_size": len(zip_bytes),
            }).encode("utf-8")
            seal_req = Request(
                f"{LEDGER_URL}/api/receipts/{receipt_id}/seal-bundle",
                data=seal_payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urlopen(seal_req, timeout=5) as seal_resp:
                seal_result = json.loads(seal_resp.read().decode())
                log(f"Bundle hash sealed: {package_hash[:16]}... ({len(zip_bytes)} bytes)")
        except Exception as e:
            log(f"Bundle seal WARNING (non-fatal): {e}")
    # ── END DUAL-HASH ──

    return zip_bytes, manifest, receipt_data

# ─── HTTP HANDLER ─────────────────────────────────────────────
class JMPGExportHandler(BaseHTTPRequestHandler):

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _json_response(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _file_response(self, data, filename, content_type):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._json_response(200, {
                "status": "healthy",
                "service": "jmpg-export-engine",
                "version": VERSION,
                "spec": JMPG_SPEC,
                "port": PORT,
                "ledger": LEDGER_URL,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        elif self.path == "/api/export/spec":
            self._json_response(200, {
                "jmpg_version": JMPG_SPEC,
                "engine_version": VERSION,
                "format": "ZIP",
                "contents": ["manifest.json", "content.json", "receipt.json", "hash.txt", "preview.txt", "media/*"],
                "supported_templates": [
                    "jornaline", "field-report", "comunicado",
                    "pressemitteilung", "internal-memo", "generic"
                ],
                "supported_media": [
                    "image/png", "image/jpeg", "image/gif", "image/webp",
                    "image/svg+xml", "video/mp4", "audio/mpeg", "application/pdf"
                ],
                "max_media_size_mb": 50,
                "content_block_types": [
                    "heading", "paragraph", "image", "video", "audio",
                    "table", "chart", "quote", "code", "divider", "list"
                ]
            })

        elif self.path == "/api/export/templates":
            self._json_response(200, {
                "templates": [
                    {
                        "id": "jornaline",
                        "name": "WINDI-Jornaline",
                        "description": "Institutional multimedia newspaper",
                        "icon": "📰",
                        "blocks": ["heading", "paragraph", "image", "video", "chart", "quote"]
                    },
                    {
                        "id": "field-report",
                        "name": "Field Report",
                        "description": "On-site documentation with photos and GPS",
                        "icon": "📋",
                        "blocks": ["heading", "paragraph", "image", "table", "list"]
                    },
                    {
                        "id": "comunicado",
                        "name": "Comunicado Oficial",
                        "description": "Official institutional communication",
                        "icon": "📜",
                        "blocks": ["heading", "paragraph", "quote", "list"]
                    },
                    {
                        "id": "pressemitteilung",
                        "name": "Pressemitteilung",
                        "description": "Press release (DE standard)",
                        "icon": "🗞️",
                        "blocks": ["heading", "paragraph", "image", "quote"]
                    },
                    {
                        "id": "internal-memo",
                        "name": "Internal Memo",
                        "description": "Internal governance communication",
                        "icon": "📝",
                        "blocks": ["heading", "paragraph", "table", "list"]
                    },
                    {
                        "id": "generic",
                        "name": "Generic Communiqué",
                        "description": "Free-form governed communication",
                        "icon": "📄",
                        "blocks": ["heading", "paragraph", "image", "video", "audio", "table", "chart", "quote", "code", "divider", "list"]
                    }
                ]
            })

        # ── TRIGGER API (P1 Sovereign Spec) ──
        elif self.path.startswith("/api/trigger/") and self.path.endswith(".jmpg"):
            # GET /api/trigger/{package_id}.jmpg - download binary trigger
            self._handle_trigger_download()

        elif self.path == "/api/trigger/status":
            # GET /api/trigger/status - check trigger subsystem
            self._json_response(200, {
                "trigger_available": TRIGGER_AVAILABLE,
                "triggers_dir": TRIGGERS_DIR,
                "trigger_count": len(os.listdir(TRIGGERS_DIR)) if os.path.isdir(TRIGGERS_DIR) else 0
            })

        elif self.path.startswith("/api/trigger/") and self.path.endswith("/verify"):
            # GET /api/trigger/{seal}/verify - verify trigger by seal
            self._handle_trigger_verify()

        else:
            self._json_response(404, {"error": "Not found", "available": [
                "/health", "/api/export/spec", "/api/export/templates",
                "POST /api/export/jmpg", "POST /api/trigger/build",
                "GET /api/trigger/{id}.jmpg", "GET /api/trigger/status",
                "GET /api/trigger/{seal}/verify"
            ]})

    def do_POST(self):
        if self.path == "/api/export/jmpg":
            self._handle_export()
        elif self.path == "/api/export/jmpg/preview":
            self._handle_preview()
        elif self.path == "/api/trigger/build":
            self._handle_trigger_build()
        else:
            self._json_response(404, {"error": "Unknown endpoint"})

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _handle_export(self):
        """
        POST /api/export/jmpg

        Body: {
            "title": "Report Title",
            "author": "Author Name",
            "template": "jornaline",
            "content_blocks": [ ... ],
            "metadata": { "doc_type": "...", "impact_level": "...", ... },
            "media": [ { "filename": "...", "mime_type": "...", "data": "base64..." } ],
            "return_format": "file" | "json"
        }

        Returns: .jmpg file or JSON with base64-encoded file
        """
        try:
            body = self._read_body()

            # Validate required fields
            title = body.get("title", "Untitled Communiqué")
            author = body.get("author", "WINDI System")
            template = body.get("template", "generic")
            content_blocks = body.get("content_blocks", [])
            metadata = body.get("metadata", {})
            media = body.get("media", [])
            return_format = body.get("return_format", "file")

            if not content_blocks:
                self._json_response(400, {
                    "error": "content_blocks is required and cannot be empty",
                    "hint": "Provide at least one content block"
                })
                return

            log(f"Export request: '{title}' template={template} blocks={len(content_blocks)} media={len(media)}")

            # Create package
            t0 = time.monotonic()
            zip_bytes, manifest, receipt = create_jmpg_package(
                title=title,
                author=author,
                template=template,
                content_blocks=content_blocks,
                metadata=metadata,
                media_refs=media
            )
            elapsed = (time.monotonic() - t0) * 1000

            log(f"Export complete: {manifest['package_id']} in {elapsed:.0f}ms")

            if return_format == "json":
                # Return as JSON with base64 data
                self._json_response(200, {
                    "success": True,
                    "package_id": manifest["package_id"],
                    "content_hash": manifest["content_hash"],
                    "manifest_hash": manifest["integrity"]["manifest_hash"],
                    "receipt_id": manifest["governance"]["receipt_id"],
                    "ledger_registered": manifest["governance"]["ledger_registered"],
                    "size_bytes": len(zip_bytes),
                    "elapsed_ms": round(elapsed, 1),
                    "filename": f"{manifest['package_id']}.jmpg",
                    "data_base64": base64.b64encode(zip_bytes).decode("ascii")
                })
            else:
                # Return as downloadable file
                filename = f"{manifest['package_id']}.jmpg"
                self._file_response(zip_bytes, filename, "application/vnd.windi.jmpg")

        except json.JSONDecodeError:
            self._json_response(400, {"error": "Invalid JSON in request body"})
        except Exception as e:
            log(f"Export error: {e}")
            self._json_response(500, {"error": str(e)})

    def _handle_preview(self):
        """
        POST /api/export/jmpg/preview

        Same body as /api/export/jmpg but returns only manifest + hash
        without creating the full package or registering with Ledger.
        """
        try:
            body = self._read_body()
            content_blocks = body.get("content_blocks", [])

            if not content_blocks:
                self._json_response(400, {"error": "content_blocks required"})
                return

            content_hash = compute_content_hash(content_blocks)
            media_count = len(body.get("media", []))

            self._json_response(200, {
                "preview": True,
                "content_hash": content_hash,
                "block_count": len(content_blocks),
                "media_count": media_count,
                "template": body.get("template", "generic"),
                "estimated_size_kb": max(1, len(json.dumps(content_blocks)) // 1024),
                "note": "Preview only — no ledger registration, no .jmpg created"
            })

        except Exception as e:
            self._json_response(500, {"error": str(e)})

    # ─── TRIGGER API HANDLERS (P1 Sovereign Spec) ─────────────────
    def _handle_trigger_build(self):
        """
        POST /api/trigger/build

        Body: {
            "creator_did": "string (64 hex chars, SHA-256 of DID)",
            "video_base64": "string (base64 encoded, max 5MB)",
            "duration_ms": 30000,
            "codec": "h264"|"av1"|"vp9",
            "stream_url": "string (URL do Vault stream)",
            "vault_ref": "string (Vault receipt reference)",
            "chapters": [{"title":"Intro","offset_ms":0}],
            "metadata": {}
        }

        Returns: JSON with package_id, seal, receipt_id
        """
        if not TRIGGER_AVAILABLE:
            self._json_response(503, {
                "error": "Trigger subsystem not available",
                "hint": "jmpg_trigger_builder module not found"
            })
            return

        try:
            body = self._read_body()

            # Required: creator_did (64 hex chars - already hashed)
            creator_did = body.get("creator_did")
            if not creator_did:
                self._json_response(400, {"error": "creator_did is required (64 hex chars)"})
                return
            if len(creator_did) != 64 or not all(c in '0123456789abcdefABCDEF' for c in creator_did):
                self._json_response(400, {"error": "creator_did must be 64 hex characters (SHA-256 hash)"})
                return

            # Required: video_base64
            video_base64 = body.get("video_base64")
            if not video_base64:
                self._json_response(400, {"error": "video_base64 is required"})
                return

            # Decode video
            try:
                video_bytes = base64.b64decode(video_base64)
            except Exception as e:
                self._json_response(400, {"error": f"Invalid base64 in video_base64: {e}"})
                return

            # Check size (max 5MB)
            if len(video_bytes) > 5 * 1024 * 1024:
                self._json_response(400, {"error": f"video_base64 too large: {len(video_bytes)} bytes (max 5MB)"})
                return

            # Optional fields
            duration_ms = body.get("duration_ms", 30000)
            codec = body.get("codec", "h264").lower()
            stream_url = body.get("stream_url", f"vault://windi/{creator_did[:16]}/stream.m3u8")
            vault_ref = body.get("vault_ref", f"VR-{creator_did[:12].upper()}")
            chapters = body.get("chapters", [])
            metadata = body.get("metadata", {})

            # Codec map
            codec_map = {"h264": 0x01, "av1": 0x02, "vp9": 0x03}
            codec_id = codec_map.get(codec, 0x01)

            log(f"Building trigger: did={creator_did[:16]}... codec={codec} duration={duration_ms}ms video={len(video_bytes)}B")

            # Step 1: Build initial trigger (without receipt_id)
            builder = JMPGTriggerBuilder(creator_did, codec_id)
            builder.set_onboard(video_bytes, duration_ms)
            builder.set_audio(True)
            builder.set_manifest(
                stream_url=stream_url,
                vault_ref=vault_ref,
                chapters=chapters,
                receipt_id=None,
                extra=metadata
            )
            initial_data = builder.build()
            initial_seal = builder.seal_hex()

            # Step 2: Register with Ledger
            receipt_id = None
            ledger_registered = False
            try:
                payload = json.dumps({
                    "type": "JMPG_TRIGGER",
                    "hash": initial_seal,
                    "data": {
                        "creator_did": creator_did,
                        "stream_url": stream_url,
                        "vault_ref": vault_ref,
                        "duration_ms": duration_ms,
                        "codec": codec
                    }
                }).encode("utf-8")
                req = Request(
                    f"{LEDGER_URL}/api/receipt",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urlopen(req, timeout=5) as resp:
                    ledger_resp = json.loads(resp.read().decode())
                    receipt_id = ledger_resp.get("receipt_id", ledger_resp.get("id"))
                    ledger_registered = True
                    log(f"Ledger registration OK: {receipt_id}")
            except Exception as e:
                # Fallback receipt_id
                receipt_id = f"VR-TRIGGER-{initial_seal[:12].upper()}"
                log(f"Ledger registration failed ({e}), using fallback: {receipt_id}")

            # Step 3: Rebuild with receipt_id in manifest
            builder = JMPGTriggerBuilder(creator_did, codec_id)
            builder.set_onboard(video_bytes, duration_ms)
            builder.set_audio(True)
            builder.set_manifest(
                stream_url=stream_url,
                vault_ref=vault_ref,
                chapters=chapters,
                receipt_id=receipt_id,
                extra=metadata
            )
            final_data = builder.build()
            package_id = builder.package_id()
            seal_hex = builder.seal_hex()

            # Step 4: Save to file
            os.makedirs(TRIGGERS_DIR, exist_ok=True)
            filepath = os.path.join(TRIGGERS_DIR, f"{package_id}.jmpg")
            with open(filepath, "wb") as f:
                f.write(final_data)

            log(f"Trigger saved: {package_id} ({len(final_data)} bytes, seal: {seal_hex[:16]}...)")

            # Return response
            self._json_response(200, {
                "status": "ok",
                "package_id": package_id,
                "seal": seal_hex,
                "size": len(final_data),
                "receipt_id": receipt_id,
                "ledger_registered": ledger_registered,
                "download_url": f"/api/trigger/{package_id}.jmpg"
            })

        except json.JSONDecodeError:
            self._json_response(400, {"error": "Invalid JSON in request body"})
        except Exception as e:
            log(f"Trigger build error: {e}")
            self._json_response(500, {"error": str(e)})

    def _handle_trigger_download(self):
        """
        GET /api/trigger/{package_id}.jmpg

        Returns: Binary .jmpg trigger file
        """
        # Extract package_id from path: /api/trigger/TRIG-20260227-XXXXXXXX.jmpg
        match = re.match(r"/api/trigger/(.+)\.jmpg$", self.path)
        if not match:
            self._json_response(400, {"error": "Invalid trigger path"})
            return

        package_id = match.group(1)
        filepath = os.path.join(TRIGGERS_DIR, f"{package_id}.jmpg")

        if not os.path.exists(filepath):
            self._json_response(404, {
                "error": "Trigger not found",
                "package_id": package_id,
                "hint": f"Build a trigger first via POST /api/trigger/build"
            })
            return

        try:
            with open(filepath, "rb") as f:
                trigger_bytes = f.read()

            log(f"Trigger download: {package_id} ({len(trigger_bytes)} bytes)")
            self._file_response(trigger_bytes, f"{package_id}.jmpg", "application/vnd.windi.jmpg")

        except Exception as e:
            log(f"Trigger download error: {e}")
            self._json_response(500, {"error": str(e)})

    def _handle_trigger_verify(self):
        """
        GET /api/trigger/{seal}/verify

        Finds trigger by seal hash in triggers directory and verifies it.

        Returns: {"valid": true/false, "header": {...}, "manifest": {...}, "seal": "..."}
        """
        if not TRIGGER_AVAILABLE:
            self._json_response(503, {"error": "Trigger subsystem not available"})
            return

        # Extract seal from path: /api/trigger/{seal}/verify
        match = re.match(r"/api/trigger/([a-fA-F0-9]+)/verify$", self.path)
        if not match:
            self._json_response(400, {"error": "Invalid verify path. Use /api/trigger/{seal}/verify"})
            return

        seal_query = match.group(1).lower()
        log(f"Verify request for seal: {seal_query[:16]}...")

        # Search triggers directory for matching seal
        if not os.path.isdir(TRIGGERS_DIR):
            self._json_response(404, {"error": "No triggers directory", "seal": seal_query})
            return

        found_file = None
        for filename in os.listdir(TRIGGERS_DIR):
            if filename.endswith(".jmpg"):
                filepath = os.path.join(TRIGGERS_DIR, filename)
                try:
                    with open(filepath, "rb") as f:
                        data = f.read()
                    parser = JMPGTriggerParser(data)
                    if parser.valid and parser.seal and parser.seal.lower().startswith(seal_query.lower()):
                        found_file = filepath
                        break
                except Exception:
                    continue

        if not found_file:
            self._json_response(404, {
                "error": "Trigger not found with seal",
                "seal_query": seal_query,
                "hint": "Provide full or partial seal hash"
            })
            return

        try:
            with open(found_file, "rb") as f:
                data = f.read()

            parser = JMPGTriggerParser(data)
            result = parser.verify()

            log(f"Verify result: valid={result['valid']} seal={result['seal'][:16] if result['seal'] else 'None'}...")

            self._json_response(200, result)

        except Exception as e:
            log(f"Trigger verify error: {e}")
            self._json_response(500, {"error": str(e)})

    def log_message(self, format, *args):
        """Override to use our logger."""
        log(f"HTTP {args[0] if args else ''}")

# ─── MAIN ─────────────────────────────────────────────────────
if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    os.makedirs(TRIGGERS_DIR, exist_ok=True)

    log(f"JMPG Export Engine v{VERSION} starting on port {PORT}")
    log(f"JMPG Spec: {JMPG_SPEC}")
    log(f"Ledger: {LEDGER_URL}")
    log(f"Trigger Builder: {'AVAILABLE' if TRIGGER_AVAILABLE else 'NOT AVAILABLE'}")
    log(f"Triggers Dir: {TRIGGERS_DIR}")

    server = ThreadingHTTPServer(("0.0.0.0", PORT), JMPGExportHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Shutting down.")
        server.server_close()
