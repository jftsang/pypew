import os
import typing
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from attr import define, field
from docx import Document

if typing.TYPE_CHECKING:
    from forms import PewSheetForm

from utils import get_neh_df

feasts_fields = ['name', 'introit', 'collect', 'epistle_ref', 'epistle',
                 'gat', 'gradual', 'alleluia', 'tract', 'gospel_ref',
                 'gospel', 'offertory', 'communion']

FEASTS_CSV = Path(os.path.dirname(__file__)) / 'data' / 'feasts.csv'


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


@define
class Feast:
    name: str = field()
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

    feasts_df = pd.read_csv(
        FEASTS_CSV
    )
    assert list(feasts_df.columns) == feasts_fields

    @classmethod
    def all(cls):
        # attrs provides a __init__ that takes kwargs
        # noinspection PyArgumentList
        return [cls(**info) for _, info in cls.feasts_df.iterrows()]

    @classmethod
    def get(cls, **kwargs):
        return get(cls.all(), **kwargs)

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
        advent1 = get(Feast.all(), name='Advent I')
        ash_wednesday = get(Feast.all(), name='Ash Wednesday')

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
        import filters  # local import to avoid circular import

        document = Document()
        document.add_heading(self.title, 0)
        p = document.add_paragraph('')
        if self.date:
            run = p.add_run(filters.english_date(self.date))
            run.italic = True
        (filters.english_date(self.date))
        document.save(path)
