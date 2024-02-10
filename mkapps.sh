#!/usr/bin/env bash
set -o xtrace

ARCH=$(uname -m)

MEILISEARCH_RELEASE_URL="https://github.com/meilisearch/meilisearch/releases"
URL_INTEL="$MEILISEARCH_RELEASE_URL/download/v1.6.1/meilisearch-macos-amd64"
URL_APPLE_SILICON="$MEILISEARCH_RELEASE_URL/download/v1.6.1/meilisearch-macos-apple-silicon"

if [ "$ARCH" = "x86_64" ]; then
  curl -L $URL_INTEL -o alfred-dict-server
else
  curl -L $URL_APPLE_SILICON -o alfred-dict-server
fi


# Build the python scripts into a standalone binary
pip3 install -r pyapp/requirements.txt
pyinstaller pyapp/BetterDict.py --onefile --noconfirm --distpath ./
