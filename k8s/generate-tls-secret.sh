#!/usr/bin/env bash
set -euo pipefail

DOMAIN="wisecow.local"
CERT_DIR="$(mktemp -d)"

openssl req -x509 -nodes \
  -days 365 \
  -newkey rsa:2048 \
  -keyout "${CERT_DIR}/tls.key" \
  -out "${CERT_DIR}/tls.crt" \
  -subj "/CN=${DOMAIN}/O=wisecow" \
  2>/dev/null

kubectl create secret tls wisecow-tls \
  --cert="${CERT_DIR}/tls.crt" \
  --key="${CERT_DIR}/tls.key" \
  --dry-run=client -o yaml | kubectl apply -f -

rm -rf "${CERT_DIR}"
echo "done: wisecow-tls secret created for ${DOMAIN}"
