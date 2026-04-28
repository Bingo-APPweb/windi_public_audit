 # Primeiro, garante SSH key
  ls -la ~/.ssh/id_ed25519 || ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519
  # Adiciona chave ao GitHub (se necessário)
  cat ~/.ssh/id_ed25519.pub
  # Executa cleanup
  ./git-cleanup.sh
  # Depois do cleanup, force push
  git push origin main --force
claude
# Backup
  sudo cp /etc/nginx/sites-available/windi-domain.com /etc/nginx/sites-available/windi-domain.com.bak.wpil
  # Editar e adicionar o bloco de /opt/windi/services/wpil/nginx-wpil.conf
  sudo nano /etc/nginx/sites-available/windi-domain.com
  # Testar e reload
  sudo nginx -t && sudo systemctl reload nginx
sudo cp /opt/windi/services/wpil/wpil.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable wpil
  sudo systemctl start wpil
  sudo systemctl status wpil
sudo cp /etc/nginx/sites-available/windi-domain.com /etc/nginx/sites-available/windi-domain.com.bak.wpil
sudo nano /etc/nginx/sites-available/windi-domain.com
sudo nginx -t && sudo systemctl reload nginx
curl https://windi-domain.com/wpil/health
sudo cp /opt/windi/services/wpil/wpil.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable wpil
  sudo systemctl start wpil
  sudo systemctl status wpil
journalctl -u wpil -n 20
 # Backup primeiro
  sudo cp /etc/nginx/sites-available/windi-domain.com /etc/nginx/sites-available/windi-domain.com.bak.wpil
  # Ver o bloco a adicionar
  cat /opt/windi/services/wpil/nginx-wpil.conf
  # Editar nginx (adicionar o bloco acima dentro do server {})
  sudo nano /etc/nginx/sites-available/windi-domain.com
  # Testar e reload
  sudo nginx -t && sudo systemctl reload nginx
 sudo nginx -t && sudo systemctl reload nginx
curl https://windi-domain.com/wpil/health
The /wpil/ nginx route needs to be added. Add this block to /etc/nginx/sites-enabled/windi-domain.com:
sudo nginx -t && sudo systemctl reload nginx
sudo bash /tmp/patch-nginx-wpil.sh
sudo bash /tmp/patch-nginx-wpil.sh
sudo cp /tmp/investor-index-patched.html /var/www/investor/index.html
sudo cp /tmp/investor-index-patched.html /var/www/investor/index.html
sudo cp /tmp/wpil-demo.html /var/www/investor/wpil-demo.html && sudo chown www-data:www-data /var/www/investor/wpil-demo.html
 # 1. Investor Demo (standalone)
  sudo cp /tmp/wpil-ceremony.html /var/www/investor/wpil-demo.html && sudo chown www-data:www-data
  /var/www/investor/wpil-demo.html
  # 2. Substituir /prove/ principal (UPGRADE)
  sudo cp /tmp/wpil-ceremony.html /opt/windi/prove/index.html && sudo chown windi:windi /opt/windi/prove/index.html
sudo cp /tmp/wpil-ceremony.html /var/www/investor/wpil-demo.html
sudo python3 ~/patch-nginx-travel-map.py && sudo nginx -t && sudo systemctl reload nginx
sudo python3 ~/patch-nginx-travel-map.py && sudo nginx -t && sudo systemctl reload nginx
sudo python3 ~/patch-investor-map.py
 # 1. Instalar BFG
  wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
  # 2. Limpar ficheiros >50MB do histórico
  java -jar bfg-1.14.0.jar --strip-blobs-bigger-than 50M .
  # 3. Limpar e reempacotar
  git reflog expire --expire=now --all
  git gc --prune=now --aggressive
  # 4. Force push (CUIDADO - reescreve histórico)
  git push origin main --force
cat /home/windi/.ssh/authorized_keys
ls -la /home/windi/.ssh/
ls -la /home/windi/
 # Primeiro, garante SSH key
 # Primeiro, garante SSH key
