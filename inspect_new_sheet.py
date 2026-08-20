import requests
import re
import csv
import io

sheet_id = "1P0G_SRgOgBSnZt2zAc3W2Gj77JVUGirTmgsMngUtEEY"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/htmlview"

res = requests.get(url)
print("Status code:", res.status_code)

# Encontrar nombres de tabs y GIDs
tabs = re.findall(r'<li id="sheet-button-([^"]+)"[^>]*><a[^>]*>([^<]+)</a>', res.text)
print("Tabs encontrados:")
for tab_id, tab_name in tabs:
    print(f"Tab ID: {tab_id} | Name: {tab_name}")

# También buscar todos los GIDs
gids = re.findall(r'gid=(\d+)', res.text)
unique_gids = sorted(list(set(gids)))
print("\nUnique GIDs:", unique_gids)

# Probar exportar cada GID
for g in unique_gids:
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={g}"
    csv_res = requests.get(csv_url)
    lines = list(csv.reader(io.StringIO(csv_res.text)))
    header = lines[0] if lines else []
    print(f"\n--- GID {g} (Rows: {len(lines)}) ---")
    print("Header:", header[:8])
    if len(lines) > 1:
        print("Row 1 sample:", lines[1][:8])
