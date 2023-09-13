# PyPew

PyPew is a Flask app that helps you generate pew sheets for services
using texts from the Book of Common Prayer. You can specify the date
of your service, the Feast from which the texts should be used, the
hymns to be sung, as well as other details such as the name of the
priest, and all this information is assembled into a web page or .docx
file for editing or printing.

There is a demonstration deployment at
[https://pypew.herokuapp.com](https://pypew.herokuapp.com) but it is
also possible to run PyPew as a desktop app.


## Running as a Flask app

1. Edit the variables in `.env` to your taste (the defaults should be
   reasonable)
2. Install the requirements: `pip install -r requirements.txt`
3. `python pypew.py`

This should start up the Flask server as well as automatically opening
up your browser to `http://localhost:5000`.


## Packaging

It is also possible to compile binaries for PyPew that can be run
without needing Python to be setup.

### Windows

  1. Set up a Python environment with the required packages: `pip install -r requirements.txt`

  2. `pip install pyinstaller`

  3. Run `build.bat` to create a folder in `dist/pypew`, containing the
     executable `pypew.exe` as well as all the necessary files and DLLs.
     (This is rather large as it includes an entire Python distribution
     as well as packages like Pandas.)

  4. If desired, use [Advanced Installer](https://advancedinstaller.com/)
     to create an .msi that will install PyPew into the 'Program Files'
     directory, together with shortcuts in the Start Menu.

### MacOS

The `build.sh` script runs PyInstaller to build `dist/pypew.app`, which
may then be put into your 'Applications' directory.


## Licensing

PyPew is licensed under the MIT License.

Distributions of the PyPew include extracts from the Book of Common
Prayer. Extracts from The Book of Common Prayer, the rights of which are
vested in the Crown, are reproduced by permission of the Crown's
patentee, Cambridge University Press.

Information about hymns is courtesy of [Hymnary.org](https://hymnary.org).
