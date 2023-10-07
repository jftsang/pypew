import datetime as dt
import sys
from functools import wraps

from docxtpl import RichText

from models import Service, ServiceItem


def nullsafe(f):
    @wraps(f)
    def ns(x):
        return f(x) if x is not None else ''

    return ns


def as_richtext(item: ServiceItem) -> RichText:
    return item.as_richtext()


def service_supertitle(service: Service) -> str:
    s = english_date(service.date)
    if service.time:
        s += f", " + service.time.strftime("%-I:%M%p").lower()
    return s


@nullsafe
def english_date(date: dt.date) -> str:
    # https://stackoverflow.com/a/74227668
    def format_date_with_ordinal(d, format_string):
        if d.day not in (11, 12, 13):
            ordinal = {'1': 'st', '2': 'nd', '3': 'rd'}.get(
                str(d.day)[-1:],
                'th'
            )
        else:
            ordinal = 'th'

        return d.strftime(format_string).replace('{th}', ordinal)

    # try:
    if sys.platform.startswith('win'):
        # https://stackoverflow.com/questions/904928/python-strftime-date-without-leading-0
        return format_date_with_ordinal(date, '%A %#d{th} %B %Y')
    else:
        return format_date_with_ordinal(date, '%A %-d{th} %B %Y')


def service_summary(service: Service) -> str:
    return service.date.strftime('%Y-%m-%d') + ' ' + service_subtitle(service)


def service_header(service: Service) -> str:
    return service.service_type


def service_subtitle(service: Service) -> str:
    # Feastday (Secondary), Fr XX YY (Preacher: AN Other)
    if service.secondary_feast:
        s = service.primary_feast.name + ' (' + service.secondary_feast.name + '), '
    else:
        s = service.primary_feast.name + ', '

    c, p = service.celebrant, service.preacher
    if c:
        if p and p != c:
            s += f' {c} (Preacher: {p})'
        else:
            s += f' {c}'
    else:
        if p:
            s += f' Preacher: {p}'
    return s


# These get registered by the Flask app, and also need to be passed into
# docxtpl.
filters_context = {
    'as_richtext': as_richtext,
    'english_date': english_date,
    'service_header': service_header,
    'service_subtitle': service_subtitle,
    'service_supertitle': service_supertitle,
    'service_summary': service_summary,
}
