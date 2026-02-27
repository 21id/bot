#!/bin/bash

# checking if there is .env file
if [ ! -f "dev.env" ]; then
  echo "There is no dev.env file in current folder."
  echo "You can passthrough env variables, but you should create dev.env file";
  exit 2
fi

# get all variables from .env
set -e
export $(grep -v '^#' dev.env | xargs)
export MONGO_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@${MONGO_HOSTS}/${MONGO_DB_NAME}${MONGO_OPTIONS}

echo "Run environment: podman(1,default), docker(2)"
read -p "... " command_id
if [ "${command_id}" -eq 2 ]; then
  command=docker
else
  command=podman
fi

${command} compose -f ./materials/docker-compose.dev.yaml up -d

python3 -m app