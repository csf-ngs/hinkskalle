#!/bin/bash

if [ "$1" = "--rebuild" ]; then
  rm -rf node_modules
  yarn install
fi
yarn serve
