import json
import os

from docx import Document
from dotmap import DotMap


class Jorm(DotMap):
    """Lightweight ORM where data is stored in a JSON file."""
    datafile = None

    class NotFoundError(Exception):
        pass

    class MultipleReturnedError(Exception):
        pass

    @classmethod
    def all(cls):
        with open(cls.datafile) as f:
            return [cls(x) for x in json.load(f)]

    @classmethod
    def filter(cls, **kwargs):
        return [
            x for x in cls.all()
            if all(x[k] == kwargs[k] for k in kwargs.keys())
        ]

    @classmethod
    def get(cls, **kwargs):
        filtered = cls.filter(**kwargs)
        n = len(filtered)
        if n == 0:
            raise cls.NotFoundError(cls, kwargs)
        if n > 1:
            raise cls.MultipleReturnedError(cls, kwargs, n)
        return filtered[0]


class Service(Jorm):
    datafile = os.path.join(os.path.dirname(__file__), 'data', 'services.json')

    def create_docx(self, path):
        document = Document()
        document.add_heading(self.name, 0)
        document.save(path)


class Extract(Jorm):
    datafile = os.path.join(os.path.dirname(__file__), 'data', 'texts.json')


class PewSheet:
    def __init__(self, service, title=None):
        self.service = service
        self.title = title or service.name
