import requests
import json
from src.config import WORKSTREAM_API_KEY, WORKSTREAM_BASE_URL

headers = {'Authorization': f'Bearer {WORKSTREAM_API_KEY}', 'Accept': 'application/json'}
res = requests.get(f'{WORKSTREAM_BASE_URL}/positions', headers=headers)
print("Positions API Status:", res.status_code)
d = res.json()
print("Type:", type(d))
if isinstance(d, dict):
    print("Keys:", d.keys())
    positions = d.get("positions", d.get("data", []))
    for p in positions[:10]:
        print(p.get("id"), "|", p.get("title"), "| status:", p.get("status"), "| applicants_count:", p.get("position_applications_count"))
elif isinstance(d, list):
    for p in d[:10]:
        print(p.get("id"), "|", p.get("title"), "| status:", p.get("status"))
