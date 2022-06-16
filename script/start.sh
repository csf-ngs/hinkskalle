#!/bin/bash

BASE_PATH=$(dirname $(readlink -f $0))/..
cd $BASE_PATH

test -e frontend/dist/index.html.subs ||
  cp frontend/dist/index.html frontend/dist/index.html.subs
sed -e "s^%VUE_APP_BACKEND_URL%^$HINKSKALLE_BACKEND_URL^" \
    -e "s^%VUE_APP_ENABLE_REGISTER%^$HINKSKALLE_ENABLE_REGISTER^" \
    -e "s^%VUE_APP_SINGULARITY_COMMAND%^$HINKSKALLE_SINGULARITY_COMMAND^" \
    frontend/dist/index.html.subs > frontend/dist/index.html

SESSION=hink
cd backend
flask db upgrade
gunicorn -u hinkskalle \
  --access-logfile - \
  --error-logfile - \
  --chdir $BASE_PATH/backend \
  -w 4 \
  --timeout 3600 \
  --worker-class gevent \
  --bind 0.0.0.0:5000 \
  wsgi:app
