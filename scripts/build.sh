#! /bin/bash

cd "$(dirname "$(realpath "${0}")")/.."
echo "Current Working Directory: '$(pwd)'"

[[ -d "$(pwd)/.venv" ]] || python -m venv .venv
[[ -d "$(pwd)/dist" ]] && rm -rfv "$(pwd)/dist"

(
  . "$(pwd)/.venv/bin/activate"
  pip install -r "$(pwd)/requirements.txt"
  pyinstaller --clean --onefile --name "tatc" --collect-data "emoji" main.py
)

cp -v "$(pwd)/LICENSE.txt" "$(pwd)/dist"
cp -v "$(pwd)/README.md" "$(pwd)/dist"
cp -rv "$(pwd)/examples" "$(pwd)/dist"
cp -rv "$(pwd)/resources" "$(pwd)/dist"
