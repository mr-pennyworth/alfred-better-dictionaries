#!/usr/bin/env bash
set -euo pipefail
set -o xtrace

ARCH="${TARGET_ARCH:-$(uname -m)}"

MEILISEARCH_RELEASE_URL="https://github.com/meilisearch/meilisearch/releases"
MS_INTEL="$MEILISEARCH_RELEASE_URL/download/v1.6.1/meilisearch-macos-amd64"
MS_APPLE="$MEILISEARCH_RELEASE_URL/download/v1.6.1/meilisearch-macos-apple-silicon"

JQ_RELEASE_URL="https://github.com/jqlang/jq/releases"
JQ_INTEL="$JQ_RELEASE_URL/download/jq-1.7.1/jq-macos-amd64"
JQ_APPLE="$JQ_RELEASE_URL/download/jq-1.7.1/jq-macos-arm64"

UV_RELEASE_URL="https://github.com/astral-sh/uv/releases"
UV_VERSION="0.10.9"
UV_INTEL="$UV_RELEASE_URL/download/$UV_VERSION/uv-x86_64-apple-darwin.tar.gz"
UV_APPLE="$UV_RELEASE_URL/download/$UV_VERSION/uv-aarch64-apple-darwin.tar.gz"

if [ "$ARCH" = "x86_64" ]; then
  curl -L $MS_INTEL -o alfred-dict-server
  curl -L $JQ_INTEL -o jq
  curl -L $UV_INTEL -o uv.tar.gz
  UV_DIR="uv-x86_64-apple-darwin"
elif [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
  curl -L $MS_APPLE -o alfred-dict-server
  curl -L $JQ_APPLE -o jq
  curl -L $UV_APPLE -o uv.tar.gz
  UV_DIR="uv-aarch64-apple-darwin"
else
  echo "Unsupported TARGET_ARCH: $ARCH" >&2
  exit 1
fi

chmod +x alfred-dict-server
chmod +x jq

tar -xzf uv.tar.gz
cp "$UV_DIR/uv" ./uv
chmod +x uv
rm -rf uv.tar.gz uv-*-apple-darwin
