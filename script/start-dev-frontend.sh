#!/bin/bash

if [ "$1" = "--rebuild" -o ! -e "node_modules" ]; then
  rm -rf node_modules
  yarn install
fi

JSON_STRING='window.configs = { \
  "VUE_APP_BACKEND_URL": "'$VUE_APP_BACKEND_URL'", \
  "VUE_APP_ENABLE_REGISTER": '$VUE_APP_ENABLE_REGISTER' \
}'

sed "s@// RUNTIME_CONFIG@${JSON_STRING}@" public/index.html.tpl > public/index.html

yarn build --watch
