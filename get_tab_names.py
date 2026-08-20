import requests
import re

url = "https://docs.google.com/spreadsheets/d/1P0G_SRgOgBSnZt2zAc3W2Gj77JVUGirTmgsMngUtEEY/edit"
res = requests.get(url)

# Buscar patrones de nombres de pestañas y GIDs
matches = re.findall(r'name:"([^"]+)",pageUrl:[^,]+,sheetId:"(\d+)"', res.text)
print("Pestañas encontradas:")
for name, gid in matches:
    print(f"GID: {gid} -> {name}")

if not matches:
    # Buscar otro formato
    matches2 = re.findall(r'\"name\":\"([^\"]+)\"[^}]+?\"sheetId\":(\d+)', res.text)
    for name, gid in matches2:
        print(f"GID: {gid} -> {name}")
