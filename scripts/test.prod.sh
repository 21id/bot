#!/bin/bash

# checking if there is .env file
if [ ! -f "prod.env" ]; then
  echo "There is no prod.env file in current folder."
  echo "You can passthrough env variables, but you should create prod.env file";
  exit 2
fi

# get all variables from .env
set -e
export $(grep -v '^#' prod.env | xargs)
export MONGO_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@${MONGO_HOSTS}/${MONGO_DB_NAME}${MONGO_OPTIONS}

# - - Setting container environment - -
echo "Run environment: podman(1,default), docker(2)"
read -p "... " command_id
if [ "${command_id}" -eq 2 ]; then
  command=docker
else
  command=podman
fi

# Building Docker image and setting
${command} build --tag 21id-bot:latest-local .

# Starting up Docker/Podman Compose with all components
compose_dir=./materials/docker-compose.prod.yaml
${command} compose -f "${compose_dir}" up -d
