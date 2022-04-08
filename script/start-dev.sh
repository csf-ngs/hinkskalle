#!/bin/bash

SESSION=hink
flask db upgrade

# can't use dev server because of weird problems
# with draining request data if it is not read
# in the route handler
# see https://github.com/pallets/flask/issues/2188
# see https://github.com/pallets/werkzeug/issues/2380
# see https://github.com/pallets/flask/issues/4523
# etc etc
# causes the oci conformance tests to fail
#flask run -h 0.0.0.0 --reload --no-debugger
gunicorn -u hinkskalle \
  --access-logfile - \
  --error-logfile - \
  --chdir /srv/hinkskalle/src/backend \
  -w 1 \
  --bind 0.0.0.0:5000 \
  --reload \
  wsgi:app
