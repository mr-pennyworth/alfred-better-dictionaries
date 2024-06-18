#!/bin/bash

ipa=$1
mp3_file="/tmp/ipa.mp3"

curl 'https://iawll6of90.execute-api.us-east-1.amazonaws.com/production' \
  -X POST \
  --data-raw "{\"text\":\"$ipa\", \"voice\":\"Salli\"}" \
  -o /tmp/b64ipa

python3 -c "print($(cat /tmp/b64ipa))" | \
  base64 --decode --input - -o "$mp3_file"

afplay "$mp3_file"
