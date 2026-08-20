import requests
import csv
import io

sheet_id = "1P0G_SRgOgBSnZt2zAc3W2Gj77JVUGirTmgsMngUtEEY"
gids = {'143582961': 'GID 143582961', '1475216791': 'GID 1475216791', '336909315': 'GID 336909315'}

for g, label in gids.items():
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={g}"
    lines = list(csv.reader(io.StringIO(requests.get(url).text)))
    print(f"=== {label} ===")
    for r in lines[1:]:
        if len(r) > 2 and r[2]:
            q = r[2]
            # Print if question is not in common basic set
            if any(k in q.lower() for k in ['wage', 'salary', 'describe', 'why do you', 'thoughts on working', 'solving', 'outside of your job', 'convicted', 'front', 'back', 'kitchen', 'shift']):
                print(" ", q[:80])
    print()
