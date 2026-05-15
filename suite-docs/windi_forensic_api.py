#!/usr/bin/env python3
"""
WINDI Forensic Ledger API v1.0.0
==================================
BaseHTTPRequestHandler API for Virtue Receipts.
Consistent with Governance API pattern (no Flask).

Port: 8101
DB:   /opt/windi/data/forensic_ledger.sqlite3

Endpoints:
  GET  /health                    → Service health
  GET  /api/receipts              → List receipts (filtered)
  GET  /api/receipts/<id>         → Single receipt
  POST /api/receipts              → Register new receipt
  POST /api/receipts/reconcile    → Hash reconciliation
  GET  /api/warroom/summary       → War Room aggregation
  GET  /api/suite/docs            → Suite v2.1 compat (alias)
  POST /api/suite/docs            → Suite v2.1 compat (adapter)

Principle: Content stays on user hardware.
           Only metadata + content_hash enters the server.
           "AI processes. Human decides. WINDI guarantees."

Author:  Guardian Dragon (Claude) — Architect (GPT) fusion
Date:    2026-02-16
"""

import json
import os
import sys
import time
import sqlite3 as _genesis_sql
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Import the data layer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/opt/windi")  # DECREE-001: Constitutional imports
from forensic_ledger import (
    init_db,
    upsert_receipt,
    list_receipts,
    get_receipt,
    reconcile_hashes,
    aggregate_warroom,
    count_receipts,
    DEFAULT_DB_PATH,
    # T7e: Chain validation (§246-IMPL)
    validate_parent_receipt,
    validate_chain_integrity,
    get_receipt_chain,
    get_receipt_children,
    # §246-IMPL D5.8: Query by wallet
    get_receipts_by_wallet,
)

# G3 Merkle Transparency Log (§246-IMPL-bis)
from merkle_service import (
    get_current_root,
    get_proof_for_receipt,
    get_leaf_by_receipt,
    verify_proof,
    compute_leaf_hash,
)

# ═══════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════

PORT = int(os.environ.get("FORENSIC_API_PORT", "8101"))
VERSION = "1.0.0"
SERVICE_NAME = f"WINDI Forensic Ledger API v{VERSION}"

# §246-IMPL: Schema versioning (D5.5)
# Allows future schema migrations without breaking legacy receipts
SCHEMA_VERSION_CURRENT = "1.0"
SCHEMA_VERSION_ACCEPTED = ["1.0"]  # Whitelist; future: ["1.0", "1.1"]


# ═══════════════════════════════════════════════════
# API Handler
# ═══════════════════════════════════════════════════

