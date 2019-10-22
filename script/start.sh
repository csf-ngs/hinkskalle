#!/bin/bash

SESSION=hink
cd /srv/hinkskalle/src/backend
source hink.env
flask run -h 0.0.0.0 --reload --no-debugger
