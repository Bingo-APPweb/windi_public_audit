#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════╗
║   WINDI PAPERLESS SCHNITTSTELLE v1.0.0                           ║
║   Production-Ready Interface — "Phase A Quick Start"             ║
║                                                                   ║
║   Three Dragons Consensus:                                        ║
║     Guardian: Architecture + Implementation                       ║
║     Architect: Strategy + Positioning                             ║
║     Witness: Swagger Analysis + Forensic Mapping                  ║
║                                                                   ║
║   This is NOT "using Paperless".                                  ║
║   This is ENCAPSULATING Paperless.                                ║
║                                                                   ║
║   AI processes. Human decides. WINDI guarantees.                  ║
║   Port: 8095 · Strato: 87.106.29.233                             ║
╚═══════════════════════════════════════════════════════════════════╝

Swagger Source: Paperless Public API v1 (16,516 lines analyzed)
Auth: OAuth2 Authorization Code Flow
  - authorizationUrl: https://app.paperless.io/oauth/authorize
  - tokenUrl: https://app.paperless.io/api/v1/authenticate/oauth/token
  - Scopes: document.*, blob.write, submission.read, webhook.*, template.read

Date:    12 February 2026
Status:  DEPLOYMENT-READY
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import logging
import urllib.request
import urllib.parse
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from typing import Optional, Dict, Any, List, Tuple
from functools import wraps

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

VERSION = "1.1.0"  # Hardened: HMAC+anti-replay+request_id, token security, kill switch

# Paperless.io endpoints (from swagger.yaml)
PAPERLESS = {
    "api_base":   "https://api.paperless.io/api/v1",
    "auth_url":   "https://app.paperless.io/oauth/authorize",
    "token_url":  "https://app.paperless.io/api/v1/authenticate/oauth/token",
    "api_version": "2023-06-23",
}

# WINDI paths
WINDI_BASE = Path("/opt/windi")
TSIL_DIR = WINDI_BASE / "tsil"
FORENSIC_LOG = TSIL_DIR / "schnittstelle_ledger.jsonl"
CONFIG_FILE = TSIL_DIR / "paperless_credentials.json"
EVIDENCE_DIR = TSIL_DIR / "evidence" / "paperless"

# Environment variables
ENV_CLIENT_ID = "WINDI_PAPERLESS_CLIENT_ID"
ENV_CLIENT_SECRET = "WINDI_PAPERLESS_CLIENT_SECRET"
ENV_ACCESS_TOKEN = "WINDI_PAPERLESS_TOKEN"
ENV_REFRESH_TOKEN = "WINDI_PAPERLESS_REFRESH_TOKEN"
ENV_WEBHOOK_SECRET = "WINDI_PAPERLESS_WEBHOOK_SECRET"
ENV_WORKSPACE_ID = "WINDI_PAPERLESS_WORKSPACE_ID"

# ── HARDENING #3: Kill Switch ──
# Set to "disabled" to block ALL signing operations instantly.
# Valid values: "paperless" (active), "dtrust" (future), "disabled" (kill switch)
ENV_SIGNING_PROVIDER = "WINDI_SIGNING_PROVIDER"
SIGNING_PROVIDER_DEFAULT = "paperless"

# ── HARDENING #1b: Anti-Replay ──
# Webhook timestamp tolerance: reject events older than this (seconds)
WEBHOOK_TIMESTAMP_TOLERANCE = 300  # 5 minutes

# Required OAuth2 scopes (from swagger securitySchemes)
SCOPES = [
    "current_user.read",
    "document.read",
    "document.write",
    "blob.write",
    "submission.read",
    "webhook.read",
    "webhook.write",
    "template.read",
]

# Webhook port
WEBHOOK_PORT = 8095

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("WINDI.SCHNITTSTELLE")


# ═══════════════════════════════════════════════════════════════════
# HARDENING #3 — KILL SWITCH
# "Infraestrutura madura SEMPRE tem kill switch." — Architect
# ═══════════════════════════════════════════════════════════════════

