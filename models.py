import datetime as dt  # avoid namespace conflict over 'date'
import os
import typing
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import jinja2
import pandas as pd
from attr import field
from dateutil.easter import easter
from docx import Document
from docxtpl import DocxTemplate

from models_base import model, AllGetMixin, nullable_field

if typing.TYPE_CHECKING:
    from forms import PewSheetForm

from utils import get_neh_df, advent, closest_sunday_to

feasts_fields = ['name', 'month', 'day', 'coeaster', 'coadvent',
                 'introit', 'collect', 'epistle_ref', 'epistle',
                 'gat', 'gradual', 'alleluia', 'tract', 'gospel_ref',
                 'gospel', 'offertory', 'communion']

FEASTS_CSV = Path(os.path.dirname(__file__)) / 'data' / 'feasts.csv'

PEW_SHEET_TEMPLATE = os.path.join('templates', 'pewSheetTemplate.docx')


@model
class Feast(AllGetMixin):
    _df = pd.read_csv(FEASTS_CSV)
    # Int64, not int, to allow null values (rather than casting them to 0)
    _df = _df.astype(
        {
            'month': 'Int64',
            'day': 'Int64',
            'coeaster': 'Int64',
            'coadvent': 'Int64'
        }
    )
    assert list(_df.columns) == feasts_fields

    name: str = field()

    # Specified for the fixed holy days, None for the movable feasts.
    # TODO - what about Remembrance Sunday and Advent Sunday? Not fixed
    #  days but also not comoving with Easter. As a hack go with 11 Nov
    #  and 30 Nov respectively but the exact dates are
    month: Optional[int] = nullable_field()
    day: Optional[int] = nullable_field()

    # For the feasts synced with Easter, the number of days since Easter
    coeaster: Optional[int] = nullable_field()
    coadvent: Optional[int] = nullable_field()

    introit: Optional[str] = nullable_field()
    collect: Optional[str] = nullable_field()
    epistle_ref: Optional[str] = nullable_field()
    epistle: Optional[str] = nullable_field()
    gat: Optional[str] = nullable_field()
    gradual: Optional[str] = nullable_field()
    alleluia: Optional[str] = nullable_field()
    tract: Optional[str] = nullable_field()
    gospel_ref: Optional[str] = nullable_field()
    gospel: Optional[str] = nullable_field()
    offertory: Optional[str] = nullable_field()
    communion: Optional[str] = nullable_field()

    def get_date(self, year=None) -> Optional[dt.date]:
        if year is None:
            year = datetime.now().year

        if self.month is not None and self.day is not None:
            # TODO Check this definition
            if self.name == 'Remembrance Sunday':
                return closest_sunday_to(dt.date(year, self.month, self.day))

            return dt.date(year, self.month, self.day)

        assert not (self.coeaster is not None and self.coadvent is not None)

        if self.coeaster is not None:
            return easter(year) + timedelta(days=self.coeaster)

        if self.coadvent is not None:
            return advent(year) + timedelta(days=self.coadvent)

        return None

    @property
    def date(self):
        """The date of the feast in the present year."""
        return self.get_date()

    def get_next_date(self, d: Optional[dt.date] = None) -> Optional[dt.date]:
        """Returns the next occurrence of this feast from the specified
        date, which may be in the next calendar year.
        """
        if d is None:
            d = dt.date.today()

        next_occurrence = self.get_date(year=d.year)
        if next_occurrence is None:
            return None
        if (next_occurrence - d).days < 0:
            next_occurrence = self.get_date(year=d.year + 1)

        return next_occurrence

    @property
    def next_date(self):
        """The next occurrence of the feast, which may be in the next
        calendar year.
        """
        return self.get_next_date()

    def create_docx(self, path):
        document = Document()
        document.add_heading(self.name, 0)
        document.save(path)


@model
class Music:
    hymns_df = get_neh_df()

    title: str = field()
    category: str = field()  # Anthem or Hymn or Plainsong
    composer: Optional[str] = field()
    lyrics: Optional[str] = field()
    ref: Optional[str] = field()

    @classmethod
    def neh_hymns(cls) -> List['Music']:
        return [
            Music(
                title=record.firstLine,
                category='Hymn',
                composer=None,
                lyrics=None,
                ref=f'NEH: {record.number}'
            ) for record in get_neh_df().itertuples()
        ]

    @classmethod
    def get_neh_hymn_by_ref(cls, ref: str) -> Optional['Music']:
        try:
            return next(filter(lambda h: h.ref == ref, cls.neh_hymns()))
        except StopIteration:
            return None

    def __str__(self):
        if self.category == 'Hymn':
            return f'{self.ref}, {self.title}'
        return super().__str__()


