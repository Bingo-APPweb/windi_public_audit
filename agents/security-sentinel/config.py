"""
W-SEC-001 Security Sentinel — Configuration
Port: 8144
"""

import os

# Service identity
SERVICE_NAME = "w-sec-001"
SERVICE_VERSION = "1.1.0"  # Added Telegram webhooks
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

# ═══════════════════════════════════════════════════════════════════════════════
# WEBHOOKS — Telegram Notification Configuration
# ═══════════════════════════════════════════════════════════════════════════════
#
# Environment variables:
#   SEC_TELEGRAM_ENABLED     - Enable/disable Telegram (default: true)
#   SEC_TELEGRAM_CHAT_ID     - Telegram chat/group ID to send alerts
#   SEC_TELEGRAM_BOT_TOKEN   - Telegram bot token from @BotFather
#
# To configure:
#   1. Create bot via @BotFather on Telegram
#   2. Get the bot token
#   3. Add bot to your security alerts chat/group
#   4. Get chat_id (use @userinfobot or API)
#   5. Export the environment variables before starting the service
#
# Example:
#   export SEC_TELEGRAM_CHAT_ID="-1001234567890"
#   export SEC_TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
#
# Anti-noise features (built-in):
#   - Only high/critical severity incidents trigger notifications
#   - 60-second debounce for same incident
#   - SEALED events always notify (30s debounce)
#
