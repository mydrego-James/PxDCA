#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"

if command -v python3.13 >/dev/null 2>&1; then
  PYTHON=python3.13
elif command -v python3.12 >/dev/null 2>&1; then
  PYTHON=python3.12
else
  echo "[ERROR] PxDCA requires Python 3.12 or 3.13." >&2
  exit 1
fi

exec "$PYTHON" scripts/bootstrap.py
