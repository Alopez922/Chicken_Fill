from src.tools.sheet_auditor import find_candidate_in_sheet, get_candidates_from_sheet_by_position
from src.tools.criteria_engine import score_candidate_with_framework

boh_cands = get_candidates_from_sheet_by_position("Back of House")
print(f"Total BOH Candidates: {len(boh_cands)}")

results = []
for c in boh_cands:
    res = score_candidate_with_framework(
        c["puesto"],
        c["parsed_qa"],
        float(str(c.get("distancia_millas", 0)).replace("mi", "").strip() or 0)
    )
    results.append({
        "name": c["nombre"],
        "percentage": res["percentage"],
        "choice": res["choice_score"],
        "distance": res["distance_score"],
        "open_text": res["open_text_score"],
        "total": res["total_score"],
        "max": res["max_possible_score"]
    })

results.sort(key=lambda x: x["percentage"], reverse=True)
print("\n--- RANKING OFICIAL BOH (NUEVO SHEET) ---")
for idx, r in enumerate(results, start=1):
    print(f"{idx}. {r['name']}: {r['percentage']}% | Total: {r['total']}/{r['max']} (Choice: {r['choice']}, Dist: {r['distance']}, AI: {r['open_text']})")