ls /la /home/windi/.ssh/
cat /home/windi/.ssh/authorized_keys
ls -la /home/windi/.ssh/
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKoCcy2iaMJaLVvMzt76TGH1X8R4havPNhvVFHruWhk1 jober@Dragon" > /home/windi/.ssh/authorized_keys
cat /home/windi/.ssh/authorized_keys
cat /etc/ssh/sshd_config | grep -E "PubkezAuth|AuthoriyedKeys|PasswordAuth|StrictModes"
grep -E "PubkeyAuth|AuthorizedKeysFile" /etc/ssh/sshd_config
ls -la /home/windi/
stat /home/windi
grep PubkeyAuth /etc/ssh/sshd_config
chmod 755 /home/windi
sudo tail -20 /var/log/auth.log
journalctl -u ssh -n 20
systemctl status ssh
systemctl restart ssh
su -
claude
claude
sudo python3 /home/windi/replace_landing_nginx.py
sudo systemctl reload nginx
sudo systemctl reload nginx
sudo sed -i 's|proxy_pass http://127.0.0.1:8145/verify/|proxy_pass http://127.0.0.1:8114/verify/|'
  /etc/nginx/sites-enabled/windi-domain.com
  sudo nginx -t && sudo systemctl reload nginx
sudo systemctl reload nginx
grep -A3 "location /verify/" /etc/nginx/sites-enabled/windi-domain.com | head -5
 sudo sed -i 's|proxy_pass http://127.0.0.1:8145/verify/;|proxy_pass http://127.0.0.1:8114/verify-public/;|'
  /etc/nginx/sites-enabled/windi-domain.com && sudo nginx -t && sudo systemctl reload nginx
  sudo sed -i 's|proxy_pass http://127.0.0.1:8145/verify/;|proxy_pass http://127.0.0.1:8114/verify-public/;|'
  /etc/nginx/sites-enabled/windi-domain.com && sudo nginx -t && sudo systemctl reload nginx
sudo sed -i 's|8145/verify/|8114/verify-public/|' /etc/nginx/sites-enabled/windi-domain.com
 sudo nginx -t
sudo systemctl reload nginx
sudo systemctl restart windi-enterprise
 # Add to nginx config (after /lab/ block):
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
  # Then test and reload:
  sudo nginx -t && sudo systemctl reload nginx
 sudo systemctl reload nginx
curl -s https://windi-domain.com/academy/health | jq .
curl -s https://windi-domain.com/academy/health | python3 -m json.tool
curl -s https://windi-domain.com/academy/health
 ss -tlnp | grep 8180
curl -s http://127.0.0.1:8180/health
grep -A5 "academy" /etc/nginx/sites-enabled/windi-domain.com
 sudo nano /etc/nginx/sites-enabled/windi-domain.com
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl reload nginx && curl -s https://windi-domain.com/academy/health
claude
claude
claude
claude
claude
sudo /opt/windi/bercario/patch_nginx_bercario.sh
 # 1. Editar nginx
  sudo nano /etc/nginx/sites-enabled/windi-domain.com
  # 2. Adicionar após "location = /portal { return 301 /portal/; }":
      # ═══════════════════════════════════════════════
      # WINDI BERÇÁRIO · Sovereign Identity Portal
      # §191-F2 · 2026-04-19
      # ═══════════════════════════════════════════════
      location /bercario/ {
          alias /opt/windi/bercario/;
          index index.html;
          try_files $uri $uri/ /bercario/index.html;
      }
      location = /bercario {
          return 301 /bercario/;
      }
  # 3. Testar e reload
  sudo nginx -t && sudo systemctl reload nginx
sudo nginx -t && sudo systemctl reload nginx
sudo /opt/windi/bercario/patch_nginx_bercario.sh
claude
claude
curl http://127.0.0.1:8015/demo/full-flow/WINDI-TRAVEL-20260418-A1B2C3
 sudo bash /opt/windi/w-actuary-001/setup-nginx.sh
