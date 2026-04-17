#!/usr/bin/env python3
"""Add W-ACADEMY-001 route to nginx config."""

import re
from pathlib import Path
from datetime import datetime

NGINX_CONF = "/etc/nginx/sites-enabled/windi-domain.com"
BACKUP_DIR = "/opt/windi/w-academy-001"

ACADEMY_ROUTE = '''
    # W-ACADEMY-001 — WINDI Institute Ausbildungsplattform
    location /academy/ {
        proxy_pass http://127.0.0.1:8180/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /academy/api/ {
        proxy_pass http://127.0.0.1:8180/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
'''

def patch():
    conf = Path(NGINX_CONF)
    content = conf.read_text()

    if "/academy/" in content:
        print("✓ Route already exists")
        return

    # Backup
    backup_name = f"nginx-backup-academy-{datetime.now().strftime('%Y%m%d_%H%M%S')}.conf"
    Path(f"{BACKUP_DIR}/{backup_name}").write_text(content)
    print(f"✓ Backup: {backup_name}")

    # Find insertion point (after /lab/ block)
    pattern = r'(location /lab/api/.*?\n    \})'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        insert_point = match.end()
        new_content = content[:insert_point] + ACADEMY_ROUTE + content[insert_point:]
        conf.write_text(new_content)
        print("✓ Route added after /lab/")
    else:
        # Fallback: add before closing server block
        new_content = content.replace("\n}\n", ACADEMY_ROUTE + "\n}\n", 1)
        conf.write_text(new_content)
        print("✓ Route added before server close")

    print("→ Run: sudo nginx -t && sudo systemctl reload nginx")

if __name__ == "__main__":
    patch()
