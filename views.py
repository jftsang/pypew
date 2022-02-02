import os
from tempfile import TemporaryDirectory, NamedTemporaryFile

from docx2pdf import convert
from flask import (
    render_template, flash, send_file, redirect, url_for, make_response
)

from forms import MyForm, PewSheetForm
from models import Service, Extract, PewSheet
from utils import logger


def index_view():
    form = MyForm()
    if form.validate_on_submit():
        flash(f"Hello, {form.name.data}, you selected "
              f"{form.selectable_one.data} and {form.selectable_two.data} "
              f"and option {form.radio.data}")

    return render_template('index.html', nav_active='Home', form=form)


def service_index_view():
    services = Service.all()
    return render_template(
        'services.html', nav_active='Services', services=services
    )


def service_detail_view(name, **kwargs):
    try:
        service = Service.get(name=name)
    except Service.NotFoundError:
        flash(f'Service {name} not found.')
        return make_response(service_index_view(), 404)

    return render_template(
        'serviceDetails.html', service=service, Extract=Extract, **kwargs
    )


def pew_sheet_create_view():
    form = PewSheetForm()
    pew_sheet = None

    if form.validate_on_submit():
        service = Service.get(name=form.service_name.data)
        pew_sheet = PewSheet(service=service, title=form.title.data)

    return render_template(
        'pewSheet.html',
        nav_active='Pew Sheets',
        form=form,
        pew_sheet=pew_sheet,
    )


def service_docx_view(name):
    filename = f'{name}.docx'
    try:
        service = Service.get(name=name)
    except Service.NotFoundError:
        flash(f'Service {name} not found.')
        return make_response(service_index_view(), 404)

    with NamedTemporaryFile() as tf:
        service.create_docx(path=tf.name)
        return send_file(
            tf.name, as_attachment=True, attachment_filename=filename
        )


def service_pdf_view(name):
    filename = f'{name}.pdf'
    try:
        service = Service.get(name=name)
    except Service.NotFoundError:
        flash(f'Service {name} not found.')
        return make_response(service_index_view(), 404)

    with TemporaryDirectory() as td:
        docx_path = os.path.join(td, 'tmp.docx')
        service.create_docx(path=docx_path)

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
            return redirect(url_for('service_detail_view', name=name), 302)


def internal_error_handler(error):
    logger.exception(error)
    return make_response(render_template('exception.html', error=error), 500)
