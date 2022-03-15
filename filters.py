from datetime import datetime
from functools import wraps

from models import Service


def nullsafe(f):
    @wraps(f)
    def ns(x):
        return f(x) if x is not None else ''
    return ns


@nullsafe
def english_date(date: datetime.date) -> str:
    return date.strftime('%A %-d %B %Y')


def service_summary(service: Service) -> str:
    return service.date.strftime('%Y-%m-%d') + ' ' + service_subtitle(service)


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


# For passing into docxtpl. (For use in Flask, these filters are also
# registered when the app is created.)
filters_context = {
   'english_date': english_date,
   'service_summary': service_summary,
   'service_subtitle': service_subtitle
}
