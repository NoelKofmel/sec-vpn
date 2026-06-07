#!/usr/bin/env bash
# Generates self-signed mTLS certs for local development.
# Output: certs/ca.{crt,key}, certs/server.{crt,key}, certs/client.{crt,key}
set -euo pipefail

CERTS_DIR="$(cd "$(dirname "$0")/.." && pwd)/certs"
mkdir -p "$CERTS_DIR"
cd "$CERTS_DIR"

echo "Generating CA..."
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
  -subj "/CN=SecVPN-Dev-CA/O=SecVPN/C=CH"

echo "Generating server (node-agent) cert..."
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr \
  -subj "/CN=node-agent/O=SecVPN/C=CH"
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt \
  -extfile <(printf "subjectAltName=DNS:node-agent,DNS:localhost,IP:127.0.0.1")

echo "Generating client (backend) cert..."
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr \
  -subj "/CN=backend/O=SecVPN/C=CH"
openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out client.crt

rm -f server.csr client.csr ca.srl

echo "Done. Certs written to $CERTS_DIR/"
echo "  CA:     ca.crt / ca.key"
echo "  Server: server.crt / server.key"
echo "  Client: client.crt / client.key"
