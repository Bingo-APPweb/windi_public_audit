# ═══════════════════════════════════════════════
# W-CACHE-001 · CONFIGURATION
# ═══════════════════════════════════════════════

import os

# Database
DATABASE_URL = os.getenv(
    "WCACHE_DATABASE_URL",
    "sqlite:////opt/windi/w-cache-001/data/wcache.db"
)

# Service
SERVICE_PORT = int(os.getenv("WCACHE_PORT", "8160"))
SERVICE_HOST = os.getenv("WCACHE_HOST", "0.0.0.0")

# Ledger integration
LEDGER_URL = os.getenv("LEDGER_URL", "http://localhost:8101")

# Default TTLs (seconds)
DEFAULT_TTL = {
    "L1_EPHEMERAL": 30,
    "L2_DETERMINISTIC": 300,
    "L3_PROVEN": 86400,  # 24h - proven entries live longer
    "L4_POLICY": 60
}

# Metrics
METRICS_ENABLED = os.getenv("WCACHE_METRICS", "true").lower() == "true"
