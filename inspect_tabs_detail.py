import requests
import re
import csv
import io

sheet_id = "1P0G_SRgOgBSnZt2zAc3W2Gj77JVUGirTmgsMngUtEEY"
gids = ['130754344', '143582961', '1475216791', '2101082756', '336909315', '72313513', '806349230', '964924413']

for g in gids:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={g}"
    res = requests.get(url)
    lines = list(csv.reader(io.StringIO(res.text)))
    print(f"=== GID {g} (Total rows: {len(lines)}) ===")
    if lines:
        for r in lines[:5]:
            print(r)
    print()
