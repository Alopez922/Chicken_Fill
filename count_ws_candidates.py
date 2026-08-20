import requests
from collections import Counter
from src.config import WORKSTREAM_API_KEY, WORKSTREAM_BASE_URL

headers = {'Authorization': f'Bearer {WORKSTREAM_API_KEY}', 'Accept': 'application/json'}
url = f"{WORKSTREAM_BASE_URL}/position_applications"
params = {"status": "in_progress", "limit": 300}
res = requests.get(url, headers=headers, params=params)
print("Applications Status:", res.status_code)
d = res.json()
apps = d.get("position_applications", d.get("data", []))
print("Total in-progress applications returned:", len(apps))

pos_counter = Counter()
stage_counter = Counter()

for a in apps:
    pos_title = (a.get("position") or {}).get("title") or a.get("position_title") or "Sin Puesto"
    stage = a.get("stage") or a.get("current_stage") or "In Progress"
    pos_counter[pos_title] += 1
    stage_counter[stage] += 1

print("\n--- Desglose por Puesto en Workstream API (En Vivo) ---")
for p, count in pos_counter.most_common():
    print(f"  * {p}: {count} candidatos")

print("\n--- Desglose por Etapa en Workstream API (En Vivo) ---")
for s, count in stage_counter.most_common():
    print(f"  * {s}: {count} candidatos")
