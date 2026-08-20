"""
Motor del Portal de Candidatos (Portal Engine)
Procesa y califica en lote a todos los candidatos del Data Lake (313) usando el Framework Oficial:
- Clasificación en los 4 niveles oficiales: GOLD (>=97%), IDEAL (75%-96%), POTENTIAL (50%-74%), DISQUALIFIED (<50% / auto-descalificado).
- Desglose exacto de los 3 sub-puntajes: CHOICE SCORE, DISTANCE SCORE, AI SCORE.
- Métricas consolidadas para el Banner Superior de KPIs.
- Caché optimizado en memoria y disco para carga instantánea.
"""
import os
import json
import time
from typing import Dict, Any, List, Optional
from src.tools.sheet_auditor import fetch_sheet_rows, resolve_true_position_from_qa
from src.tools.criteria_engine import score_candidate_with_framework

PORTAL_CACHE_FILE = "src/tools/portal_scored_cache.json"

def get_portal_scored_candidates(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Retorna la lista completa de candidatos calificados y clasificados con el Framework Oficial,
    junto con los contadores para las tarjetas KPI superiores.
    """
    # 1. Intentar cargar desde caché si es reciente (< 60 segundos)
    if not force_refresh and os.path.exists(PORTAL_CACHE_FILE):
        try:
            with open(PORTAL_CACHE_FILE, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                cache_time = cached_data.get("timestamp", 0)
                if time.time() - cache_time < 60:  # 60 seg
                    return cached_data
        except Exception as e:
            print(f"[Portal Cache Read Error] {e}")


    # 2. Descargar filas del Google Sheet Data Lake
    cands = fetch_sheet_rows()
    scored_candidates = []

    kpi_counts = {
        "total": len(cands),
        "gold": 0,
        "ideal": 0,
        "potential": 0,
        "disqualified": 0
    }

    for c in cands:
        nombre = c.get("nombre", "Sin Nombre")
        puesto_raw = c.get("puesto_raw_sheet") or c.get("puesto", "Front of House Team Member")
        qa_list = c.get("parsed_qa", [])
        dist_miles = float(c.get("distancia_millas", 0.0))
        
        # Resolver puesto real (evitar desfases de n8n)
        true_pos = resolve_true_position_from_qa(puesto_raw, qa_list)

        # Calificar con el Framework Oficial
        eval_res = score_candidate_with_framework(true_pos, qa_list, dist_miles)
        
        pct = eval_res["percentage"]
        cls_name = eval_res["classification"]
        is_disq = eval_res["is_disqualified"]

        # TRATAMIENTO ESPECIAL ESTRICTO PARA SYSTEMS ANALYST
        sa_details = None
        if "systems analyst" in true_pos.lower():
            from src.tools.systems_analyst_evaluator import evaluate_systems_analyst_applicant
            sa_eval = evaluate_systems_analyst_applicant(c)
            sa_details = sa_eval
            # Soporte para ambas claves (is_approved y approved)
            approved_flag = sa_eval.get("is_approved") or sa_eval.get("approved", False)
            if not approved_flag:
                is_disq = True
                pct = 0.0
                eval_res["summary"] = sa_eval.get("disqualification_reason", "Descalificado en evaluacion tecnica de TI.")
            else:
                is_disq = False
                # Usar el score_percentage ya calculado por el evaluador SA
                # (incluye bonus por años de exp + bonus por certificaciones)
                pct = sa_eval.get("score_percentage", 75.0)
                eval_res["summary"] = sa_eval.get("verdict_summary", "Candidato tecnico calificado.")


        # Mapeo estándar de clasificación para el Portal
        portal_class = "Potential"
        if is_disq or pct < 50.0:
            portal_class = "Disqualified"
            kpi_counts["disqualified"] += 1
        elif pct >= 97.0:
            portal_class = "GOLD"
            kpi_counts["gold"] += 1
        elif pct >= 75.0:
            portal_class = "Ideal"
            kpi_counts["ideal"] += 1
        else:
            portal_class = "Potential"
            kpi_counts["potential"] += 1

        # Extraer desglose de subpuntajes
        choice_score = 0.0
        distance_score = 10.0 if dist_miles <= 10.0 else 5.0
        ai_score = 0.0

        for d in eval_res.get("details", []):
            sc = float(d.get("score", 0.0))
            cat = str(d.get("category", "")).lower()
            q_name = str(d.get("question", "")).lower()
            if "open text" in cat or "ai" in cat or d.get("is_open_text", False):
                ai_score += sc
            elif "distance" in cat or "commute" in q_name or "distance" in q_name:
                distance_score = sc
            else:
                choice_score += sc

        # Formatear dirección limpia
        raw_addr = c.get("direccion", "")
        if not raw_addr or raw_addr.lower() in ["none", "no especificada", "n/a"]:
            addr_clean = "Dirección no especificada"
        else:
            addr_clean = raw_addr

        candidate_card = {
            "uuid": c.get("uuid"),
            "nombre": nombre,
            "email": c.get("email", ""),
            "telefono": c.get("telefono", ""),
            "puesto": true_pos,
            "puesto_original_sheet": puesto_raw,
            "fecha_postulacion": c.get("fecha_postulacion", ""),
            "estado": c.get("estado", "Review Stage"),
            "direccion": addr_clean,
            "distancia_millas": dist_miles,
            "distancia_texto": c.get("distancia_texto", f"{dist_miles} mi"),
            "link_cv_resume": c.get("link_cv_resume", ""),
            "link_perfil": c.get("link_perfil", ""),
            "overall_score": pct,
            "classification": portal_class,
            "is_disqualified": is_disq,
            "sa_details": sa_details,
            "choice_score": round(choice_score, 1),
            "distance_score": round(distance_score, 1),
            "ai_score": round(ai_score, 1),
            "total_points": eval_res["total_score"],
            "max_points": eval_res["max_possible_score"],
            "summary": eval_res.get("summary", ""),
            "details": eval_res.get("details", []),
            "parsed_qa": qa_list
        }
        scored_candidates.append(candidate_card)

    # Ordenar por defecto: Prioridad (Mejores candidatos primero)
    scored_candidates.sort(key=lambda x: (not x["is_disqualified"], x["overall_score"]), reverse=True)

    result_payload = {
        "timestamp": time.time(),
        "kpis": kpi_counts,
        "total_candidatos": len(scored_candidates),
        "candidatos": scored_candidates
    }

    # Guardar en caché
    try:
        os.makedirs(os.path.dirname(PORTAL_CACHE_FILE), exist_ok=True)
        with open(PORTAL_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Portal Cache Save Error] {e}")

    return result_payload
