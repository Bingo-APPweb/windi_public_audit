#!/usr/bin/env python3
"""
Complete nginx fix for clone.windia4desk.tech:
  /                    → static DSGVO dashboard
  /api/extract         → clone_server:8092
  /api/sanctuary/*     → sanctuary_api:8093
  /api/*               → clone_server:8092 (proxy to HUB)
  /marketplace etc     → existing static files (unchanged)
"""
import os, subprocess

# Step 1: Fix sanctuary port 8092 → 8093
sanc = '/opt/windi/core/sanctuary_api.py'
c = open(sanc).read()
if '8092' in c:
    c = c.replace('8092', '8093')
    open(sanc, 'w').write(c)
    print('✅ Sanctuary port: 8092 → 8093')
elif '8093' in c:
    print('ℹ️  Sanctuary already on 8093')

# Step 2: Update nginx
NGINX_CONF = None
for p in ['/etc/nginx/sites-enabled/clone.windia4desk.tech',
          '/etc/nginx/sites-available/clone.windia4desk.tech']:
    if os.path.exists(p):
        NGINX_CONF = p
        break
if not NGINX_CONF:
    r = subprocess.run(['grep','-rl','clone.windia4desk','/etc/nginx/'], capture_output=True, text=True)
    if r.stdout.strip(): NGINX_CONF = r.stdout.strip().split('\n')[0]

if not NGINX_CONF:
    print('❌ Nginx conf not found'); exit(1)

n = open(NGINX_CONF).read()

old_loc = """    location / {
        proxy_pass http://127.0.0.1:8092;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }"""

new_loc = """    # Landing page (DSGVO dashboard)
    location = / {
        types { } default_type "text/html; charset=utf-8";
        alias /opt/windi/core/windi_public_dashboard.html;
    }

    # Sanctuary API (scan engine)
    location /api/sanctuary/ {
        proxy_pass http://127.0.0.1:8093/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # Clone API (extract + HUB proxy)
    location /api/ {
        proxy_pass http://127.0.0.1:8092/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        client_max_body_size 20M;
    }

    # Static + editor from clone-app
    location /static/ {
        proxy_pass http://127.0.0.1:8092/static/;
        proxy_set_header Host $host;
    }

    location /editor {
        proxy_pass http://127.0.0.1:8092/editor;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }"""

if old_loc in n:
    n = n.replace(old_loc, new_loc)
    open(NGINX_CONF, 'w').write(n)
    print(f'✅ Nginx updated: {NGINX_CONF}')
    print('   /              → DSGVO dashboard (static)')
    print('   /api/sanctuary → sanctuary:8093')
    print('   /api/*         → clone_server:8092')
else:
    print('⚠️  Location block not found exactly')
    # Show what we have
    for i, line in enumerate(n.split('\n')):
        if 'location' in line.strip()[:10] or 'proxy_pass' in line:
            print(f'  L{i}: {line.rstrip()}')

print('\nNEXT STEPS:')
print('  1. sudo nginx -t && sudo systemctl reload nginx')
print('  2. cd /opt/windi/core && nohup python3 sanctuary_api.py > /tmp/sanctuary.log 2>&1 &')
print('  3. Test: curl -s https://clone.windia4desk.tech/ | head -5')
