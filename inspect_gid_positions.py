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
    
    # Extraer algunas preguntas específicas de este tab
    questions = []
    for r in lines[1:]:
        if len(r) > 2 and r[2].strip() and r[2].strip() not in questions:
            questions.append(r[2].strip())
            
    print(f"Total Preguntas: {len(questions)}")
    for q in questions[:6]:
        print(f"  - {q}")
    # Ver si hay preguntas específicas de cocina, driver, analyst, etc.
    specifics = [q for q in questions if any(k in q.lower() for k in ['driver', 'delivery', 'system', 'analyst', 'shift', 'director', 'cook', 'kitchen', 'food in large volumes', 'banking', 'cash deposits'])]
    print("Preguntas específicas encontradas:")
    for s in specifics:
        print(f"    * {s}")
    print("-" * 50)
