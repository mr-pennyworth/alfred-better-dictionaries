#!/bin/bash

# Make a copy of the original 'factory-version' workflow
cp info.plist info.plist.orig

chmod +x ./BetterDict
chmod +x ./alfred-dict-server
chmod +x ./jq

xattr -d com.apple.quarantine ./AlfredExtraPane.app
xattr -d com.apple.quarantine ./alfred-dict-server
xattr -d com.apple.quarantine ./BetterDict
xattr -d com.apple.quarantine ./cocoaDialog.app
xattr -d com.apple.quarantine ./jq

open ./AlfredExtraPane.app

# Kill instances running from previous version of workflow
killall alfred-dict-server
