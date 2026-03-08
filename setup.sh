#!/bin/bash

# Make a copy of the original 'factory-version' workflow
if [ ! -f info.plist.orig ]; then
  cp info.plist info.plist.orig
fi

set -uo pipefail

chmod +x ./alfred-dict-server
chmod +x ./jq
chmod +x ./uv

function deQuarantine {
  # If the extended attribute doesn't exist, don't bother
  # printing the error "No such xattr...", as those messages
  # can be mistaken as "errors".
  xattr -d com.apple.quarantine "$1" 2> /dev/null || true
}

deQuarantine ./AlfredExtraPane.app
deQuarantine ./alfred-dict-server
deQuarantine ./cocoaDialog.app
deQuarantine ./jq
deQuarantine ./uv

WORKFLOW_DATA_DIR="${alfred_workflow_data:-}"
if [ -z "$WORKFLOW_DATA_DIR" ]; then
  exit 0
fi

VENV_DIR="$WORKFLOW_DATA_DIR/.venv"
VENV_PY="$VENV_DIR/bin/python"
REQ_FILE="./pyapp/requirements.txt"
REQ_SHA_FILE="$VENV_DIR/.requirements.sha256"
REQ_SHA=$(shasum -a 256 "$REQ_FILE" | awk '{print $1}')
PY_TARGET="3.14"

mkdir -p "$WORKFLOW_DATA_DIR"

# Ensure workflow runtime always uses Python 3.14.
if [ -x "$VENV_PY" ]; then
  CURRENT_PY_VER=$("$VENV_PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
  if [ "$CURRENT_PY_VER" != "$PY_TARGET" ]; then
    rm -rf "$VENV_DIR"
  fi
fi

if [ ! -x "$VENV_PY" ]; then
  UV_PYTHON_PREFERENCE=managed ./uv venv --python "$PY_TARGET" "$VENV_DIR"
fi

if [ ! -f "$REQ_SHA_FILE" ] || [ "$REQ_SHA" != "$(cat "$REQ_SHA_FILE")" ]; then
  ./uv pip install --python "$VENV_PY" -r "$REQ_FILE"
  printf "%s" "$REQ_SHA" > "$REQ_SHA_FILE"
fi

defaults write com.runningwithcrayons.Alfred experimental.presssecretary -bool YES
open ./AlfredExtraPane.app

# Kill instances running from previous version of workflow
killall -q alfred-dict-server || true
