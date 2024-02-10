#!/usr/bin/env bash
set -o xtrace

ARCH=$(uname -m)

MEILISEARCH_RELEASE_URL="https://github.com/meilisearch/meilisearch/releases"
MS_INTEL="$MEILISEARCH_RELEASE_URL/download/v1.6.1/meilisearch-macos-amd64"
MS_APPLE="$MEILISEARCH_RELEASE_URL/download/v1.6.1/meilisearch-macos-apple-silicon"

JQ_RELEASE_URL="https://github.com/jqlang/jq/releases"
JQ_INTEL="$JQ_RELEASE_URL/download/jq-1.7.1/jq-macos-amd64"
JQ_APPLE="$JQ_RELEASE_URL/download/jq-1.7.1/jq-macos-arm64"

if [ "$ARCH" = "x86_64" ]; then
  curl -L $MS_INTEL -o alfred-dict-server
  curl -L $JQ_INTEL -o jq
else
  curl -L $MS_APPLE -o alfred-dict-server
  curl -L $JQ_APPLE -o jq
fi

chmod +x alfred-dict-server
chmod +x jq


# Build the python scripts into a standalone binary
pip3 install -r pyapp/requirements.txt
pyinstaller pyapp/BetterDict.py --onefile --noconfirm --distpath ./
