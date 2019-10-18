#!/bin/bash

SESSION=hink
cd /srv/backend
flask run -h 0.0.0.0 --reload --no-debugger