sudo bash /opt/windi/w-actuary-001/nginx-apply-patch.sh
sudo bash /opt/windi/w-actuary-001/nginx-apply-patch.sh
 sudo systemctl reload nginx
sudo systemctl reload nginx && curl -s https://windi-domain.com/actuary/health | python3 -m json.tool
sudo rm /etc/nginx/sites-enabled/windi-domain.com &&   sudo ln -s /etc/nginx/sites-available/windi-domain.com /etc/nginx/sites-enabled/windi-domain.com &&   sudo nginx -t &&   sudo systemctl reload nginx
curl -s https://windi-domain.com/actuary/health | python3 -m json.tool
 sudo /usr/sbin/nginx -t
sudo /usr/sbin/nginx -t && sudo systemctl reload nginx && echo "OK"
 sudo sed -i '232,236d' /etc/nginx/sites-available/windi-domain.com &&   sudo /usr/sbin/nginx -t &&   sudo systemctl reload nginx &&   curl -s https://windi-domain.com/actuary/health | python3 -m json.tool
sudo bash /opt/windi/w-actuary-001/nginx-final.sh
 # Health (público)
  curl -s https://windi-domain.com/actuary/api/health | jq .security_level
  # → "LEVEL_2"
  # Demo sanitizado (sem internals)
  curl -s https://windi-domain.com/actuary/api/demo/full-flow/WINDI-TRAVEL-20260418-A1B2C3 | jq .score
  # → só adjustment_factor + explanation (sem final_score)
  # Audit log
  cat /opt/windi/w-actuary-001/logs/audit.log | tail -1
curl -s https://windi-domain.com/actuary/api/health | python3 -m json.tool
# Lista receipts reais
  curl -s https://windi-domain.com/actuary/api/real/receipts | python3 -m json.tool
  # Flow completo com TRAVEL real
  curl -s https://windi-domain.com/actuary/api/real/flow/WINDI-TRAVEL-20260416221745-F1D46419 | python3 -m json.tool
 # 1. BACKUP adicional (segurança)
  sudo cp /etc/nginx/sites-available/windi-domain.com /etc/nginx/sites-available/windi-domain.com.bak-pre-patch
  # 2. APLICAR patch
  sudo cp /opt/windi/backups/windi-domain.com.patched /etc/nginx/sites-available/windi-domain.com
  # 3. TESTAR sintaxe (OBRIGATÓRIO)
  sudo nginx -t
  # 4. SE nginx -t OK → RELOAD
  sudo systemctl reload nginx
  # 5. SMOKE TEST imediato
  curl -I https://windi-domain.com/enterprise/
  curl -I https://windi-domain.com/verify-public/health
 curl -X POST http://localhost:8101/api/receipts     -H "Content-Type: application/json"     -d '{
      "receipt_id": "WINDI-INCIDENT-20260420-DARK-LAUNCH-GAP",
      "actor": "human-dragon",
      "doc_type": "incident",
      "doc_name": "Dark-Launch Gap — Enterprise + Verify Public",
      "governance_level": "MEDIUM",
      "content_hash": "sha256:nginx-patch-v2.2",
      "invariants": ["I11", "I14"],
      "stage": "C6",
      "notes": "Services UP but not exposed via gateway. Fixed: added upstreams windi_enterprise:8150, windi_verify:8114.
  Routes /enterprise/, /verify-public/. Tree v2.1→v2.2."
    }'
claude
claude
 # Passo 4 — Stop + Disable (requer sudo)
  sudo systemctl stop windi-enterprise windi-export-engine windi-leads windi-clone
  sudo systemctl disable windi-enterprise windi-export-engine windi-leads windi-clone
  # Truncate do log root-owned
  sudo truncate -s 0 /opt/windi/logs/w-enterprise-001.log
  # Verificar disabled
  systemctl list-unit-files --type=service | grep -E 'windi-enterprise|windi-export-engine|windi-leads|windi-clone'
 # 1. Backup
  sudo cp /etc/nginx/sites-available/windi-domain.com /opt/windi/backups/nginx-pre-travel-$(date +%Y%m%d-%H%M%S).conf
  # 2. Apply patch
  sudo cp /tmp/windi-domain.com.patched /etc/nginx/sites-available/windi-domain.com
  # 3. Validate
  sudo nginx -t
  # 4. Reload (só se nginx -t passou)
  sudo systemctl reload nginx
