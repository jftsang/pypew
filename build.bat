:: Build directory
pyinstaller^
    -y^
    --paths src^
    --add-data "src\pypew\templates;pypew\templates"^
    --add-data "src\pypew\static;pypew\static"^
    --add-data "src\pypew\data;pypew\data"^
    --icon "src\pypew\static\favicon_io\favicon.ico"^
    src\pypew\__main__.py

:: Build single executable
pyinstaller^
    -y^
    --onefile^
    --paths src^
    --add-data "src\pypew\templates;pypew\templates"^
    --add-data "src\pypew\static;pypew\static"^
    --add-data "src\pypew\data;pypew\data"^
    --icon "src\pypew\static\favicon_io\favicon.ico"^
    src\pypew\__main__.py