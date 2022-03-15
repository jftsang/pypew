import os
import typing
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import List, Optional

import jinja2
import pandas as pd
from attr import define, field
from dateutil.easter import easter
from docx import Document
from docxtpl import DocxTemplate

if typing.TYPE_CHECKING:
    from forms import PewSheetForm

from utils import get_neh_df

feasts_fields = ['name', 'introit', 'collect', 'epistle_ref', 'epistle',
                 'gat', 'gradual', 'alleluia', 'tract', 'gospel_ref',
                 'gospel', 'offertory', 'communion', 'month', 'day',
                 'coeaster']

FEASTS_CSV = Path(os.path.dirname(__file__)) / 'data' / 'feasts.csv'

PEW_SHEET_TEMPLATE = os.path.join('templates', 'pewSheetTemplate.docx')


class NotFoundError(Exception):
    pass


class MultipleReturnedError(Exception):
    pass


def get(collection, **kwargs):
    f = lambda x: all(getattr(x, k) == v for k, v in kwargs.items())
    filtered = list(filter(f, collection))

    n = len(filtered)
    if n == 0:
        raise NotFoundError(kwargs)
    if n > 1:
        raise MultipleReturnedError(kwargs, n)
    return filtered[0]


class AllGetMixin:
    _df = None

    @classmethod
    def all(cls):
        # attrs provides a __init__ that takes kwargs
        # noinspection PyArgumentList
        return [cls(**info) for _, info in cls._df.iterrows()]

    @classmethod
    def get(cls, **kwargs):
        return get(cls.all(), **kwargs)


@define
class Feast(AllGetMixin):
    name: str = field()

    # Specified for the fixed holy days, None for the movable feasts.
    # TODO - what about Remembrance Sunday and Advent Sunday? Not fixed
    #  days but also not comoving with Easter. As a hack go with 11 Nov
    #  and 30 Nov respectively but the exact dates are
    month: Optional[int] = field()
    day: Optional[int] = field()

    # For the feasts synced with Easter, the number of days since Easter
    coeaster: Optional[int] = field()

    introit: str = field()
    collect: str = field()
    epistle_ref: str = field()
    epistle: str = field()
    gat: str = field()
    gradual: str = field()
    alleluia: str = field()
    tract: str = field()
    gospel_ref: str = field()
    gospel: str = field()
    offertory: str = field()
    communion: str = field()

    _df = pd.read_csv(FEASTS_CSV)
    # Int64, not int, to allow null values
    _df = _df.astype({'month': 'Int64', 'day': 'Int64', 'coeaster': 'Int64'})
    assert list(_df.columns) == feasts_fields

    @property
    def date(self, year=None) -> Optional[date]:
        if year is None:
            year = datetime.now().year

        if self.month is not pd.NA and self.day is not pd.NA:
            return date(year, self.month, self.day)

        if self.coeaster is not pd.NA:
            return easter(year) + timedelta(days=self.coeaster)

        return None

    def create_docx(self, path):
        document = Document()
        document.add_heading(self.name, 0)
        document.save(path)


@define
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


@define
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
