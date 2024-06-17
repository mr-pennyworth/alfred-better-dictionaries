#!/bin/bash

# Make a copy of the original 'factory-version' workflow
cp info.plist info.plist.orig

chmod +x ./BetterDict
chmod +x ./alfred-dict-server
chmod +x ./jq

function deQuarantine {
  # If the extended attribute doesn't exist, don't bother
  # printing the error "No such xattr...", as those messages
  # can be mistaken as "errors".
  xattr -d com.apple.quarantine "$1" 2> /dev/null
}

deQuarantine ./AlfredExtraPane.app
deQuarantine ./alfred-dict-server
deQuarantine ./BetterDict
deQuarantine ./cocoaDialog.app
deQuarantine ./jq

open ./AlfredExtraPane.app

# Kill instances running from previous version of workflow
killall -q alfred-dict-server
