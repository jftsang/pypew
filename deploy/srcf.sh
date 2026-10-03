#!/bin/bash
set -eux
files="$(dirname $0)"
bindto="unix:web.sock"

export SERVER_NAME=jmft2.user.srcf.net
export SCRIPT_NAME=/pypew

. /home/jmft2/venvs/py312/bin/activate

cd "$(dirname "$files")"

# `wsgi:app` became `pypew.wsgi:app` in the src/ restructure. The package is
# no longer importable from the repo root alone, so make sure it is installed
# into the venv (e.g. `uv sync --frozen --no-dev` before running this).
exec gunicorn pypew.wsgi:app \
    -w 4 \
    --bind "$bindto" \
    --log-level debug