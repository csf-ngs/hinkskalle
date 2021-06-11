#!/bin/bash

cd backend/
SESSION=hink
flask db upgrade
flask rq worker
