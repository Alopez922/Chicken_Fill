import sys
from src.tools.sheet_auditor import fetch_sheet_rows, get_candidates_from_sheet_by_position
from src.tools.criteria_engine import score_candidate_with_framework, get_tab_gid_for_position

print("============================================================")
print("AUDITORIA EN VIVO: 7 PUESTOS OFICIALES Y SUS CANDIDATOS REALES")
print("============================================================")

positions_to_test = [
    "Front of House Team Member",
    "Back of House Team Member",
    "Front of the House Director",
    "Director of Back of House Operations – High-Volume Restaurant",
    "Shift Leader",
    "Systems Analyst",
    "Chick-fil-A Delivery Driver"
]

all_rows = fetch_sheet_rows()

for pos in positions_to_test:
    gid = get_tab_gid_for_position(pos)
    cands = get_candidates_from_sheet_by_position(pos)
    print(f"\n[PUESTO] {pos}")
    print(f"   GID Asignado: {gid} | Total Candidatos Filtrados: {len(cands)}")
    
    if cands:
        sample_cand = cands[0]
        eval_res = score_candidate_with_framework(
            pos,
            sample_cand.get("parsed_qa", []),
            float(str(sample_cand.get("distancia_millas", 0)).replace("mi", "").strip() or 0)
        )
        print(f"   * Candidato Muestra: {sample_cand['nombre']}")
        print(f"   * Puntuacion: {eval_res['percentage']}% ({eval_res['total_score']}/{eval_res['max_possible_score']} pts)")
        print(f"   * Desglose: Choice={eval_res['choice_score']} pts | Distancia={eval_res['distance_score']} pts | AI={eval_res['open_text_score']} pts")
        print(f"   * Clasificacion: {eval_res['classification']}")
        print(f"   * Preguntas Evaluadas: {eval_res['evaluated_questions_count']}")
    else:
        print("   (No hay candidatos para esta posicion en el sheet actual)")
    print("-" * 60)
