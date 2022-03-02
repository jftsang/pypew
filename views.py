import json
import logging
import os
from tempfile import NamedTemporaryFile, TemporaryDirectory
from time import time
from typing import List
from urllib.parse import urlencode

import pandas as pd
from docx2pdf import convert
from flask import (flash, make_response, redirect, render_template, request,
                   send_file, url_for)
from werkzeug.datastructures import ImmutableMultiDict

from forms import PewSheetForm, UpdateTextsForm
from models import Feast, Music, NotFoundError, Service, get
from utils import logger

TEXTS_CSV = os.path.join(os.path.dirname(__file__), 'data', 'feasts.csv')

COOKIE_NAME = 'previousPewSheets'

def index_view():
    return render_template('index.html')


def feast_index_view():
    feasts = Feast.all()
    return render_template(
        'feasts.html', feasts=feasts
    )


def feast_detail_view(name, **kwargs):
    try:
        feasts = Feast.all()
        feast = get(feasts, name=name)
    except NotFoundError:
        flash(f'Feast {name} not found.')
        return make_response(feast_index_view(), 404)

    return render_template('feastDetails.html', feast=feast, feasts=feasts, **kwargs)


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
        resp.set_cookie(COOKIE_NAME, json.dumps(hist))
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


def feast_docx_view(name):
    filename = f'{name}.docx'
    try:
        feast = Feast.get(name=name)
    except Feast.NotFoundError:
        flash(f'Feast {name} not found.')
        return make_response(feast_index_view(), 404)

    with NamedTemporaryFile() as tf:
        feast.create_docx(path=tf.name)
        return send_file(
            tf.name, as_attachment=True, attachment_filename=filename
        )


def feast_pdf_view(name):
    filename = f'{name}.pdf'
    try:
        feast = Feast.get(name=name)
    except Feast.NotFoundError:
        flash(f'Feast {name} not found.')
        return make_response(feast_index_view(), 404)

    with TemporaryDirectory() as td:
        docx_path = os.path.join(td, 'tmp.docx')
        feast.create_docx(path=docx_path)

        pdf_path = os.path.join(td, 'tmp.pdf')
        try:
            # Note that convert() may fail silently:
            # https://github.com/AlJohri/docx2pdf/issues/56
            # https://github.com/AlJohri/docx2pdf/pull/57
            convert(docx_path, pdf_path)
            return send_file(
                pdf_path, as_attachment=True, attachment_filename=filename
            )
        except Exception as exc:
            logger.exception(exc)
            flash(
                'Conversion from DOCX to PDF was unsuccessful. '
                'Try downloading the .docx version instead. '
                'The server reported:',
                'warning'
            )
            flash(str(exc), 'danger')
            return redirect(url_for('feast_detail_view', name=name), 302)


def texts_view():
    form = UpdateTextsForm()

    if form.is_submitted():
        if form.validate():
            with open(TEXTS_CSV, 'w') as f:
                f.write(form.csv.data)
            flash('Texts successfully updated.')

    else:
        try:
            with open(TEXTS_CSV) as f:
                form.csv.data = f.read()
        except FileNotFoundError:
            form.csv.data = ''

    return render_template('texts.html', form=form)


def texts_download_csv_view():
    return send_file(
        TEXTS_CSV, as_attachment=True, attachment_filename='feasts.csv'
    )


def texts_download_xlsx_view():
    with TemporaryDirectory() as td:
        xlsx_path = os.path.join(td, 'tmp.xlsx')
        df = pd.read_csv(TEXTS_CSV)
        df.to_excel(xlsx_path, index=False)
        return send_file(
            xlsx_path, as_attachment=True, attachment_filename='feasts.xlsx'
        )


def internal_error_handler(error):
    logger.exception(error)
    return make_response(render_template('exception.html', error=error), 500)


def not_found_handler(error):
    return make_response(render_template('404.html', error=error), 404)
