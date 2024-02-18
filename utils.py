import logging
import os
from datetime import timedelta, date
from functools import lru_cache
from pathlib import Path
from typing import Optional

from appdirs import AppDirs


class NoPandasError(RuntimeError):
    pass


cache_dir = AppDirs("pypew").user_cache_dir
os.makedirs(cache_dir, exist_ok=True)

logger = logging.getLogger("pypew")
logger.setLevel(logging.INFO)


def str2date(s: Optional[str]) -> date:
    """Parse the date string if one is given. If None or empty, return
    today.
    """
    if not s:
        return date.today()
    return date.fromisoformat(s)


@lru_cache()
def get_neh_df():
    try:
        import pandas as pd
    except ImportError:
        raise NoPandasError(
            'Pandas not available, can\'t load hymn information'
        )

    df = pd.read_csv(
        Path(__file__).parent / 'data/neh.csv'
    )

    assert 'number' in df.columns
    assert 'firstLine' in df.columns
    return df


def sunday_after(d: date) -> date:
    # 1 for Monday, 7 for Sunday
    dow = d.isoweekday()
    if dow == 7:
        return d + timedelta(days=7)
    else:
        return d + timedelta(days=7 - dow)


def closest_sunday_to(d: date) -> date:
    # 1 for Monday, 7 for Sunday
    dow = d.isoweekday()
    if dow in {1, 2, 3}:
        return d - timedelta(days=dow)
    if dow in {4, 5, 6}:
        return d + timedelta(days=7-dow)

    return d


def advent(year: int) -> date:
    """Date of Advent Sunday. Fourth Sunday before Christmas Day."""
    christmas = date(year=year, month=12, day=25)
    # 1 for Monday, 7 for Sunday
    christmas_dow = christmas.isoweekday()
    if christmas_dow != 7:
        return christmas - timedelta(days=christmas_dow + 7*3)
    else:
        return christmas - timedelta(7 * 4)
