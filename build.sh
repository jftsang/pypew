#!/bin/bash
set -eux
pyinstaller -w -F -y \
               --add-data "templates:templates" \
               --add-data "static:static" \
               --add-data "data:data" \
               --icon "pypew.icns" \
               pypew.py
