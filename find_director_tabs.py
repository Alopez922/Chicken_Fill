import requests
import csv
import io

sheet_id = "1P0G_SRgOgBSnZt2zAc3W2Gj77JVUGirTmgsMngUtEEY"
gids = ['143582961', '1475216791', '336909315', '130754344', '2101082756', '72313513', '806349230']

for g in gids:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={g}"
    res = requests.get(url)
    lines = list(csv.reader(io.StringIO(res.text)))
    print(f"=== GID {g} ===")
    unique_qs = []
    for r in lines[1:]:
        if len(r) > 2 and r[2] and r[2] not in unique_qs:
            unique_qs.append(r[2])
    print("Distinct Questions:", len(unique_qs))
    for q in unique_qs:
        if any(k in q.lower() for k in ['director', 'shift', 'leader', 'evaluating', 'terminating', 'volume', 'driver', 'license', 'dell', 'systems', 'safe']):
            print(f"  * {q}")
    print()
