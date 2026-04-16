#!/usr/bin/env python3
"""
Patch nginx to add /travel/map/ route for W-TRAVEL-MAP-001
Usage: sudo python3 patch-nginx-travel-map.py
"""

import shutil
from datetime import datetime

NGINX_CONF = "/etc/nginx/sites-enabled/windi-domain.com"
BACKUP = f"/tmp/nginx-backup-travel-map-{datetime.now().strftime('%Y%m%d_%H%M%S')}.conf"

SNIPPET = '''    # ═══ W-TRAVEL-MAP-001 :8153 (Berlin Pitch) ═══
    location ^~ /travel/map/ {
        proxy_pass http://127.0.0.1:8153/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

'''

MARKER = "    # ═══ WINDI TRAVEL :8126 ═══"

# Read
with open(NGINX_CONF) as f:
    content = f.read()

# Check if already patched
if "W-TRAVEL-MAP-001" in content:
    print("Already patched. Exiting.")
    exit(0)

# Backup
shutil.copy(NGINX_CONF, BACKUP)
print(f"Backup: {BACKUP}")

# Insert snippet before marker
if MARKER not in content:
    print(f"ERROR: Marker not found: {MARKER}")
    exit(1)

new_content = content.replace(MARKER, SNIPPET + MARKER)

# Write
with open(NGINX_CONF, "w") as f:
    f.write(new_content)

print("Patched! Now run:")
print("  sudo nginx -t && sudo systemctl reload nginx")
