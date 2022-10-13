#!/bin/bash

if [ "$1" = "--rebuild" -o ! -e "node_modules" ]; then
  rm -rf node_modules
  yarn install
fi

JSON_STRING='window.configs = { \
  "VUE_APP_BACKEND_URL": "'$HINKSKALLE_BACKEND_URL'" \
}'

sed "s@// RUNTIME_CONFIG@${JSON_STRING}@" public/index.html.tpl > public/index.html

yarn build --watch
