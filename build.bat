:: Build directory
pyinstaller^
    -y^
    --paths .^
    --add-data "templates;templates"^
    --add-data "static;static"^
    --add-data "data;data"^
    --icon "static\favicon_io\favicon.ico"^
    pypew.py

:: Build single executable
pyinstaller^
    -y^
    --onefile^
    --paths .^
    --add-data "templates;templates"^
    --add-data "static;static"^
    --add-data "data;data"^
    --icon "static\favicon_io\favicon.ico"^
    pypew.py
