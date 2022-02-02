from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, RadioField, DateField
from wtforms.validators import DataRequired

from models import Service


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
