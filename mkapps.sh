#!/usr/bin/env bash
set -o xtrace

# Pick the correct meilisearch binary for the arch
git lfs pull
cp "meilisearch-$(uname -m)" alfred-dict-server

# Build the python scripts into a standalone binary
pip3 install -r pyapp/requirements.txt
pyinstaller pyapp/BetterDict.py --onefile --noconfirm --distpath ./
