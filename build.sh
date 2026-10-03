#!/bin/bash
set -eux
pyinstaller -w -F -y \
               --paths "src" \
               --add-data "src/pypew/templates:pypew/templates" \
               --add-data "src/pypew/static:pypew/static" \
               --add-data "src/pypew/data:pypew/data" \
               --icon "pypew.icns" \
               src/pypew/__main__.py