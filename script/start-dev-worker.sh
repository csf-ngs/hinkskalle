#!/bin/bash

SESSION=hink
flask db upgrade
flask rq worker
