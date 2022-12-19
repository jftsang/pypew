import math
from pathlib import Path

import pandas as pd
import yaml
from pandas._libs.missing import NA
from slugify import slugify  # python-slugify, not slugify

from models import FEASTS_CSV

feastdir = Path(FEASTS_CSV).parent / 'feasts'
df = pd.read_csv(FEASTS_CSV).to_dict(orient='records')

def isnan(x):
    if x is NA:
        return True
    try:
        f = float(x)
        if math.isnan(f):
            return True

    except ValueError:
        pass

    return False


for d in df:
    poppands = []
    for k, v in d.items():
        if isnan(v):
            poppands.append(k)
    for p in poppands:
        d.pop(p)

    # convert fields, if they exist
    for key in {'month', 'day', 'coeaster', 'coadvent'}:
        if key in d:
            d[key] = int(d[key])

sluglist = []

for row in df:
    text = yaml.safe_dump(
        row,
        sort_keys=False,
        width=72,
        indent=4,
        default_flow_style=False,
    )

    sluglist.append(slug := slugify(row['name']))
    with open(
        (feastdir / slug).with_suffix('.yaml'),
        'w'
    ) as file:
        file.write(text)

with open(feastdir / '_list.txt', 'w') as f:
    for x in sluglist:
        f.write(x + '\n')
