"""Boilerplate code for models. Actual business logic in models.py."""
# import humps as humps
import json

import cattr
import pandas as pd
from attr import field, define


class NotFoundError(Exception):
    pass


class MultipleReturnedError(Exception):
    pass


def nullable_field(*args, **kwargs):
    """Pandas will treat empty fields as pd.NA or as nan; convert
    all of these to None.
    """
    kwargs.pop('converter', None)
    return field(*args, **kwargs, converter=lambda x: None if pd.isna(x) else x)


class JSONEncoder(json.JSONEncoder):
    encoders = {}

    @classmethod
    def default(cls, obj):
        if type(obj) in cls.encoders:
            return cls.encoders[type(obj)](obj)
        return json.JSONEncoder().default(obj)


class JSONDecoder(json.JSONDecoder):
    NotImplemented  # TODO


def model(clazz):
    clazz = define(clazz)
    JSONEncoder.encoders[clazz] = lambda obj: cattr.Converter().unstructure(obj)
    # JSONDecoder.decoders[clazz] = lambda jobj: cattr.Converter().structure(jobj, clazz)
    # clazz.load = classmethod(lambda cls, d: _converter.load(d, cls))
    return clazz


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
