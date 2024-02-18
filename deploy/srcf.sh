#!/bin/bash
set -eux
files="$(dirname $0)"
bindto="unix:web.sock"

export SERVER_NAME=jmft2.user.srcf.net
export SCRIPT_NAME=/pypew

. /home/jmft2/venvs/py38/bin/activate

cd "$(dirname "$files")"
exec gunicorn wsgi:app \
    -w 4 \
    --bind "$bindto" \
    --log-level debug
