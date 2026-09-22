#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  ./install.sh
fi

if ! .venv/bin/python -c "import fastmcp, jsonschema, sys; assert (3, 12) <= sys.version_info[:2] < (3, 14); assert fastmcp.__version__ == '3.4.7'" >/dev/null 2>&1; then
  ./install.sh
fi

if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export PYTHONPATH="$PWD"
exec .venv/bin/python -m server.fastmcp_service
