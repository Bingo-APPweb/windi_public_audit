"""
WINDI Agent Security Middleware
=================================
Authentication, input validation, and rate limiting for the Agent API.

"The Agent that protects governance must itself be governed."
"""

import hashlib
import hmac
import os
import re
import time
from functools import wraps
from typing import Optional


# ═══ TOKEN MANAGEMENT ═══

def generate_agent_token() -> str:
    """Generate a secure random token for Agent API authentication."""
    return hashlib.sha256(os.urandom(64)).hexdigest()


def load_token(token_path: str = None) -> Optional[str]:
    """
    Load the authentication token from file.
    If no file exists, generate and save a new one.
    """
    token_path = token_path or "/opt/windi/agents/constitutional-agent/.agent_token"
    
    try:
        if os.path.exists(token_path):
            with open(token_path, 'r') as f:
                return f.read().strip()
        else:
            token = generate_agent_token()
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, 'w') as f:
                f.write(token)
            os.chmod(token_path, 0o600)  # Owner read/write only
            return token
    except OSError:
        # Fallback for environments where file creation isn't possible
        return os.environ.get("WINDI_AGENT_TOKEN", generate_agent_token())


def verify_token(provided: str, expected: str) -> bool:
    """
    Constant-time token comparison to prevent timing attacks.
    """
    if not provided or not expected:
        return False
    return hmac.compare_digest(provided, expected)


# ═══ INPUT VALIDATION ═══

SHA256_PATTERN = re.compile(r'^[a-fA-F0-9]{64}$')

def validate_document_hash(hash_str: str) -> bool:
    """Validate that a string is a valid SHA-256 hex hash."""
    return bool(SHA256_PATTERN.match(hash_str))


def validate_doc_type(doc_type: str) -> bool:
    """Validate document type against allowed values."""
    allowed = {
        "CONTRACT", "INVOICE", "APPROVAL", "REPORT",
        "POLICY", "AUDIT", "MEMO", "LETTER",
        "REGULATION", "CERTIFICATE", "UNKNOWN",
    }
    return doc_type.upper() in allowed


def validate_request_size(content_length: Optional[int], max_bytes: int = 10 * 1024 * 1024) -> bool:
    """Validate request size doesn't exceed maximum (default 10MB)."""
    if content_length is None:
        return True  # Let other checks handle empty requests
    return content_length <= max_bytes


# ═══ RATE LIMITING (Simple in-memory) ═══

class RateLimiter:
    """
    Simple in-memory rate limiter.
    For production, use nginx rate limiting (see SECURITY.md).
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict = {}  # ip -> list of timestamps
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if client is within rate limits."""
        now = time.time()
        
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Clean old entries
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < self.window_seconds
        ]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        self.requests[client_ip].append(now)
        return True


# ═══ CODE INTEGRITY ═══

def compute_code_hash(agent_dir: str = None) -> str:
    """
    Compute SHA-256 hash of all Agent source files.
    
    This proves which exact code was running when a governance event
    was processed. Essential for audit trail.
    """
    agent_dir = agent_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    hasher = hashlib.sha256()
    
    for root, dirs, files in sorted(os.walk(agent_dir)):
        # Skip __pycache__ and hidden directories
        dirs[:] = [d for d in sorted(dirs) if not d.startswith(('.', '__'))]
        
        for filename in sorted(files):
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'rb') as f:
                        hasher.update(f.read())
                except OSError:
                    continue
    
    return hasher.hexdigest()
