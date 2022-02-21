import os

import pandas as pd
from attr import define, field
from docx import Document

feasts_fields = ['name', 'introit', 'collect', 'epistle_ref', 'epistle',
                 'gat', 'gradual', 'alleluia', 'tract', 'gospel_ref',
                 'gospel', 'offertory', 'communion']


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
        os.path.join(os.path.dirname(__file__), 'data', 'feasts.csv')
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
class Service:
    primary_feast: Feast = field()
    secondary_feast: Feast = field()


class PewSheet:
    def __init__(self, feast, title=None):
        self.feast = feast
        self.title = title or feast.name
