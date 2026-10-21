#!/bin/bash

# Usage:
#   scripts/test.sh                       - all tests
#   scripts/test.sh unit | integration    - one suite (integration needs Docker)
#   scripts/test.sh infrastructure/s21    - tests matching a module path
#   scripts/test.sh -k verification       - any other args are passed to pytest

# Running from repo root, so app package and pyproject.toml are found
cd "$(dirname "$0")/.." || exit 2
python=${PYTHON:-python3}

if [[ $# -eq 0 ]]; then
  args=()
elif [[ "$1" == "unit" || "$1" == "integration" ]]; then
  args=(-m "$1" "${@:2}")
elif [[ "$1" != -* ]]; then
  # Module path: app/tests/unit/<path>*.py or app/tests/integration/<path>*.py
  target=${1#app/tests/}
  target=${target#unit/}
  target=${target#integration/}
  dir=$(dirname "${target}")
  name=$(basename "${target}" .py)
  matches=()
  for suite in unit integration; do
    for file in app/tests/${suite}/${dir}/test_${name}*.py app/tests/${suite}/${target}; do
      [[ -e "${file}" ]] && matches+=("${file}")
    done
  done
  if [[ ${#matches[@]} -eq 0 ]]; then
    # Not a path - treating it as a keyword
    args=(-k "$1" "${@:2}")
  else
    args=("${matches[@]}" "${@:2}")
  fi
else
  args=("$@")
fi

${python} -m pytest -q "${args[@]}"
exit $?
