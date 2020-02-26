#!/bin/bash

docker-compose exec api bash -c 'cd backend && source hink.env && python3 -m unittest discover -s Hinkskalle/tests'
