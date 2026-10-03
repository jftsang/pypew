# PyPew

PyPew is a Flask app that helps you generate pew sheets for services
using texts from the Book of Common Prayer. You can specify the date
of your service, the Feast from which the texts should be used, the
hymns to be sung, as well as other details such as the name of the
priest, and all this information is assembled into a web page or .docx
file for editing or printing.

There is a demonstration deployment at <https://jmft2.user.srcf.net/pypew/>
but it is also possible to run PyPew as a desktop app.


## Running as a Flask app

The project uses [uv](https://docs.astral.sh/uv/) for dependency
management. Requires Python 3.12 or later.

1. Edit the variables in `.env` to your taste (the defaults should be
   reasonable)
2. Install the dependencies: `uv sync`
3. `uv run pypew`

This should start up the Flask server as well as automatically opening
up your browser to `http://localhost:5000`.

Add `--debug` to run in Flask debug mode, or `--no-launch` to suppress
opening the browser.

Alternatively, `uv run python -m pypew` works the same way, and
`uv run gunicorn pypew.wsgi:app` serves it under gunicorn.


## Development

```
uv sync                        # install runtime + dev dependencies
uv run pypew --debug           # run from a source checkout
uv run python -m unittest      # run the test suite
uv run ruff check .            # lint
uv run ruff format .           # format
uv build                       # build a wheel and sdist
```

The package lives in `src/pypew/`, with the feast data, templates and
static files bundled inside it. `scripts/` holds development helper
scripts that are not part of the installed package; install their extra
with `uv sync --extra scripts` if you need them.


## Packaging

It is also possible to compile binaries for PyPew that can be run
without needing Python to be setup.

### Windows

  1. Set up the build environment: `uv sync --group build`

  2. Run `build.bat` to create a folder in `dist/pypew`, containing the
     executable `pypew.exe` as well as all the necessary files and DLLs.
     (This is rather large as it includes an entire Python distribution
     as well as packages like Pandas.)

  4. If desired, use [Advanced Installer](https://advancedinstaller.com/)
     to create an .msi that will install PyPew into the 'Program Files'
     directory, together with shortcuts in the Start Menu.

### MacOS

The `build.sh` script runs PyInstaller to build `dist/pypew.app`, which
may then be put into your 'Applications' directory.


## Deploying

`src/pypew/wsgi.py` exposes the WSGI application as `app`, suitable for
`gunicorn pypew.wsgi:app`. See `deploy/srcf.sh` for the deployment used
by the demonstration instance.


## Licensing

PyPew is licensed under the MIT License.

Distributions of the PyPew include extracts from the Book of Common
Prayer. Extracts from The Book of Common Prayer, the rights of which are
vested in the Crown, are reproduced by permission of the Crown's
patentee, Cambridge University Press.

Information about hymns is courtesy of [Hymnary.org](https://hymnary.org).
