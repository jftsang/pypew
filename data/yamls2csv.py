from pathlib import Path

import pandas as pd
import yaml
from pyxtension.streams import stream

feastdir = Path(__file__).parent / 'feasts'
slugs = (feastdir / '_list.txt').read_text().splitlines()
feastlist = []

feasts: list[dict] = (
    stream(slugs)
    .map(lambda slug: (feastdir / slug).with_suffix('.yaml'))
    .map(open)
    .map(yaml.safe_load)
    .to_list()
)

df = pd.DataFrame.from_records(feasts)
fields = "name,month,day,coeaster,coadvent,introit,collect,epistle_ref,epistle,gat,gradual,alleluia,tract,gospel_ref,gospel,offertory,communion".split(
    ","
)
df = df[fields]

df.to_csv(feastdir.parent / "feasts.csv", index=False)
