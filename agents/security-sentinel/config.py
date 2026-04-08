"""
W-SEC-001 Security Sentinel — Configuration
Port: 8144
"""

import os

# Service identity
SERVICE_NAME = "w-sec-001"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = int(os.getenv("SEC_PORT", "8144"))

# Correlation settings
CORRELATION_WINDOW_SECONDS = int(os.getenv("SEC_CORRELATION_WINDOW", "300"))  # 5 minutes
MERGE_THRESHOLD = int(os.getenv("SEC_MERGE_THRESHOLD", "5"))
ESCALATION_THRESHOLD = int(os.getenv("SEC_ESCALATION_THRESHOLD", "25"))
CRITICAL_THRESHOLD = int(os.getenv("SEC_CRITICAL_THRESHOLD", "100"))

# External services
LEDGER_URL = os.getenv("LEDGER_URL", "http://127.0.0.1:8101")
MAESTRO_URL = os.getenv("MAESTRO_URL", "http://127.0.0.1:8106")

# Critical endpoints that escalate severity
CRITICAL_ENDPOINTS = {
    "/gateway/call",
    "/auth/login",
    "/session/refresh",
    "/api/receipts",
    "/core/seal",
    "/ledger/anchor",
    "/identity/verify",
}

# Event types that warrant immediate attention
HIGH_PRIORITY_EVENT_TYPES = {
    "token_replay_detected",
    "forbidden_endpoint_access",
    "merkle_integrity_failed",
    "constitutional_violation_attempt",
    "seal_forgery_attempt",
    "ledger_tamper_attempt",
}

# Logging
LOG_DIR = os.getenv("SEC_LOG_DIR", "/opt/windi/logs/security")
