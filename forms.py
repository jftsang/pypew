from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, HiddenField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea

from models import Feast, Music

hymns = [('', 'None')] + [(h.ref, h.title) for h in Music.neh_hymns()]


class PewSheetForm(FlaskForm):
    feast_names = [feast.name for feast in Feast.all()]
    title = HiddenField('Title')
    primary_feast_name = SelectField('Primary Feast', choices=feast_names)
    secondary_feast_name = SelectField('Secondary Feast',
                                       choices=[''] + feast_names)
    date = DateField('Date', validators=[DataRequired()])
    celebrant = StringField('Celebrant')
    preacher = StringField('Preacher')

    introit_hymn = SelectField('Introit Hymn', choices=hymns)
    offertory_hymn = SelectField('Offertory Hymn', choices=hymns)
    recessional_hymn = SelectField('Recessional Hymn', choices=hymns)

    anthem_title = StringField('Anthem')
    anthem_composer = StringField('Anthem composer')
    anthem_lyrics = StringField('Anthem lyrics', widget=TextArea())

    class Meta:
        csrf = False

    # https://discord.com/channels/531221516914917387/590290790241009673/948217938459107339
    def is_submitted(self):
        return bool(request.args)
