import requests
from collections import Counter
from src.config import WORKSTREAM_API_KEY, WORKSTREAM_BASE_URL

headers = {'Authorization': f'Bearer {WORKSTREAM_API_KEY}', 'Accept': 'application/json'}
url = f"{WORKSTREAM_BASE_URL}/position_applications"
params = {"status": "in_progress", "limit": 350}
res = requests.get(url, headers=headers, params=params)
d = res.json()
apps = d.get("position_applications", d.get("data", []))

# Agrupar exactamente como las pestañas de Workstream:
# 1. Pestaña "Applications" (Review Stage, Availability, etc. pendientes de entrevista)
applications_tab = [a for a in apps if not any(k in (a.get("stage") or a.get("current_stage") or "").lower() for k in ["interview", "offer", "hired"])]
# 2. Pestaña "Interviews"
interviews_tab = [a for a in apps if "interview" in (a.get("stage") or a.get("current_stage") or "").lower()]

print(f"Total en pestaña 'Applications': {len(applications_tab)}")
print(f"Total en pestaña 'Interviews': {len(interviews_tab)}")
print(f"Total general en progreso: {len(apps)}")

pos_applications = Counter()
for a in applications_tab:
    pos_title = (a.get("position") or {}).get("title") or a.get("position_title") or "Sin Puesto"
    pos_applications[pos_title] += 1

print("\n--- Desglose de Pestaña 'Applications' (313) por Puesto ---")
for p, c in pos_applications.most_common():
    print(f"  * {p}: {c} candidatos")
