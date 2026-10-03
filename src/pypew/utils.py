import logging
import os
from functools import lru_cache

from appdirs import AppDirs

from .paths import NEH_CSV


class NoPandasError(RuntimeError):
    pass


cache_dir = AppDirs("pypew").user_cache_dir
os.makedirs(cache_dir, exist_ok=True)

logger = logging.getLogger("pypew")
logger.setLevel(logging.INFO)


@lru_cache
def get_neh_df():
    try:
        import pandas as pd
    except ImportError:
        # FIXME(B904): chained exception would be clearer
        raise NoPandasError("Pandas not available, can't load hymn information")

    df = pd.read_csv(NEH_CSV)

    assert "number" in df.columns
    assert "firstLine" in df.columns
    return df
