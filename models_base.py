"""Boilerplate code for models. Actual business logic in models.py."""


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
