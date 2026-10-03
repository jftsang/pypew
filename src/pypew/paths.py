"""Resource locations.

Everything the app reads at runtime lives inside the package directory, so
the same code works from a source checkout, an installed wheel, and a
PyInstaller onefile bundle.
"""

import sys
from pathlib import Path


def base_dir() -> Path:
    """Directory holding the bundled data, templates and static files.

    PyInstaller extracts a onefile bundle into a temporary directory and
    rebases the bundled resources underneath it, so that is the base there.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        return Path(meipass) / "pypew"
    return Path(__file__).parent


BASE_DIR = base_dir()
DATA_DIR = BASE_DIR / "data"
FEASTS_DIR = DATA_DIR / "feasts"
NEH_CSV = DATA_DIR / "neh.csv"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
PEW_SHEET_TEMPLATE = TEMPLATES_DIR / "pewSheetTemplate.docx"
