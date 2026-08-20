from src.tools.sheet_auditor import find_candidate_in_sheet

# Casos hipotéticos de typos
tests = [
    'raymon colo',        # Faltan letras (n y n)
    'raymond col',        # Apellido incompleto
    'raymon colon',       # Solo falta la n del nombre
    'Raimond Colon',      # Error ortográfico
    'raymon',             # Solo nombre con typo
    'colon',              # Solo apellido
    'kennedy boldin',     # Typo en apellido
    'nevaya gren',        # Typo en apellido
]

for q in tests:
    res = find_candidate_in_sheet(q)
    if res:
        print(f'Buscar: "{q}" -> Encontrado: "{res["nombre"]}" | Puesto: {res["puesto"]}')
    else:
        print(f'Buscar: "{q}" -> NO ENCONTRADO')
