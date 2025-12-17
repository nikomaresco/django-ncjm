#!/bin/bash

if [ "$1" == "dev" ]; then
    CONFIG_FILE=".docker/ncjm-dev.yml"
else
    CONFIG_FILE=".docker/ncjm-prod.yml"
fi

docker compose -f $CONFIG_FILE up