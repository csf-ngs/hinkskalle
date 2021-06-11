#!/bin/bash

SESSION=hink
flask db upgrade
flask run -h 0.0.0.0 --reload --no-debugger
