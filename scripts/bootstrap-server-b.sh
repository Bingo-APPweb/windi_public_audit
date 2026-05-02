#!/bin/bash
# ============================================================
# WINDI Server B Bootstrap Script v1.0
# Galho B — Camada INTERPRET (Ollama)
# Preparado por: Liga IA+H — 02 Mai 2026
# Revisado com 5 correcções do Human Dragon
# ============================================================

set -e  # Parar em caso de erro

echo "=== FASE 1 — Sistema Base ==="
export DEBIAN_FRONTEND=noninteractive
apt update
apt upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"
apt install -y curl wget git htop tmux ufw unattended-upgrades

echo "=== FASE 2 — User windi ==="
useradd -m -s /bin/bash windi
mkdir -p /home/windi/.ssh
cp /root/.ssh/authorized_keys /home/windi/.ssh/
chown -R windi:windi /home/windi/.ssh
chmod 700 /home/windi/.ssh
chmod 600 /home/windi/.ssh/authorized_keys
echo "windi ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/windi
chmod 440 /etc/sudoers.d/windi

echo "=== FASE 3 — Hostname ==="
hostnamectl set-hostname windi-b
echo "127.0.1.1 windi-b" >> /etc/hosts

echo "=== FASE 4 — Firewall ==="
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow from 87.106.29.233 to any port 11434 comment 'Ollama from Server A only'
ufw --force enable

echo "=== FASE 5 — Ollama ==="
curl -fsSL https://ollama.com/install.sh | sh
systemctl enable ollama
systemctl start ollama

echo "=== FASE 6 — Pull Modelo Inicial ==="
ollama pull mistral:7b

echo "=== FASE 7 — Etiquetagem e Patches Automáticos ==="
cat > /etc/motd << 'EOF'
================================================
  WINDI Server B — Galho B / Camada INTERPRET
  Ollama inference layer · NO ledger · NO DIDs
  Sister of: windi-a (87.106.29.233)
  IP: 85.215.131.0
================================================
EOF

# Activar unattended-upgrades (já instalado em Fase 1)
echo 'APT::Periodic::Update-Package-Lists "1";' > /etc/apt/apt.conf.d/20auto-upgrades
echo 'APT::Periodic::Unattended-Upgrade "1";' >> /etc/apt/apt.conf.d/20auto-upgrades

echo ""
echo "================================================"
echo "  BOOTSTRAP COMPLETO — Server B (windi-b)"
echo "  Próximo passo manual: validar SSH com user windi"
echo "  Depois: hardening SSH (PermitRootLogin no)"
echo "================================================"
