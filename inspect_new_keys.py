import requests
import csv
import io

sheet_id = "1P0G_SRgOgBSnZt2zAc3W2Gj77JVUGirTmgsMngUtEEY"
gids = ['130754344', '143582961', '1475216791', '2101082756', '336909315', '72313513', '806349230', '964924413']

for g in gids:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={g}"
    res = requests.get(url)
    lines = list(csv.reader(io.StringIO(res.text)))
    print(f"=== GID {g} (Rows: {len(lines)}) ===")
    if lines:
        print("Header:", lines[0])
        # Find unique question_keys
        q_keys = set()
        for r in lines[1:]:
            if len(r) > 1 and r[1]:
                q_keys.add(r[1])
        print("Sample question_keys:", sorted(list(q_keys))[:10])
    print("-" * 50)