sudo systemctl reload nginx
 # 1. Aplicar patch
  sudo cp /tmp/nginx-patched.conf /etc/nginx/sites-available/windi-domain.com
  # 2. Testar sintaxe
  sudo nginx -t
  # 3. Reload se OK
  sudo systemctl reload nginx
  # 4. Testar verify_url canónica
  curl -sI https://windi-domain.com/verify-public/WINDI-SEAL-20260420123254-BF75F4AE | head -5
# Selo do dia: código → git → Ledger → verify URL
  curl -X POST https://windi-domain.com/dev-api/v1/seal     -H "Authorization: Bearer $TOKEN"     -F "file=@commit-bundle.txt"     -F "actor_did=did:windi:dragon-001"     -F "intent=governance"     -F "context=git-commit-bundle-20260420"
Windi2026
# 1. Backup
  sudo cp /etc/nginx/sites-available/windi-domain.com /opt/windi/backups/nginx-pre-devapi-$(date +%Y%m%d_%H%M%S).conf
  # 2. Editar nginx (inserir upstream na zona de upstreams, location na zona de locations)
  sudo nano /etc/nginx/sites-available/windi-domain.com
  # 3. Testar e recarregar
  sudo nginx -t && sudo systemctl reload nginx
sudo systemctl reload nginx
# 1. Inserir upstream (linha 61)
  sudo sed -i '61a upstream windi_devapi      { server 127.0.0.1:8200 max_fails=3 fail_timeout=30s; keepalive 16; }'
  /etc/nginx/sites-available/windi-domain.com
  # 2. Inserir location (linha 314)
  sudo sed -i '314a\    location /dev-api/ { proxy_pass http://windi_devapi/; proxy_http_version 1.1; proxy_set_header Host
  $host; proxy_set_header X-Real-IP $remote_addr; client_max_body_size 50M; add_header X-WINDI-Service "W-DEV-API-001" always;
  }' /etc/nginx/sites-available/windi-domain.com
  # 3. Testar e recarregar
  sudo nginx -t && sudo systemctl reload nginx
sudo nano /etc/nginx/sites-available/windi-domain.com
sudo nginx -t && sudo systemctl reload nginx
sudo nano /etc/nginx/sites-available/windi-domain.com
  # Vai para linha 161, insere o bloco ACIMA
  # Ctrl+O, Enter, Ctrl+X
  sudo nginx -t && sudo systemctl reload nginx
