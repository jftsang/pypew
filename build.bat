pyinstaller -y^
               --paths .^
               --add-data "templates;templates"^
               --add-data "static;static"^
               --add-data "data;data"^
               --icon "static\favicon_io\favicon.ico"^
               pypew.py
