import json
import os
from time import time
from urllib.parse import urlencode

import dotenv
from flask import (make_response, render_template, request)
from werkzeug.datastructures import ImmutableMultiDict

from forms import PewSheetForm
from models import Service
from utils import logger

__all__ = ['pew_sheet_create_view', 'pew_sheet_clear_history_endpoint']

dotenv.load_dotenv()
COOKIE_NAME = os.environ.get('COOKIE_NAME', 'previousPewSheets')


def pew_sheet_create_view():
    form = PewSheetForm(request.args)

    service = None

    # Update the history of previous services before creating the
    # response, so that the newly created service gets displayed.
    # However, this history needs to be generated anyway even if no
    # service was generated (either because no data was given or because
    # validation failed).
    if form.validate_on_submit():
        service = Service.from_form(form)

    try:
        hist = json.loads(request.cookies.get(COOKIE_NAME))
    except Exception as exc:
        logger.warning(exc)
        hist = []

    previous_services = []
    for x in hist:
        try:
            args = ImmutableMultiDict(x['args'])
            previous_service = Service.from_form(PewSheetForm(args))
            # Don't duplicate the current service, but make sure it's always at
            # the top
            if previous_service != service:
                previous_services.append((urlencode(args), previous_service))
        except Exception as exc:
            logger.warning(exc)
            pass

    if service is not None:
        hist.append({
            'timestamp': time(),
            'args': request.args,
        })
        previous_services.append((urlencode(request.args), service))

        resp = make_response(render_template(
            'pewSheet.html', form=form, service=service,
            previous_services=previous_services[::-1],
            cookie_name=COOKIE_NAME
        ))
        resp.set_cookie(COOKIE_NAME, json.dumps(hist), secure=True)
        return resp

    else:
        return render_template(
            'pewSheet.html', form=form, service=service,
            previous_services=previous_services[::-1],
            cookie_name = COOKIE_NAME
        )


def pew_sheet_clear_history_endpoint():
    resp = make_response('', 204)
    resp.set_cookie(COOKIE_NAME, '')
    return resp
