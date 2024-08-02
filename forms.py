from flask import request
from flask_wtf import FlaskForm
from wtforms import DateField, HiddenField, SelectField, SelectMultipleField, \
    StringField
from wtforms import (
    TimeField,
)
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea

from models import Feast, Music
from utils import logger

hymns = [('', 'None')] + [(h.ref, f'{h.ref} - {h.title}') for h in
                          Music.neh_hymns()]

translations = [('', 'None')] + [(h.translation, f'{h.translation}') for h in
                          Music.neh_hymns()]


class PewSheetForm(FlaskForm):
    title = HiddenField('Title')
    feasts = Feast.upcoming()
    feast_choices = [(feast.slug, feast.name) for feast in feasts]
    primary_feast = SelectField(
        'Primary Feast',
        choices=feast_choices,
    )
    secondary_feasts = SelectMultipleField(
        'Secondary Feasts',
        choices=[('', '')] + feast_choices,
    )
    date = DateField('Date', validators=[DataRequired()])
    time = TimeField('Time', validators=[DataRequired()])
    celebrant = StringField('Celebrant')
    preacher = StringField('Preacher')

    introit_hymn = SelectField('Introit Hymn', choices=hymns)
    offertory_hymn = SelectField('Offertory Hymn', choices=hymns)
    recessional_hymn = SelectField('Recessional Hymn', choices=hymns)

    anthem_title = StringField('Anthem')
    anthem_composer = StringField('Anthem composer')
    anthem_lyrics = StringField('Anthem lyrics', widget=TextArea())
    anthem_translation = SelectField('Anthem Translation', choices=translations)

    class Meta:
        csrf = False

    # https://discord.com/channels/531221516914917387/590290790241009673/948217938459107339
    def is_submitted(self):
        return bool(request.args)
