#!/usr/bin/env python3
"""
WINDI Wisdom Publisher v0.1.0
─────────────────────────────
Pipeline: Wisdom Block (N3+) → Human Approval → SGE Scan → Trilingual Format
         → Ledger Seal → Library Deploy → Vault Broadcast

Principle: "AI processes. Human decides. WINDI guarantees."
I9 Compliance: Publisher PROPOSES, never executes without human_approved=True.

Location: /opt/windi/engine/wisdom/publisher.py
Depends:  wisdom_manager.py, Ledger (:8101), Vault (:8106)
"""

import json
import hashlib
import uuid
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from http.client import HTTPConnection

# ── Configuration ────────────────────────────────────────────────────────────

WISDOM_DIR = Path("/opt/windi/engine/wisdom")
LIBRARY_DIR = Path("/var/www/library")          # Static files served by nginx
LIBRARY_BOOKS_DIR = LIBRARY_DIR / "books"
STORYBOOK_SCHEMA_VERSION = "1.0.0"

LEDGER_HOST = "127.0.0.1"
LEDGER_PORT = 8101
VAULT_HOST = "127.0.0.1"
VAULT_PORT = 8106

# Minimum maturity level for publication candidacy
MIN_PUBLISH_LEVEL = 3  # N3+

# ── Storybook Schema ────────────────────────────────────────────────────────

def create_storybook_manifest(book_id: str, title: dict, description: dict,
                               author: str = "Human Dragon + WINDI Council") -> dict:
    """
    Create a new Storybook manifest (index.json).
    
    title/description are trilingual dicts: {"pt": ..., "en": ..., "de": ...}
    """
    return {
        "schema_version": STORYBOOK_SCHEMA_VERSION,
        "book_id": book_id,
        "title": title,
        "description": description,
        "author": author,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "languages": ["pt", "en", "de"],
        "chapters": [],
        "governance": {
            "sovereignty": "I9_ENABLED",
            "sge_validated": False,
            "ledger_sealed": False,
            "ledger_receipt_id": None,
            "vault_broadcast": False
        },
        "status": "DRAFT"  # DRAFT → REVIEW → SEALED → PUBLISHED
    }


