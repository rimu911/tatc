#! /bin/bash

cd "$(dirname "$(realpath "${0}")")/.."
echo "Current Working Directory: '$(pwd)'"

[[ -d "$(pwd)/.venv" ]] || python3 -m venv .venv

(
  . "$(pwd)/.venv/bin/activate"
  pip install -r "$(pwd)/requirements.txt"
)