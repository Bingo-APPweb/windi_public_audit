#!/bin/bash
# W-MAIL-001 — Generate TRUE Ed25519 (Guardian Opção B)
# Replaces fake Ed25519 (RSA) with real Ed25519 key

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "W-MAIL-001 — Generating TRUE Ed25519 DKIM Key"
echo "Guardian Opção B: Dual signing real desde Genesis"
echo "═══════════════════════════════════════════════════════════════"

# ── FASE 1: Backup estado actual ──────────────────────────────
echo ""
echo "[FASE 1/6] Backup estado actual..."

mkdir -p /opt/windi/w-mail-001/backups/ed25519-fix-$(date +%Y%m%d-%H%M)
BACKUP_DIR="/opt/windi/w-mail-001/backups/ed25519-fix-$(date +%Y%m%d-%H%M)"

# Backup KeyTable e SigningTable
docker exec windi-mailserver cat /tmp/docker-mailserver/opendkim/KeyTable > "$BACKUP_DIR/KeyTable.before"
docker exec windi-mailserver cat /tmp/docker-mailserver/opendkim/SigningTable > "$BACKUP_DIR/SigningTable.before"

# Backup chaves RSA (queremos preservar) - usando docker cp
docker cp windi-mailserver:/tmp/docker-mailserver/opendkim/keys/windisites.de/rsa.private "$BACKUP_DIR/rsa.private"
docker cp windi-mailserver:/tmp/docker-mailserver/opendkim/keys/windisites.de/rsa.txt "$BACKUP_DIR/rsa.txt" 2>/dev/null || true

echo "✅ Backup criado: $BACKUP_DIR"

# ── FASE 2: Remover "Ed25519 falso" (RSA duplicado) ───────────
echo ""
echo "[FASE 2/6] Removendo Ed25519 falso (RSA duplicado)..."

docker exec windi-mailserver rm -f /tmp/docker-mailserver/opendkim/keys/windisites.de/ed25519.private
docker exec windi-mailserver rm -f /tmp/docker-mailserver/opendkim/keys/windisites.de/ed25519.txt

echo "✅ Chaves RSA falsamente nomeadas removidas"

# ── FASE 3: Verificar suporte Ed25519 ─────────────────────────
echo ""
echo "[FASE 3/6] Verificando suporte Ed25519..."

echo "OpenDKIM version:"
docker exec windi-mailserver opendkim -V 2>&1 | head -1 || echo "opendkim -V failed"

echo ""
echo "Checking opendkim-genkey Ed25519 support:"
docker exec windi-mailserver opendkim-genkey --help 2>&1 | grep -i ed25519 || echo "No Ed25519 support in opendkim-genkey"

# ── FASE 4: Gerar Ed25519 verdadeiro (via openssl) ────────────
echo ""
echo "[FASE 4/6] Gerando Ed25519 TRUE via openssl..."

docker exec windi-mailserver bash -c '
cd /tmp/docker-mailserver/opendkim/keys/windisites.de/

# Gerar chave privada Ed25519
openssl genpkey -algorithm ED25519 -out ed25519.private

# Extrair chave pública em formato DER raw (últimos 32 bytes = chave Ed25519 pura)
openssl pkey -in ed25519.private -pubout -outform DER | tail -c 32 | base64 -w 0 > ed25519.pub.raw

# Criar arquivo .txt no formato DKIM
PUBKEY=$(cat ed25519.pub.raw)
echo "ed25519._domainkey IN TXT \"v=DKIM1; k=ed25519; p=${PUBKEY}\"" > ed25519.txt

# Permissions
chown opendkim:opendkim ed25519.private ed25519.txt 2>/dev/null || chown root:root ed25519.private ed25519.txt
chmod 600 ed25519.private
chmod 644 ed25519.txt

# Cleanup
rm -f ed25519.pub.raw
'

echo "✅ Ed25519 key generated via openssl"

# ── FASE 5: Reconfigurar OpenDKIM ─────────────────────────────
echo ""
echo "[FASE 5/6] Reconfigurando OpenDKIM KeyTable..."

docker exec windi-mailserver bash -c '
cat > /tmp/docker-mailserver/opendkim/KeyTable << EOF
ed25519._domainkey.windisites.de windisites.de:ed25519:/etc/opendkim/keys/windisites.de/ed25519.private
rsa._domainkey.windisites.de windisites.de:rsa:/etc/opendkim/keys/windisites.de/rsa.private
EOF
'

echo "✅ KeyTable reconfigured with TRUE Ed25519"

# SigningTable should already be correct (both selectors)
echo ""
echo "Current SigningTable:"
docker exec windi-mailserver cat /tmp/docker-mailserver/opendkim/SigningTable

# ── FASE 6: Restart OpenDKIM + Postfix ────────────────────────
echo ""
echo "[FASE 6/6] Restarting OpenDKIM and Postfix..."

docker exec windi-mailserver supervisorctl restart opendkim || echo "⚠️  OpenDKIM restart via supervisorctl failed, trying pkill..."
docker exec windi-mailserver pkill -HUP opendkim 2>/dev/null || true

docker exec windi-mailserver supervisorctl restart postfix || echo "⚠️  Postfix restart via supervisorctl failed"

sleep 3

# Check logs
echo ""
echo "Checking logs for errors:"
docker exec windi-mailserver tail -20 /var/log/mail.log | grep -iE "opendkim|error" || echo "(no recent errors)"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Ed25519 Generation Complete"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "NEXT: Run Guardian verification commands:"
echo ""
echo "  sudo docker exec windi-mailserver ls -la /tmp/docker-mailserver/opendkim/keys/windisites.de/"
echo "  sudo docker exec windi-mailserver cat /tmp/docker-mailserver/opendkim/keys/windisites.de/ed25519.txt"
echo "  sudo docker exec windi-mailserver openssl pkey -in /tmp/docker-mailserver/opendkim/keys/windisites.de/ed25519.private -text -noout | head -3"
echo ""
echo "Guardian criteria:"
echo "  ✅ ed25519.private < 300 bytes"
echo "  ✅ ed25519.txt contains k=ed25519 (NOT k=rsa)"
echo "  ✅ Public key ~44 chars base64 (NOT ~390)"
echo "  ✅ openssl pkey reports ED25519 Private-Key"
echo ""
echo "If all pass → Guardian approval → Publish to Strato"
echo "═══════════════════════════════════════════════════════════════"