def create_chapter(chapter_id: str, title: dict, content: dict,
                    symbol: str = "🌱", wisdom_block_id: str = None,
                    maturity_level: int = 3) -> dict:
    """
    Create a chapter entry for a Storybook.
    
    title/content are trilingual dicts: {"pt": ..., "en": ..., "de": ...}
    """
    return {
        "chapter_id": chapter_id,
        "title": title,
        "content": content,
        "symbol": symbol,
        "wisdom_source": {
            "block_id": wisdom_block_id,
            "maturity_level": maturity_level
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "content_hash": _hash_content(content)
    }


# ── Publisher Pipeline ───────────────────────────────────────────────────────

class WisdomPublisher:
    """
    The Sovereign Publisher.
    
    Pipeline stages:
    1. CANDIDATE  - Wisdom Block reaches N3+, flagged as publishable
    2. APPROVED   - Human Dragon clicks approve (I9 gate)
    3. SANITIZED  - SGE scan confirms no governance violations
    4. FORMATTED  - Trilingual content structured into Storybook chapter
    5. SEALED     - Virtue Receipt generated via Ledger
    6. PUBLISHED  - Deployed to Library static files
    7. BROADCAST  - Vault notified of new publication
    """

    def __init__(self):
        self.candidates = []  # Pending Wisdom Blocks for review
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create Library directories if they don't exist."""
        LIBRARY_BOOKS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Stage 1: Candidacy ───────────────────────────────────────────────

    def propose_candidate(self, wisdom_block: dict) -> dict:
        """
        Check if a Wisdom Block qualifies for publication.
        Returns candidate status. Does NOT publish (I9).
        """
        block_id = wisdom_block.get("id", "unknown")
        level = wisdom_block.get("maturity_level", 0)
        
        if level < MIN_PUBLISH_LEVEL:
            return {
                "status": "REJECTED",
                "reason": f"Maturity N{level} < N{MIN_PUBLISH_LEVEL} minimum",
                "block_id": block_id
            }
        
        candidate = {
            "status": "CANDIDATE",
            "block_id": block_id,
            "maturity_level": level,
            "proposed_at": datetime.now(timezone.utc).isoformat(),
            "human_approved": False,  # I9: awaits Human Dragon
            "sge_cleared": False,
            "ledger_sealed": False
        }
        self.candidates.append(candidate)
        
        return candidate

    # ── Stage 2: Human Approval (I9 Gate) ────────────────────────────────

    def approve_candidate(self, block_id: str, approved: bool = True,
                           human_note: str = "") -> dict:
        """
        Human Dragon approves or rejects a candidate.
        This is the I9 gate — nothing publishes without this.
        """
        for c in self.candidates:
            if c["block_id"] == block_id:
                c["human_approved"] = approved
                c["human_note"] = human_note
                c["approved_at"] = datetime.now(timezone.utc).isoformat()
                c["status"] = "APPROVED" if approved else "VETOED"
                return c
        
        return {"status": "NOT_FOUND", "block_id": block_id}

    # ── Stage 3: SGE Scan ────────────────────────────────────────────────

    def sge_scan(self, content: dict) -> dict:
        """
        Run SGE semantic governance check on content.
        For v0.1: basic keyword scan. Future: full 7-layer SGE.
        """
        # Combine all language content for scanning
        all_text = " ".join([
            content.get("pt", ""),
            content.get("en", ""),
            content.get("de", "")
        ]).lower()
        
        # Basic risk indicators (v0.1 - will be replaced by full SGE)
        risk_keywords = [
            "password", "credential", "api_key", "secret",
            "ssn", "credit_card", "private_key"
        ]
        
        found_risks = [kw for kw in risk_keywords if kw in all_text]
        
        risk_level = "R0" if not found_risks else f"R{min(len(found_risks), 5)}"
        cleared = len(found_risks) == 0
        
        return {
            "sge_version": "v0.1-publisher",
            "risk_level": risk_level,
            "cleared": cleared,
            "flags": found_risks,
            "scanned_at": datetime.now(timezone.utc).isoformat()
        }

    # ── Stage 4: Trilingual Formatter ────────────────────────────────────

    def format_chapter(self, raw_content: dict, chapter_meta: dict) -> dict:
        """
        Format raw trilingual content into a Storybook chapter structure.
        Validates that all three languages are present.
        """
        required_langs = ["pt", "en", "de"]
        missing = [lang for lang in required_langs if lang not in raw_content 
                    or not raw_content[lang].strip()]
        
        if missing:
            return {
                "status": "INCOMPLETE",
                "missing_languages": missing,
                "message": f"Chapter requires all 3 languages. Missing: {missing}"
            }
        
        return create_chapter(
            chapter_id=chapter_meta.get("chapter_id", f"ch_{uuid.uuid4().hex[:8]}"),
            title=chapter_meta.get("title", {"pt": "Sem título", "en": "Untitled", "de": "Ohne Titel"}),
            content=raw_content,
            symbol=chapter_meta.get("symbol", "🌱"),
            wisdom_block_id=chapter_meta.get("wisdom_block_id"),
            maturity_level=chapter_meta.get("maturity_level", 3)
        )

    # ── Stage 5: Ledger Seal ─────────────────────────────────────────────

    def seal_to_ledger(self, storybook: dict) -> dict:
        """
        Generate Virtue Receipt and seal in Forensic Ledger.
        Returns receipt or error.
        """
        content_hash = _hash_content(storybook)
        book_id = storybook.get("book_id", "unknown")
        title_en = storybook.get("title", {}).get("en", "Unknown")
        
        receipt_payload = {
            "id": f"WPB-{book_id}-{uuid.uuid4().hex[:8]}",
            "actor": "Human Dragon",
            "app": "wisdom-publisher",
            "doc_name": title_en,
            "doc_type": "doc",
            "governance_level": "HIGH",
            "sge_score": 100,
            "content_hash": content_hash,
            "book_id": book_id,
            "chapters_count": len(storybook.get("chapters", [])),
            "impact_level": "MED",
            "department_code": "WISDOM",
            "flow_status": "SEALED",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            conn = HTTPConnection(LEDGER_HOST, LEDGER_PORT, timeout=10)
            body = json.dumps(receipt_payload)
            conn.request("POST", "/api/receipts", body=body,
                        headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            data = json.loads(resp.read().decode())
            conn.close()
            
            if resp.status in (200, 201):
                return {
                    "status": "SEALED",
                    "receipt_id": data.get("id", data.get("receipt_id")),
                    "content_hash": content_hash,
                    "ledger_response": data
                }
            else:
                return {
                    "status": "LEDGER_ERROR",
                    "http_status": resp.status,
                    "detail": data
                }
        except Exception as e:
            return {
                "status": "LEDGER_UNREACHABLE",
                "error": str(e)
            }

    # ── Stage 6: Publish to Library ──────────────────────────────────────

    def publish_to_library(self, storybook: dict, seal_receipt: dict) -> dict:
        """
        Deploy the Storybook as static JSON to the Library directory.
        Only executes if seal_receipt confirms SEALED status.
        """
        if seal_receipt.get("status") != "SEALED":
            return {
                "status": "BLOCKED",
                "reason": "Cannot publish without Ledger seal",
                "seal_status": seal_receipt.get("status")
            }
        
        book_id = storybook["book_id"]
        book_dir = LIBRARY_BOOKS_DIR / book_id
        book_dir.mkdir(parents=True, exist_ok=True)
        
        # Inject seal into manifest
        storybook["governance"]["ledger_sealed"] = True
        storybook["governance"]["ledger_receipt_id"] = seal_receipt.get("receipt_id")
        storybook["governance"]["sge_validated"] = True
        storybook["status"] = "PUBLISHED"
        storybook["updated_at"] = datetime.now(timezone.utc).isoformat()
        storybook["published_at"] = datetime.now(timezone.utc).isoformat()
        
        # Write manifest
        manifest_path = book_dir / "index.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(storybook, f, ensure_ascii=False, indent=2)
        
        # Write individual chapter files for lazy loading
        for chapter in storybook.get("chapters", []):
            ch_path = book_dir / f"{chapter['chapter_id']}.json"
            with open(ch_path, "w", encoding="utf-8") as f:
                json.dump(chapter, f, ensure_ascii=False, indent=2)
        
        # Update library catalog
        self._update_catalog(storybook)
        
        return {
            "status": "PUBLISHED",
            "book_id": book_id,
            "path": str(manifest_path),
            "url": f"/library/books/{book_id}/index.json",
            "chapters_published": len(storybook.get("chapters", []))
        }

    # ── Stage 7: Vault Broadcast ─────────────────────────────────────────

    def broadcast_to_vault(self, publication_result: dict, storybook: dict) -> dict:
        """
        Notify Vault of the new publication for audit trail.
        """
        if publication_result.get("status") != "PUBLISHED":
            return {"status": "SKIPPED", "reason": "Not published yet"}
        
        vault_payload = {
            "doc_type": "doc",
            "book_id": storybook.get("book_id"),
            "title": storybook.get("title", {}).get("en", "Unknown"),
            "published_at": publication_result.get("published_at", 
                            datetime.now(timezone.utc).isoformat()),
            "content_hash": _hash_content(storybook),
            "library_url": publication_result.get("url"),
            "chapters_count": publication_result.get("chapters_published", 0)
        }
        
        try:
            conn = HTTPConnection(VAULT_HOST, VAULT_PORT, timeout=10)
            body = json.dumps(vault_payload)
            conn.request("POST", "/api/receipts", body=body,
                        headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            data = json.loads(resp.read().decode())
            conn.close()
            
            return {
                "status": "BROADCAST",
                "vault_response": data
            }
        except Exception as e:
            return {
                "status": "VAULT_UNREACHABLE",
                "error": str(e),
                "note": "Publication succeeded. Vault sync can retry later."
            }

    # ── Full Pipeline (orchestrator) ─────────────────────────────────────

    def execute_pipeline(self, storybook: dict, human_approved: bool = False,
                          human_note: str = "") -> dict:
        """
        Execute the full publication pipeline.
        
        CRITICAL: human_approved must be explicitly True.
        This is the I9 gate — the pipeline will NOT proceed without it.
        
        Returns a complete pipeline report.
        """
        pipeline_id = f"PUB-{uuid.uuid4().hex[:8]}"
        report = {
            "pipeline_id": pipeline_id,
            "book_id": storybook.get("book_id"),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "stages": {}
        }
        
        # ── I9 Gate ──
        if not human_approved:
            report["stages"]["i9_gate"] = {
                "status": "BLOCKED",
                "reason": "I9: Human approval required. Set human_approved=True."
            }
            report["final_status"] = "AWAITING_HUMAN"
            return report
        
        report["stages"]["i9_gate"] = {
            "status": "APPROVED",
            "human_note": human_note,
            "approved_at": datetime.now(timezone.utc).isoformat()
        }
        
        # ── SGE Scan ──
        all_content = {}
        for ch in storybook.get("chapters", []):
            for lang in ["pt", "en", "de"]:
                text = ch.get("content", {}).get(lang, "")
                all_content[lang] = all_content.get(lang, "") + " " + text
        
        sge_result = self.sge_scan(all_content)
        report["stages"]["sge_scan"] = sge_result
        
        if not sge_result["cleared"]:
            report["final_status"] = "SGE_BLOCKED"
            report["stages"]["sge_scan"]["message"] = (
                f"Content flagged: {sge_result['flags']}. "
                "Review and sanitize before publishing."
            )
            return report
        
        # ── Ledger Seal ──
        seal_result = self.seal_to_ledger(storybook)
        report["stages"]["ledger_seal"] = seal_result
        
        if seal_result["status"] != "SEALED":
            report["final_status"] = "SEAL_FAILED"
            return report
        
        # ── Library Deploy ──
        pub_result = self.publish_to_library(storybook, seal_result)
        report["stages"]["library_deploy"] = pub_result
        
        if pub_result["status"] != "PUBLISHED":
            report["final_status"] = "DEPLOY_FAILED"
            return report
        
        # ── Vault Broadcast ──
        vault_result = self.broadcast_to_vault(pub_result, storybook)
        report["stages"]["vault_broadcast"] = vault_result
        
        # ── Final ──
        report["final_status"] = "PUBLISHED"
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        report["public_url"] = pub_result.get("url")
        
        return report

    # ── Catalog Management ───────────────────────────────────────────────

    def _update_catalog(self, storybook: dict):
        """Update the master catalog of all published Storybooks."""
        catalog_path = LIBRARY_DIR / "catalog.json"
        
        if catalog_path.exists():
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        else:
            catalog = {
                "catalog_version": "1.0.0",
                "books": [],
                "updated_at": None
            }
        
        # Add or update entry
        book_entry = {
            "book_id": storybook["book_id"],
            "title": storybook["title"],
            "author": storybook.get("author", "Unknown"),
            "chapters_count": len(storybook.get("chapters", [])),
            "status": storybook["status"],
            "published_at": storybook.get("published_at"),
            "url": f"/library/books/{storybook['book_id']}/index.json"
        }
        
        # Replace if exists, append if new
        existing_ids = [b["book_id"] for b in catalog["books"]]
        if book_entry["book_id"] in existing_ids:
            idx = existing_ids.index(book_entry["book_id"])
            catalog["books"][idx] = book_entry
        else:
            catalog["books"].append(book_entry)
        
        catalog["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        with open(catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

    # ── List candidates/published ────────────────────────────────────────

    def list_candidates(self) -> list:
        """List all pending publication candidates."""
        return [c for c in self.candidates if c["status"] == "CANDIDATE"]

    def list_published(self) -> list:
        """List all published Storybooks from the catalog."""
        catalog_path = LIBRARY_DIR / "catalog.json"
        if not catalog_path.exists():
            return []
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        return catalog.get("books", [])


# ── Utility Functions ────────────────────────────────────────────────────────

def _hash_content(data: dict) -> str:
    """SHA-256 hash of JSON content for integrity verification."""
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# ── CLI Interface ────────────────────────────────────────────────────────────

def main():
    """CLI for Wisdom Publisher management."""
    import sys
    
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════╗
║   WINDI Wisdom Publisher v0.1.0                  ║
║   "AI processes. Human decides. WINDI guarantees"║
╠══════════════════════════════════════════════════╣
║ Commands:                                        ║
║   list       - Show published Storybooks         ║
║   candidates - Show pending candidates           ║
║   info <id>  - Show Storybook details            ║
║   health     - Check pipeline dependencies       ║
╚══════════════════════════════════════════════════╝
        """)
        return
    
    cmd = sys.argv[1]
    publisher = WisdomPublisher()
    
    if cmd == "list":
        books = publisher.list_published()
        if not books:
            print("📚 No published Storybooks yet.")
        else:
            print(f"📚 Published Storybooks ({len(books)}):")
            for b in books:
                title = b.get("title", {}).get("en", "?")
                print(f"  📖 {b['book_id']}: {title} ({b['chapters_count']} chapters)")
    
    elif cmd == "candidates":
        cands = publisher.list_candidates()
        if not cands:
            print("🌱 No pending candidates.")
        else:
            print(f"🌱 Pending candidates ({len(cands)}):")
            for c in cands:
                print(f"  ⏳ {c['block_id']} (N{c['maturity_level']}) — {c['proposed_at']}")
    
    elif cmd == "info" and len(sys.argv) > 2:
        book_id = sys.argv[2]
        book_path = LIBRARY_BOOKS_DIR / book_id / "index.json"
        if book_path.exists():
            with open(book_path, "r", encoding="utf-8") as f:
                book = json.load(f)
            print(json.dumps(book, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Storybook '{book_id}' not found.")
    
    elif cmd == "health":
        print("🏥 Publisher Health Check:")
        
        # Check Ledger
        try:
            conn = HTTPConnection(LEDGER_HOST, LEDGER_PORT, timeout=5)
            conn.request("GET", "/health")
            resp = conn.getresponse()
            print(f"  📒 Ledger :{LEDGER_PORT} — {'✅ UP' if resp.status == 200 else '⚠️ ' + str(resp.status)}")
            conn.close()
        except:
            print(f"  📒 Ledger :{LEDGER_PORT} — ❌ UNREACHABLE")
        
        # Check Vault
        try:
            conn = HTTPConnection(VAULT_HOST, VAULT_PORT, timeout=5)
            conn.request("GET", "/health")
            resp = conn.getresponse()
            print(f"  🏛️ Vault  :{VAULT_PORT} — {'✅ UP' if resp.status == 200 else '⚠️ ' + str(resp.status)}")
            conn.close()
        except:
            print(f"  🏛️ Vault  :{VAULT_PORT} — ❌ UNREACHABLE")
        
        # Check Library dir
        lib_ok = LIBRARY_DIR.exists() and os.access(LIBRARY_DIR, os.W_OK)
        print(f"  📚 Library dir — {'✅ OK' if lib_ok else '❌ NOT WRITABLE'}")
        
        # Check catalog
        cat_path = LIBRARY_DIR / "catalog.json"
        if cat_path.exists():
            with open(cat_path, "r") as f:
                cat = json.load(f)
            print(f"  📋 Catalog — ✅ {len(cat.get('books', []))} books")
        else:
            print(f"  📋 Catalog — 🆕 Will be created on first publish")
    
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
