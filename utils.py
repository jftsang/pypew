import logging
from functools import lru_cache

import pandas as pd

logger = logging.getLogger("pypew")


@lru_cache()
def get_neh_df():
    url = 'https://hymnary.org/instances?qu=hymnalNumber%3Aneh1985%20in%3Ainstances&sort=displayTitle&order=asc&export=csv&limit=10000'
    df = pd.read_csv(url)
    return df
