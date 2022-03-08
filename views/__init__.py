import os
from tempfile import TemporaryDirectory
from traceback import format_exc

import pandas as pd
from flask import (flash, make_response, render_template, send_file)

from forms import UpdateTextsForm
from models import FEASTS_CSV
from utils import logger
from .feast_views import *
from .pew_sheet_views import *


def index_view():
    return render_template('index.html')


def acknowledgements_view():
    return render_template('acknowledgements.html')


def texts_view():
    form = UpdateTextsForm()

    if form.is_submitted():
        if form.validate():
            with open(FEASTS_CSV, 'w') as f:
                f.write(form.csv.data)
            flash('Texts successfully updated.')

    else:
        try:
            with open(FEASTS_CSV) as f:
                form.csv.data = f.read()
        except FileNotFoundError:
            form.csv.data = ''

    return render_template('texts.html', form=form)


def texts_download_csv_view():
    return send_file(
        FEASTS_CSV, as_attachment=True, attachment_filename='feasts.csv'
    )


def texts_download_xlsx_view():
    with TemporaryDirectory() as td:
        xlsx_path = os.path.join(td, 'tmp.xlsx')
        df = pd.read_csv(FEASTS_CSV)
        df.to_excel(xlsx_path, index=False)
        return send_file(
            xlsx_path, as_attachment=True, attachment_filename='feasts.xlsx'
        )


def internal_error_handler(error):
    logger.exception(error)
    return make_response(render_template('exception.html', error=format_exc()), 500)


def not_found_handler(error):
    return make_response(render_template('404.html', error=error), 404)