@model
class Service:
    # Mandatory fields first, then fields with default values.
    title: str = field()
    date: datetime.date = field()
    primary_feast: Feast = field()
    secondary_feast: Optional[Feast] = field(default=None)
    celebrant: str = field(default='')
    preacher: str = field(default='')
    introit_hymn: Optional[Music] = field(default=None)
    offertory_hymn: Optional[Music] = field(default=None)
    recessional_hymn: Optional[Music] = field(default=None)
    anthem: Optional[Music] = field(default=None)

    # One can't call methods in jinja2 templates, so one must provide
    # everything as member properties instead.

    @property
    def collects(self) -> List[str]:
        out = []
        if self.primary_feast.collect:
            out.append(self.primary_feast.collect)
        if self.secondary_feast and self.secondary_feast.collect:
            out.append(self.secondary_feast.collect)

        # Collects for Advent I and Ash Wednesday are repeated
        # throughout Advent and Lent respectively.
        advent1 = Feast.get(name='Advent I')
        ash_wednesday = Feast.get(name='Ash Wednesday')

        if 'Advent' in self.primary_feast.name and self.primary_feast != advent1:
            out.append(advent1.collect)

        if 'Lent' in self.primary_feast.name:
            out.append(ash_wednesday.collect)

        return out

    # TODO primary or secondary?
    @property
    def introit_proper(self) -> str:
        return self.primary_feast.introit

    @property
    def gat(self) -> str:
        return self.primary_feast.gat

    @property
    def gat_propers(self) -> List[str]:
        propers = []
        if 'Gradual' in self.primary_feast.gat:
            propers.append(self.primary_feast.gradual)
        if 'Alleluia' in self.primary_feast.gat:
            propers.append(self.primary_feast.alleluia)
        if 'Tract' in self.primary_feast.gat:
            propers.append(self.primary_feast.tract)
        return propers

    @property
    def offertory_proper(self) -> str:
        return self.primary_feast.offertory

    @property
    def communion_proper(self) -> str:
        return self.primary_feast.communion

    @property
    def epistle_ref(self) -> str:
        return self.primary_feast.epistle_ref

    @property
    def epistle(self) -> str:
        return self.primary_feast.epistle

    @property
    def gospel_ref(self) -> str:
        return self.primary_feast.gospel_ref

    @property
    def gospel(self) -> str:
        return self.primary_feast.gospel

    @classmethod
    def from_form(cls, form: 'PewSheetForm') -> 'Service':
        primary_feast = Feast.get(name=form.primary_feast_name.data)
        if form.secondary_feast_name.data:
            secondary_feast = Feast.get(name=form.secondary_feast_name.data)
        else:
            secondary_feast = None

        if form.anthem_title.data or form.anthem_composer.data or form.anthem_lyrics.data:
            anthem = Music(
                title=form.anthem_title.data,
                composer=form.anthem_composer.data,
                lyrics=form.anthem_lyrics.data,
                category='Anthem',
                ref=None
            )
        else:
            anthem = None

        return Service(
            title=form.title.data,
            date=form.date.data,
            celebrant=form.celebrant.data,
            preacher=form.preacher.data,
            primary_feast=primary_feast,
            secondary_feast=secondary_feast,
            introit_hymn=Music.get_neh_hymn_by_ref(form.introit_hymn.data),
            offertory_hymn=Music.get_neh_hymn_by_ref(form.offertory_hymn.data),
            recessional_hymn=Music.get_neh_hymn_by_ref(form.recessional_hymn.data),
            anthem=anthem,
        )

    def create_docx(self, path):
        doc = DocxTemplate(PEW_SHEET_TEMPLATE)
        jinja_env = jinja2.Environment(autoescape=True)
        jinja_env.globals['len'] = len

        # local import to avoid circular import
        from filters import filters_context

        jinja_env.filters.update(filters_context)
        doc.render({'service': self}, jinja_env)
        doc.save(path)