sudo nginx -t && sudo systemctl reload nginx
ssh windi@87.106.29.233
claude
claude
claude
claude
sudo cp /etc/nginx/sites-enabled/windi-domain.com /etc/nginx/sites-enabled/windi-domain.com.bak.$(date +%Y%m%d%H%M%S

sudo cp /etc/nginx/sites-enabled/windi-domain.com /etc/nginx/sites-enabled/windi-domain.com.bak.$(date +%Y%m%d%H%M%
sudo nano /etc/nginx/sites-enabled/windi-domain.com
 sudo nginx -t && sudo systemctl reload nginx
sudo nano /etc/nginx/sites-enabled/windi-domain.com
sudo nginx -t && sudo systemctl reload nginx
sudo nano /etc/nginx/sites-enabled/windi-domain.com
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl stop windi-masterarbeit
sudo systemctl disable windi-masterarbeit
 # 1. Editar nginx
  sudo nano /etc/nginx/sites-enabled/windi-domain.com
  # 2. Ir para linha 422 (depois do bloco /library/)
  # 3. Colar o conteúdo de:
  cat /opt/windi/patches/nginx-docs-routes-20260423.conf
  # 4. Testar e recarregar
  sudo nginx -t && sudo systemctl reload nginx
sudo nginx -t && sudo systemctl reload nginx
sudo nano /etc/nginx/sites-enabled/windi-domain.com
sudo nginx -t && sudo systemctl reload nginx
sudo nano /etc/nginx/sites-enabled/windi-domain.com
sudo nginx -t && sudo systemctl reload nginx
claude
claude
claude
claude
claude
claude
curl http://127.0.0.1:8150/vera/quality/health
sudo nano /etc/nginx/sites-available/windi-domain.com
sudo nano /etc/nginx/sites-available/windi-domain.com
  sudo nginx -t
  sudo systemctl reload nginx
 sudo systemctl reload nginx
claude
claude
claude
xuxuhormoniousschalimeninafamilia
source /opt/windi/venv-poe/bin/activate
python3 /opt/windi/keys/keygen-001.py
source /opt/windi/venv-poe/bin/activate
python3 /opt/windi/keys/keygen-001.py
source /opt/windi/venv-poe/bin/activate && python3 /opt/windi/keys/sign-test.py
 # 1. Backup
  sudo cp /etc/nginx/sites-available/windi-domain.com /etc/nginx/sites-available/windi-domain.com.bak.$(date +%Y%m%d%H%M%S)
  # 2. Fix linha 595 (mudar proxy_pass)
  sudo sed -i 's|proxy_pass http://windi_genesis/;|proxy_pass http://windi_genesis/api/genesis/;|'
  /etc/nginx/sites-available/windi-domain.com
  # 3. Testar config
  sudo nginx -t
  # 4. Se OK, reload
  sudo systemctl reload nginx
  # 5. Testar endpoint
  curl -s https://windi-domain.com/api/genesis/validate
sudo systemctl reload nginx && curl -s https://windi-domain.com/api/genesis/validate
# Verificar linha actual
  grep -n "proxy_pass http://windi_genesis" /etc/nginx/sites-available/windi-domain.com
  # Aplicar fix (escapando correctamente)
  sudo sed -i 's|proxy_pass http://windi_genesis/;|proxy_pass http://windi_genesis/api/genesis/;|g'
  /etc/nginx/sites-available/windi-domain.com
  # Verificar mudança
  grep -n "proxy_pass http://windi_genesis" /etc/nginx/sites-available/windi-domain.com
  # Test e reload
  sudo nginx -t && sudo systemctl reload nginx
 sudo nano /etc/nginx/sites-available/windi-domain.com
 sudo nginx -t && sudo systemctl reload nginx
 sudo nano /etc/nginx/sites-available/windi-domain.com
sudo nginx -t && sudo systemctl reload nginx
sudo sed -i '79,99d' /etc/nginx/sites-available/windi-domain.com
grep -n "DID-Web" /etc/nginx/sites-available/windi-domain.com
sudo nginx -t
sudo sed -i '596a\
  \
      # ── §207 DID-Web Bridge (W3C DID-CORE 1.1) ──────────────────\
      location = /.well-known/did.json {\
          proxy_pass http://windi_genesis/.well-known/did.json;\
          proxy_http_version 1.1;\
          add_header Content-Type "application/did+ld+json";\
          add_header Access-Control-Allow-Origin "*";\
      }\
  \
      location ^~ /u/ {\
          proxy_pass http://windi_genesis/u/;\
          proxy_http_version 1.1;\
          add_header Content-Type "application/did+ld+json";\
          add_header Access-Control-Allow-Origin "*";\
      }\
  \
      location ^~ /api/did-web/ {\
          proxy_pass http://windi_genesis/api/did-web/;\
          proxy_http_version 1.1;\
      }' /etc/nginx/sites-available/windi-domain.com
  # Verificar e recarregar
  sudo nginx -t && sudo systemctl reload nginx
 sudo sed -i '/location \^~ \/static\//i\
      # ── Shared static assets ─────────────────────────────────\
      location ^~ /shared/ {\
          alias /opt/windi/shared/static/;\
          expires 7d;\
          add_header Cache-Control "public";\
      }\
  ' /etc/nginx/sites-available/windi-domain.com
  # Testar e recarregar
  sudo nginx -t && sudo systemctl reload nginx
Windi2026
 sudo systemctl disable windi-leads.service
  sudo systemctl stop windi-leads.service
  sudo systemctl stop windi-leads.service
  sudo systemctl disable windi-leads.service
 sudo systemctl stop windi-leads.service && sudo systemctl disable windi-leads.service
sudo systemctl reset-failed windi-leads.service
sudo nano /etc/nginx/sites-enabled/windi-domain.com +345
sudo nginx -t && sudo systemctl reload nginx
sudo sed -i '286 a\
  \
      # ── Verify Public Web (3 Modes: Document, Hash, QR) ────\
      location /verify-public/web/ {\
          alias /opt/windi/verify-public/web/;\
          index index.html;\
          try_files $uri $uri/ =404;\
          add_header Cache-Control "public, max-age=3600";\
          add_header X-WINDI-Service "verify-public-web" always;\
      }' /etc/nginx/sites-enabled/windi-domain.com
Windi2026
sudo sed -i '286 a\
  \
      # ── Verify Public Web (3 Modes: Document, Hash, QR) ────\
      location /verify-public/web/ {\
          alias /opt/windi/verify-public/web/;\
          index index.html;\
          try_files $uri $uri/ =404;\
          add_header Cache-Control "public, max-age=3600";\
          add_header X-WINDI-Service "verify-public-web" always;\
      }' /etc/nginx/sites-enabled/windi-domain.com
sudo nginx -t && sudo systemctl reload nginx
sudo sed -i '296,304d' /etc/nginx/sites-enabled/windi-domain.com
sudo nginx -t && sudo systemctl reload nginx
 # Timer
  sudo tee /etc/systemd/system/windi-verify-health.timer << 'EOF'
  [Unit]
  Description=WINDI Verify Health Check Timer

  [Timer]
  OnBootSec=1min
  OnUnitActiveSec=5min

  [Install]
  WantedBy=timers.target
  EOF

  # Service
  sudo tee /etc/systemd/system/windi-verify-health.service << 'EOF'
  [Unit]
  Description=WINDI Verify Health Check

  [Service]
  Type=oneshot
  ExecStart=/bin/bash -c 'curl -sf http://localhost:8114/health || systemctl restart windi-verify-public'
  EOF

  # Enable
  sudo systemctl daemon-reload
  sudo systemctl enable --now windi-verify-health.timer


EOF

  sudo systemctl daemon-reload
  sudo systemctl enable --now windi-verify-health.timer
sudo tee /etc/systemd/system/windi-verify-health.service << 'EOF'
  [Unit]
  Description=WINDI Verify Health Check

  [Service]
  Type=oneshot
  ExecStart=/bin/bash -c 'curl -sf http://localhost:8114/health || systemctl restart windi-verify-public'
  EOF
EOF

sudo systemctl daemon-reload
  sudo systemctl start windi-verify-health.timer
  systemctl status windi-verify-health.timer
 sudo tee /etc/systemd/system/windi-verify-health.service << 'EOF'
  [Unit]
  Description=WINDI Verify Health Check

  [Service]
  Type=oneshot
  User=root
  ExecStart=/bin/bash -c 'curl -sf http://localhost:8114/health || systemctl restart windi-verify-public'
  EOF
EOF

sudo systemctl daemon-reload
sudo systemctl start windi-verify-health.service && echo "✅ OK"
sudo bash /tmp/fix-law-redirect.sh
sudo bash /tmp/fix-law-redirect.sh
  # Remove ONE of the duplicate "location = /law/" blocks
  sudo nginx -t && sudo systemctl reload nginx
sudo systemctl reload nginx
curl -sI https://windi-domain.com/law/ | grep -i location
sudo bash /tmp/fix-law-clean.sh
sudo bash /tmp/fix-law-rewrite.sh
sudo bash /tmp/fix-law-exact.sh
sudo bash /tmp/fix-law-final.sh
/opt/windi/verify-public/web/verify.html.bak.20260426
claude
claude
claude
