#! /bin/bash

cd "$(dirname "$(realpath "${0}")")/.."
echo "Current Working Directory: '$(pwd)'"

[[ -d "$(pwd)/.venv" ]] || python -m venv .venv

(
  source . "$(pwd)/.venv/bin/activate"
  pip install -r "$(pwd)/requirements.txt"
  pyinstaller --clean "$(pwd)/tatc.spec"
)

# copy LICENSE file
cp -v "$(pwd)/LICENSE.txt" "$(pwd)/dist"

# copy README.md file
cp -v "$(pwd)/README.md" "$(pwd)/dist"

# copy all necessary standard files
cp -v "$(pwd)/examples/"* "$(pwd)/dist"