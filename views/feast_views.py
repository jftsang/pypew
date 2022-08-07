import os
from tempfile import NamedTemporaryFile, TemporaryDirectory

import datetime as dt
from typing import Optional

import cattrs
from docx2pdf import convert
from flask import (flash, make_response, redirect, render_template, send_file,
                   url_for, request, jsonify)

from filters import english_date
from models import Feast
from models_base import NotFoundError, get
from utils import logger, str2date

__all__ = ['feast_index_view', 'feast_index_api', 'feast_date_api',
           'feast_upcoming_api', 'feast_detail_view', 'feast_detail_api',
           'feast_docx_view', 'feast_pdf_view']


def feast_index_view():
    feasts = Feast.all()
    return render_template(
        'feasts.html', feasts=feasts
    )


def feast_index_api():
    feasts = Feast.all()
    return jsonify(cattrs.unstructure(feasts))


def feast_upcoming_api():
    """API to get a list of upcoming feasts relative to the specified
    date, with the soonest first.
    """
    s = request.args.get('date')
    try:
        date = str2date(s)
    except ValueError:
        return make_response(f'Bad date {s}', 400)

    def none2datemax(d: Optional[dt.date]) -> dt.date:
        """Put unspecified dates at the end of the list."""
        if d is None:
            return dt.date.max
        return d

    sorted_feasts = sorted(enumerate(Feast.all()),
                           key=lambda nf: none2datemax(nf[1].get_next_date(date)))
    return jsonify([{
        'index': n, 'name': f.name, 'next': english_date(f.get_next_date(date))
    } for n, f in sorted_feasts])


def feast_date_api(name):
    try:
        year = request.args.get('year')
        feast = Feast.get(name=name)
        return jsonify(feast.get_date(year=year))
    except NotFoundError:
        return make_response(f"Feast {name} not found", 404)


def feast_detail_view(name):
    try:
        feasts = Feast.all()
        feast = get(feasts, name=name)
    except NotFoundError:
        flash(f'Feast {name} not found.')
        return make_response(feast_index_view(), 404)

    return render_template('feastDetails.html', feast=feast, feasts=feasts)


def feast_detail_api(name):
    try:
        feasts = Feast.all()
        feast = get(feasts, name=name)
    except NotFoundError:
        flash(f'Feast {name} not found.')
        return make_response(feast_index_view(), 404)

    return jsonify(cattrs.unstructure(feast))


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
