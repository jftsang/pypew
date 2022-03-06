import json
import os
from time import time
from urllib.parse import parse_qs, urlencode

import dotenv
from flask import (make_response, render_template, request, session)
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

    if form.validate_on_submit():
        service = Service.from_form(form)

    stored_history = session.get(COOKIE_NAME, [])
    stored_history = set(stored_history)  # drop duplicates
    if service is not None:
        stored_history.add(urlencode(request.args))

    # Update the stored history (might not have changed if the service
    # creation was unsuccessful). Session data must be JSON
    # serializable, so convert back to a list
    stored_history = list(stored_history)

    session[COOKIE_NAME] = stored_history

    previous_services = []
    for x in stored_history:
        try:
            args = ImmutableMultiDict(parse_qs(x, keep_blank_values=True))
            previous_service = Service.from_form(PewSheetForm(args))
            previous_services.append((urlencode(args), previous_service))
        except Exception as exc:
            logger.warning(exc)
            pass

    previous_services.sort(key=lambda args_service: args_service[1].date)

    return render_template(
        'pewSheet.html', form=form, service=service,
        previous_services=previous_services
    )


def pew_sheet_clear_history_endpoint():
    session[COOKIE_NAME] = {}
    return make_response('', 204)
