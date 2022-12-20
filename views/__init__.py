import os
from tempfile import TemporaryDirectory
from traceback import format_exc

import pandas as pd
from flask import (flash, make_response, render_template, send_file)

from forms import UpdateTextsForm
from models import FEASTS_CSV
from utils import logger
from .feast_views import *
from .pew_sheet_views import *


def index_view():
    return render_template('index.html')


def acknowledgements_view():
    return render_template('acknowledgements.html')


def internal_error_handler(error):
    logger.exception(error)
    return make_response(render_template('exception.html', error=format_exc()), 500)


def not_found_handler(error):
    return make_response(render_template('404.html', error=error), 404)
