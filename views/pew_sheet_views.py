import os
import uuid
from urllib.parse import parse_qs, urlencode

import dotenv
from flask import (flash, make_response, redirect, render_template, request,
                   send_file, session, url_for)
from werkzeug.datastructures import ImmutableMultiDict

from forms import PewSheetForm, FeastForm
from models import Feast, Service
from utils import cache_dir, logger

__all__ = ['pew_sheet_create_view', 'pew_sheet_clear_history_endpoint', 'pew_sheet_docx_view', 'create_feast']

dotenv.load_dotenv()
COOKIE_NAME = os.environ.get('COOKIE_NAME', 'previousPewSheets')

def create_feast():
    feastForm = FeastForm(request.args)
    print('Into feast creation...')
    Feast.to_yaml(feastForm)
    return make_response('', 204)

def pew_sheet_create_view():
    feastFormFields = ["name", "month", "day", "collect", "introit", "offertory", "tract", "gradual", "alleluia"]
    feastForm = FeastForm(request.args)
    form = PewSheetForm(request.args)
    if not form.primary_feast.data:
        form.primary_feast.data = Feast.next().slug
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
        previous_services=previous_services, feastForm=feastForm, feastFormFields=feastFormFields
    )


def pew_sheet_clear_history_endpoint():
    session[COOKIE_NAME] = {}
    return make_response('', 204)


def pew_sheet_docx_view():
    form = PewSheetForm(request.args)
    if not form.validate_on_submit():
        flash(
            'Sorry, I could not create a service from that information. '
            'Please check the values that you provided.',
            'danger')
        for k, es in form.errors.items():
            for e in es:
                flash(f'{k}: {e}', 'danger')
        return redirect(
            url_for('pew_sheet_create_view') + '?' + urlencode(request.args),
            400)

    service = Service.from_form(form)

    datestamp = service.date.strftime("%Y-%m-%d")

    filename = f'{datestamp} {service.title}.docx'
    temp_docx = os.path.join(cache_dir, f"pew_sheet_{str(uuid.uuid4())}.docx")
    service.create_docx(temp_docx)
    return send_file(
        temp_docx, as_attachment=True, download_name=filename
    )
