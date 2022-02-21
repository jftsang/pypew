import os
from tempfile import TemporaryDirectory, NamedTemporaryFile

import pandas as pd
from docx2pdf import convert
from flask import (
    render_template, flash, send_file, redirect, url_for, make_response
)

from forms import PewSheetForm, UpdateTextsForm
from models import Feast, PewSheet, NotFoundError, get
from utils import logger

TEXTS_CSV = os.path.join(os.path.dirname(__file__), 'data', 'feasts.csv')


def index_view():
    return render_template('index.html', nav_active='Home')


def feast_index_view():
    feasts = Feast.all()
    return render_template(
        'feasts.html', nav_active='Feasts', feasts=feasts
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
    form = PewSheetForm()
    pew_sheet = None

    if form.validate_on_submit():
        feast = Feast.get(name=form.feast_name.data)
        pew_sheet = PewSheet(feast=feast, title=form.title.data)

    return render_template(
        'pewSheet.html',
        nav_active='Pew Sheets',
        form=form,
        pew_sheet=pew_sheet,
    )


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

    return render_template('texts.html', form=form, nav_active='Texts')


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
    return make_response(render_template('404.html'), 404)