class ForensicLedgerHandler(BaseHTTPRequestHandler):
    """HTTP handler for the Forensic Ledger API."""

    # ── Response helpers ──

    def _cors(self):
        """CORS headers for Suite frontend."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _json(self, code, data):
        """Send JSON response."""
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        """Read and parse JSON body."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw)

    # ── OPTIONS (CORS preflight) ──

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── GET routes ──

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = parse_qs(parsed.query)

        # Helper to get single query param
        def q(key, default=None):
            vals = qs.get(key, [])
            return vals[0] if vals else default

        # ── /health ──
        if path == "/health":
            receipt_count = count_receipts()
            self._json(200, {
                "service": SERVICE_NAME,
                "status": "healthy",
                "port": PORT,
                "db": DEFAULT_DB_PATH,
                "receipts": receipt_count,
                "privacy": "content_not_stored",
                "protocol": "Three Dragons v1.1 — I9 Active",
                "decree": "DECREE-001-LIVING-TREE",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # ── /api/tree/health — DECREE-001 Constitutional Check ──
        elif path == "/api/tree/health":
            from constitutional.tree_health import check_all_organs
            import asyncio
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(check_all_organs())
            loop.close()
            self._json(200, result)

        # ── /api/tree/decree — Constitutional Decree Info ──
        elif path == "/api/tree/decree":
            self._json(200, {
                "id": "DECREE-001",
                "name": "A Árvore Viva",
                "name_en": "The Living Tree",
                "sealed": "2026-04-12",
                "author": "Human Dragon",
                "invariants": ["I1", "I9", "I11", "I12", "I14"],
                "status": "CONSTITUTIONAL",
                "quote_pt": "O servidor WINDI é uma Árvore Viva. Cada serviço é um galho.",
                "articles": 7,
            })

        # ── /api/did/validate/{did} — DECREE-001 Article 4: DID Cross-Validation ──
        elif path.startswith("/api/did/validate/"):
            did = path.split("/")[-1]
            if not did or did == "validate":
                self._json(400, {
                    "ok": False,
                    "error": "did_required",
                    "message": "Usage: /api/did/validate/{did}",
                    "example": "/api/did/validate/did:windi:abc123",
                })
                return

            from constitutional.did_sovereign import validate_did_sync
            result = validate_did_sync(did)
            status_code = 200 if result.get("valid") else 404
            self._json(status_code, result)

        # ── /api/did/tiers — DID Tier Information ──
        elif path == "/api/did/tiers":
            from constitutional.did_sovereign import DIDTier, get_tier_info, ORGAN_ACCESS
            tiers = []
            for tier in DIDTier:
                info = get_tier_info(tier)
                info["accessible_organs"] = ORGAN_ACCESS.get(tier, [])
                tiers.append(info)
            self._json(200, {
                "decree": "DECREE-001-LIVING-TREE",
                "article": "Article 4: DID Cross-Validation",
                "tiers": tiers,
                "principle": "One DID, one identity, the whole tree.",
            })

        # ── /api/receipts ──
        elif path == "/api/receipts":
            limit = min(int(q("limit", "50")), 500)
            offset = int(q("offset", "0"))
            actor = q("actor")
            status = q("status")
            doc_type = q("type") or q("doc_type")
            gov = q("governance_level") or q("gov")
            min_sge_str = q("min_sge")
            min_sge = float(min_sge_str) if min_sge_str else None

            data = list_receipts(
                limit=limit,
                offset=offset,
                actor=actor,
                status=status,
                doc_type=doc_type,
                governance_level=gov,
                min_sge=min_sge,
            )
            self._json(200, {
                "ok": True,
                "receipts": data,
                "count": len(data),
                "privacy": "content_not_stored",
            })

        # ── /api/receipts/<id> ──
        elif path.startswith("/api/receipts/") and path.count("/") == 3:
            receipt_id = path.split("/")[-1]
            r = get_receipt(receipt_id)
            if r:
                self._json(200, {"ok": True, "receipt": r})
            else:
                self._json(404, {"ok": False, "error": "not_found", "id": receipt_id})

        # ═══════════════════════════════════════════════════
        # T7e: Chain Validation Endpoints (§246-IMPL)
        # ═══════════════════════════════════════════════════

        # ── /api/receipts/<id>/validate — Chain integrity check ──
        elif path.endswith("/validate") and "/api/receipts/" in path:
            parts = path.split("/")
            receipt_id = parts[-2]  # /api/receipts/{id}/validate
            result = validate_chain_integrity(receipt_id)
            status_code = 200 if result.get("valid") else 409
            self._json(status_code, {
                "ok": result.get("valid"),
                **result,
                "invariant": "I11",
                "constitutional_gate": "T7e",
            })

        # ── /api/receipts/<id>/chain — Get ancestry chain ──
        elif path.endswith("/chain") and "/api/receipts/" in path:
            parts = path.split("/")
            receipt_id = parts[-2]  # /api/receipts/{id}/chain
            chain = get_receipt_chain(receipt_id)
            self._json(200, {
                "ok": True,
                "receipt_id": receipt_id,
                "chain": chain,
                "depth": len(chain),
            })

        # ── /api/receipts/<id>/children — Get direct children ──
        elif path.endswith("/children") and "/api/receipts/" in path:
            parts = path.split("/")
            receipt_id = parts[-2]  # /api/receipts/{id}/children
            children = get_receipt_children(receipt_id)
            self._json(200, {
                "ok": True,
                "receipt_id": receipt_id,
                "children": children,
                "count": len(children),
            })

        # ── /api/receipts/by-wallet/{wallet_id} — §246-IMPL D5.8 ──
        elif "/api/receipts/by-wallet/" in path and not path.endswith("/by-wallet/"):
            # Extract wallet_id from path
            wallet_id = path.split("/api/receipts/by-wallet/")[1].split("?")[0]
            if not wallet_id:
                self._json(400, {"error": "wallet_id required", "code": "MISSING_WALLET_ID"})
                return

            # Validate wallet_id format (basic check)
            if not wallet_id.startswith("did:windi:"):
                self._json(400, {"error": "invalid wallet_id format", "code": "INVALID_WALLET_ID"})
                return

            # Parse query params
            try:
                limit = int(q("limit", "50"))
                if limit < 1 or limit > 200:
                    self._json(400, {"error": "limit exceeds max 200", "code": "LIMIT_EXCEEDED"})
                    return
            except ValueError:
                self._json(400, {"error": "invalid limit value", "code": "INVALID_LIMIT"})
                return

            try:
                offset = int(q("offset", "0"))
                if offset < 0:
                    self._json(400, {"error": "offset must be >= 0", "code": "INVALID_OFFSET"})
                    return
            except ValueError:
                self._json(400, {"error": "invalid offset value", "code": "INVALID_OFFSET"})
                return

            doc_type = q("doc_type")
            order = q("order", "desc").lower()
            if order not in ("asc", "desc"):
                self._json(400, {"error": "order must be 'asc' or 'desc'", "code": "INVALID_ORDER"})
                return

            # Parse since/until (ISO 8601 to unix timestamp)
            since_ts = None
            until_ts = None
            since_str = q("since")
            until_str = q("until")

            if since_str:
                try:
                    since_dt = datetime.fromisoformat(since_str.replace("Z", "+00:00"))
                    since_ts = int(since_dt.timestamp())
                except ValueError:
                    self._json(400, {"error": "invalid since format (use ISO 8601)", "code": "INVALID_SINCE"})
                    return

            if until_str:
                try:
                    until_dt = datetime.fromisoformat(until_str.replace("Z", "+00:00"))
                    until_ts = int(until_dt.timestamp())
                except ValueError:
                    self._json(400, {"error": "invalid until format (use ISO 8601)", "code": "INVALID_UNTIL"})
                    return

            # Validate since < until
            if since_ts and until_ts and since_ts > until_ts:
                self._json(400, {"error": "since must precede until", "code": "INVALID_DATE_RANGE"})
                return

            # Execute query
            result = get_receipts_by_wallet(
                wallet_id=wallet_id,
                limit=limit,
                offset=offset,
                doc_type=doc_type,
                since=since_ts,
                until=until_ts,
                order=order
            )

            self._json(200, {"ok": True, **result})

        # ═══════════════════════════════════════════════════════════
        # G3 Merkle Transparency Log Endpoints (§246-IMPL-bis)
        # Genesis: 66189307d9094eab1353f9352d141d3bd45a633dada9fe4254c8c56fa9ac59cb
        # Invariants: I9, I11 (IRREMEDIÁVEL), I14
        # ═══════════════════════════════════════════════════════════

        # ── /api/merkle/root ──
        elif path == "/api/merkle/root":
            root = get_current_root()
            if root:
                self._json(200, {
                    "ok": True,
                    "root_hash": root["root_hash"],
                    "leaf_count": root["leaf_count"],
                    "created_at": root["created_at"],
                    "predecessor": root.get("predecessor"),
                    "invariant": "I11 — IRREMEDIÁVEL",
                    "spec": "§246-IMPL-bis G3 MERKLE"
                })
            else:
                self._json(404, {
                    "ok": False,
                    "error": "no_merkle_root",
                    "message": "Merkle tree not initialized"
                })

        # ── /api/merkle/proof/{receipt_id} ──
        elif path.startswith("/api/merkle/proof/") and path.count("/") == 4:
            receipt_id = path.split("/")[-1]
            if not receipt_id:
                self._json(400, {"ok": False, "error": "receipt_id required"})
                return

            proof_data = get_proof_for_receipt(receipt_id)
            if proof_data:
                self._json(200, {
                    "ok": True,
                    **proof_data,
                    "invariant": "I11",
                    "spec": "§246-IMPL-bis G3 MERKLE"
                })
            else:
                self._json(404, {
                    "ok": False,
                    "error": "not_found",
                    "receipt_id": receipt_id,
                    "message": "Receipt not found in Merkle log"
                })

        # ── /api/merkle/verify/{receipt_id} ──
        elif path.startswith("/api/merkle/verify/") and path.count("/") == 4:
            receipt_id = path.split("/")[-1]
            if not receipt_id:
                self._json(400, {"ok": False, "error": "receipt_id required"})
                return

            # Get receipt to compute leaf hash
            receipt = get_receipt(receipt_id)
            if not receipt:
                self._json(404, {
                    "ok": False,
                    "error": "receipt_not_found",
                    "receipt_id": receipt_id
                })
                return

            # Get proof
            proof_data = get_proof_for_receipt(receipt_id)
            if not proof_data:
                self._json(404, {
                    "ok": False,
                    "error": "not_in_merkle_log",
                    "receipt_id": receipt_id,
                    "message": "Receipt exists but not in Merkle log"
                })
                return

            # Verify
            leaf_hash = compute_leaf_hash(receipt_id, receipt["content_hash"])
            is_valid = verify_proof(leaf_hash, proof_data["proof"], proof_data["root_hash"])

            self._json(200, {
                "ok": True,
                "verified": is_valid,
                "receipt_id": receipt_id,
                "leaf_hash": leaf_hash,
                "root_hash": proof_data["root_hash"],
                "leaf_index": proof_data["leaf_index"],
                "invariant": "I11",
                "spec": "§246-IMPL-bis G3 MERKLE"
            })

        # ── /api/merkle/leaf/{receipt_id} ──
        elif path.startswith("/api/merkle/leaf/") and path.count("/") == 4:
            receipt_id = path.split("/")[-1]
            leaf = get_leaf_by_receipt(receipt_id)
            if leaf:
                self._json(200, {"ok": True, **leaf})
            else:
                self._json(404, {
                    "ok": False,
                    "error": "not_found",
                    "receipt_id": receipt_id
                })

        # ── /api/warroom/summary ──
        elif path == "/api/warroom/summary":
            summary = aggregate_warroom()
            self._json(200, {"ok": True, "summary": summary})

        # ── /api/suite/docs (backwards compat with Suite v2.1) ──
        elif path == "/api/suite/docs":
            limit = min(int(q("limit", "50")), 200)
            doc_type = q("type")

            data = list_receipts(limit=limit, doc_type=doc_type)

            # Map to Suite v2.1 format for backwards compatibility
            documents = []
            for r in data:
                documents.append({
                    "id": r["id"],
                    "name": r["doc_name"],
                    "type": r["doc_type"],
                    "governance_level": r["governance_level"],
                    "sge_score": r["sge_score"],
                    "hash": r["content_hash"],
                    "template_id": r.get("template_id"),
                    "created_at": datetime.fromtimestamp(
                        r["created_at"], tz=timezone.utc
                    ).isoformat() if r.get("created_at") else None,
                    "sealed": 1 if r.get("status") == "sealed" else 0,
                })

            self._json(200, {
                "documents": documents,
                "count": len(documents),
                "source": "forensic_ledger",
            })

        # ── /api/suite/docs/stats (backwards compat) ──
        elif path == "/api/suite/docs/stats":
            summary = aggregate_warroom()
            self._json(200, {
                "total_documents": summary["total"],
                "by_type": {
                    t["type"]: t["count"] for t in summary.get("by_type", [])
                },
                "by_governance_level": {
                    g["level"]: g["count"] for g in summary.get("by_governance", [])
                },
                "latest": summary.get("latest"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # ── /api/verify/<id> (JMPG integrity verification) ──
        elif path.startswith("/api/verify/") and path.count("/") == 3:
            receipt_id = path.split("/")[-1]
            r = get_receipt(receipt_id)
            if r:
                self._json(200, {
                    "ok": True,
                    "receipt_id": r["id"],
                    "content_hash": r["content_hash"],
                    "bundle_hash": r.get("bundle_hash"),
                    "size_bytes": r.get("bundle_size") or r.get("bytes"),
                    "registered_at": r["created_at"],
                    "governance_level": r["governance_level"],
                    "sge_score": r["sge_score"],
                    "status": r.get("status", "sealed"),
                    "algorithm": "SHA-256",
                    "privacy": "content_not_stored",
                })
            else:
                self._json(404, {
                    "ok": False,
                    "error": "not_found",
                    "receipt_id": receipt_id,
                    "status": "NOT_FOUND",
                })

        else:
            self._json(404, {"ok": False, "error": "not_found", "path": path})

    # ── POST routes ──

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # ── /api/receipts ──
        if path == "/api/receipts":
            try:
                r = self._read_body()

                # Validate required fields
                # G1 FIX (§246-IMPL): wallet_id added as required
                required = [
                    "id", "actor", "app", "doc_name", "doc_type",
                    "content_hash", "governance_level", "sge_score",
                    "wallet_id",  # D5.1: Anchor identity field
                ]
                missing = [k for k in required if k not in r]
                if missing:
                    self._json(400, {
                        "ok": False,
                        "error": f"missing_fields: {', '.join(missing)}",
                    })
                    return

                # ═══════════════════════════════════════════════════════════
                # §191-A + §191-B — CONSTITUTIONAL DID GATE (I9 + I-XVI enforcement)
                # "Nenhuma acção relevante acontece sem um DID."
                # "DID não é só formato. DID é existência."
                # Ledger é a RAIZ da verdade. Sem DID válido E EXISTENTE, nada sela.
                # 19 Abril 2026 · Liga IA+H
                # ═══════════════════════════════════════════════════════════
                actor = r.get("actor", "").strip()

                # Lista de actores proibidos (variações de anónimo)
                FORBIDDEN_ACTORS = {"anon", "anonymous", "unknown", "system", "bot", "test", ""}

                # §191-B FIX 1: DID Existential Validation
                GENESIS_DB = Path("/opt/windi/did-genesis/did_genesis.db")

                def did_exists_in_genesis(did: str) -> bool:
                    """Query Genesis DB to verify DID actually exists."""
                    if not GENESIS_DB.exists():
                        return True  # Graceful degradation
                    try:
                        conn = _genesis_sql.connect(str(GENESIS_DB), timeout=3)
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT 1 FROM identities WHERE LOWER(did) = LOWER(?) AND status = 'active' LIMIT 1",
                            (did,)
                        )
                        exists = cursor.fetchone() is not None
                        if not exists:
                            cursor.execute(
                                "SELECT 1 FROM did_aliases WHERE LOWER(alias_actor) = LOWER(?) AND status = 'active' LIMIT 1",
                                (did,)
                            )
                            exists = cursor.fetchone() is not None
                        conn.close()
                        return exists
                    except Exception:
                        return True  # Fail open

                # Validação: actor deve ser DID válido OU email
                def is_valid_actor(a: str) -> bool:
                    if not a or a.lower() in FORBIDDEN_ACTORS:
                        return False
                    # DID format: did:windi:*
                    if a.startswith("did:windi:"):
                        if len(a) <= 10:
                            return False
                        # §191-B: Also verify DID exists in Genesis
                        return did_exists_in_genesis(a)
                    # Email format: *@*
                    if "@" in a and "." in a:
                        return True
                    return False

                if not is_valid_actor(actor):
                    # Check if it's a format issue or existence issue
                    error_type = "did_required"
                    message = "Ledger requires sovereign identity. Anonymous actors forbidden."
                    if actor.startswith("did:windi:") and len(actor) > 10:
                        error_type = "did_not_found"
                        message = f"DID '{actor}' not found in Genesis Registry. Identity must exist before action."
                    self._json(403, {
                        "ok": False,
                        "error": error_type,
                        "message": message,
                        "invariant": "I9 + I-XVI",
                        "law": "Lei I — Existência antes de Acção",
                        "article": "Art. 14 EU AI Act",
                        "hint": "Provide valid DID (did:windi:*) that exists in Genesis, or verified email as actor.",
                        "examples": ["did:windi:dragon-001", "operator@company.com"]
                    })
                    return

                # Validate types
                # §191: Added service-control types for W-SERVICE-CONTROL restart audit trail
                # §248: Added constitutional for governance laws (Lei V+)
                # §261: Added cognitive_handoff for W-BIND-001 session continuity primitive
                VALID_DOC_TYPES = (
                    "doc", "xlsx", "pptx", "jmpg", "communique", "compliance_passport", "cartaz", "canvas",
                    "service-restart-initiated", "service-restart-completed", "audit-bundle", "constitutional",
                    "cognitive_handoff"
                )
                if r["doc_type"] not in VALID_DOC_TYPES:
                    self._json(400, {
                        "ok": False,
                        "error": f"invalid doc_type: {r['doc_type']}",
                    })
                    return

                if r["governance_level"] not in ("LOW", "MED", "MEDIUM", "HIGH", "CRIT", "GOLD", "SILVER", "BRONZE"):
                    self._json(400, {
                        "ok": False,
                        "error": f"invalid governance_level: {r['governance_level']}",
                    })
                    return

                # ═══════════════════════════════════════════════════
                # §246-IMPL D5.5: SCHEMA VERSION GATE
                # Required for all new receipts. Enables future migrations.
                # ═══════════════════════════════════════════════════
                schema_version = r.get("schema_version")
                if not schema_version:
                    self._json(400, {
                        "ok": False,
                        "error": "schema_version is required",
                        "accepted": SCHEMA_VERSION_ACCEPTED,
                        "hint": f"Add 'schema_version': '{SCHEMA_VERSION_CURRENT}' to your request",
                    })
                    return

                if schema_version not in SCHEMA_VERSION_ACCEPTED:
                    self._json(400, {
                        "ok": False,
                        "error": f"schema_version '{schema_version}' not accepted",
                        "accepted": SCHEMA_VERSION_ACCEPTED,
                    })
                    return

                # ═══════════════════════════════════════════════════
                # G1 FIX (§246-IMPL): wallet_id validation
                # D5.1: wallet_id is anchor identity, maps to actor
                # Format check enforced only when chaining (backward compat)
                # ═══════════════════════════════════════════════════
                wallet_id = r.get("wallet_id", "").strip()
                parent_receipt_id = r.get("parent_receipt_id")

                # When chaining, wallet_id MUST be valid DID format
                if parent_receipt_id and not wallet_id.startswith("did:windi:"):
                    self._json(400, {
                        "ok": False,
                        "error": "invalid_wallet_id",
                        "message": "wallet_id must be valid DID (did:windi:...) when chaining receipts",
                        "spec": "D5.1",
                        "invariant": "I11",
                        "constitutional": True,
                    })
                    return

                # Map wallet_id to actor (D5 semantic: wallet_id is the canonical identity)
                # This preserves backward compat: actor column stores wallet_id
                if wallet_id:
                    r["actor"] = wallet_id

                # Defaults
                r.setdefault("created_at", int(time.time()))
                r.setdefault("status", "sealed")
                r.setdefault("tags", [])
                r.setdefault("flags", [])
                r.setdefault("isp_context", "")

                # ═══════════════════════════════════════════════════
                # T7e: CHAIN INTEGRITY GATE (§246-IMPL G2+G5 FIX)
                # Constitutional: Broken chain cannot create future trust
                # G5: Full chain validation, not just parent
                # G2: Wallet consistency across chain
                # ═══════════════════════════════════════════════════
                if parent_receipt_id:
                    # G5 FIX: Full chain validation
                    chain_result = validate_chain_integrity(parent_receipt_id)
                    if not chain_result.get("valid"):
                        self._json(409, {
                            "ok": False,
                            "error": "chain_integrity_broken",
                            "code": "T7e_CHAIN_CORRUPTED",
                            "message": "Cannot seal over corrupted chain",
                            "violations": chain_result.get("violations", []),
                            "spec": "D5.4",
                            "invariant": "I11",
                            "constitutional": True,
                            "parent_receipt_id": parent_receipt_id,
                        })
                        return

                    # G2 FIX: Wallet consistency check
                    parent = get_receipt(parent_receipt_id)
                    if parent and parent.get("actor") != wallet_id:
                        self._json(409, {
                            "ok": False,
                            "error": "wallet_mismatch",
                            "code": "D5.4_WALLET_CONSISTENCY",
                            "message": f"wallet_id '{wallet_id}' != parent wallet '{parent.get('actor')}'",
                            "spec": "D5.4",
                            "invariant": "I11",
                            "constitutional": True,
                            "parent_receipt_id": parent_receipt_id,
                        })
                        return

                # TODO: Ed25519 signature verification
                # if r.get("ed25519_sig") and r.get("ed25519_pub"):
                #     verify_ed25519(canonical_receipt_payload(r), r["ed25519_sig"], r["ed25519_pub"])

                upsert_receipt(r)

                print(f"[FORENSIC] ◆ Receipt: {r['id']} | {r['doc_name']} | {r['governance_level']} | SGE {r['sge_score']}")
                self._json(201, {
                    "ok": True,
                    "stored": True,
                    "id": r["id"],
                    "privacy": "content_not_stored",
                    "message": f"Virtue Receipt '{r['id']}' sealed in Forensic Ledger",
                })

            except json.JSONDecodeError:
                self._json(400, {"ok": False, "error": "invalid_json"})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})

        # ── /api/receipts/reconcile ──
        elif path == "/api/receipts/reconcile":
            try:
                payload = self._read_body()
                hashes = payload.get("hashes", [])
                actor = payload.get("actor")

                if not hashes:
                    self._json(400, {"ok": False, "error": "hashes_required"})
                    return

                matched = reconcile_hashes(hashes, actor=actor)
                self._json(200, {
                    "ok": True,
                    "matched": matched,
                    "count": len(matched),
                    "submitted": len(hashes),
                })

            except json.JSONDecodeError:
                self._json(400, {"ok": False, "error": "invalid_json"})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})

        # ── /api/suite/docs (backwards compat adapter) ──
        elif path == "/api/suite/docs":
            try:
                data = self._read_body()

                # Adapt Suite v2.1 format to Forensic Receipt format
                receipt = {
                    "id": data.get("id"),
                    "actor": data.get("actor", "suite-user"),
                    "app": "suite",
                    "doc_name": data.get("name", "Untitled"),
                    "doc_type": data.get("type", "doc"),
                    "local_filename": data.get("local_filename"),
                    "content_hash": data.get("hash", data.get("content_hash", "0x0000")),
                    "governance_level": data.get("governance_level", "LOW"),
                    "sge_score": float(data.get("sge_score", 0)),
                    "isp_context": data.get("isp_context", ""),
                    "template_id": data.get("template_id"),
                    "created_at": int(time.time()),
                    "status": "sealed" if data.get("sealed", 1) else "draft",
                    "tags": [],
                    "flags": [],
                    "metadata": data.get("metadata", {}),
                }

                # Validate minimum
                if not receipt["id"] or not receipt["doc_name"]:
                    self._json(400, {"ok": False, "error": "id and name required"})
                    return

                upsert_receipt(receipt)

                print(f"[FORENSIC] ◆ Suite Receipt: {receipt['id']} | {receipt['doc_name']}")
                self._json(201, {
                    "status": "registered",
                    "document_id": receipt["id"],
                    "message": f"Document '{receipt['doc_name']}' registered in Forensic Ledger",
                })

            except json.JSONDecodeError:
                self._json(400, {"ok": False, "error": "invalid_json"})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})

        # ── /api/receipts/<id>/seal-bundle (update bundle_hash after ZIP) ──
        elif path.endswith("/seal-bundle") and "/api/receipts/" in path:
            try:
                # Extract receipt_id: /api/receipts/JMPG-xxx/seal-bundle
                parts = path.split("/")
                receipt_id = parts[-2]  # e.g. "JMPG-20260218-ABC123"

                data = self._read_body()
                bundle_hash = data.get("bundle_hash")
                bundle_size = data.get("bundle_size")

                if not bundle_hash:
                    self._json(400, {"ok": False, "error": "bundle_hash required"})
                    return

                # Update the existing receipt
                import sqlite3 as _sql
                con = _sql.connect(DEFAULT_DB_PATH)
                try:
                    cur = con.execute(
                        "UPDATE receipts SET bundle_hash = ?, bundle_size = ? WHERE id = ?",
                        (bundle_hash, bundle_size, receipt_id)
                    )
                    con.commit()
                    if cur.rowcount > 0:
                        print(f"[FORENSIC] ◆ Bundle sealed: {receipt_id} | hash={bundle_hash[:16]}... | size={bundle_size}")
                        self._json(200, {
                            "ok": True,
                            "receipt_id": receipt_id,
                            "bundle_hash": bundle_hash,
                            "bundle_size": bundle_size,
                            "message": f"Bundle hash sealed for '{receipt_id}'",
                        })
                    else:
                        self._json(404, {"ok": False, "error": f"receipt {receipt_id} not found"})
                finally:
                    con.close()

            except json.JSONDecodeError:
                self._json(400, {"ok": False, "error": "invalid_json"})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})

        # ── /api/ledger/seal (C5.1: Cartaz Forensic Seal) ──
        elif path == "/api/ledger/seal":
            try:
                data = self._read_body()

                # Accept flexible payload from agent-palette-cartaz
                receipt = {
                    "id": data.get("id"),
                    "actor": data.get("actor", "anonymous"),
                    "device_id": data.get("device_id"),
                    "app": data.get("app", "agent-palette"),
                    "doc_name": data.get("doc_name", "Untitled"),
                    "doc_type": data.get("doc_type", "cartaz"),
                    "local_filename": data.get("local_filename"),
                    "content_hash": data.get("content_hash", ""),
                    "bytes": data.get("bytes", 0),
                    "governance_level": data.get("governance_level", "MEDIUM"),
                    "sge_score": float(data.get("sge_score", 0.95)),
                    "isp_context": data.get("isp_context", ""),
                    "template_id": data.get("template_id"),
                    "tags": data.get("tags", []),
                    "flags": data.get("flags", []),
                    "created_at": data.get("created_at", int(time.time())),
                    "status": data.get("status", "sealed"),
                    "metadata": data.get("metadata", {}),
                }

                # Validate minimum required
                if not receipt["id"]:
                    self._json(400, {"ok": False, "error": "id required"})
                    return
                if not receipt["content_hash"]:
                    self._json(400, {"ok": False, "error": "content_hash required"})
                    return

                upsert_receipt(receipt)

                print(f"[FORENSIC] ◆ Cartaz Seal: {receipt['id']} | {receipt['doc_name']} | SGE {receipt['sge_score']}")
                self._json(201, {
                    "ok": True,
                    "sealed": True,
                    "receipt_id": receipt["id"],
                    "content_hash": receipt["content_hash"],
                    "doc_type": receipt["doc_type"],
                    "governance_level": receipt["governance_level"],
                    "sge_score": receipt["sge_score"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "privacy": "content_not_stored",
                    "message": f"Cartaz '{receipt['id']}' sealed in Forensic Ledger",
                })

            except json.JSONDecodeError:
                self._json(400, {"ok": False, "error": "invalid_json"})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})

        else:
            self._json(404, {"ok": False, "error": "not_found", "path": path})

    # ── Logging ──

    def log_message(self, format, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[FORENSIC {ts}] {args[0]}")


# ═══════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    server = HTTPServer(("0.0.0.0", PORT), ForensicLedgerHandler)

    print(f"")
    print(f"  ◆ {SERVICE_NAME}")
    print(f"  ◆ Port: {PORT}")
    print(f"  ◆ DB:   {DEFAULT_DB_PATH}")
    print(f"  ◆ Privacy: content_not_stored")
    print(f"")
    print(f"  Endpoints:")
    print(f"    GET  /health                  — Service health")
    print(f"    GET  /api/receipts            — List Virtue Receipts")
    print(f"    GET  /api/receipts/<id>       — Single receipt")
    print(f"    POST /api/receipts            — Seal new receipt")
    print(f"    POST /api/receipts/reconcile  — Hash reconciliation")
    print(f"    GET  /api/warroom/summary     — War Room aggregation")
    print(f"    GET  /api/suite/docs          — Suite v2.1 compat")
    print(f"    POST /api/suite/docs          — Suite v2.1 compat")
    print(f"    POST /api/ledger/seal         — C5.1 Cartaz Forensic Seal")
    print(f"")
    print(f"  ◆ AI processes. Human decides. WINDI guarantees.")
    print(f"")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[FORENSIC] Shutdown.")
        server.server_close()
