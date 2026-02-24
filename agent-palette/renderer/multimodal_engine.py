#!/usr/bin/env python3
"""
WINDI Multimodal Engine — Part 2B: OCR, Image Analysis, URL Verification
"AI processes. Human decides. WINDI guarantees."

Provides multimodal input processing for the Agent Palette:
- OCR: Extract text from images (PNG, JPG, PDF scans)
- Image Analysis: Describe image content for document embedding
- URL Verification: Fetch and analyze web content for references

Design:
- Graceful degradation if dependencies unavailable
- Local processing preferred (Tesseract OCR)
- Async processing for large files
"""

import base64
import hashlib
import io
import json
import re
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

# ── Configuration ──
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_URL_CONTENT = 500 * 1024  # 500KB
SUPPORTED_IMAGE_FORMATS = ["png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"]
URL_TIMEOUT = 15

# ── Dependency checks ──
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    pytesseract = None

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None


class MultimodalEngine:
    """
    Multimodal input processor for OCR, images, and URLs.

    Usage:
        engine = MultimodalEngine()

        # OCR from image bytes
        result = engine.ocr_image(image_bytes)

        # Analyze URL
        result = engine.analyze_url("https://example.com/doc")
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._stats = {
            "ocr_processed": 0,
            "images_analyzed": 0,
            "urls_verified": 0,
            "errors": 0,
        }
        self._initialized = True

    def get_capabilities(self) -> dict:
        """Report available multimodal capabilities."""
        return {
            "ocr": {
                "available": HAS_PIL and HAS_TESSERACT,
                "engine": "tesseract" if HAS_TESSERACT else None,
                "formats": SUPPORTED_IMAGE_FORMATS if HAS_PIL else [],
            },
            "image_analysis": {
                "available": HAS_PIL,
                "features": ["dimensions", "format", "mode", "hash"] if HAS_PIL else [],
            },
            "url_verification": {
                "available": True,
                "parser": "beautifulsoup" if HAS_BS4 else "basic",
                "max_content_kb": MAX_URL_CONTENT // 1024,
            },
        }

    # ═══════════════════════════════════════════════════════════════════════
    # OCR — Optical Character Recognition
    # ═══════════════════════════════════════════════════════════════════════

    def ocr_image(
        self,
        image_data: bytes,
        language: str = "deu+eng+por"
    ) -> dict:
        """
        Extract text from image using Tesseract OCR.

        Args:
            image_data: Image bytes (PNG, JPG, etc.)
            language: Tesseract language codes (default: German+English+Portuguese)

        Returns:
            Dict with extracted text, confidence, and metadata
        """
        if not HAS_PIL or not HAS_TESSERACT:
            return {
                "success": False,
                "error": "OCR not available (requires Pillow + pytesseract)",
                "text": "",
            }

        if len(image_data) > MAX_IMAGE_SIZE:
            return {
                "success": False,
                "error": f"Image too large (max {MAX_IMAGE_SIZE // 1024 // 1024}MB)",
                "text": "",
            }

        try:
            # Load image
            img = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Perform OCR
            text = pytesseract.image_to_string(img, lang=language)

            # Get detailed data for confidence
            data = pytesseract.image_to_data(img, lang=language, output_type=pytesseract.Output.DICT)
            confidences = [c for c in data["conf"] if c != -1]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            self._stats["ocr_processed"] += 1

            return {
                "success": True,
                "text": text.strip(),
                "confidence": round(avg_confidence, 2),
                "word_count": len(text.split()),
                "language_hint": language,
                "image_size": f"{img.width}x{img.height}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self._stats["errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "text": "",
            }

    def ocr_base64(self, base64_data: str, language: str = "deu+eng+por") -> dict:
        """OCR from base64-encoded image."""
        try:
            # Strip data URL prefix if present
            if "," in base64_data:
                base64_data = base64_data.split(",", 1)[1]

            image_bytes = base64.b64decode(base64_data)
            return self.ocr_image(image_bytes, language)
        except Exception as e:
            return {
                "success": False,
                "error": f"Invalid base64 data: {e}",
                "text": "",
            }

    # ═══════════════════════════════════════════════════════════════════════
    # Image Analysis
    # ═══════════════════════════════════════════════════════════════════════

    def analyze_image(self, image_data: bytes) -> dict:
        """
        Analyze image properties (dimensions, format, hash).

        Args:
            image_data: Image bytes

        Returns:
            Dict with image metadata
        """
        if not HAS_PIL:
            return {
                "success": False,
                "error": "Image analysis not available (requires Pillow)",
            }

        try:
            img = Image.open(io.BytesIO(image_data))

            # Compute perceptual hash (simple average hash)
            img_hash = self._compute_image_hash(img)

            self._stats["images_analyzed"] += 1

            return {
                "success": True,
                "format": img.format or "unknown",
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "aspect_ratio": round(img.width / img.height, 2) if img.height else 0,
                "size_bytes": len(image_data),
                "content_hash": hashlib.sha256(image_data).hexdigest()[:16],
                "perceptual_hash": img_hash,
                "has_transparency": img.mode in ("RGBA", "LA", "PA"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self._stats["errors"] += 1
            return {
                "success": False,
                "error": str(e),
            }

    def _compute_image_hash(self, img: "Image.Image") -> str:
        """Compute simple average hash for image similarity."""
        try:
            # Resize to 8x8 grayscale
            small = img.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
            pixels = list(small.getdata())
            avg = sum(pixels) / len(pixels)
            # Generate hash based on pixel values above/below average
            bits = "".join("1" if p > avg else "0" for p in pixels)
            return hex(int(bits, 2))[2:].zfill(16)
        except Exception:
            return "0" * 16

    # ═══════════════════════════════════════════════════════════════════════
    # URL Verification
    # ═══════════════════════════════════════════════════════════════════════

    def verify_url(self, url: str) -> dict:
        """
        Verify and analyze a URL for document references.

        Args:
            url: URL to verify

        Returns:
            Dict with URL metadata, title, summary
        """
        # Validate URL format
        if not url.startswith(("http://", "https://")):
            return {
                "success": False,
                "error": "Invalid URL format (must start with http:// or https://)",
            }

        try:
            # Fetch URL
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "WINDI-Agent-Palette/1.0 (Document Verification)",
                    "Accept": "text/html,application/xhtml+xml,*/*",
                }
            )

            with urllib.request.urlopen(req, timeout=URL_TIMEOUT) as resp:
                content_type = resp.headers.get("Content-Type", "")
                content_length = int(resp.headers.get("Content-Length", 0))

                # Check content size
                if content_length > MAX_URL_CONTENT:
                    return {
                        "success": True,
                        "verified": True,
                        "url": url,
                        "status": resp.status,
                        "content_type": content_type,
                        "warning": f"Content too large to analyze ({content_length} bytes)",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                # Read content
                content = resp.read(MAX_URL_CONTENT)

                # Parse based on content type
                if "text/html" in content_type or "application/xhtml" in content_type:
                    analysis = self._analyze_html(content, url)
                else:
                    analysis = {
                        "title": None,
                        "description": None,
                        "content_preview": content[:200].decode("utf-8", errors="replace"),
                    }

                self._stats["urls_verified"] += 1

                return {
                    "success": True,
                    "verified": True,
                    "url": url,
                    "status": resp.status,
                    "content_type": content_type,
                    "content_length": len(content),
                    "title": analysis.get("title"),
                    "description": analysis.get("description"),
                    "content_preview": analysis.get("content_preview"),
                    "content_hash": hashlib.sha256(content).hexdigest()[:16],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        except urllib.error.HTTPError as e:
            self._stats["errors"] += 1
            return {
                "success": False,
                "verified": False,
                "url": url,
                "error": f"HTTP {e.code}: {e.reason}",
            }
        except urllib.error.URLError as e:
            self._stats["errors"] += 1
            return {
                "success": False,
                "verified": False,
                "url": url,
                "error": f"URL Error: {e.reason}",
            }
        except Exception as e:
            self._stats["errors"] += 1
            return {
                "success": False,
                "verified": False,
                "url": url,
                "error": str(e),
            }

    def _analyze_html(self, content: bytes, url: str) -> dict:
        """Extract metadata from HTML content."""
        try:
            html = content.decode("utf-8", errors="replace")

            if HAS_BS4:
                soup = BeautifulSoup(html, "html.parser")

                # Extract title
                title = None
                if soup.title:
                    title = soup.title.string
                if not title:
                    og_title = soup.find("meta", property="og:title")
                    if og_title:
                        title = og_title.get("content")

                # Extract description
                desc = None
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    desc = meta_desc.get("content")
                if not desc:
                    og_desc = soup.find("meta", property="og:description")
                    if og_desc:
                        desc = og_desc.get("content")

                # Get text preview
                body = soup.find("body")
                text_content = body.get_text(separator=" ", strip=True)[:500] if body else ""

                return {
                    "title": title,
                    "description": desc,
                    "content_preview": text_content[:200] if text_content else None,
                }
            else:
                # Basic parsing without BeautifulSoup
                title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
                title = title_match.group(1).strip() if title_match else None

                desc_match = re.search(
                    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
                    html, re.I
                )
                desc = desc_match.group(1).strip() if desc_match else None

                # Remove tags for preview
                text = re.sub(r"<[^>]+>", " ", html)
                text = re.sub(r"\s+", " ", text).strip()

                return {
                    "title": title,
                    "description": desc,
                    "content_preview": text[:200] if text else None,
                }

        except Exception as e:
            return {
                "title": None,
                "description": None,
                "content_preview": None,
                "parse_error": str(e),
            }

    def get_stats(self) -> dict:
        """Get multimodal engine statistics."""
        return {
            "multimodal_engine": self._stats.copy(),
            "capabilities": self.get_capabilities(),
        }


# ── Singleton accessor ──
_multimodal_engine = None


def get_multimodal_engine() -> MultimodalEngine:
    """Get or create the singleton MultimodalEngine instance."""
    global _multimodal_engine
    if _multimodal_engine is None:
        _multimodal_engine = MultimodalEngine()
    return _multimodal_engine


# ── API Handler Functions ──
def handle_ocr_request(handler):
    """
    Handle POST /api/multimodal/ocr

    Accepts:
    - JSON with base64 image: {"image": "base64...", "language": "deu+eng"}
    - Multipart form with image file
    """
    try:
        content_type = handler.headers.get("Content-Type", "")
        content_length = int(handler.headers.get("Content-Length", 0))
        body = handler.rfile.read(content_length)

        engine = get_multimodal_engine()

        if "application/json" in content_type:
            data = json.loads(body.decode("utf-8"))
            if "image" not in data:
                return _json_response(handler, 400, {"error": "Missing 'image' field"})

            result = engine.ocr_base64(
                data["image"],
                data.get("language", "deu+eng+por")
            )
        else:
            # Assume raw image bytes
            result = engine.ocr_image(body)

        return _json_response(handler, 200, result)

    except Exception as e:
        return _json_response(handler, 500, {"error": str(e)})


def handle_image_analysis(handler):
    """
    Handle POST /api/multimodal/analyze-image

    Accepts:
    - JSON with base64 image: {"image": "base64..."}
    - Raw image bytes
    """
    try:
        content_type = handler.headers.get("Content-Type", "")
        content_length = int(handler.headers.get("Content-Length", 0))
        body = handler.rfile.read(content_length)

        engine = get_multimodal_engine()

        if "application/json" in content_type:
            data = json.loads(body.decode("utf-8"))
            if "image" not in data:
                return _json_response(handler, 400, {"error": "Missing 'image' field"})

            # Decode base64
            base64_data = data["image"]
            if "," in base64_data:
                base64_data = base64_data.split(",", 1)[1]
            image_bytes = base64.b64decode(base64_data)
        else:
            image_bytes = body

        result = engine.analyze_image(image_bytes)
        return _json_response(handler, 200, result)

    except Exception as e:
        return _json_response(handler, 500, {"error": str(e)})


def handle_url_verification(handler):
    """
    Handle POST /api/multimodal/verify-url

    Expected JSON body:
    {"url": "https://example.com/document"}
    """
    try:
        content_length = int(handler.headers.get("Content-Length", 0))
        body = handler.rfile.read(content_length).decode("utf-8")
        data = json.loads(body)

        if "url" not in data:
            return _json_response(handler, 400, {"error": "Missing 'url' field"})

        engine = get_multimodal_engine()
        result = engine.verify_url(data["url"])
        return _json_response(handler, 200, result)

    except Exception as e:
        return _json_response(handler, 500, {"error": str(e)})


def handle_multimodal_capabilities(handler):
    """Handle GET /api/multimodal/capabilities"""
    engine = get_multimodal_engine()
    return _json_response(handler, 200, engine.get_capabilities())


def handle_multimodal_stats(handler):
    """Handle GET /api/multimodal/stats"""
    engine = get_multimodal_engine()
    return _json_response(handler, 200, engine.get_stats())


def route_multimodal_api(handler, method, path):
    """
    Route dispatcher for multimodal API endpoints.
    Returns True if handled, False otherwise.
    """
    clean_path = path.rstrip("/")
    # Support /palette/api/... prefix from UI
    if clean_path.startswith("/palette"):
        clean_path = clean_path[8:]  # Remove "/palette"

    if method == "POST" and clean_path == "/api/multimodal/ocr":
        handle_ocr_request(handler)
        return True

    if method == "POST" and clean_path == "/api/multimodal/analyze-image":
        handle_image_analysis(handler)
        return True

    if method == "POST" and clean_path == "/api/multimodal/verify-url":
        handle_url_verification(handler)
        return True

    if method == "GET" and clean_path == "/api/multimodal/capabilities":
        handle_multimodal_capabilities(handler)
        return True

    if method == "GET" and clean_path == "/api/multimodal/stats":
        handle_multimodal_stats(handler)
        return True

    return False


def _json_response(handler, status_code, data):
    """Send a JSON response."""
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


# ── CLI Test ──
if __name__ == "__main__":
    import sys

    print("WINDI Multimodal Engine - Part 2B")
    print("=" * 50)

    engine = MultimodalEngine()
    caps = engine.get_capabilities()

    print(f"OCR Available: {caps['ocr']['available']}")
    print(f"Image Analysis: {caps['image_analysis']['available']}")
    print(f"URL Verification: {caps['url_verification']['available']}")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "url" and len(sys.argv) > 2:
            result = engine.verify_url(sys.argv[2])
            print(json.dumps(result, indent=2))
        elif cmd == "stats":
            stats = engine.get_stats()
            print(json.dumps(stats, indent=2))
        else:
            print("Usage: multimodal_engine.py [url <url>|stats]")
