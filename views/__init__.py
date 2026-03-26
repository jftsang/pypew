from traceback import format_exc

from flask import (make_response, render_template, request)

import dateexpr
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


def dateexpr_view():
    dexpr = request.args.get('dexpr') or ""
    try:
        date = dateexpr.parse(dexpr) if dexpr else None
        error = None
    except Exception as e:
        date = None
        error = repr(e)

    examples = [
        "4th Sunday before Christmas",
        "Epiphany",
        "1st Sunday after 13 days after Christmas",
        "Easter",
        "Easter Monday",
        "17 weeks after Easter",
        "11 November",
        "Remembrance Sunday",
    ]
    return render_template(
        'dateexpr.html',
        dexpr=dexpr or "",
        date=date,
        error=error,
        examples=examples
    )
