#!/usr/bin/env sh
set -eu

if [ -n "${PYTHON:-}" ]; then
    PYTHON_BIN="$PYTHON"
elif [ -x "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
elif [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    PYTHON_BIN="python3"
fi

"$PYTHON_BIN" -m pytest test/unit
"$PYTHON_BIN" -m coverage erase
"$PYTHON_BIN" -m coverage run -m pytest test/unit
"$PYTHON_BIN" -m coverage report -m smartusbhub.py
