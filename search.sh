#!/bin/bash

query="$1"
dict_id="$2"
PORT=6789
IP=127.0.0.1

function is_server_up() {
  pgrep alfred-dict-server > /dev/null
}

function start_server() {
  ./alfred-dict-server \
     --db-path "$alfred_workflow_data/db" \
     --http-payload-size-limit 1000000000 \
     --http-addr "$IP:$PORT" > "$alfred_workflow_data/db.log" 2>&1 & 
}

if ! is_server_up; then
  start_server
fi

search_endpoint="http://$IP:$PORT/indexes/$dict_id/search"
items=$(curl "$search_endpoint" \
        --data "{ \"q\": \"$query\", \"limit\": 9 }" \
        | ./jq '.hits')

echo "{ \"items\": $items }" \
  | 'AlfredExtraPane.app/Contents/Resources/scripts/alfred-extra-pane'
