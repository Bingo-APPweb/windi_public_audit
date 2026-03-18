"""
WINDI ID Genesis — Configuration
Three Dragons Protocol v1.1 · I1-I9 Active
"AI processes. Human decides. WINDI guarantees."
"""
import os

# ── Service ──
SERVICE_NAME = "WINDI_ID_GENESIS"
VERSION = "1.0.0"
PORT = 8096
HOST = "0.0.0.0"

# ── Paths ──
BASE_DIR = "/opt/windi/leads"
DB_PATH = os.path.join(BASE_DIR, "leads.db")
LEDGER_PATH = os.path.join(BASE_DIR, "genesis_ledger.jsonl")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# ── Admin ──
ADMIN_EMAIL = os.environ.get("WINDI_ADMIN_EMAIL", "jobernc@gmail.com")
ADMIN_USER = os.environ.get("WINDI_ADMIN_USER")
ADMIN_PASS = os.environ.get("WINDI_ADMIN_PASS")
if not ADMIN_USER or not ADMIN_PASS:
    raise RuntimeError("WINDI_ADMIN_USER/PASS não definidas — verificar .env")


# ── SMTP (pilot: localhost sendmail or external) ──
SMTP_HOST = os.environ.get("WINDI_SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("WINDI_SMTP_PORT", "25"))
SMTP_USER = os.environ.get("WINDI_SMTP_USER", "")
SMTP_PASS = os.environ.get("WINDI_SMTP_PASS", "")
SMTP_FROM = os.environ.get("WINDI_SMTP_FROM", "noreply@a4desk.de")
SMTP_USE_TLS = os.environ.get("WINDI_SMTP_TLS", "false").lower() == "true"

# ── URLs ──
BASE_URL = os.environ.get("WINDI_BASE_URL", "https://admin.windia4desk.tech")
ACTIVATE_URL = f"{BASE_URL}/clone/activate"
ADMIN_URL = f"{BASE_URL}/clone/admin"

# ── Rate Limiting ──
LEAD_RATE_LIMIT = 10  # per hour per IP

# ── CORS ──
CORS_ORIGINS = [
    "https://www.a4desk.de",
    "https://admin.windia4desk.tech",
    "https://a4desk.de",
]

# ── I9: Prohibition of Autonomy Escalation ──
# These flags MUST remain False. Changing them violates I9 (IRREMEDIABLE).
AUTO_APPROVE_LEADS = False  # NEVER set to True
AUTO_GENERATE_KEYS = False  # NEVER without human approval
