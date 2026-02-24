#!/usr/bin/env python3
"""
WINDI Wisdom Engine — Part 2A: Wisdom Candidate Protocol
"AI processes. Human decides. WINDI guarantees."

Enables users to flag documents/insights as "wisdom candidates" for
feeding into the WINDI Wisdom Protocol.

A wisdom candidate is:
- An insight derived from document creation
- A pattern worth preserving for institutional memory
- A governance decision worth indexing

Endpoints:
  POST /api/wisdom/candidate  → Submit a wisdom candidate
  GET  /api/wisdom/stats      → Wisdom pipeline statistics
"""

import json
import hashlib
import threading
import time
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──
WISDOM_PROTOCOL_URL = "http://localhost:8107/api/wisdom/ingest"
CANDIDATES_DB_PATH = Path("/opt/windi/data/wisdom_candidates.jsonl")
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]

# Candidate categories
WISDOM_CATEGORIES = {
    "pattern": "Recurring governance pattern",
    "insight": "Novel insight from document analysis",
    "decision": "Governance decision worth preserving",
    "template": "Reusable template pattern",
    "risk": "Risk pattern for future reference",
    "best_practice": "Best practice observation",
}


class WisdomEngine:
    """
    Manages wisdom candidate submissions to the Wisdom Protocol.

    Usage:
        engine = WisdomEngine()
        result = engine.submit_candidate(
            doc_serial="WINDI-2026-0008",
            content_hash="abc123...",
            insight="User discovered efficient pattern for invoices",
            category="pattern",
            source_type="invoice",
            tier="HIGH"
        )
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
            "submitted": 0,
            "synced": 0,
            "pending": 0,
            "failed": 0,
        }
        self._pending_queue = []
        self._init_storage()
        self._initialized = True

    def _init_storage(self):
        """Ensure storage directory exists."""
        CANDIDATES_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    def submit_candidate(
        self,
        doc_serial: str,
        content_hash: str,
        insight: str,
        category: str = "insight",
        source_type: str = "document",
        tier: str = "MED",
        metadata: dict = None,
    ) -> dict:
        """
        Submit a wisdom candidate for processing.

        Args:
            doc_serial: WINDI serial number of source document
            content_hash: SHA-256 hash of source content
            insight: The wisdom/insight to preserve
            category: One of WISDOM_CATEGORIES
            source_type: Document type (invoice, memo, etc.)
            tier: Governance tier (FREE/MED/HIGH)
            metadata: Additional metadata

        Returns:
            Submission result with candidate_id and status
        """
        if category not in WISDOM_CATEGORIES:
            category = "insight"

        candidate_id = f"WC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

        candidate = {
            "id": candidate_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "doc_serial": doc_serial,
            "content_hash": content_hash,
            "insight": insight,
            "category": category,
            "category_label": WISDOM_CATEGORIES[category],
            "source_type": source_type,
            "tier": tier,
            "status": "pending",
            "metadata": metadata or {},
            "app": "agent-palette",
            "version": "1.0.0",
        }

        # Compute insight hash for deduplication
        insight_hash = hashlib.sha256(insight.encode()).hexdigest()[:16]
        candidate["insight_hash"] = insight_hash

        # Store locally first
        self._store_candidate(candidate)
        self._stats["submitted"] += 1

        # Async sync to Wisdom Protocol
        thread = threading.Thread(
            target=self._sync_candidate,
            args=(candidate,),
            daemon=True
        )
        thread.start()

        return {
            "success": True,
            "candidate_id": candidate_id,
            "category": category,
            "status": "submitted",
            "insight_preview": insight[:100] + "..." if len(insight) > 100 else insight,
        }

    def _store_candidate(self, candidate: dict):
        """Store candidate to local JSONL file."""
        try:
            with open(CANDIDATES_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(candidate, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[wisdom_engine] Warning: Failed to store candidate: {e}")

    def _sync_candidate(self, candidate: dict):
        """Sync candidate to Wisdom Protocol with retry."""
        self._stats["pending"] += 1

        for attempt in range(MAX_RETRIES):
            try:
                data = json.dumps(candidate).encode()
                req = urllib.request.Request(
                    WISDOM_PROTOCOL_URL,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in (200, 201):
                        self._stats["pending"] -= 1
                        self._stats["synced"] += 1
                        return {"status": "synced", "attempt": attempt + 1}
            except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                else:
                    self._stats["pending"] -= 1
                    self._stats["failed"] += 1
                    self._pending_queue.append({
                        "candidate": candidate,
                        "error": str(e),
                        "failed_at": datetime.now(timezone.utc).isoformat()
                    })
                    # Still stored locally, just not synced
                    return {"status": "stored_locally", "error": str(e)}

        return {"status": "stored_locally"}

    def get_stats(self) -> dict:
        """Get wisdom engine statistics."""
        return {
            "wisdom_engine": {
                "submitted": self._stats["submitted"],
                "synced": self._stats["synced"],
                "pending": self._stats["pending"],
                "failed": self._stats["failed"],
                "queue_size": len(self._pending_queue),
            },
            "categories": list(WISDOM_CATEGORIES.keys()),
        }

    def get_recent_candidates(self, limit: int = 10) -> list:
        """Get recent wisdom candidates from local storage."""
        try:
            if not CANDIDATES_DB_PATH.exists():
                return []

            candidates = []
            with open(CANDIDATES_DB_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        candidates.append(json.loads(line))

            return candidates[-limit:][::-1]  # Last N, reversed (newest first)
        except Exception as e:
            return [{"error": str(e)}]


# ── Singleton accessor ──
_wisdom_engine = None


def get_wisdom_engine() -> WisdomEngine:
    """Get or create the singleton WisdomEngine instance."""
    global _wisdom_engine
    if _wisdom_engine is None:
        _wisdom_engine = WisdomEngine()
    return _wisdom_engine


# ── API Handler Functions ──
def handle_wisdom_candidate(handler):
    """
    Handle POST /api/wisdom/candidate

    Expected JSON body:
    {
        "doc_serial": "WINDI-2026-0008",
        "content_hash": "abc123...",
        "insight": "User discovered efficient pattern...",
        "category": "pattern",  // optional, defaults to "insight"
        "source_type": "invoice",
        "tier": "HIGH",
        "metadata": {}  // optional
    }
    """
    import json

    try:
        content_length = int(handler.headers.get("Content-Length", 0))
        body = handler.rfile.read(content_length).decode("utf-8")
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError) as e:
        return _json_response(handler, 400, {"error": f"Invalid JSON: {e}"})

    # Validate required fields
    required = ["doc_serial", "content_hash", "insight"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return _json_response(handler, 400, {
            "error": f"Missing required fields: {', '.join(missing)}"
        })

    engine = get_wisdom_engine()
    result = engine.submit_candidate(
        doc_serial=data["doc_serial"],
        content_hash=data["content_hash"],
        insight=data["insight"],
        category=data.get("category", "insight"),
        source_type=data.get("source_type", "document"),
        tier=data.get("tier", "MED"),
        metadata=data.get("metadata"),
    )

    return _json_response(handler, 200, result)


def handle_wisdom_stats(handler):
    """Handle GET /api/wisdom/stats"""
    engine = get_wisdom_engine()
    stats = engine.get_stats()
    stats["recent"] = engine.get_recent_candidates(5)
    return _json_response(handler, 200, stats)


def route_wisdom_api(handler, method, path):
    """
    Route dispatcher for wisdom API endpoints.
    Returns True if handled, False otherwise.
    """
    clean_path = path.rstrip("/")
    # Support /palette/api/... prefix from UI
    if clean_path.startswith("/palette"):
        clean_path = clean_path[8:]  # Remove "/palette"

    if method == "POST" and clean_path == "/api/wisdom/candidate":
        handle_wisdom_candidate(handler)
        return True

    if method == "GET" and clean_path == "/api/wisdom/stats":
        handle_wisdom_stats(handler)
        return True

    return False


def _json_response(handler, status_code, data):
    """Send a JSON response."""
    import json
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

    print("WINDI Wisdom Engine - Part 2A")
    print("=" * 50)

    engine = WisdomEngine()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "submit":
            result = engine.submit_candidate(
                doc_serial="WINDI-2026-TEST",
                content_hash="test123abc",
                insight="Test wisdom insight for pattern recognition",
                category="pattern",
                source_type="memo",
                tier="HIGH"
            )
            print(json.dumps(result, indent=2))
        elif cmd == "stats":
            stats = engine.get_stats()
            print(json.dumps(stats, indent=2))
        elif cmd == "recent":
            recent = engine.get_recent_candidates()
            print(json.dumps(recent, indent=2))
        else:
            print("Usage: wisdom_engine.py [submit|stats|recent]")
    else:
        stats = engine.get_stats()
        print(f"Submitted: {stats['wisdom_engine']['submitted']}")
        print(f"Synced: {stats['wisdom_engine']['synced']}")
        print(f"Categories: {', '.join(stats['categories'])}")
