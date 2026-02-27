#!/bin/bash

# Prompting user to choose build environment (docker / podman)
echo "- Build environment: podman (1,default), docker (2)"
read -p "... " command_id
if [[ "${command_id}" == "2" ]]; then
  command=docker
else
  command=podman
fi

# Prompting user to choose build tag
echo "- Build tag: 21id_bot:latest (1,default), ghcr.io/21id/bot:latest-manual (2), ghcr.io/21id/bot:latest (3)"
read -p "... " tag_id
if [[ "${tag_id}" == "2" ]]; then
  tag=ghcr.io/21id/bot:latest-manual
elif [[ "${tag_id}" == "3" ]]; then
  tag=ghcr.io/21id/bot:latest
else
  tag=21id_bot:latest
fi

# Building image for linux/amd64 (as set in Dockerfile)
${command} build -t ${tag} .

# If tag with GHCR is chosen - ask if user want to push it
if [[ "${tag_id}" == "2" || "${tag_id}" == "3" ]]; then
  echo "- Push? N (default) / Y"
  read -p "... " push
  if [[ "${push}" == "y" || "${push}" == "Y" ]]; then
    ${command} push ${tag}
    echo "Pushed succesfully!"
  fi
fi