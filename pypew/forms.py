from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, RadioField
from wtforms.validators import DataRequired


class MyForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    selectable_one = SelectField('selectable one', choices=['Foo', 'Bar', 'Baz'])
    selectable_two = SelectField('selectable two', choices=['Foo', 'Bar', 'Baz'])
    radio = RadioField('radio', choices=[(1, 'option 1'), (2, 'option 2')],
                       validators=[DataRequired()])
