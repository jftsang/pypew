import logging
import os
from functools import lru_cache

import pandas as pd

logger = logging.getLogger("pypew")


@lru_cache()
def get_neh_df():
    try:
        url = 'https://hymnary.org/instances?qu=hymnalNumber%3Aneh1985%20in%3Ainstances&sort=displayTitle&order=asc&export=csv&limit=10000'
        df = pd.read_csv(url)
    except Exception as exc:
        logging.warning(f'Couldn\'t read NEH index from hymnary.org: {exc}')
        df = pd.read_csv(os.path.join('data', 'neh.csv'))

    assert 'number' in df.columns
    assert 'firstLine' in df.columns
    return df
