#!/bin/bash

cd backend/
SESSION=hink
flask rq worker
