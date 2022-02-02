#!/bin/bash
set -eux
pyinstaller -F --add-data "templates:templates" \
               --add-data "static:static" \
               --add-data "data:data" \
               pypew.py
