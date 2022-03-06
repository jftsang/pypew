import os
from tempfile import NamedTemporaryFile
from urllib.parse import parse_qs, urlencode

import dotenv
import jinja2
from docxtpl import DocxTemplate
from flask import (flash, make_response, redirect, render_template, request,
                   send_file, session, url_for)
from werkzeug.datastructures import ImmutableMultiDict

from filters import filters_context
from forms import PewSheetForm
from models import Service
from utils import logger

__all__ = ['pew_sheet_create_view', 'pew_sheet_clear_history_endpoint', 'pew_sheet_docx_view']

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


def pew_sheet_docx_view():
    form = PewSheetForm(request.args)
    if not form.validate_on_submit():
        flash('Sorry, I could not create a service from that information. Please check the values that you provided.', 'danger')
        for k, es in form.errors.items():
            for e in es:
                flash(f'{k}: {e}', 'danger')
        return redirect(url_for('pew_sheet_create_view') + '?' + urlencode(request.args), 400)

    service = Service.from_form(form)
    doc = DocxTemplate(os.path.join('templates', 'pewSheetTemplate.docx'))
    jinja_env = jinja2.Environment(autoescape=True)
    jinja_env.globals['len'] = len
    jinja_env.filters.update(filters_context)
    doc.render({'service': service}, jinja_env)
    with NamedTemporaryFile() as tf:
        doc.save(tf.name)
        return send_file(
            tf.name, as_attachment=True, attachment_filename='pew_sheet.docx'
        )
