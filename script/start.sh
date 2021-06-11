#!/bin/bash

test -e frontend/dist/index.html.subs ||
  cp frontend/dist/index.html frontend/dist/index.html.subs
sed -e "s^%VUE_APP_BACKEND_URL%^$BACKEND_URL^" \
    -e "s^%VUE_APP_ENABLE_REGISTER%^$ENABLE_REGISTER^" \
    frontend/dist/index.html.subs > frontend/dist/index.html

SESSION=hink
cd backend
flask db upgrade
gunicorn -u hinkskalle \
  --access-logfile - \
  --error-logfile - \
  --chdir /srv/hinkskalle/backend \
  -w 4 \
  --timeout 3600 \
  --worker-class gevent \
  --bind 0.0.0.0:5000 \
  wsgi:app
