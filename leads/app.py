"""
WINDI ID Genesis — Lead Capture + Identity Provisioning API
Three Dragons Protocol v1.1 · I1-I9 Active

Port 8096 · "Cada lead é uma semente. Cada WINDI ID, um nascimento."

Endpoints:
  POST /api/leads           → Capture new lead (from landing page)
  GET  /health              → Service health
  GET  /admin/leads         → Admin UI (Basic Auth)
  POST /admin/leads/{id}/approve  → Approve lead → Generate WINDI ID
  POST /admin/leads/{id}/reject   → Reject lead
  POST /admin/leads/{id}/revoke   → Revoke (DSGVO Art.17)
  GET  /activate/{token}    → Activation page
  POST /api/activate/{token}→ Complete activation (store public key)
  GET  /admin/ledger        → View forensic ledger
"""
import os
import sys
import uuid
import json
import secrets
import hashlib
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from functools import wraps

# ── Ensure our directory is in path ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import db
import ledger

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/tmp/leads.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("windi-genesis")

# ── Try FastAPI, fallback to built-in HTTP ──
try:
    from fastapi import FastAPI, Request, HTTPException, Depends, Response
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    USE_FASTAPI = True
    log.info("FastAPI + Uvicorn available")
except ImportError:
    USE_FASTAPI = False
    log.info("FastAPI not available, using built-in HTTP server")

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def generate_lead_id() -> str:
    """Generate a unique lead ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    short = uuid.uuid4().hex[:8]
    return f"LEAD-{ts}-{short}"

def generate_windi_id() -> str:
    """Generate a unique WINDI ID (UUID v4 with prefix)."""
    return f"WINDI-{uuid.uuid4().hex}"

def generate_activation_token() -> str:
    """Generate a secure one-time activation token."""
    return secrets.token_urlsafe(48)

def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send email via SMTP. Returns True on success."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = config.SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if config.SMTP_PORT == 465:
            import ssl
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, context=context)
        elif config.SMTP_USE_TLS:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)

        if config.SMTP_USER:
            server.login(config.SMTP_USER, config.SMTP_PASS)

        server.sendmail(config.SMTP_FROM, [to], msg.as_string())
        server.quit()
        log.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        log.warning(f"Email failed to {to}: {e}")
        return False

def notify_admin(lead: dict):
    """Send notification email to admin about new lead."""
    subject = f"🐉 New Lead: {lead.get('name', '?')} ({lead.get('interest', '?')})"
    html = f"""
    <div style="font-family: 'Outfit', sans-serif; background: #0a0a0a; color: #e8e6e3; padding: 30px;">
      <h2 style="color: #c8a438;">🐉 WINDI Lead Capture</h2>
      <table style="color: #e8e6e3; border-collapse: collapse;">
        <tr><td style="padding: 8px; color: #888;">Lead ID:</td>
            <td style="padding: 8px;"><strong>{lead.get('lead_id', '')}</strong></td></tr>
        <tr><td style="padding: 8px; color: #888;">Name:</td>
            <td style="padding: 8px;">{lead.get('name', '')}</td></tr>
        <tr><td style="padding: 8px; color: #888;">Email:</td>
            <td style="padding: 8px;">{lead.get('email', '')}</td></tr>
        <tr><td style="padding: 8px; color: #888;">Company:</td>
            <td style="padding: 8px;">{lead.get('company', '-')}</td></tr>
        <tr><td style="padding: 8px; color: #888;">Interest:</td>
            <td style="padding: 8px;">{lead.get('interest', '')}</td></tr>
        <tr><td style="padding: 8px; color: #888;">Source:</td>
            <td style="padding: 8px;">{lead.get('source', '')}</td></tr>
        <tr><td style="padding: 8px; color: #888;">Time:</td>
            <td style="padding: 8px;">{lead.get('created_at', '')}</td></tr>
      </table>
      <br>
      <a href="{config.ADMIN_URL}/leads" 
         style="background: #c8a438; color: #0a0a0a; padding: 12px 24px; 
                text-decoration: none; font-weight: 700; border-radius: 4px;">
        Review & Approve →
      </a>
      <p style="color: #555; margin-top: 20px; font-size: 12px;">
        Three Dragons Protocol v1.1 · I9: No auto-approval permitted.
      </p>
    </div>
    """
    send_email(config.ADMIN_EMAIL, subject, html)

def send_activation_email(lead: dict):
    """Send activation email to the approved lead."""
    token = lead.get("activation_token", "")
    activate_link = f"{config.ACTIVATE_URL}/{token}"
    windi_id = lead.get("windi_id", "")

    subject = "🐉 Your WINDI ID is ready — Activate now"
    html = f"""
    <div style="font-family: 'Outfit', sans-serif; background: #0a0a0a; color: #e8e6e3; padding: 30px; max-width: 600px;">
      <h2 style="color: #c8a438;">🐉 Welcome to WINDI</h2>
      <p>Your governance identity has been approved.</p>
      
      <div style="background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 20px; margin: 20px 0;">
        <p style="color: #888; margin: 0;">Your WINDI ID:</p>
        <p style="color: #c8a438; font-family: 'JetBrains Mono', monospace; font-size: 14px; word-break: break-all;">
          {windi_id}
        </p>
      </div>
      
      <p>Click below to activate your identity. During activation, a cryptographic key pair 
         will be generated in your browser — your private key never leaves your device.</p>
      
      <a href="{activate_link}" 
         style="display: inline-block; background: #c8a438; color: #0a0a0a; padding: 14px 28px; 
                text-decoration: none; font-weight: 700; border-radius: 4px; margin: 16px 0;">
        Activate Your WINDI ID →
      </a>
      
      <p style="color: #888; font-size: 13px; margin-top: 20px;">
        This link is valid once. After activation, every document you analyze, 
        sign, or approve will be cryptographically linked to your WINDI ID.
      </p>
      
      <hr style="border-color: #333; margin: 24px 0;">
      <p style="color: #555; font-size: 11px;">
        AI processes. Human decides. WINDI guarantees.<br>
        WINDI Publishing House · Kempten (Allgäu) · Germany
      </p>
    </div>
    """
    send_email(lead.get("email", ""), subject, html)


# ═══════════════════════════════════════════════════════════════
# ADMIN HTML TEMPLATE
# ═══════════════════════════════════════════════════════════════

def render_admin_html(leads_list: list, stats: dict, ledger_info: dict) -> str:
    """Render the admin dashboard HTML."""
    status_colors = {
        "PENDING": "#f0a030",
        "APPROVED": "#3090f0",
        "ACTIVE": "#30c060",
        "REJECTED": "#888",
        "REVOKED": "#c03030",
    }

    rows = ""
    for lead in leads_list:
        status = lead.get("status", "PENDING")
        color = status_colors.get(status, "#888")
        actions = ""
        if status == "PENDING":
            actions = f"""
                <form method="POST" action="/clone/admin/leads/{lead['lead_id']}/approve" style="display:inline;">
                    <button type="submit" style="background:#c8a438;color:#0a0a0a;border:none;padding:6px 16px;
                            cursor:pointer;font-weight:700;border-radius:4px;">APPROVE</button>
                </form>
                <form method="POST" action="/clone/admin/leads/{lead['lead_id']}/reject" style="display:inline;margin-left:8px;">
                    <button type="submit" style="background:#333;color:#888;border:1px solid #555;padding:6px 16px;
                            cursor:pointer;border-radius:4px;">Reject</button>
                </form>
            """
        elif status == "ACTIVE":
            actions = f"""
                <form method="POST" action="/clone/admin/leads/{lead['lead_id']}/revoke" style="display:inline;"
                      onsubmit="return confirm('DSGVO Art.17: PII will be permanently deleted. Continue?');">
                    <button type="submit" style="background:#1a1a1a;color:#c03030;border:1px solid #c03030;
                            padding:6px 16px;cursor:pointer;border-radius:4px;">Revoke</button>
                </form>
            """

        windi_id = lead.get("windi_id") or ""
        windi_display = f"<code style='color:#c8a438;font-size:11px;'>{windi_id[:20]}...</code>" if windi_id else "-"

        rows += f"""
        <tr style="border-bottom:1px solid #222;">
            <td style="padding:12px 8px;color:#888;font-size:12px;">{lead.get('lead_id','')[:20]}</td>
            <td style="padding:12px 8px;">{lead.get('name','[revoked]') or '[revoked]'}</td>
            <td style="padding:12px 8px;color:#aaa;">{lead.get('email','[revoked]') or '[revoked]'}</td>
            <td style="padding:12px 8px;color:#888;">{lead.get('company','') or '-'}</td>
            <td style="padding:12px 8px;color:#888;">{lead.get('interest','')}</td>
            <td style="padding:12px 8px;">
                <span style="color:{color};font-weight:700;background:{color}22;padding:3px 10px;
                             border-radius:12px;font-size:12px;">{status}</span>
            </td>
            <td style="padding:12px 8px;">{windi_display}</td>
            <td style="padding:12px 8px;color:#888;font-size:11px;">{(lead.get('created_at',''))[:16]}</td>
            <td style="padding:12px 8px;">{actions}</td>
        </tr>
        """

    stats_html = " · ".join(
        f"<span style='color:{status_colors.get(k,'#888')}'>{k}: {v}</span>"
        for k, v in stats.items() if k != "total"
    )

    chain_status = "✅ INTACT" if ledger_info.get("valid") else "❌ BROKEN"
    chain_color = "#30c060" if ledger_info.get("valid") else "#c03030"

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WINDI Lead Admin · Three Dragons</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:#0a0a0a; color:#e8e6e3; font-family:'Outfit',sans-serif; padding:24px; }}
        h1 {{ color:#c8a438; font-size:24px; margin-bottom:4px; }}
        .subtitle {{ color:#888; font-size:14px; margin-bottom:24px; }}
        .stats {{ margin-bottom:20px; font-size:14px; }}
        .chain {{ font-size:13px; margin-bottom:24px; color:{chain_color}; font-family:'JetBrains Mono',monospace; }}
        table {{ width:100%; border-collapse:collapse; }}
        th {{ text-align:left; padding:12px 8px; color:#c8a438; font-size:12px; text-transform:uppercase;
              letter-spacing:1px; border-bottom:2px solid #c8a438; }}
        tr:hover {{ background:#111; }}
        .footer {{ margin-top:32px; color:#444; font-size:11px; text-align:center; }}
        a {{ color:#c8a438; }}
    </style>
</head>
<body>
    <h1>🐉 WINDI Lead Admin</h1>
    <div class="subtitle">Three Dragons Protocol v1.1 · I9: Human Approval Required</div>
    
    <div class="stats">
        Total: <strong>{stats.get('total', 0)}</strong> · {stats_html}
    </div>
    <div class="chain">
        Forensic Ledger: {chain_status} · {ledger_info.get('entries', 0)} entries · 
        <a href="/clone/admin/ledger" style="color:#888;">View Ledger →</a>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Lead ID</th><th>Name</th><th>Email</th><th>Company</th>
                <th>Interest</th><th>Status</th><th>WINDI ID</th>
                <th>Created</th><th>Actions</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    
    <div class="footer">
        WINDI ID Genesis v{config.VERSION} · AI processes. Human decides. WINDI guarantees.
    </div>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
# ACTIVATION PAGE TEMPLATE
# ═══════════════════════════════════════════════════════════════

def render_activation_html(lead: dict) -> str:
    """Render the activation page with WebCrypto key generation."""
    windi_id = lead.get("windi_id", "")
    token = lead.get("activation_token", "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Activate Your WINDI ID</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:#0a0a0a; color:#e8e6e3; font-family:'Outfit',sans-serif; 
               display:flex; justify-content:center; align-items:center; min-height:100vh; padding:24px; }}
        .card {{ background:#111; border:1px solid #222; border-radius:16px; padding:40px; max-width:520px; width:100%; }}
        h1 {{ color:#c8a438; font-size:22px; margin-bottom:8px; }}
        .windi-id {{ background:#0a0a0a; border:1px solid #333; border-radius:8px; padding:16px; margin:20px 0;
                     font-family:'JetBrains Mono',monospace; font-size:13px; color:#c8a438; word-break:break-all; }}
        .step {{ margin:20px 0; padding:16px; background:#1a1a1a; border-radius:8px; }}
        .step-num {{ color:#c8a438; font-weight:700; }}
        .btn {{ background:#c8a438; color:#0a0a0a; border:none; padding:14px 28px; font-size:16px;
                font-weight:700; border-radius:8px; cursor:pointer; width:100%; margin-top:20px;
                font-family:'Outfit',sans-serif; }}
        .btn:hover {{ background:#d4b44a; }}
        .btn:disabled {{ background:#333; color:#666; cursor:not-allowed; }}
        .status {{ margin-top:16px; padding:12px; border-radius:8px; display:none; }}
        .status.success {{ display:block; background:#30c06020; border:1px solid #30c060; color:#30c060; }}
        .status.error {{ display:block; background:#c0303020; border:1px solid #c03030; color:#c03030; }}
        .fingerprint {{ font-family:'JetBrains Mono',monospace; font-size:11px; color:#888; margin-top:8px; word-break:break-all; }}
        .footer {{ margin-top:24px; color:#444; font-size:11px; text-align:center; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🐉 Activate Your WINDI ID</h1>
        <p style="color:#888;">Your governance identity is ready for activation.</p>
        
        <div class="windi-id">{windi_id}</div>
        
        <div class="step">
            <p><span class="step-num">Step 1:</span> Click the button below.</p>
            <p style="color:#888; font-size:13px; margin-top:4px;">
                A cryptographic key pair (Ed25519-equivalent) will be generated 
                <strong>in your browser</strong>. Your private key never leaves your device.
            </p>
        </div>
        
        <div class="step">
            <p><span class="step-num">Step 2:</span> Save your private key securely.</p>
            <p style="color:#888; font-size:13px; margin-top:4px;">
                You will receive a download of your key file. Store it safely — 
                it is your sovereign proof of identity.
            </p>
        </div>
        
        <button class="btn" id="activateBtn" onclick="activateIdentity()">
            🔐 Generate Keys & Activate
        </button>
        
        <div id="statusMsg" class="status"></div>
        <div id="fingerprint" class="fingerprint"></div>
        
        <div class="footer">
            AI processes. Human decides. WINDI guarantees.<br>
            WINDI Publishing House · Kempten (Allgäu)
        </div>
    </div>

    <script>
    async function activateIdentity() {{
        const btn = document.getElementById('activateBtn');
        const status = document.getElementById('statusMsg');
        const fpDiv = document.getElementById('fingerprint');
        btn.disabled = true;
        btn.textContent = '⏳ Generating keys...';

        try {{
            // Generate ECDSA P-256 key pair (WebCrypto standard, closest to Ed25519 in browsers)
            const keyPair = await crypto.subtle.generateKey(
                {{ name: 'ECDSA', namedCurve: 'P-256' }},
                true,  // extractable
                ['sign', 'verify']
            );

            // Export public key as JWK
            const publicKeyJwk = await crypto.subtle.exportKey('jwk', keyPair.publicKey);
            const publicKeyStr = JSON.stringify(publicKeyJwk);

            // Export private key for user to save
            const privateKeyJwk = await crypto.subtle.exportKey('jwk', keyPair.privateKey);

            // Compute fingerprint (SHA-256 of public key)
            const encoder = new TextEncoder();
            const pubKeyData = encoder.encode(publicKeyStr);
            const hashBuffer = await crypto.subtle.digest('SHA-256', pubKeyData);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            const fingerprint = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

            // Send public key to server
            const response = await fetch('/clone/api/activate/{token}', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    public_key: publicKeyStr,
                    key_fingerprint: fingerprint
                }})
            }});

            const data = await response.json();

            if (data.status === 'activated') {{
                // Success — offer private key download
                const blob = new Blob(
                    [JSON.stringify({{
                        windi_id: '{windi_id}',
                        key_type: 'ECDSA-P256',
                        private_key: privateKeyJwk,
                        public_key: publicKeyJwk,
                        fingerprint: fingerprint,
                        activated_at: new Date().toISOString(),
                        warning: 'KEEP THIS FILE SECURE. It is your sovereign proof of identity.'
                    }}, null, 2)],
                    {{ type: 'application/json' }}
                );
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'WINDI_KEY_' + fingerprint.slice(0, 16) + '.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                status.className = 'status success';
                status.innerHTML = '✅ <strong>WINDI ID Activated!</strong><br>Your key file has been downloaded. Store it securely.';
                fpDiv.textContent = 'Fingerprint: ' + fingerprint;
                btn.textContent = '✅ Activated';
            }} else {{
                throw new Error(data.error || 'Activation failed');
            }}
        }} catch (err) {{
            status.className = 'status error';
            status.textContent = '❌ ' + err.message;
            btn.disabled = false;
            btn.textContent = '🔐 Retry Activation';
        }}
    }}
    </script>
</body>
</html>"""


