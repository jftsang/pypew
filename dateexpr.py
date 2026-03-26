import datetime as dt
import re
from datetime import date

import dateutil
import dateutil.parser
from dateutil.easter import easter

aliases = {
    "Christmas": "25 December",
    "Christmas Day": "Christmas",
    "Advent Sunday": "4th Sunday before Christmas",
    "Good Friday": "Friday before Easter",
    "Easter Sunday": "Easter",
    "Easter Monday": "day after Easter",
    "Remembrance Day": "11 November",
    "Remembrance Sunday": "Sunday nearest Remembrance Day",
}

dowmap = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6
}


def parse_simple(expr: str, year=None) -> date:
    if expr in aliases:
        return parse(aliases[expr], year)

    if year is not None:
        reference = date(year, 1, 1)
    else:
        reference = date.today()

    if expr == "Easter":
        d = easter(reference.year)
    else:
        d = dateutil.parser.parse(expr).replace(year=reference.year).date()
    return d


def parse_compound(expr: str, year=None) -> date:
    # Break at the first operator word, recurse on the rest
    m = re.search("(?P<modifier>.*?) (?P<op>before|after|nearest) (?P<base>.*)", expr)
    if not m:
        return parse_simple(expr, year)
    modifier = m.group("modifier")
    op = m.group("op")
    base = m.group("base")
    basedate = parse_compound(base, year)

    print(modifier, op, base, sep=" | ")

    if op in {"after", "before"}:
        m = re.match(r"(?:(?P<num>\d+)\w* )?(?P<unit>\w+)", modifier)
        # breakpoint()
        if not m:
            raise ValueError
        num = int(m.group("num") or 1)
        unit = m.group("unit")

        return apply_relative_clause(basedate, op, num, unit)

    elif op == "nearest":
        m = re.match(r"(?P<what>\w+)", modifier)
        if not m:
            raise ValueError
        what = m.group("what")

        return apply_nearest_clause(basedate, what)

    else:
        raise ValueError

    return basedate


def apply_relative_clause(base: date, op: str, num: int, unit: str) -> date:
    unit = unit.rstrip("s")
    if unit == "week":
        num *= 7
        unit = "day"

    if unit == "day":
        if op == "after":
            return base + dt.timedelta(days=num)
        elif op == "before":
            return base - dt.timedelta(days=num)
        else:
            raise ValueError

    if unit in dowmap:
        if op == "after":
            days_until_first = (dowmap[unit] - base.weekday()) % 7
            if days_until_first == 0:
                return base + dt.timedelta(days=num * 7)
            else:
                return base + dt.timedelta(days=(num - 1) * 7 + days_until_first)
        elif op == "before":
            days_before_first = (base.weekday() - dowmap[unit]) % 7
            if days_before_first == 0:
                return base - dt.timedelta(days=num * 7)
            else:
                return base - dt.timedelta(days=(num - 1) * 7 + days_before_first)
        else:
            raise ValueError

    raise ValueError


def apply_nearest_clause(base: date, what: str) -> date:
    dow = dowmap[what]

    if dow == base.weekday():
        return base

    delta = (dow - base.weekday()) % 7
    if delta > 3:
        delta -= 7
    if delta < -3:
        delta += 7

    return base + dt.timedelta(days=delta)


def parse(expr: str, year=None) -> date:
    if expr in aliases:
        return parse(aliases[expr], year)
    return parse_compound(expr, year)
