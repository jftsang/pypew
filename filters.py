from datetime import datetime

from models import Service


def english_date(date: datetime.date) -> str:
    return date.strftime('%A %-d %B %Y')


def celebrant_and_preacher(service: Service) -> str:
    c, p = service.celebrant, service.preacher
    if c:
        if p and p != c:
            return f'{c}. Preacher: {p}.'
        else:
            return c
    else:
        if p:
            return f'Preacher: {p}.'
        else:
            return ''
