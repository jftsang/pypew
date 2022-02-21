from io import StringIO

import pandas as pd
import pandas.errors
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, RadioField, DateField, FileField
from wtforms.validators import DataRequired, StopValidation
from wtforms.widgets import TextArea

from models import Feast, feasts_fields


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
        if set(df.columns) != set(feasts_fields):
            raise StopValidation(f'The CSV is expected to have the field names {feasts_fields}')


class MyForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    selectable_one = SelectField('selectable one', choices=['Foo', 'Bar', 'Baz'])
    selectable_two = SelectField('selectable two', choices=['Foo', 'Bar', 'Baz'])
    radio = RadioField('radio', choices=[(1, 'option 1'), (2, 'option 2')],
                       validators=[DataRequired()])


class PewSheetForm(FlaskForm):
    feast_names = [feast.name for feast in Feast.all()]
    title = StringField('Title', validators=[DataRequired()])
    primary_feast_name = SelectField('Feast', choices=feast_names)
    secondary_feast_name = SelectField('Feast', choices=feast_names)
    date = DateField('Date', validators=[DataRequired()])


class UpdateTextsForm(FlaskForm):
    csv = StringField('CSV', widget=TextArea(), validators=[DataRequired(), IsCsv()])
    xlsx = FileField('Excel')
