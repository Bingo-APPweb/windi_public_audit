#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# WINDI Phase 3: Generate mTLS Certificates
# ═══════════════════════════════════════════════════════════════════
# Creates:
#   - CA (Certificate Authority)
#   - Hub server certificate
#   - Example node client certificate
# ═══════════════════════════════════════════════════════════════════

set -e

CERT_DIR="$(dirname "$0")/certs"
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

echo "═══════════════════════════════════════════════════"
echo "  WINDI mTLS Certificate Generation"
echo "═══════════════════════════════════════════════════"
echo ""

# ─── CA Certificate ──────────────────────────────────────────────────
echo "1. Creating Certificate Authority..."
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
    -subj "/C=DE/ST=Bavaria/L=Munich/O=WINDI Federation/OU=Certificate Authority/CN=WINDI CA"
echo "   Created: ca.crt, ca.key"

# ─── Hub Server Certificate ──────────────────────────────────────────
echo ""
echo "2. Creating Hub server certificate..."

# Create config for SAN
cat > hub.cnf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = DE
ST = Bavaria
L = Munich
O = WINDI Federation
OU = Hub
CN = hub.windi.local

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = hub.windi.local
DNS.2 = localhost
DNS.3 = *.windi.local
IP.1 = 127.0.0.1
EOF

openssl genrsa -out hub.key 2048
openssl req -new -key hub.key -out hub.csr -config hub.cnf
openssl x509 -req -days 365 -in hub.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out hub.crt -extensions v3_req -extfile hub.cnf
rm hub.csr hub.cnf
echo "   Created: hub.crt, hub.key"

# ─── Example Node Certificate ────────────────────────────────────────
echo ""
echo "3. Creating example node certificate..."

NODE_ID="node:example-org-munich-01"
NODE_DOMAIN="windi.example-org.de"

cat > node.cnf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = DE
ST = Bavaria
L = Munich
O = Example Organization
OU = WINDI Node
CN = ${NODE_ID}

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${NODE_DOMAIN}
URI.1 = windi://${NODE_ID}
EOF

openssl genrsa -out node-example.key 2048
openssl req -new -key node-example.key -out node-example.csr -config node.cnf
openssl x509 -req -days 365 -in node-example.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out node-example.crt -extensions v3_req -extfile node.cnf
rm node-example.csr node.cnf
echo "   Created: node-example.crt, node-example.key"

# ─── Summary ─────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════"
echo "  Certificates Generated Successfully"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  Files created in: $CERT_DIR"
echo ""
echo "  CA:"
echo "    ca.crt          - CA certificate (distribute to nodes)"
echo "    ca.key          - CA private key (keep secure!)"
echo ""
echo "  Hub Server:"
echo "    hub.crt         - Server certificate"
echo "    hub.key         - Server private key"
echo ""
echo "  Example Node:"
echo "    node-example.crt - Client certificate"
echo "    node-example.key - Client private key"
echo ""
echo "  To create additional node certs, use:"
echo "    ./generate-node-cert.sh <node_id> <domain>"
echo ""
