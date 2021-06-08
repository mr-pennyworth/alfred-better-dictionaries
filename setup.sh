#!/bin/bash

# Make a copy of the original 'factory-version' workflow
cp info.plist info.plist.orig

chmod +x ./jq
chmod +x ./alfred-dict-server

xattr -d com.apple.quarantine ./AlfredExtraPane.app
xattr -d com.apple.quarantine ./alfred-dict-server
xattr -d com.apple.quarantine ./BetterDict.app
xattr -d com.apple.quarantine ./jq

open ./AlfredExtraPane.app

# Kill instances running from previous version of workflow
killall alfred-dict-server

open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
osascript <<END
  tell application "System Preferences"
    activate
  end tell
END
