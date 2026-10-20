from traceback import format_exc

from flask import make_response, render_template, request

from ..dateexpr import EXAMPLES, parse
from ..utils import logger
from .feast_views import *  # FIXME(F403): re-exported for the app's url rules
from .pew_sheet_views import *  # FIXME(F403): re-exported for the app's url rules


def index_view():
    return render_template("index.html")


def acknowledgements_view():
    return render_template("acknowledgements.html")


def internal_error_handler(error):
    logger.exception(error)
    return make_response(render_template("exception.html", error=format_exc()), 500)


def not_found_handler(error):
    return make_response(render_template("404.html", error=error), 404)


def dateexpr_view():
    dexpr = request.args.get("dexpr") or ""
    try:
        date = parse(dexpr) if dexpr else None
        error = None
    except Exception as e:  # FIXME(BLE001): any parse failure is shown to the user
        date = None
        error = repr(e)

    return render_template(
        "dateexpr.html", dexpr=dexpr or "", date=date, error=error, examples=EXAMPLES
    )