def render_activation_invalid_html() -> str:
    return """<!DOCTYPE html><html><head><meta charset="UTF-8">
    <title>Invalid Token</title>
    <style>body{background:#0a0a0a;color:#e8e6e3;font-family:'Outfit',sans-serif;
    display:flex;justify-content:center;align-items:center;min-height:100vh;}
    .card{background:#111;border:1px solid #c03030;border-radius:16px;padding:40px;
    max-width:400px;text-align:center;}</style></head><body>
    <div class="card"><h2 style="color:#c03030;">Invalid or Expired Token</h2>
    <p style="color:#888;margin-top:12px;">This activation link is no longer valid.
    Contact support if you need assistance.</p></div></body></html>"""


# ═══════════════════════════════════════════════════════════════
# LEDGER VIEW TEMPLATE
# ═══════════════════════════════════════════════════════════════

def render_ledger_html(entries: list, chain_info: dict) -> str:
    chain_status = "✅ CHAIN INTACT" if chain_info.get("valid") else "❌ CHAIN BROKEN"
    chain_color = "#30c060" if chain_info.get("valid") else "#c03030"

    event_colors = {
        "LEAD_RECEIVED": "#f0a030",
        "WINDI_ID_GENESIS": "#c8a438",
        "WINDI_ID_ACTIVATION": "#30c060",
        "WINDI_ID_REVOCATION": "#c03030",
        "SYSTEM": "#3090f0",
    }

    rows = ""
    for e in reversed(entries):
        ec = event_colors.get(e.get("event", ""), "#888")
        rows += f"""<tr style="border-bottom:1px solid #1a1a1a;">
            <td style="padding:8px;color:#555;font-family:'JetBrains Mono',monospace;font-size:11px;">{e.get('seq','')}</td>
            <td style="padding:8px;color:#888;font-size:11px;">{e.get('ts','')[:19]}</td>
            <td style="padding:8px;color:{ec};font-weight:600;font-size:12px;">{e.get('event','')}</td>
            <td style="padding:8px;color:#888;font-family:'JetBrains Mono',monospace;font-size:11px;">{e.get('entity_id','')[:24]}</td>
            <td style="padding:8px;color:#555;font-family:'JetBrains Mono',monospace;font-size:10px;">{e.get('hash','')[:24]}...</td>
        </tr>"""

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <title>WINDI Forensic Ledger</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>*{{margin:0;padding:0;box-sizing:border-box;}}body{{background:#0a0a0a;color:#e8e6e3;font-family:'Outfit',sans-serif;padding:24px;}}
    h1{{color:#c8a438;font-size:22px;margin-bottom:16px;}}
    table{{width:100%;border-collapse:collapse;}}th{{text-align:left;padding:8px;color:#c8a438;font-size:11px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid #c8a438;}}
    .chain{{color:{chain_color};font-family:'JetBrains Mono',monospace;font-size:13px;margin-bottom:20px;}}
    a{{color:#c8a438;}}</style></head><body>
    <h1>🔗 Forensic Ledger</h1>
    <div class="chain">{chain_status} · {chain_info.get('entries',0)} entries</div>
    <p style="margin-bottom:16px;"><a href="/clone/admin/leads">← Back to Leads</a></p>
    <table><thead><tr><th>#</th><th>Timestamp</th><th>Event</th><th>Entity</th><th>Hash</th></tr></thead>
    <tbody>{rows}</tbody></table></body></html>"""


# ═══════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════

if USE_FASTAPI:
    import base64

    app = FastAPI(
        title="WINDI ID Genesis",
        version=config.VERSION,
        docs_url=None,
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Basic Auth helper ──
    def verify_admin(request: Request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Basic "):
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Basic realm=WINDI"})
        try:
            decoded = base64.b64decode(auth[6:]).decode("utf-8")
            user, pwd = decoded.split(":", 1)
            if user == config.ADMIN_USER and pwd == config.ADMIN_PASS:
                return user
        except Exception:
            pass
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Basic realm=WINDI"})

    # ── Health ──
    @app.get("/health")
    async def health():
        stats = db.get_lead_stats()
        chain = ledger.verify_chain()
        return {
            "service": config.SERVICE_NAME,
            "version": config.VERSION,
            "status": "RUNNING",
            "port": config.PORT,
            "leads": stats,
            "ledger": {
                "valid": chain["valid"],
                "entries": chain["entries"],
            },
            "i9_enforced": not config.AUTO_APPROVE_LEADS,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ── Lead Capture (public) ──
    @app.post("/api/leads")
    async def create_lead(request: Request):
        # Rate limiting
        client_ip = request.client.host if request.client else "unknown"
        if not db.check_rate_limit(client_ip, "leads", config.LEAD_RATE_LIMIT):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        name = body.get("name", "").strip()
        email = body.get("email", "").strip()
        if not name or not email:
            raise HTTPException(status_code=400, detail="Name and email are required")

        lead_id = generate_lead_id()
        result = db.create_lead(
            lead_id=lead_id,
            name=name,
            email=email,
            company=body.get("company", ""),
            interest=body.get("interest", "free"),
            source=body.get("source", "landing"),
            lang=body.get("lang", "de"),
            ip_address=client_ip,
        )

        if "error" in result:
            raise HTTPException(status_code=409, detail=result["error"])

        # Forensic ledger entry (NO PII!)
        ledger.append(
            event=ledger.EVENT_LEAD_RECEIVED,
            entity_id=lead_id,
            payload={"interest": body.get("interest", "free"), "source": body.get("source", "landing")},
        )

        # Notify admin
        lead_data = db.get_lead_by_id(lead_id)
        notify_admin(lead_data)

        log.info(f"New lead: {lead_id}")
        return {
            "status": "received",
            "lead_id": lead_id,
            "message": "Thank you! We'll be in touch.",
            "timestamp": result["created_at"],
        }

    # ── G3 Hook: Register Wallet (from wallet_provisioning) ──
    @app.post("/api/leads/register")
    async def register_wallet(request: Request):
        """Called by wallet_provisioning.py G3 hook (fire-and-forget)."""
        try:
            body = await request.json()
        except Exception:
            return {"status": "error", "detail": "Invalid JSON"}

        wallet_id = body.get("wallet_id", "")
        email = body.get("email", "")
        tier = body.get("tier", "PIONEER")
        source = body.get("source", "wallet_provision")

        if not wallet_id:
            return {"status": "error", "detail": "wallet_id required"}

        # Log to forensic ledger (no PII)
        ledger.append(
            event="WALLET_REGISTERED",
            entity_id=wallet_id,
            payload={"tier": tier, "source": source},
        )

        log.info(f"G3 Hook: wallet registered {wallet_id} (tier={tier})")
        return {"status": "registered", "wallet_id": wallet_id}

    # ── Admin: List Leads ──
    @app.get("/admin/leads", response_class=HTMLResponse)
    async def admin_leads(request: Request, user: str = Depends(verify_admin)):
        leads_list = db.get_leads_by_status()
        stats = db.get_lead_stats()
        chain = ledger.verify_chain()
        return render_admin_html(leads_list, stats, chain)

    # ── Admin: Approve Lead (I9-GUARDED) ──
    @app.post("/admin/leads/{lead_id}/approve", response_class=HTMLResponse)
    async def approve_lead(lead_id: str, request: Request, user: str = Depends(verify_admin)):
        # I9 CHECK: This endpoint requires human authentication (Basic Auth)
        assert not config.AUTO_APPROVE_LEADS, "I9 VIOLATION: Auto-approve is forbidden"

        lead = db.get_lead_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        if lead["status"] != "PENDING":
            raise HTTPException(status_code=400, detail=f"Lead is {lead['status']}, not PENDING")

        windi_id = generate_windi_id()
        token = generate_activation_token()

        success = db.approve_lead(lead_id, windi_id, token, approved_by=user)
        if not success:
            raise HTTPException(status_code=500, detail="Approval failed")

        # GENESIS EVENT in forensic ledger
        ledger.append(
            event=ledger.EVENT_GENESIS,
            entity_id=windi_id,
            payload={
                "lead_id": lead_id,
                "approved_by": user,
                "key_type": "non-custodial",
                "i9_human_approval": True,
            },
        )

        # Send activation email
        updated_lead = db.get_lead_by_id(lead_id)
        send_activation_email(updated_lead)

        log.info(f"GENESIS: {windi_id} (lead: {lead_id}, approved by: {user})")

        # ─── WALLET AUTO-PROVISION ──────────────────────────────
        try:
            import requests as _req
            _wallet = _req.post(
                "http://localhost:8099/api/wallet/bridge/approve",
                json={
                    "lead_id": lead_id,
                    "name": lead.get("name", ""),
                    "email": lead.get("email", ""),
                    "company": lead.get("company", "-"),
                    "interest": lead.get("interest", "free"),
                    "approved_by": user,
                },
                timeout=5,
            )
            if _wallet.status_code in (200, 201):
                log.info(f"WALLET: {_wallet.json().get('wallet_id', '?')} provisioned for {lead_id}")
            else:
                log.warning(f"WALLET: provision failed for {lead_id}: {_wallet.status_code}")
        except Exception as _we:
            log.warning(f"WALLET: bridge unreachable for {lead_id}: {_we}")
        # ─── END WALLET ────────────────────────────────────────

        # Redirect back to admin
        return HTMLResponse(
            content=f'<html><head><meta http-equiv="refresh" content="0;url=/clone/admin/leads"></head></html>',
            status_code=303,
        )

    # ── Admin: Reject Lead ──
    @app.post("/admin/leads/{lead_id}/reject", response_class=HTMLResponse)
    async def reject_lead(lead_id: str, request: Request, user: str = Depends(verify_admin)):
        conn = db.get_db()
        conn.execute("UPDATE leads SET status = 'REJECTED' WHERE lead_id = ? AND status = 'PENDING'",
                      (lead_id,))
        conn.commit()
        conn.close()
        log.info(f"Lead rejected: {lead_id}")
        return HTMLResponse(content='<html><head><meta http-equiv="refresh" content="0;url=/clone/admin/leads"></head></html>')

    # ── Admin: Revoke (DSGVO Art.17) ──
    @app.post("/admin/leads/{lead_id}/revoke", response_class=HTMLResponse)
    async def revoke_lead(lead_id: str, request: Request, user: str = Depends(verify_admin)):
        lead = db.get_lead_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        windi_id = lead.get("windi_id", lead_id)
        success = db.revoke_lead(lead_id)
        if success:
            ledger.append(
                event=ledger.EVENT_REVOCATION,
                entity_id=windi_id,
                payload={"lead_id": lead_id, "reason": "DSGVO_ART17", "revoked_by": user},
            )
            log.info(f"REVOKED: {windi_id} (DSGVO Art.17)")

        return HTMLResponse(content='<html><head><meta http-equiv="refresh" content="0;url=/clone/admin/leads"></head></html>')

    # ── Activation Page (public, token-gated) ──
    @app.get("/activate/{token}", response_class=HTMLResponse)
    async def activation_page(token: str):
        lead = db.get_lead_by_token(token)
        if not lead or lead["status"] != "APPROVED":
            return HTMLResponse(content=render_activation_invalid_html(), status_code=404)
        return render_activation_html(lead)

    # ── Activation API (public, token-gated) ──
    @app.post("/api/activate/{token}")
    async def activate(token: str, request: Request):
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        public_key = body.get("public_key", "")
        fingerprint = body.get("key_fingerprint", "")

        if not public_key or not fingerprint:
            raise HTTPException(status_code=400, detail="public_key and key_fingerprint required")

        result = db.activate_lead(token, public_key, fingerprint)
        if not result:
            raise HTTPException(status_code=404, detail="Invalid or already used token")

        windi_id = result.get("windi_id", "")

        # Ledger: activation event
        ledger.append(
            event=ledger.EVENT_ACTIVATION,
            entity_id=windi_id,
            payload={"key_fingerprint": fingerprint, "key_type": "ECDSA-P256-non-custodial"},
        )

        log.info(f"ACTIVATED: {windi_id} (fingerprint: {fingerprint[:16]}...)")
        return {
            "status": "activated",
            "windi_id": windi_id,
            "key_fingerprint": fingerprint,
            "message": "Your WINDI ID is now active. Welcome to governance sovereignty.",
        }

    # ── Admin: Ledger View ──
    @app.get("/admin/ledger", response_class=HTMLResponse)
    async def admin_ledger(request: Request, user: str = Depends(verify_admin)):
        entries = ledger.get_entries(limit=100)
        chain = ledger.verify_chain()
        return render_ledger_html(entries, chain)


# ═══════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════

def migrate_from_old_system():
    """Import leads from old leads.jsonl if it exists."""
    old_file = os.path.join(config.BASE_DIR, "leads.jsonl")
    if not os.path.exists(old_file):
        return
    
    count = 0
    with open(old_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                existing = db.get_lead_by_id(entry.get("lead_id", ""))
                if not existing:
                    db.create_lead(
                        lead_id=entry.get("lead_id", generate_lead_id()),
                        name=entry.get("name", ""),
                        email=entry.get("email", ""),
                        company=entry.get("company", ""),
                        interest=entry.get("interest", "free"),
                        source=entry.get("source", "migration"),
                    )
                    count += 1
            except Exception as e:
                log.warning(f"Migration skip: {e}")
    
    if count > 0:
        log.info(f"Migrated {count} leads from old system")
        # Rename old file
        os.rename(old_file, old_file + ".migrated")


def main():
    log.info(f"""
╔═══════════════════════════════════════════════════════════════════╗
║   WINDI ID Genesis v{config.VERSION}                                     ║
║   Port {config.PORT} · "Cada lead é uma semente."                        ║
║   Three Dragons Protocol v1.1 · I1-I9 Active                   ║
║   I9: Auto-approve = {config.AUTO_APPROVE_LEADS} (MUST be False)                  ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    # Initialize
    db.init_db()
    migrate_from_old_system()

    # System ledger entry
    ledger.append(
        event=ledger.EVENT_SYSTEM,
        entity_id="GENESIS-SERVICE",
        payload={"action": "startup", "version": config.VERSION},
    )

    if USE_FASTAPI:
        uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
    else:
        log.error("FastAPI/Uvicorn required. Install: pip install fastapi uvicorn")
        sys.exit(1)


if __name__ == "__main__":
    main()
