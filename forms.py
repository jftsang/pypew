from io import StringIO
from unittest import TestCase

import pandas as pd
import pandas.errors
from attr import fields
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, FileField
from wtforms.validators import DataRequired, StopValidation
from wtforms.widgets import TextArea

from models import Feast


class IsCsv:
    def __init__(self):
        self.field_flags = {"required": True}

    def __call__(self, form, field):
        """Checks that the submitted text is valid csv and that the
        expected columns are present."""
        try:
            df = pd.read_csv(StringIO(field.data))
        except pandas.errors.ParserError:
            field.errors[:] = []
            raise StopValidation("This needs to be valid CSV.")

        expected_columns = {f.name for f in fields(Feast)}
        try:
                TestCase().assertSetEqual(set(df.columns), expected_columns)
        except AssertionError as exc:
            raise StopValidation(f'The CSV is expected to have the field names {expected_columns} but you provided {set(df.columns)}. {exc}')


class PewSheetForm(FlaskForm):
    feast_names = [feast.name for feast in Feast.all()]
    title = StringField('Title', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    celebrant = StringField('Celebrant')
    preacher = StringField('Preacher')
    primary_feast_name = SelectField('Primary Feast', choices=feast_names)
    secondary_feast_name = SelectField('Secondary Feast', choices=[''] + feast_names)
    anthem_title = StringField('Anthem')
    anthem_composer = StringField('Anthem composer')
    anthem_lyrics = StringField('Anthem lyrics', widget=TextArea())


class UpdateTextsForm(FlaskForm):
    csv = StringField('CSV', widget=TextArea(), validators=[DataRequired(), IsCsv()])
    xlsx = FileField('Excel')
