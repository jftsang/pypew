from datetime import datetime

from models import Service


def english_date(date: datetime.date) -> str:
    return date.strftime('%A %-d %B %Y')


def service_subtitle(service: Service) -> str:
    c, p = service.celebrant, service.preacher
    if service.secondary_feast:
        s = service.primary_feast.name + ' (' + service.secondary_feast.name + ').'
    else:
        s = service.primary_feast.name + '.'
    if c:
        if p and p != c:
            s += f' {c}. Preacher: {p}.'
        else:
            s += f' {c}.'
    else:
        if p:
            s += f' Preacher: {p}.'
    return s
