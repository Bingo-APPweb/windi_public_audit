#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# WINDI Phase 3: Generate Node Client Certificate
# ═══════════════════════════════════════════════════════════════════
# Usage: ./generate-node-cert.sh <node_id> <domain> [org_name]
# Example: ./generate-node-cert.sh node:deutschebank-frankfurt-01 windi.deutschebank.de "Deutsche Bank"
# ═══════════════════════════════════════════════════════════════════

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <node_id> <domain> [org_name]"
    echo "Example: $0 node:deutschebank-frankfurt-01 windi.deutschebank.de 'Deutsche Bank'"
    exit 1
fi

NODE_ID="$1"
NODE_DOMAIN="$2"
ORG_NAME="${3:-WINDI Node}"

CERT_DIR="$(dirname "$0")/certs"
cd "$CERT_DIR"

# Sanitize node_id for filename
FILENAME=$(echo "$NODE_ID" | sed 's/[^a-zA-Z0-9-]/_/g')

echo "Generating certificate for: $NODE_ID"

cat > "${FILENAME}.cnf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = DE
O = ${ORG_NAME}
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

openssl genrsa -out "${FILENAME}.key" 2048
openssl req -new -key "${FILENAME}.key" -out "${FILENAME}.csr" -config "${FILENAME}.cnf"
openssl x509 -req -days 365 -in "${FILENAME}.csr" -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out "${FILENAME}.crt" -extensions v3_req -extfile "${FILENAME}.cnf"

rm "${FILENAME}.csr" "${FILENAME}.cnf"

echo ""
echo "Created:"
echo "  ${FILENAME}.crt"
echo "  ${FILENAME}.key"
echo ""
echo "To use with curl:"
echo "  curl --cert ${FILENAME}.crt --key ${FILENAME}.key --cacert ca.crt https://hub.windi.local/..."
