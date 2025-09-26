import math
from pathlib import Path

import pandas as pd
import yaml
from pyxtension.streams import stream


def float2intstring(x):
    if x is pd.NA:
        return ""
    try:
        f = float(x)
    except ValueError:
        return ""

    if math.isnan(f):
        return ""

    return str(int(x))


def fix_records(r):
    for key in ["month", "day", "coeaster", "coadvent"]:
        if key in r:
            r[key] = float2intstring(r[key])
        else:
            r[key] = ""
    return r  # mutates, but for chaining

feastdir = Path(__file__).parent / 'feasts'
slugs = (feastdir / '_list.txt').read_text().splitlines()
feastlist = []

feasts: list[dict] = (
    stream(slugs)
    .map(lambda slug: (feastdir / slug).with_suffix('.yaml'))
    .map(open)
    .map(yaml.safe_load)
    .map(fix_records)
    .to_list()
)

df = pd.DataFrame.from_records(feasts)
fields = "name,month,day,coeaster,coadvent,introit,collect,epistle_ref,epistle,gat,gradual,alleluia,tract,gospel_ref,gospel,offertory,communion".split(
    ","
)
df = df[fields]
df.dtypes['coeaster'] = 'Int64'
df.dtypes['coadvent'] = 'Int64'

df.to_csv(feastdir.parent / "feasts.csv", index=False)
