#!/usr/bin/env bash
# Local development only: no credentials, API calls, packaging tools or GUI.
set -euo pipefail
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -n "${PYTHON:-}" ]]; then
    DEV_PYTHON="$PYTHON"
elif command -v python3.12 >/dev/null 2>&1; then
    DEV_PYTHON=python3.12
else
    DEV_PYTHON=python3
fi
"$DEV_PYTHON" -c 'import sys, tkinter; assert sys.version_info >= (3, 10), "Python >=3.10 required"' || {
    printf '%s\n' 'Install Python >=3.10 with venv and Tcl/Tk bindings (for example python3-venv and python3-tk on Debian/Ubuntu).'
    exit 1
}
if [[ ! -x "$REPO_ROOT/.venv/bin/python" ]]; then
    "$DEV_PYTHON" -m venv "$REPO_ROOT/.venv"
fi
"$REPO_ROOT/.venv/bin/python" -c 'import sys, tkinter; assert sys.version_info >= (3, 10), "Recreate .venv with Python >=3.10"'
"$REPO_ROOT/.venv/bin/python" -m pip install --disable-pip-version-check -r "$REPO_ROOT/app/requirements-runtime.txt"
"$REPO_ROOT/.venv/bin/python" -c 'from zoneinfo import ZoneInfo; print("Ready:", ZoneInfo("America/Sao_Paulo"))'
printf '%s\n' "Verify: $REPO_ROOT/.venv/bin/python $REPO_ROOT/scripts/verify.py"