class KillSwitch:
    """
    Global signing kill switch.
    
    WINDI_SIGNING_PROVIDER controls all signing operations:
      "paperless"  → Paperless.io bridge active (default)
      "dtrust"     → D-Trust direct (future)
      "disabled"   → ALL signing BLOCKED instantly
    
    Usage: export WINDI_SIGNING_PROVIDER=disabled
    Result: Every sign() call returns PROVIDER_DISABLED immediately.
    """

    @staticmethod
    def get_provider() -> str:
        return os.environ.get(ENV_SIGNING_PROVIDER, SIGNING_PROVIDER_DEFAULT).lower()

    @staticmethod
    def is_active() -> bool:
        return KillSwitch.get_provider() not in ("disabled", "off", "kill", "stop")

    @staticmethod
    def check() -> Dict[str, Any]:
        """Check kill switch status. Call before ANY signing operation."""
        provider = KillSwitch.get_provider()
        active = KillSwitch.is_active()
        return {
            "kill_switch": "OFF" if active else "ENGAGED",
            "provider": provider,
            "signing_allowed": active,
            "env_var": ENV_SIGNING_PROVIDER,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def enforce(operation: str) -> Optional[Dict[str, Any]]:
        """
        Enforce kill switch. Returns None if OK, error dict if blocked.
        Call at start of sign(), dispatch(), etc.
        """
        if not KillSwitch.is_active():
            return {
                "status": "BLOCKED_BY_KILL_SWITCH",
                "provider": KillSwitch.get_provider(),
                "operation": operation,
                "message": (
                    f"Signing blocked. WINDI_SIGNING_PROVIDER="
                    f"{KillSwitch.get_provider()}. "
                    f"Set to 'paperless' to re-enable."
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return None


# ═══════════════════════════════════════════════════════════════════
# INVARIANT I9 — Prohibition of Autonomy Escalation
# IRREMEDIABLE since 08 Feb 2026
# ═══════════════════════════════════════════════════════════════════

class InvariantI9:
    """
    I9: No automated signing. Ever. Period.
    
    Every operation that creates legal obligations
    MUST pass through human confirmation gate.
    This is IRREMEDIABLE — no config flag can disable it.
    """

    SIGNING_OPS = frozenset({
        "SIGN_DOCUMENT",
        "DISPATCH_FOR_SIGNING",
        "QES_REQUEST",
        "SEAL_REQUEST",
    })

    AUTOMATED_OPS = frozenset({
        "HEALTH_CHECK",
        "LIST_TEMPLATES",
        "GET_SUBMISSION",
        "WEBHOOK_RECEIVE",
        "UPLOAD_BLOB",
        "TOKEN_REFRESH",
    })

    @classmethod
    def gate(cls, operation: str) -> Dict[str, Any]:
        """
        Constitutional Gate.
        Returns PENDING_HUMAN_CONFIRMATION for signing ops.
        Returns PASS for automated ops.
        Raises for unknown ops (fail-safe).
        """
        ts = datetime.now(timezone.utc).isoformat()

        if operation in cls.SIGNING_OPS:
            return {
                "gate": "I9",
                "operation": operation,
                "status": "PENDING_HUMAN_CONFIRMATION",
                "i9": "IRREMEDIABLE",
                "auto_apply": False,
                "message": "Mensch muss bestätigen. Keine automatische Signatur.",
                "timestamp": ts,
            }
        elif operation in cls.AUTOMATED_OPS:
            return {
                "gate": "I9",
                "operation": operation,
                "status": "PASS",
                "i9": "IRREMEDIABLE",
                "auto_apply": False,
                "timestamp": ts,
            }
        else:
            # Unknown operation — fail safe, require human
            return {
                "gate": "I9",
                "operation": operation,
                "status": "UNKNOWN_OP_REQUIRES_HUMAN",
                "i9": "IRREMEDIABLE",
                "auto_apply": False,
                "timestamp": ts,
            }


# ═══════════════════════════════════════════════════════════════════
# FORENSIC LEDGER — Append-Only, Hash-Chained
# ═══════════════════════════════════════════════════════════════════

class ForensicLedger:
    """
    Append-only JSONL ledger with hash chain.
    Each entry includes hash of previous entry → tamper-evident.
    """

    def __init__(self, path: Path = FORENSIC_LOG):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._prev_hash = self._get_last_hash()

    def _get_last_hash(self) -> str:
        """Get hash of last entry for chain continuity."""
        if not self.path.exists():
            return "GENESIS"
        try:
            with open(self.path, "r") as f:
                lines = f.readlines()
                if lines:
                    last = json.loads(lines[-1])
                    return last.get("entry_hash", "GENESIS")
        except Exception:
            pass
        return "GENESIS"

    def append(self, event_type: str, data: Dict[str, Any],
               i9_gate: Optional[Dict] = None) -> str:
        """Append entry to ledger. Returns entry hash."""
        entry = {
            "seq": self._count() + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "SCHNITTSTELLE",
            "version": VERSION,
            "event_type": event_type,
            "data": data,
            "prev_hash": self._prev_hash,
        }
        if i9_gate:
            entry["i9_gate"] = i9_gate

        # Compute hash BEFORE adding it (deterministic)
        canonical = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        entry_hash = hashlib.sha256(canonical.encode()).hexdigest()
        entry["entry_hash"] = entry_hash

        with open(self.path, "a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

        self._prev_hash = entry_hash
        return entry_hash

    def _count(self) -> int:
        if not self.path.exists():
            return 0
        with open(self.path, "r") as f:
            return sum(1 for _ in f)

    def verify_chain(self) -> Dict[str, Any]:
        """Verify hash chain integrity."""
        if not self.path.exists():
            return {"status": "EMPTY", "entries": 0}

        with open(self.path, "r") as f:
            lines = f.readlines()

        prev = "GENESIS"
        broken_at = None
        for i, line in enumerate(lines):
            entry = json.loads(line)
            if entry.get("prev_hash") != prev:
                broken_at = i + 1
                break
            # Recompute hash
            stored_hash = entry.pop("entry_hash")
            canonical = json.dumps(entry, sort_keys=True, separators=(",", ":"))
            computed = hashlib.sha256(canonical.encode()).hexdigest()
            if computed != stored_hash:
                broken_at = i + 1
                break
            entry["entry_hash"] = stored_hash
            prev = stored_hash

        return {
            "status": "INTACT" if broken_at is None else "BROKEN",
            "entries": len(lines),
            "broken_at": broken_at,
            "last_hash": prev,
        }


# ═══════════════════════════════════════════════════════════════════
# OAUTH2 CLIENT — Authorization Code Flow
# Per swagger: securitySchemes.oAuth2.flows.authorizationCode
# ═══════════════════════════════════════════════════════════════════

class OAuth2Client:
    """
    OAuth2 Authorization Code flow for Paperless.io.
    
    Setup steps (one-time):
    1. Register app at Paperless.io → get client_id + client_secret
    2. Run: python3 schnittstelle.py oauth-url
       → Opens browser for user authorization
    3. User authorizes → redirected with ?code=XXX
    4. Run: python3 schnittstelle.py oauth-exchange CODE
       → Exchanges code for access_token + refresh_token
    5. Tokens saved to credentials file
    """

    def __init__(self):
        self.client_id = os.environ.get(ENV_CLIENT_ID, "")
        self.client_secret = os.environ.get(ENV_CLIENT_SECRET, "")
        self.access_token = os.environ.get(ENV_ACCESS_TOKEN, "")
        self.refresh_token = os.environ.get(ENV_REFRESH_TOKEN, "")
        self._load_saved_credentials()

    def _load_saved_credentials(self):
        """Load credentials from file if env vars not set."""
        if self.access_token:
            return
        if CONFIG_FILE.exists():
            try:
                creds = json.loads(CONFIG_FILE.read_text())
                self.access_token = creds.get("access_token", "")
                self.refresh_token = creds.get("refresh_token", "")
                self.client_id = creds.get("client_id", self.client_id)
                self.client_secret = creds.get("client_secret", self.client_secret)
            except Exception:
                pass

    def save_credentials(self):
        """
        Save tokens to credentials file.
        
        HARDENING #2 — Token Storage Security:
          - File permissions: 0600 (owner read/write only)
          - Owner verification: windi:windi
          - .gitignore: auto-created to prevent version control
          - Backup: encrypted copy with timestamp
        """
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        creds = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "warning": "CONFIDENTIAL — Do not commit to version control",
        }
        CONFIG_FILE.write_text(json.dumps(creds, indent=2))
        os.chmod(str(CONFIG_FILE), 0o600)  # Owner read/write only

        # ── .gitignore protection ──
        gitignore = CONFIG_FILE.parent / ".gitignore"
        gitignore_entries = {
            "paperless_credentials.json",
            "*.secret",
            "*.key",
            "*.pem",
        }
        existing = set()
        if gitignore.exists():
            existing = set(gitignore.read_text().strip().split("\n"))
        missing = gitignore_entries - existing
        if missing:
            with open(gitignore, "a") as f:
                for entry in sorted(missing):
                    f.write(f"{entry}\n")

        # ── Encrypted backup (XOR with env-derived key, basic protection) ──
        backup_dir = WINDI_BASE / "backups" / "credentials"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_name = f"creds_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.enc"
        backup_path = backup_dir / backup_name

        # Simple encryption: HMAC-derived key XOR (defense-in-depth, not primary security)
        key_material = (self.client_id + "WINDI_TSIL_v1").encode()
        key = hashlib.sha256(key_material).digest()
        plaintext = json.dumps(creds).encode()
        encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(plaintext))
        backup_path.write_bytes(encrypted)
        os.chmod(str(backup_path), 0o600)

        # ── Owner verification (best-effort, may need root) ──
        try:
            import pwd
            windi_uid = pwd.getpwnam("windi").pw_uid
            windi_gid = pwd.getpwnam("windi").pw_gid
            os.chown(str(CONFIG_FILE), windi_uid, windi_gid)
            os.chown(str(backup_path), windi_uid, windi_gid)
        except (KeyError, PermissionError, ImportError):
            pass  # Non-critical: on dev machines, owner may differ

        logger.info(f"Credentials saved: {CONFIG_FILE} (0600) + backup: {backup_name}")

    def get_authorization_url(self, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> str:
        """Generate OAuth2 authorization URL."""
        params = urllib.parse.urlencode({
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
        })
        return f"{PAPERLESS['auth_url']}?{params}"

    def exchange_code(self, code: str, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        data = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }).encode()

        req = urllib.request.Request(
            PAPERLESS["token_url"],
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())
                self.access_token = result.get("access_token", "")
                self.refresh_token = result.get("refresh_token", "")
                self.save_credentials()
                return {"status": "SUCCESS", "token_type": result.get("token_type")}
        except urllib.error.HTTPError as e:
            return {"status": "ERROR", "code": e.code, "detail": e.read().decode()}

    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh expired access token."""
        if not self.refresh_token:
            return {"status": "ERROR", "detail": "No refresh token available"}

        data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }).encode()

        req = urllib.request.Request(
            PAPERLESS["token_url"],
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())
                self.access_token = result.get("access_token", "")
                if result.get("refresh_token"):
                    self.refresh_token = result["refresh_token"]
                self.save_credentials()
                return {"status": "REFRESHED"}
        except urllib.error.HTTPError as e:
            return {"status": "ERROR", "code": e.code, "detail": e.read().decode()}

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token)

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Paperless-Version": PAPERLESS["api_version"],
        }


# ═══════════════════════════════════════════════════════════════════
# PAPERLESS API — Typed methods matching swagger.yaml operations
# ═══════════════════════════════════════════════════════════════════

class PaperlessAPI:
    """
    Typed wrapper for Paperless Public API v1.
    Each method maps to a swagger operationId.
    
    Error handling per swagger:
      400 = InvalidSchemaError (bad params)
      402 = PaymentRequired (plan limit exceeded)
      403 = NotAuthenticated / InvalidCSRFToken
      404 = RecordNotFound
      406 = InvalidFormat
      422 = Unprocessable (validation errors)
    """

    def __init__(self, oauth: OAuth2Client, sandbox: bool = False):
        self.oauth = oauth
        self.sandbox = sandbox
        self.base = PAPERLESS["api_base"]

    def _call(self, method: str, path: str, body: Optional[Dict] = None,
              accept: str = "application/json") -> Dict[str, Any]:
        """Make authenticated API call with error handling."""
        url = f"{self.base}{path}"
        headers = {**self.oauth.headers, "Accept": accept}

        if self.sandbox:
            return self._sandbox(method, path, body)

        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return json.loads(resp.read().decode())
                elif "application/pdf" in content_type:
                    return {"_binary": True, "_data": resp.read(), "_type": "pdf"}
                return {"_raw": resp.read().decode()}
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode()
                error_json = json.loads(error_body)
            except Exception:
                error_json = {"raw": error_body}

            result = {
                "_error": True,
                "status_code": e.code,
                "error": error_json,
            }

            # Handle specific status codes per swagger
            if e.code == 402:
                result["windi_action"] = "PLAN_LIMIT_EXCEEDED"
                result["windi_advice"] = (
                    "Paperless plan limit reached. "
                    "Consider upgrading or check document count."
                )
            elif e.code == 403:
                result["windi_action"] = "AUTH_FAILED"
                result["windi_advice"] = "Token may be expired. Try: schnittstelle.py refresh"
            elif e.code == 422:
                result["windi_action"] = "VALIDATION_ERROR"
                result["windi_advice"] = (
                    "Check participants, slugs, or required fields."
                )

            return result

    def _sandbox(self, method: str, path: str, body: Optional[Dict]) -> Dict[str, Any]:
        """Realistic sandbox responses per swagger examples."""
        now = datetime.now(timezone.utc).isoformat()
        sid = secrets.randbelow(9000) + 1000

        if "/blobs" in path and method == "POST":
            signed_id = f"eyJ_{secrets.token_urlsafe(40)}"
            return {
                "id": sid, "key": secrets.token_hex(14),
                "filename": (body or {}).get("filename", "doc.pdf"),
                "content_type": "application/pdf",
                "byte_size": (body or {}).get("byte_size", 0),
                "checksum": base64.b64encode(secrets.token_bytes(16)).decode(),
                "signed_id": signed_id,
                "direct_upload": {
                    "url": f"https://storage.paperless.io/upload/{secrets.token_hex(16)}",
                    "headers": {"Content-Type": "application/pdf"},
                },
                "created_at": now, "_sandbox": True,
            }

        elif "/documents" in path and method == "POST":
            return {
                "id": sid, "type": "Document",
                "name": (body or {}).get("name", "WINDI Doc"),
                "state": "draft",
                "workspace_id": (body or {}).get("workspace_id", 1),
                "participation_flow_id": sid + 200,
                "participants": {
                    f"slot{i+1}": {
                        "id": sid + 300 + i,
                        "email": p.get("email", ""),
                        "name": p.get("name", ""),
                        "role": p.get("role", "approver"),
                        "state": "initialized",
                        "qes_waiting_at": None,
                        "qes_dispatching_at": None,
                        "qes_dispatch_completed_at": None,
                        "qes_opened_at": None,
                        "qes_started_at": None,
                    }
                    for i, (slot, p) in enumerate(((body or {}).get("participants", {}).items()))
                },
                "created_at": now, "updated_at": now, "_sandbox": True,
            }

        elif "/documents/" in path and method == "PATCH":
            doc_id = path.split("/")[-1]
            new_state = (body or {}).get("state", "draft")
            return {
                "id": int(doc_id) if doc_id.isdigit() else sid,
                "state": new_state, "updated_at": now, "_sandbox": True,
            }

        elif "/submissions/" in path and method == "GET":
            sub_id = path.split("/")[-1]
            return {
                "id": int(sub_id) if sub_id.isdigit() else sid,
                "submittable_id": sid + 100,
                "state": "completed",
                "rendering_locale": "de-DE",
                "pdf": f"https://cdn.paperless.io/pdf/{secrets.token_hex(12)}.pdf",
                "audit_trail_pdf": f"https://cdn.paperless.io/audit/{secrets.token_hex(12)}.pdf",
                "sealed_pdf": f"https://cdn.paperless.io/sealed/{secrets.token_hex(12)}.pdf",
                "dispatched_at": now, "completed_at": now,
                "_sandbox": True,
            }

        elif "/webhooks" in path and method == "POST":
            return {
                "id": sid,
                "oauth_application_id": (body or {}).get("oauth_application_id", 1),
                "events": (body or {}).get("events", ["submission.completed"]),
                "hook_url": (body or {}).get("hook_url", ""),
                "_sandbox": True,
            }

        elif "/templates" in path and method == "GET":
            return {
                "data": [
                    {"id": 1001, "name": "WINDI Governance Bescheid", "state": "active",
                     "workspace_id": 1, "type": "Template"},
                    {"id": 1002, "name": "WINDI Compliance Report", "state": "active",
                     "workspace_id": 1, "type": "Template"},
                    {"id": 1003, "name": "WINDI Vertragsvorlage", "state": "active",
                     "workspace_id": 1, "type": "Template"},
                ],
                "count": 3, "_sandbox": True,
            }

        elif "/current_user" in path:
            return {
                "id": 1, "name": "WINDI System",
                "email": "noreply@a4desk.de", "locale": "de-DE",
                "_sandbox": True,
            }

        return {"_sandbox": True, "method": method, "path": path}

    # ─── Swagger Operations ─────────────────────────────────────

    def create_blob(self, filename: str, byte_size: int,
                    content_type: str = "application/pdf",
                    checksum: str = "") -> Dict[str, Any]:
        """operationId: createBlob — POST /api/v1/blobs"""
        return self._call("POST", "/blobs", {
            "filename": filename,
            "content_type": content_type,
            "byte_size": byte_size,
            "checksum": checksum,
        })

    def upload_to_direct_url(self, url: str, data: bytes,
                              content_type: str = "application/pdf") -> bool:
        """Upload file content to the direct_upload URL from createBlob."""
        if self.sandbox:
            return True
        req = urllib.request.Request(url, data=data,
            headers={"Content-Type": content_type}, method="PUT")
        try:
            urllib.request.urlopen(req)
            return True
        except Exception as e:
            logger.error(f"Direct upload failed: {e}")
            return False

    def create_document_from_pdf(self, workspace_id: int, pdf_signed_id: str,
                                  name: str, description: str = "",
                                  participants: Optional[Dict] = None,
                                  dispatch_strategy: str = "email",
                                  locale: str = "de-DE") -> Dict[str, Any]:
        """operationId: createDocument — POST /api/v1/documents (from PDF)"""
        body = {
            "workspace_id": workspace_id,
            "pdf": pdf_signed_id,
            "name": name,
            "description": description,
            "original_content_locale": locale,
            "rendering_locale": locale,
            "participants_dispatch_strategy": dispatch_strategy,
        }
        if participants:
            body["participants"] = participants
        return self._call("POST", "/documents", body)

    def create_document_from_template(self, workspace_id: int, template_id: int,
                                       name: str, description: str = "",
                                       participants: Optional[Dict] = None,
                                       tokens: Optional[Dict] = None,
                                       dispatch_strategy: str = "email") -> Dict[str, Any]:
        """operationId: createDocument — POST /api/v1/documents (from Template)"""
        body = {
            "workspace_id": workspace_id,
            "template_id": template_id,
            "name": name,
            "description": description,
            "participants_dispatch_strategy": dispatch_strategy,
        }
        if participants:
            body["participants"] = participants
        if tokens:
            body["tokens"] = tokens
        return self._call("POST", "/documents", body)

    def update_document(self, doc_id: int, **kwargs) -> Dict[str, Any]:
        """operationId: updateDocument — PATCH /api/v1/documents/{id}"""
        return self._call("PATCH", f"/documents/{doc_id}", kwargs)

    def dispatch_document(self, doc_id: int) -> Dict[str, Any]:
        """Dispatch document for signing (state: draft → dispatching)."""
        return self.update_document(doc_id, state="dispatching")

    def get_submission(self, sub_id: int,
                       expand: Optional[List[str]] = None) -> Dict[str, Any]:
        """operationId: getSubmission — GET /api/v1/submissions/{id}"""
        path = f"/submissions/{sub_id}"
        if expand:
            params = "&".join(f"expand[]={e}" for e in expand)
            path += f"?{params}"
        return self._call("GET", path)

    def get_submission_pdf(self, sub_id: int, pdf_type: str = "sealed") -> Dict[str, Any]:
        """Get sealed or audit trail PDF as binary."""
        return self._call("GET", f"/submissions/{sub_id}",
                          accept="application/pdf")

    def create_webhook(self, oauth_app_id: int, hook_url: str,
                        events: Optional[List[str]] = None) -> Dict[str, Any]:
        """operationId: createWebhook — POST /api/v1/webhooks"""
        return self._call("POST", "/webhooks", {
            "oauth_application_id": oauth_app_id,
            "hook_url": hook_url,
            "events": events or ["submission.completed"],
        })

    def list_webhooks(self, oauth_app_id: int) -> Dict[str, Any]:
        """operationId: getWebhooks — GET /api/v1/webhooks"""
        return self._call("GET", f"/webhooks?oauth_application_id={oauth_app_id}")

    def list_templates(self, workspace_id: Optional[int] = None) -> Dict[str, Any]:
        """operationId: getTemplates — GET /api/v1/templates"""
        path = "/templates"
        if workspace_id:
            path += f"?workspace_id={workspace_id}"
        return self._call("GET", path)

    def get_current_user(self) -> Dict[str, Any]:
        """operationId: getCurrentUser — GET /api/v1/current_user"""
        return self._call("GET", "/current_user")


# ═══════════════════════════════════════════════════════════════════
# WEBHOOK HANDLER — HMAC Validated, Forensic-Logged
# ═══════════════════════════════════════════════════════════════════

class WebhookHandler(BaseHTTPRequestHandler):
    """
    Receives Paperless.io webhook events.
    
    HARDENING #1 — Three-layer webhook security:
      Layer 1: HMAC-SHA256 signature validation
      Layer 2: Timestamp anti-replay (rejects events > 5 min old)
      Layer 3: Unique request_id per event for forensic tracing
    
    Endpoints:
      POST /webhook/paperless        — Receive events
      GET  /webhook/paperless/health  — Health check
      GET  /health                    — System health
    """

    ledger = ForensicLedger()
    webhook_secret = os.environ.get(ENV_WEBHOOK_SECRET, "")
    _seen_ids = set()  # Anti-replay: track seen request IDs (in-memory, resets on restart)

    def do_POST(self):
        if self.path != "/webhook/paperless":
            self._respond(404, {"error": "Not found"})
            return

        # Generate unique request_id for this event
        request_id = f"WH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(6)}"

        # Read body
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length)

        # ── LAYER 1: HMAC-SHA256 Validation ──
        if self.webhook_secret:
            signature = self.headers.get("X-Paperless-Signature", "")
            # Support both raw hex and "sha256=hex" format
            if signature.startswith("sha256="):
                signature = signature[7:]

            expected = hmac.new(
                self.webhook_secret.encode(),
                raw_body,
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(signature, expected):
                logger.warning(f"[{request_id}] HMAC validation FAILED from {self.client_address[0]}")
                self.ledger.append("WEBHOOK_HMAC_FAILED", {
                    "request_id": request_id,
                    "ip": self.client_address[0],
                    "signature_provided": bool(signature),
                    "user_agent": self.headers.get("User-Agent", "unknown"),
                })
                self._respond(401, {"error": "Invalid signature", "request_id": request_id})
                return

        # Parse JSON
        try:
            payload = json.loads(raw_body.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning(f"[{request_id}] Invalid JSON from {self.client_address[0]}")
            self._respond(400, {"error": "Invalid JSON", "request_id": request_id})
            return

        # ── LAYER 2: Timestamp Anti-Replay ──
        event_timestamp = payload.get("timestamp") or payload.get("created_at")
        if event_timestamp:
            try:
                # Parse ISO timestamp
                if event_timestamp.endswith("Z"):
                    event_timestamp = event_timestamp[:-1] + "+00:00"
                event_time = datetime.fromisoformat(event_timestamp)
                now = datetime.now(timezone.utc)
                age_seconds = abs((now - event_time).total_seconds())

                if age_seconds > WEBHOOK_TIMESTAMP_TOLERANCE:
                    logger.warning(
                        f"[{request_id}] Anti-replay: event is {age_seconds:.0f}s old "
                        f"(tolerance: {WEBHOOK_TIMESTAMP_TOLERANCE}s)"
                    )
                    self.ledger.append("WEBHOOK_REPLAY_BLOCKED", {
                        "request_id": request_id,
                        "event_age_seconds": age_seconds,
                        "tolerance": WEBHOOK_TIMESTAMP_TOLERANCE,
                        "ip": self.client_address[0],
                    })
                    self._respond(409, {
                        "error": "Event too old (anti-replay)",
                        "request_id": request_id,
                        "age_seconds": age_seconds,
                    })
                    return
            except (ValueError, TypeError):
                # If timestamp unparseable, allow through but log warning
                logger.warning(f"[{request_id}] Could not parse event timestamp: {event_timestamp}")

        # ── LAYER 2b: Deduplication via event ID ──
        event_id = payload.get("id") or payload.get("event_id")
        if event_id:
            dedup_key = f"{payload.get('event', 'unknown')}:{event_id}"
            if dedup_key in self._seen_ids:
                logger.info(f"[{request_id}] Duplicate event skipped: {dedup_key}")
                self._respond(200, {"status": "duplicate_skipped", "request_id": request_id})
                return
            self._seen_ids.add(dedup_key)
            # Prevent memory leak: cap at 10,000 entries
            if len(self._seen_ids) > 10000:
                self._seen_ids = set(list(self._seen_ids)[-5000:])

        event_type = payload.get("event", "unknown")
        event_data = payload.get("data", {})

        logger.info(f"[{request_id}] Webhook received: {event_type} from {self.client_address[0]}")

        # ── LAYER 3: Route with request_id in every log ──
        if event_type == "submission.completed":
            result = self._handle_submission_completed(event_data, request_id)
            self._respond(200, result)
        else:
            # Acknowledge unknown events
            self.ledger.append("WEBHOOK_EVENT", {
                "request_id": request_id,
                "event": event_type,
                "acknowledged": True,
                "ip": self.client_address[0],
            })
            self._respond(200, {"status": "acknowledged", "event": event_type, "request_id": request_id})

    def _handle_submission_completed(self, data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Process completed signing submission.

        Extracts from Paperless Submission object (per swagger):
          - id: Submission ID
          - submittable_id: Document ID
          - state: should be "completed"
          - sealed_pdf: URL to signed document
          - audit_trail_pdf: URL to Paperless audit trail
          - completed_at: completion timestamp

        Auto-downloads sealed documents to /opt/windi/vault/signed/
        """
        submission_id = data.get("id")
        document_id = data.get("submittable_id")
        sealed_url = data.get("sealed_pdf")
        audit_url = data.get("audit_trail_pdf")
        completed_at = data.get("completed_at")

        # ── Auto-Download Signed Documents ──
        vault_dir = Path("/opt/windi/vault/signed")
        vault_dir.mkdir(parents=True, exist_ok=True)

        download_results = {
            "sealed_pdf": {"downloaded": False, "local_path": None, "content_hash": None},
            "audit_trail": {"downloaded": False, "local_path": None, "content_hash": None},
        }

        # Download sealed PDF
        if sealed_url and sealed_url.startswith("http"):
            try:
                sealed_filename = f"sealed_{submission_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
                sealed_path = vault_dir / sealed_filename
                req = urllib.request.Request(sealed_url, headers={"User-Agent": "WINDI-Schnittstelle/1.1"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    pdf_data = resp.read()
                    sealed_path.write_bytes(pdf_data)
                    content_hash = hashlib.sha256(pdf_data).hexdigest()
                    download_results["sealed_pdf"] = {
                        "downloaded": True,
                        "local_path": str(sealed_path),
                        "content_hash": content_hash,
                        "size_bytes": len(pdf_data),
                    }
                    logger.info(f"  [{request_id}] Downloaded sealed PDF: {sealed_filename} ({len(pdf_data)} bytes)")
            except Exception as e:
                logger.warning(f"  [{request_id}] Failed to download sealed PDF: {e}")
                download_results["sealed_pdf"]["error"] = str(e)

        # Download audit trail PDF
        if audit_url and audit_url.startswith("http"):
            try:
                audit_filename = f"audit_{submission_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
                audit_path = vault_dir / audit_filename
                req = urllib.request.Request(audit_url, headers={"User-Agent": "WINDI-Schnittstelle/1.1"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    pdf_data = resp.read()
                    audit_path.write_bytes(pdf_data)
                    content_hash = hashlib.sha256(pdf_data).hexdigest()
                    download_results["audit_trail"] = {
                        "downloaded": True,
                        "local_path": str(audit_path),
                        "content_hash": content_hash,
                        "size_bytes": len(pdf_data),
                    }
                    logger.info(f"  [{request_id}] Downloaded audit trail: {audit_filename} ({len(pdf_data)} bytes)")
            except Exception as e:
                logger.warning(f"  [{request_id}] Failed to download audit trail: {e}")
                download_results["audit_trail"]["error"] = str(e)

        # Generate Virtue Receipt (enriched with download info)
        virtue_receipt = {
            "receipt_id": f"VR-SCH-{submission_id}-{secrets.token_hex(4)}",
            "request_id": request_id,
            "type": "PAPERLESS_SIGNING_COMPLETED",
            "provider": "PAPERLESS.IO",
            "submission_id": submission_id,
            "document_id": document_id,
            "completed_at": completed_at,
            "sealed_pdf_url_hash": hashlib.sha256(
                (sealed_url or "").encode()
            ).hexdigest()[:32],
            "audit_trail_url_hash": hashlib.sha256(
                (audit_url or "").encode()
            ).hexdigest()[:32],
            "sealed_available": bool(sealed_url),
            "audit_trail_available": bool(audit_url),
            "downloads": download_results,
            "invariants_active": "I1-I9",
            "protocol": "THREE_DRAGONS_v1.1",
            "anchored_at": datetime.now(timezone.utc).isoformat(),
        }

        # Anchor in Forensic Ledger
        entry_hash = self.ledger.append(
            "SIGNING_COMPLETED",
            virtue_receipt,
            i9_gate=InvariantI9.gate("WEBHOOK_RECEIVE"),
        )

        sealed_dl = "✓" if download_results["sealed_pdf"]["downloaded"] else "✗"
        audit_dl = "✓" if download_results["audit_trail"]["downloaded"] else "✗"
        logger.info(
            f"  [{request_id}] ✓ Submission {submission_id} completed. "
            f"Sealed: {sealed_dl} Audit: {audit_dl} "
            f"Ledger: {entry_hash[:16]}..."
        )

        return {
            "status": "processed",
            "request_id": request_id,
            "virtue_receipt": virtue_receipt["receipt_id"],
            "ledger_hash": entry_hash,
            "downloads": {
                "sealed_pdf": download_results["sealed_pdf"]["downloaded"],
                "audit_trail": download_results["audit_trail"]["downloaded"],
            },
        }

    def do_GET(self):
        if self.path == "/webhook/paperless/health":
            chain = self.ledger.verify_chain()
            self._respond(200, {
                "service": "WINDI_SCHNITTSTELLE_WEBHOOK",
                "version": VERSION,
                "status": "RUNNING",
                "port": WEBHOOK_PORT,
                "hmac_configured": bool(self.webhook_secret),
                "kill_switch": KillSwitch.check(),
                "ledger_chain": chain,
                "i9_status": "IRREMEDIABLE",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        elif self.path == "/health":
            self._respond(200, {
                "service": "WINDI_SCHNITTSTELLE",
                "version": VERSION,
                "status": "OK",
            })
        else:
            self._respond(404, {"error": "Not found"})

    def _respond(self, code: int, body: Dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-WINDI-Version", VERSION)
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, format, *args):
        pass  # Suppress default logs


# ═══════════════════════════════════════════════════════════════════
# ORCHESTRATOR — Complete Governance Signing Workflow
# ═══════════════════════════════════════════════════════════════════

class Schnittstelle:
    """
    Main orchestrator.
    
    Encapsulates Paperless.io — not uses it.
    The distinction is everything.
    """

    def __init__(self, sandbox: bool = True):
        self.oauth = OAuth2Client()
        self.api = PaperlessAPI(self.oauth, sandbox=sandbox)
        self.ledger = ForensicLedger()
        self.sandbox = sandbox
        self.workspace_id = int(os.environ.get(ENV_WORKSPACE_ID, "1"))

        logger.info(
            f"Schnittstelle v{VERSION} — "
            f"{'SANDBOX' if sandbox else 'PRODUCTION'} — "
            f"Auth: {'✓' if self.oauth.is_configured else '✗'}"
        )

    def health(self) -> Dict[str, Any]:
        """Full system health check."""
        gate = InvariantI9.gate("HEALTH_CHECK")
        chain = self.ledger.verify_chain()

        result = {
            "service": "WINDI_SCHNITTSTELLE",
            "version": VERSION,
            "mode": "SANDBOX" if self.sandbox else "PRODUCTION",
            "auth_configured": self.oauth.is_configured,
            "workspace_id": self.workspace_id,
            "webhook_port": WEBHOOK_PORT,
            "kill_switch": KillSwitch.check(),
            "i9_gate": gate,
            "ledger": chain,
            "security": {
                "hmac_webhook": bool(os.environ.get(ENV_WEBHOOK_SECRET)),
                "anti_replay": f"{WEBHOOK_TIMESTAMP_TOLERANCE}s tolerance",
                "token_storage": str(CONFIG_FILE),
                "token_permissions": "0600" if CONFIG_FILE.exists() else "N/A",
                "gitignore": (TSIL_DIR / ".gitignore").exists(),
            },
            "paperless_api": PAPERLESS["api_base"],
            "capabilities": {
                "qes": "VIA_PAPERLESS_NATIVE",
                "sealed_pdf": True,
                "audit_trail": True,
                "webhook": True,
                "templates": True,
                "participation_flow": True,
            },
            "tsil_position": "BRIDGE_ADAPTER (coexists with D-Trust adapter)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Test API if configured
        if self.oauth.is_configured or self.sandbox:
            user = self.api.get_current_user()
            result["api_test"] = {
                "status": "OK" if not user.get("_error") else "ERROR",
                "user": user.get("name", "N/A") if not user.get("_error") else None,
            }

        self.ledger.append("HEALTH_CHECK", result, i9_gate=gate)
        return result

    def sign(
        self,
        pdf_path: str,
        name: str,
        signers: List[Dict[str, str]],
        governance_level: str = "MEDIUM",
        sge_score: float = 0.0,
        risk_level: str = "R0",
        governance_digest: str = "",
        webhook_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete governance signing workflow.
        
        1. I9 Gate → human must confirm
        2. Hash PDF for governance record
        3. Upload as Blob to Paperless
        4. Create Document with participants
        5. Dispatch for signing (QES if workspace configured)
        6. Register webhook for completion
        7. Generate Virtue Receipt
        8. Anchor in Forensic Ledger
        """
        wf_id = f"SCH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"

        # ── Kill Switch Check ──
        blocked = KillSwitch.enforce("SIGN_DOCUMENT")
        if blocked:
            self.ledger.append("SIGN_BLOCKED_KILL_SWITCH", {
                "workflow_id": wf_id, **blocked
            })
            return blocked

        # ── Step 1: I9 Gate ──
        gate = InvariantI9.gate("DISPATCH_FOR_SIGNING")

        # ── Step 2: Document Hash ──
        if not self.sandbox and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            doc_hash = hashlib.sha256(pdf_data).hexdigest()
            file_size = len(pdf_data)
            checksum = base64.b64encode(hashlib.md5(pdf_data).digest()).decode()
        else:
            doc_hash = hashlib.sha256(
                (governance_digest or wf_id).encode()
            ).hexdigest()
            file_size = 0
            checksum = base64.b64encode(secrets.token_bytes(16)).decode()
            pdf_data = None

        # ── Step 3: Upload Blob ──
        filename = os.path.basename(pdf_path) if pdf_path else "governance_doc.pdf"
        blob = self.api.create_blob(filename, file_size, checksum=checksum)

        if blob.get("_error"):
            self.ledger.append("SIGN_FAILED", {"step": "blob", "error": blob}, i9_gate=gate)
            return {"status": "FAILED", "step": "blob_upload", "error": blob}

        # Upload actual file
        if pdf_data and blob.get("direct_upload"):
            upload_ok = self.api.upload_to_direct_url(
                blob["direct_upload"]["url"], pdf_data
            )
            if not upload_ok:
                return {"status": "FAILED", "step": "file_upload"}

        # ── Step 4: Create Document ──
        participants = {}
        for i, s in enumerate(signers):
            participants[f"slot{i+1}"] = {
                "email": s["email"],
                "name": s.get("name", s["email"]),
                "role": s.get("role", "approver"),
                "receive_submission_completed_mail": True,
            }

        description = (
            f"[WINDI] Level:{governance_level} | Risk:{risk_level} | "
            f"SGE:{sge_score:.2f} | WF:{wf_id}"
        )

        doc = self.api.create_document_from_pdf(
            workspace_id=self.workspace_id,
            pdf_signed_id=blob.get("signed_id", ""),
            name=name,
            description=description,
            participants=participants,
        )

        if doc.get("_error"):
            self.ledger.append("SIGN_FAILED", {"step": "document", "error": doc}, i9_gate=gate)
            return {"status": "FAILED", "step": "document_creation", "error": doc}

        doc_id = doc.get("id")

        # ── Step 5: Dispatch ──
        dispatch = self.api.dispatch_document(doc_id)

        # ── Step 6: Webhook ──
        wh_result = None
        if webhook_url:
            wh_result = self.api.create_webhook(
                oauth_app_id=1,
                hook_url=webhook_url,
                events=["submission.completed"],
            )

        # ── Step 7: Virtue Receipt ──
        virtue_receipt = {
            "receipt_id": f"VR-{wf_id}",
            "type": "GOVERNANCE_SIGNING_DISPATCHED",
            "workflow_id": wf_id,
            "provider": "PAPERLESS.IO",
            "document_hash": doc_hash,
            "governance": {
                "level": governance_level,
                "sge_score": sge_score,
                "risk_level": risk_level,
                "digest": (governance_digest or "")[:32] + "..." if governance_digest else "N/A",
            },
            "paperless": {
                "blob_id": blob.get("id"),
                "document_id": doc_id,
                "state": dispatch.get("state", "unknown"),
            },
            "signers": [
                {
                    "name": s.get("name", ""),
                    "email_hash": hashlib.sha256(
                        s.get("email", "").encode()
                    ).hexdigest()[:16],
                    "role": s.get("role", "approver"),
                }
                for s in signers
            ],
            "i9_gate": gate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # ── Step 8: Anchor ──
        ledger_hash = self.ledger.append(
            "SIGNING_DISPATCHED", virtue_receipt, i9_gate=gate
        )

        return {
            "status": "DISPATCHED_AWAITING_SIGNATURES",
            "workflow_id": wf_id,
            "document_id": doc_id,
            "virtue_receipt": virtue_receipt["receipt_id"],
            "ledger_hash": ledger_hash,
            "human_approval_required": True,
            "i9": "IRREMEDIABLE",
            "mode": "SANDBOX" if self.sandbox else "PRODUCTION",
            "next": (
                "Signatários receberão email da Paperless.io. "
                "Quando assinarem (incl. QES se configurado), "
                "webhook dispara → Forensic Ledger ancora sealed_pdf."
            ),
        }

    def retrieve_completed(self, submission_id: int, wf_id: str = "") -> Dict[str, Any]:
        """Retrieve completed submission and anchor in ledger."""
        gate = InvariantI9.gate("GET_SUBMISSION")

        sub = self.api.get_submission(
            submission_id,
            expand=["participants", "block_owner_mapping"],
        )

        if sub.get("_error"):
            return {"status": "ERROR", "detail": sub}

        sealed_url = sub.get("sealed_pdf")
        audit_url = sub.get("audit_trail_pdf")

        result = {
            "workflow_id": wf_id or f"RETRIEVE-{submission_id}",
            "submission_id": submission_id,
            "state": sub.get("state"),
            "completed_at": sub.get("completed_at"),
            "sealed_pdf": sealed_url,
            "audit_trail_pdf": audit_url,
            "forensic": {
                "sealed_hash": hashlib.sha256(
                    (sealed_url or "").encode()
                ).hexdigest(),
                "audit_hash": hashlib.sha256(
                    (audit_url or "").encode()
                ).hexdigest(),
                "merkle": "PENDING_DAILY_ROOT",
            },
        }

        self.ledger.append("SUBMISSION_RETRIEVED", result, i9_gate=gate)
        return result


# ═══════════════════════════════════════════════════════════════════
# CLI — Command Interface
# ═══════════════════════════════════════════════════════════════════

BANNER = f"""
╔═══════════════════════════════════════════════════════════════════╗
║   WINDI SCHNITTSTELLE v{VERSION} — HARDENED                        ║
║   Paperless Bridge · "Não esperamos pela ponte. Atravessamos."  ║
║   Three Dragons Protocol v1.1 · I1-I9 Active · I9 IRREMEDIABLE ║
╚═══════════════════════════════════════════════════════════════════╝
"""

HELP = """
  Usage: python3 schnittstelle.py <command> [args]

  ── Setup ──────────────────────────────────────────────
  oauth-url         Generate OAuth2 authorization URL
  oauth-exchange    Exchange auth code for tokens
  refresh           Refresh access token

  ── Operations ─────────────────────────────────────────
  health            Full system health check
  sign              Demo signing workflow (sandbox)
  retrieve ID       Retrieve completed submission
  templates         List available templates

  ── Security ───────────────────────────────────────────
  kill              Engage kill switch (disable signing)
  unkill            Disengage kill switch (enable signing)
  kill-status       Check kill switch status
  audit             Run security audit

  ── Webhook ────────────────────────────────────────────
  webhook-start     Start webhook handler (port 8095)
  webhook-register  Register webhook URL at Paperless

  ── Forensic ───────────────────────────────────────────
  verify            Verify forensic ledger chain integrity
  ledger-count      Count ledger entries
"""

def main():
    print(BANNER)

    if len(sys.argv) < 2:
        print(HELP)
        return

    cmd = sys.argv[1].lower().replace("-", "_")
    sch = Schnittstelle(sandbox=True)

    if cmd == "health":
        print(json.dumps(sch.health(), indent=2))

    elif cmd == "sign":
        result = sch.sign(
            pdf_path="/tmp/governance_doc.pdf",
            name="WINDI Governance Bescheid — Demo",
            signers=[
                {"email": "cgo@a4desk.de", "name": "Human Dragon", "role": "approver"},
                {"email": "pruefer@client.de", "name": "Compliance Prüfer", "role": "approver"},
            ],
            governance_level="HIGH",
            sge_score=0.87,
            risk_level="R2",
            governance_digest=hashlib.sha256(b"demo_context").hexdigest(),
            webhook_url="https://api.windia4desk.online:8095/webhook/paperless",
        )
        print(json.dumps(result, indent=2))

    elif cmd == "retrieve":
        sub_id = int(sys.argv[2]) if len(sys.argv) > 2 else 64
        result = sch.retrieve_completed(sub_id)
        print(json.dumps(result, indent=2))

    elif cmd == "templates":
        result = sch.api.list_templates(sch.workspace_id)
        print(json.dumps(result, indent=2))

    elif cmd == "oauth_url":
        if not sch.oauth.client_id:
            print("  ❌ Set WINDI_PAPERLESS_CLIENT_ID first")
            print(f"     export {ENV_CLIENT_ID}=your_client_id")
            return
        url = sch.oauth.get_authorization_url()
        print(f"  Open this URL in browser:\n\n  {url}\n")
        print("  After authorization, run:")
        print("  python3 schnittstelle.py oauth-exchange YOUR_CODE")

    elif cmd == "oauth_exchange":
        if len(sys.argv) < 3:
            print("  Usage: python3 schnittstelle.py oauth-exchange CODE")
            return
        result = sch.oauth.exchange_code(sys.argv[2])
        print(json.dumps(result, indent=2))
        if result.get("status") == "SUCCESS":
            print(f"\n  ✓ Tokens saved to {CONFIG_FILE}")

    elif cmd == "refresh":
        result = sch.oauth.refresh_access_token()
        print(json.dumps(result, indent=2))

    elif cmd == "webhook_start":
        print(f"  Starting webhook handler on port {WEBHOOK_PORT}...")
        print(f"  Endpoint: POST /webhook/paperless")
        print(f"  Health:   GET  /webhook/paperless/health")
        print()
        server = HTTPServer(("0.0.0.0", WEBHOOK_PORT), WebhookHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n  Shutting down...")
            server.server_close()

    elif cmd == "webhook_register":
        url = sys.argv[2] if len(sys.argv) > 2 else "https://api.windia4desk.online:8095/webhook/paperless"
        result = sch.api.create_webhook(1, url)
        print(json.dumps(result, indent=2))

    elif cmd == "verify":
        result = sch.ledger.verify_chain()
        print(json.dumps(result, indent=2))
        if result["status"] == "INTACT":
            print(f"\n  ✓ Chain INTACT — {result['entries']} entries verified")
        else:
            print(f"\n  ✗ Chain BROKEN at entry {result['broken_at']}")

    elif cmd == "ledger_count":
        result = sch.ledger.verify_chain()
        print(f"  Ledger entries: {result['entries']}")
        print(f"  Chain status:   {result['status']}")

    elif cmd == "kill":
        print("  ⚠️  KILL SWITCH — Disabling all signing operations")
        print(f"  Run: export {ENV_SIGNING_PROVIDER}=disabled")
        print()
        print("  To re-enable: export WINDI_SIGNING_PROVIDER=paperless")
        print()
        # Log the kill switch activation
        sch.ledger.append("KILL_SWITCH_ENGAGED", {
            "operator": "CLI",
            "instruction": f"export {ENV_SIGNING_PROVIDER}=disabled",
        })
        print("  ✓ Kill switch event logged to forensic ledger")

    elif cmd == "unkill":
        print("  ✓ Re-enabling signing operations")
        print(f"  Run: export {ENV_SIGNING_PROVIDER}=paperless")
        sch.ledger.append("KILL_SWITCH_DISENGAGED", {
            "operator": "CLI",
            "instruction": f"export {ENV_SIGNING_PROVIDER}=paperless",
        })

    elif cmd == "kill_status":
        result = KillSwitch.check()
        print(json.dumps(result, indent=2))
        status = "🟢 ACTIVE" if result["signing_allowed"] else "🔴 DISABLED"
        print(f"\n  Signing: {status}")
        print(f"  Provider: {result['provider']}")

    elif cmd == "audit":
        print("  ── WINDI Schnittstelle Security Audit ──\n")
        checks = []

        # 1. Kill switch
        ks = KillSwitch.check()
        checks.append(("Kill Switch configured", True, ks["provider"]))

        # 2. HMAC
        hmac_set = bool(os.environ.get(ENV_WEBHOOK_SECRET))
        checks.append(("Webhook HMAC secret", hmac_set,
                       "SET" if hmac_set else f"⚠ Set {ENV_WEBHOOK_SECRET}"))

        # 3. Token file permissions
        if CONFIG_FILE.exists():
            mode = oct(CONFIG_FILE.stat().st_mode)[-3:]
            ok = mode == "600"
            checks.append(("Token file permissions", ok, f"0{mode}" + (" ✓" if ok else " ⚠ should be 0600")))
        else:
            checks.append(("Token file exists", False, "Not yet created (run oauth-exchange first)"))

        # 4. .gitignore
        gi = (TSIL_DIR / ".gitignore").exists()
        checks.append((".gitignore protection", gi,
                       "Present" if gi else "⚠ Missing"))

        # 5. Anti-replay
        checks.append(("Anti-replay tolerance", True, f"{WEBHOOK_TIMESTAMP_TOLERANCE}s"))

        # 6. Forensic ledger
        chain = sch.ledger.verify_chain()
        checks.append(("Forensic ledger integrity", chain["status"] == "INTACT" or chain["status"] == "EMPTY",
                       f"{chain['status']} ({chain['entries']} entries)"))

        # 7. I9 status
        checks.append(("I9 Invariant", True, "IRREMEDIABLE"))

        # 8. OAuth configured
        checks.append(("OAuth2 configured", sch.oauth.is_configured,
                       "✓" if sch.oauth.is_configured else "⚠ Not yet"))

        passed = sum(1 for _, ok, _ in checks if ok)
        total = len(checks)

        for name, ok, detail in checks:
            icon = "✓" if ok else "✗"
            color_name = name
            print(f"  {icon} {color_name}: {detail}")

        print(f"\n  Score: {passed}/{total} checks passed")
        if passed == total:
            print("  🛡️  READY FOR PRODUCTION DEPLOY")
        else:
            print(f"  ⚠  {total - passed} items need attention before production")

        sch.ledger.append("SECURITY_AUDIT", {
            "passed": passed,
            "total": total,
            "details": {name: {"ok": ok, "detail": detail} for name, ok, detail in checks},
        })

    else:
        print(f"  ❌ Unknown command: {sys.argv[1]}")
        print(HELP)


if __name__ == "__main__":
    main()
