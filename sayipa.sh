#!/bin/bash

ipa=$1
mp3_file="/tmp/ipa.mp3"

curl "https://www.ipaaudio.click/audio" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  --data "{\"ipa\": \"$ipa\"}" \
  -o "$mp3_file"

afplay "$mp3_file"
