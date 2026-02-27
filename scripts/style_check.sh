#!/bin/bash

black ./app
flake8 ./app
mypy ./app