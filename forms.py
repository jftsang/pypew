from io import StringIO

import pandas as pd
import pandas.errors
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, RadioField, DateField, FileField
from wtforms.validators import DataRequired, StopValidation
from wtforms.widgets import TextArea

from models import Service


class IsCsv:
    def __init__(self):
        self.field_flags = {"required": True}

    def __call__(self, form, field):
        """Checks that the submitted text is valid csv."""
        try:
            pd.read_csv(StringIO(field.data))
        except pandas.errors.ParserError:
            field.errors[:] = []
            raise StopValidation("This needs to be valid CSV.")


class MyForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    selectable_one = SelectField('selectable one', choices=['Foo', 'Bar', 'Baz'])
    selectable_two = SelectField('selectable two', choices=['Foo', 'Bar', 'Baz'])
    radio = RadioField('radio', choices=[(1, 'option 1'), (2, 'option 2')],
                       validators=[DataRequired()])


class PewSheetForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    service_name = SelectField('Service', choices=[s.name for s in Service.all()])
    date = DateField('Date', validators=[DataRequired()])


class UpdateTextsForm(FlaskForm):
    csv = StringField('CSV', widget=TextArea(), validators=[DataRequired(), IsCsv()])
    xlsx = FileField('Excel')
