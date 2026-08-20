import requests
import csv
import io

sheet_id = "1P0G_SRgOgBSnZt2zAc3W2Gj77JVUGirTmgsMngUtEEY"

# Comprobar tab por tab
tab_names = {
    '130754344': 'FOH (Front of House)',
    '2101082756': 'BOH (Back of House)',
    '72313513': 'DD (Delivery Driver)',
    '806349230': 'SA (Systems Analyst)',
    '143582961': 'GID 143582961',
    '1475216791': 'GID 1475216791',
    '336909315': 'GID 336909315'
}

for g in ['143582961', '1475216791', '336909315']:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={g}"
    lines = list(csv.reader(io.StringIO(requests.get(url).text)))
    print(f"=== {g} (Rows: {len(lines)}) ===")
    for r in lines[1:]:
        if len(r) > 6 and ('director' in r[6].lower() or 'shift' in r[6].lower() or 'lead' in r[6].lower() or 'kitchen' in r[6].lower() or 'boh' in r[6].lower() or 'foh' in r[6].lower() or 'dining' in r[6].lower()):
            print(f"  [{r[1]}] opt='{r[3]}' ideal='{r[6]}'")
    print("-" * 50)
