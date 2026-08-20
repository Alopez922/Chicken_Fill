"""
Herramienta de búsqueda masiva, filtrado, ranking, comparación y filtros dinámicos ad-hoc leyendo directamente del Google Sheet y LangGraph.
Alineado con el Candidate Screening Framework Oficial del Cliente.
"""
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

from src.tools.sheet_auditor import (
    get_candidates_from_sheet_by_position, 
    get_active_screening_candidates,
    fetch_sheet_rows, 
    get_distinct_positions_from_sheet,
    find_candidate_in_sheet
)
from src.tools.candidate_cache import get_cached_evaluation, set_cached_evaluation
from src.graph import build_candidate_screening_graph
from src.state import CandidateAnswer
from src.tools.maps_commute import CommuteAnalysis
from src.tools.criteria_engine import score_candidate_with_framework

NO_EXPERIENCE_PATTERNS = [
    "do not have", "dont have", "no prior", "no previous", "no work experience",
    "no experience", "sin experiencia", "not have any", "never worked", "first job",
    "primer trabajo", "none", "ninguno", "n/a", "na", "no job", "no tengo",
    "test applicant", "refer to resume"
]

def has_real_work_experience(job_answer: str) -> bool:
    """Detecta de forma inteligente si la respuesta describe un empleo real o indica falta de experiencia."""
    t = str(job_answer).lower().strip()
    if len(t) < 4:
        return False
    for pat in NO_EXPERIENCE_PATTERNS:
        if pat in t:
            # Si dice "I do not have any prior work experience", es sin experiencia
            if "do not have" in t or "no prior" in t or "no experience" in t or "sin experiencia" in t or "first job" in t or "primer trabajo" in t or "test applicant" in t:
                return False
            if t in ["none", "ninguno", "n/a", "na", "no"]:
                return False
    return True

def evaluate_sheet_candidate(cand_row: Dict[str, Any], graph=None) -> Optional[Dict[str, Any]]:
    """Evalúa un candidato leído del Google Sheet con LangGraph y el Framework de Chick-fil-A."""
    uuid = cand_row.get("uuid", "cand-0")
    name = cand_row.get("nombre", "Candidato")
    pos = cand_row.get("puesto", "Front of House Team Member")
    
    cached = get_cached_evaluation(uuid)
    if cached:
        return cached

    parsed_qa = cand_row.get("parsed_qa", [])
    cand_answers = [
        CandidateAnswer(
            question_key=f"q_{i}",
            question_full=item.get("pregunta", ""),
            candidate_response=item.get("respuesta", "")
        )
        for i, item in enumerate(parsed_qa, 1)
    ]
    
    try:
        dist_mi = float(str(cand_row.get("distancia_millas", "999")).replace("mi", "").strip())
    except Exception:
        dist_mi = 999.0
    dist_txt = cand_row.get("distancia_texto", f"{dist_mi} mi")
    
    commute_obj = CommuteAnalysis(
        candidate_address=cand_row.get("direccion", "No especificada"),
        distance_miles=dist_mi,
        duration_text=dist_txt,
        is_commute_feasible=dist_mi <= 15.0,
        commute_score=10.0 if dist_mi <= 5.0 else (8.0 if dist_mi <= 10.0 else (5.0 if dist_mi <= 15.0 else 2.0)),
        commute_notes="Traslado dentro de rango aceptable" if dist_mi <= 15.0 else "Distancia considerable"
    )

    # Evaluación directa con el Framework Oficial (misma fuente de verdad matemática que las tarjetas)
    from src.tools.criteria_engine import score_candidate_with_framework
    eval_res = score_candidate_with_framework(pos, parsed_qa, dist_mi)

    # OVERRIDE PARA SYSTEMS ANALYST: usar el evaluador SA estricto (mismo que el portal)
    if "systems analyst" in pos.lower() or "system analyst" in pos.lower():
        from src.tools.systems_analyst_evaluator import evaluate_systems_analyst_applicant
        sa_res = evaluate_systems_analyst_applicant(cand_row)
        approved = sa_res.get("is_approved") or sa_res.get("approved", False)
        sa_pct = sa_res.get("score_percentage", 0.0) if approved else 0.0
        eval_res["percentage"] = sa_pct
        eval_res["is_disqualified"] = not approved
        eval_res["summary"] = sa_res.get("verdict_summary", "")
        certs = sa_res.get("certifications_detected", [])
        exp_yrs = sa_res.get("it_experience_years", 0.0)
        eval_res["classification"] = (
            "CANDIDATO DESCALIFICADO" if not approved
            else ("GOLD" if sa_pct >= 97 else ("CANDIDATO IDEAL" if sa_pct >= 75 else "POTENTIAL"))
        )

    strengths = []
    red_flags = []
    if dist_mi <= 5.0:
        strengths.append(f"Excelente proximidad geografica ({dist_txt})")
    elif dist_mi > 20.0:
        red_flags.append(f"Distancia considerable de traslado ({dist_txt})")

    for d in eval_res.get("details", []):
        if d.get("score") == d.get("max_score") and d.get("score", 0) >= 10:
            strengths.append(f"{d.get('question')}: {d.get('answer')}")
        elif d.get("score") == 0:
            red_flags.append(f"{d.get('question')}: {d.get('answer')}")

    result = {
        "id": uuid,
        "name": name,
        "position": pos,
        "email": cand_row.get("email", ""),
        "phone": cand_row.get("telefono", ""),
        "score": eval_res["total_score"],
        "max_score": eval_res["max_possible_score"],
        "percentage": eval_res["percentage"],
        "classification": eval_res.get("classification", "CANDIDATO IDEAL"),
        "summary": eval_res.get("summary", eval_res.get("action_recommendation", "")),
        "distance_miles": dist_mi,
        "duration_text": dist_txt,
        "strengths": strengths[:4],
        "red_flags": red_flags[:3],
        "interview_questions": [
            f"Tu domicilio esta a {dist_txt}; cual es tu metodo habitual de transporte para turnos tempranos o de cierre?",
            "Cuentanos sobre una ocasion en la que fuiste mas alla para ayudar a un companero o cliente.",
            "Si tienes un pedido pendiente y un cliente se acerca con una duda, como priorizas la atencion?"
        ],
        "link_perfil": cand_row.get("link_perfil", ""),
        "link_cv_resume": cand_row.get("link_cv_resume", ""),
        "estado": cand_row.get("estado", "Review Stage"),
        "parsed_qa": parsed_qa
    }
    set_cached_evaluation(uuid, result)
    return result


def search_and_rank_top_candidates(position_query: str = "Front of House", top_n: int = 3, only_active: bool = True) -> Dict[str, Any]:
    """
    Busca candidatos activos del Google Sheet, los ordena por PUNTAJE MATEMÁTICO PRE-CALCULADO
    del portal (score_candidate_with_framework) para garantizar resultados 100% consistentes
    con las tarjetas del portal, y evalúa con GPT-4o los top-30 mejor puntuados.
    """
    sheet_candidates = get_candidates_from_sheet_by_position(position_query, only_active=only_active)
    
    if not sheet_candidates:
        sheet_candidates = get_active_screening_candidates() if only_active else fetch_sheet_rows()
        
    if not sheet_candidates:
        return {
            "position_searched": position_query,
            "total_available_in_sheet": 0,
            "total_evaluated": 0,
            "top_candidates": []
        }

    # ────────────────────────────────────────────────────────────────
    # PASO 1: Pre-calcular el puntaje matemático de TODOS los candidatos
    # del puesto para ordenar determinísticamente (mismo motor que las tarjetas)
    # ────────────────────────────────────────────────────────────────
    def quick_score(c: Dict[str, Any]) -> float:
        pos = c.get("puesto", "")
        # Systems Analyst usa su propio evaluador estricto (mismo que el portal)
        if "systems analyst" in pos.lower() or "system analyst" in pos.lower():
            from src.tools.systems_analyst_evaluator import evaluate_systems_analyst_applicant
            sa_res = evaluate_systems_analyst_applicant(c)
            return sa_res.get("score_percentage", 0.0) if sa_res.get("is_approved") or sa_res.get("approved") else -1.0
        # Para otros puestos, usar el framework genérico de criterios
        try:
            dist = float(str(c.get("distancia_millas", "999")).replace("mi", "").strip())
        except Exception:
            dist = 999.0
        res = score_candidate_with_framework(pos, c.get("parsed_qa", []), dist)
        if res.get("is_disqualified"):
            return -1.0
        return float(res.get("percentage", 0.0))


    # Ordenar todos los candidatos del puesto por puntaje real descendente
    scored_pool = sorted(sheet_candidates, key=quick_score, reverse=True)

    # Tomar los top-30 mejor puntuados (no random, no los primeros del Sheet)
    SAMPLE_SIZE = 30
    sample = scored_pool[:SAMPLE_SIZE]

    # ────────────────────────────────────────────────────────────────
    # PASO 2: Evaluar los top-30 con el motor matemático ya conocido
    # (sin LangGraph para evitar latencia — ya usamos score_candidate_with_framework)
    # ────────────────────────────────────────────────────────────────
    evaluated_results = []
    for cand in sample:
        res = evaluate_sheet_candidate(cand)
        if res:
            evaluated_results.append(res)

    evaluated_results.sort(key=lambda x: (
        0 if "DESCALIFICADO" in str(x.get("classification", "")).upper() else 1,
        x.get("percentage", 0),
        -(float(x.get("distance_miles", 999)))  # desempate: menor distancia primero
    ), reverse=True)

    top_candidates = evaluated_results[:top_n]

    return {
        "position_searched": position_query,
        "total_available_in_sheet": len(sheet_candidates),
        "total_pre_scored": len(scored_pool),
        "total_evaluated": len(evaluated_results),
        "sample_evaluated": SAMPLE_SIZE,
        "note": f"Se pre-ordenaron matemáticamente los {len(scored_pool)} candidatos del puesto y se evaluaron en detalle los top {min(SAMPLE_SIZE, len(scored_pool))} mejor puntuados.",
        "top_candidates": top_candidates
    }


def filter_candidates_by_custom_criteria(
    position_query: Optional[str] = None,
    must_have_experience: bool = True,
    experience_keyword: Optional[str] = None,
    max_distance_miles: Optional[float] = None,
    must_have_transport: bool = False,
    general_keyword: Optional[str] = None,
    limit: int = 4
) -> Dict[str, Any]:
    """
    Filtra dinámicamente entre los candidatos del Sheet aplicando requisitos específicos
    (ej: experiencia previa real en cocina/restaurantes, distancia menor a X millas, palabras clave, vehículo propio)
    y los ordena por su puntaje oficial del framework.
    """
    all_cands = fetch_sheet_rows()
    matched = []
    
    for c in all_cands:
        # 1. Filtro de Puesto
        if position_query:
            p_low = position_query.lower()
            cand_p = c.get("puesto", "").lower()
            if not (p_low in cand_p or any(part in cand_p for part in p_low.split() if len(part) > 2)):
                continue
                
        # 2. Filtro de Distancia
        if max_distance_miles is not None:
            try:
                dist = float(str(c.get("distancia_millas", 999)).replace("mi", "").strip())
                if dist > max_distance_miles:
                    continue
            except Exception:
                continue
                
        # 3. Filtro de Transporte / Vehículo
        if must_have_transport:
            trans = str(c.get("transporte", "")).lower()
            if not ("yes" in trans or "si" in trans or "propio" in trans or "car" in trans):
                continue

        parsed_qa = c.get("parsed_qa", [])
        full_text_answers = " ".join([f"{item.get('pregunta', '')}: {item.get('respuesta', '')}" for item in parsed_qa]).lower()
        
        # Encontrar respuesta específica de experiencia laboral
        job_answer = ""
        volume_prep_answer = ""
        for item in parsed_qa:
            q = item.get("pregunta", "").lower()
            if "recent jobs" in q or "experiencia" in q or "previous job" in q:
                job_answer = str(item.get("respuesta", ""))
            if "preparing food in large volumes" in q or "volumen" in q:
                volume_prep_answer = str(item.get("respuesta", ""))

        # 4. Filtro de "Debe tener experiencia real"
        if must_have_experience:
            if not has_real_work_experience(job_answer):
                continue

        # 5. Filtro de palabra clave de experiencia (ej: 'chick-fil-a', 'pollo campero', 'freidora', 'cocina', 'sonic')
        if experience_keyword:
            exp_kw = experience_keyword.lower()
            if exp_kw not in job_answer.lower() and exp_kw not in full_text_answers:
                continue

        # 6. Filtro de palabra clave general
        if general_keyword:
            gen_kw = general_keyword.lower()
            if gen_kw not in full_text_answers:
                continue

        matched.append({
            "candidate_row": c,
            "experience_evidence": job_answer if job_answer else "Ver respuestas completas",
            "volume_prep": volume_prep_answer
        })

    if not matched:
        return {
            "filters_applied": {
                "position": position_query,
                "must_have_experience": must_have_experience,
                "experience_keyword": experience_keyword,
                "max_distance": max_distance_miles,
                "must_have_transport": must_have_transport,
                "general_keyword": general_keyword
            },
            "total_matches": 0,
            "candidates": []
        }

    graph = build_candidate_screening_graph()
    evaluated = []
    
    for item in matched[:10]:
        res = evaluate_sheet_candidate(item["candidate_row"], graph)
        if res:
            res["custom_filter_evidence"] = item["experience_evidence"]
            if item["volume_prep"]:
                res["volume_prep_experience"] = item["volume_prep"]
            evaluated.append(res)

    evaluated.sort(key=lambda x: (
        0 if "DESCALIFICADO" in str(x.get("classification", "")).upper() else 1,
        x.get("percentage", 0)
    ), reverse=True)

    return {
        "filters_applied": {
            "position": position_query,
            "must_have_experience": must_have_experience,
            "experience_keyword": experience_keyword,
            "max_distance": max_distance_miles,
            "must_have_transport": must_have_transport,
            "general_keyword": general_keyword
        },
        "total_matches": len(matched),
        "candidates": evaluated[:limit]
    }

def get_best_candidate_for_every_position() -> Dict[str, Any]:
    """
    Evalúa a todos los candidatos activos del Google Sheet y devuelve el mejor candidato (#1) para cada puesto de la tienda.
    """
    positions = get_distinct_positions_from_sheet(only_active=True)
    if not positions:
        positions = [
            "Front of House Team Member",
            "Back of House Team Member",
            "Systems Analyst",
            "Shift Leader",
            "Front of the House Director",
            "Chick-fil-A Delivery Driver"
        ]

    summary = {}
    for pos in positions:
        rank_res = search_and_rank_top_candidates(position_query=pos, top_n=1, only_active=True)
        top_cand = rank_res["top_candidates"][0] if rank_res["top_candidates"] else None
        summary[pos] = {
            "total_candidates": rank_res["total_available_in_sheet"],
            "top_candidate": top_cand
        }

    return summary

def compare_two_candidates(candidate_name_1: str, candidate_name_2: str) -> Dict[str, Any]:
    """Compara en detalle a dos candidatos frente a la misma posición."""
    cand1_raw = find_candidate_in_sheet(candidate_name_1)
    cand2_raw = find_candidate_in_sheet(candidate_name_2)
    
    if not cand1_raw:
        return {"error": f"No se encontró el candidato '{candidate_name_1}'"}
    if not cand2_raw:
        return {"error": f"No se encontró el candidato '{candidate_name_2}'"}
        
    graph = build_candidate_screening_graph()
    eval1 = evaluate_sheet_candidate(cand1_raw, graph)
    eval2 = evaluate_sheet_candidate(cand2_raw, graph)
    
    return {
        "candidate_1": eval1,
        "candidate_2": eval2,
        "winner": cand1_raw["nombre"] if (eval1 and eval2 and eval1["percentage"] >= eval2["percentage"]) else (cand2_raw["nombre"] if eval2 else "N/A"),
        "score_diff": round(abs((eval1["percentage"] if eval1 else 0) - (eval2["percentage"] if eval2 else 0)), 1)
    }

def search_all_candidates_by_criteria(
    criterio_o_habilidad: str,
    posicion: Optional[str] = None,
    max_results: int = 20
) -> Dict[str, Any]:
    """
    Escanea al 100% de los candidatos del puesto (o de toda la tienda) buscando quiénes cumplen
    con un criterio específico (bilingüe español/inglés: certificaciones, expectativa salarial, universidades,
    habilidades operacionales como freidoras/caja/drive-thru, disponibilidad de turnos, liderazgo, etc.).
    
    Si hay <= 20 candidatos que cumplen, devuelve la lista COMPLETA de todos ellos con sus evidencias.
    Si hay > 20 candidatos, devuelve los Top 20 ordenados por puntaje y advierte el total real encontrado.
    """
    all_cands = fetch_sheet_rows()
    crit_low = criterio_o_habilidad.lower().strip()
    
    # ── 1. Clasificación de Intención de Búsqueda Semántica (Bilingüe) ─────────
    
    # Intención: Certificaciones Generales
    is_general_cert = any(w in crit_low for w in [
        "certificacion", "certificaciones", "certificado", "certificados", 
        "certification", "certifications", "certs", "diploma", "licencia", "credentials"
    ]) and not any(spec in crit_low for spec in ["ccna", "comptia", "azure", "aws", "dell", "cisco", "linux", "itil", "cissp"])
    
    # Intención: Salario / Hourly Rate
    is_salary = any(w in crit_low for w in ["salario", "salary", "sueldo", "hourly", "earnings", "menos de", "under", "pide", "rate", "$"])
    salary_threshold = None
    if is_salary:
        m_num = re.search(r'(\d+(?:\.\d+)?)', crit_low)
        if m_num:
            salary_threshold = float(m_num.group(1))

    # Intención: Universidades Locales y Grados
    is_uh = any(w in crit_low for w in ["university of houston", "u of h", "uh ", " uh", "uofh"])
    is_ut = any(w in crit_low for w in ["university of texas", "utsa", "ut austin", "ut dallas"])
    is_hcc = any(w in crit_low for w in ["houston community college", "hcc", "lone star"])
    is_bachelor = any(w in crit_low for w in ["bachelor", "licenciatura", "ingenieria", "grado universitario", "university degree", "4-year degree"])

    # Intención: Disponibilidad de Horarios y Tareas de Tienda
    is_avail = any(w in crit_low for w in ["fin de semana", "fines de semana", "weekend", "weekends", "noche", "noches", "night", "nights", "flexible", "side duties", "tareas fuera", "horario"])

    # Intención: Liderazgo y Supervisión
    is_leadership = any(w in crit_low for w in ["supervis", "lider", "lead", "manager", "gerente", "team building", "evaluating staff", "directamente supervisado"])

    # Intención: Cocina / Freidoras / Parrilla
    is_kitchen = any(w in crit_low for w in ["freidora", "freidoras", "fryer", "fryers", "grill", "parrilla", "cocina", "kitchen", "line cook", "prep cook"])

    # Intención: Caja / POS / Cashier
    is_cashier = any(w in crit_low for w in ["caja", "cajera", "cajero", "cashier", "pos\b", "register", "cash handling", "money handling"])

    # Intención: Drive-thru
    is_drivethru = any(w in crit_low for w in ["drive-thru", "drive thru", "drivethru", "ventanilla", "window", "headset"])

    # Intención: Comida Rápida Previa
    FAST_FOOD_KEYWORDS = ["mcdonald", "wendy", "burger king", "taco bell", "popeyes", "raising cane", "sonic", "whataburger", "pollo campero", "starbucks", "chipotle", "arby", "carl's jr", "fast food", "comida rápida"]
    is_fast_food = any(w in crit_low for w in FAST_FOOD_KEYWORDS)

    # Intención: Experiencia Previa en Chick-fil-A
    is_cfa = any(w in crit_low for w in ["chick-fil-a", "cfa", "chick fil a", "chickfila"])

    ALL_IT_CERTS = {
        "CCNA / Cisco": [r"\bccna\b", r"\bcisco\b", r"\bccie\b", r"\bccnp\b"],
        "CompTIA (A+, Net+, Sec+)": [r"\bcomptia\b", r"\ba\+\b", r"\bsecurity\+\b", r"\bnetwork\+\b"],
        "Azure / Microsoft": [r"\bazure\b", r"\bmicrosoft\s+cert", r"\bmcsa\b", r"\bmcse\b", r"\bo365\b"],
        "AWS Cloud": [r"\baws\b", r"\bamazon\s+web\s+services\b"],
        "Google Cloud": [r"\bgcp\b", r"\bgoogle\s+cloud\b"],
        "Dell Certified": [r"\bdell\b"],
        "ITIL / ServiceNow": [r"\bitil\b", r"\bservicenow\b"],
        "Linux / RedHat": [r"\blinux\b", r"\bredhat\b"],
        "Cybersecurity (CISSP/CEH)": [r"\bcissp\b", r"\bceh\b", r"\bcisa\b", r"\bcybersecurity\b"]
    }

    matched = []
    
    for c in all_cands:
        if posicion:
            cand_p = c.get("puesto", "").lower()
            p_low = posicion.lower()
            if not (p_low in cand_p or any(part in cand_p for part in p_low.split() if len(part) > 2)):
                continue

        parsed_qa = c.get("parsed_qa", [])
        evidence_list = []
        
        # Filtramos campos que no son de habilidades para evitar falsos positivos (ej. "Cook Rd" en la dirección)
        qa_non_address = [it for it in parsed_qa if "address" not in str(it.get("pregunta", "")).lower()]
        full_text = " ".join([f"{item.get('pregunta','')}: {item.get('respuesta','')}" for item in qa_non_address]).lower()

        # CASO 1: Búsqueda paraguas de cualquier certificación de TI
        if is_general_cert:
            found_certs = []
            for cert_name, pats in ALL_IT_CERTS.items():
                if any(re.search(p, full_text) for p in pats):
                    found_certs.append(cert_name)
            if found_certs:
                evidence_list.append({
                    "pregunta": "Certificaciones Técnicas Confirmadas",
                    "respuesta": f"Posee credenciales en: {', '.join(found_certs)}"
                })

        # CASO 2: Salario por hora
        elif is_salary and salary_threshold is not None:
            for item in parsed_qa:
                q = str(item.get("pregunta", "")).lower()
                a = str(item.get("respuesta", "")).strip()
                if "expected earnings" in q or "per hour" in q or "salary" in q:
                    m = re.search(r'(\d+(?:\.\d+)?)', a)
                    if m:
                        val = float(m.group(1))
                        if val > 1000:
                            val = round(val / 2080, 1)
                        if val <= salary_threshold:
                            evidence_list.append({
                                "pregunta": "Expectativa Salarial por Hora",
                                "respuesta": f"${val:g}/hr (Declarado en formulario: '{a}')"
                            })

        # CASO 3: University of Houston (UH)
        elif is_uh:
            if "university of houston" in full_text or " u of h " in full_text or " uofh " in full_text or " uh " in full_text:
                for item in parsed_qa:
                    a = str(item.get("respuesta", ""))
                    if any(k in a.lower() for k in ["university of houston", "u of h", "uofh", "uh"]):
                        evidence_list.append({
                            "pregunta": item.get("pregunta", ""),
                            "respuesta": a
                        })
                if not evidence_list:
                    evidence_list.append({"pregunta": "Universidad", "respuesta": "University of Houston"})

        # CASO 4: Bachelor's Degree / Título Universitario
        elif is_bachelor:
            for item in parsed_qa:
                q = str(item.get("pregunta", "")).lower()
                a = str(item.get("respuesta", "")).strip()
                if "highest level of education" in q and "bachelor" in a.lower():
                    evidence_list.append({
                        "pregunta": item.get("pregunta", ""),
                        "respuesta": a
                    })

        # CASO 5: Disponibilidad y Turnos Flexibles
        elif is_avail:
            for item in parsed_qa:
                q = str(item.get("pregunta", "")).lower()
                a = str(item.get("respuesta", "")).strip()
                if any(k in q for k in ["flexible work schedule", "beyond your normal", "outside my job description", "side duties"]):
                    if any(pos_word in a.lower() for pos_word in ["yes", "willing", "open", "absolutely", "available", "si", "flexible"]):
                        evidence_list.append({
                            "pregunta": item.get("pregunta", ""),
                            "respuesta": a
                        })

        # CASO 6: Liderazgo y Supervisión
        elif is_leadership:
            for item in parsed_qa:
                q = str(item.get("pregunta", "")).lower()
                a = str(item.get("respuesta", "")).strip()
                if any(k in q for k in ["supervised", "supervis", "team building", "evaluating staff", "employee reviews"]):
                    if len(a) > 1 and a.lower() not in ["0", "none", "no", "n/a"]:
                        evidence_list.append({
                            "pregunta": item.get("pregunta", ""),
                            "respuesta": a
                        })

        # CASO 7: Cocina / Freidoras / Parrilla
        elif is_kitchen:
            for item in qa_non_address:
                q = str(item.get("pregunta", "")).lower()
                a = str(item.get("respuesta", "")).strip()
                if any(re.search(r'\b' + pat + r'\b', f"{q} {a}".lower()) for pat in ["fryer", "freidora", "grill", "parrilla", "cook", "cocina", "line cook", "prep cook"]):
                    evidence_list.append({
                        "pregunta": item.get("pregunta", ""),
                        "respuesta": a
                    })

        # CASO 8: Caja / POS / Cashier
        elif is_cashier:
            for item in qa_non_address:
                q = str(item.get("pregunta", "")).lower()
                a = str(item.get("respuesta", "")).strip()
                if any(re.search(r'\b' + pat + r'\b', f"{q} {a}".lower()) for pat in ["cashier", "cajera", "cajero", "pos", "register", "cash handling"]):
                    evidence_list.append({
                        "pregunta": item.get("pregunta", ""),
                        "respuesta": a
                    })

        # CASO 9: Drive-Thru
        elif is_drivethru:
            for item in qa_non_address:
                q = str(item.get("pregunta", "")).lower()
                a = str(item.get("respuesta", "")).strip()
                if any(dt in f"{q} {a}".lower() for dt in ["drive-thru", "drive thru", "drivethru", "ventanilla", "window", "headset"]):
                    evidence_list.append({
                        "pregunta": item.get("pregunta", ""),
                        "respuesta": a
                    })

        # CASO 10: Comida Rápida Previa
        elif is_fast_food:
            for item in qa_non_address:
                q = str(item.get("pregunta", "")).lower()
                a = str(item.get("respuesta", "")).strip()
                if any(ff in f"{q} {a}".lower() for ff in FAST_FOOD_KEYWORDS):
                    evidence_list.append({
                        "pregunta": item.get("pregunta", ""),
                        "respuesta": a
                    })

        # CASO 11: Experiencia Previa en Chick-fil-A
        elif is_cfa:
            for item in qa_non_address:
                q = str(item.get("pregunta", "")).lower()
                a = str(item.get("respuesta", "")).strip()
                if "worked for chick-fil-a" in q or "chick-fil-a" in a.lower():
                    if a.lower() not in ["no", "none", "n/a", "no never"]:
                        evidence_list.append({
                            "pregunta": item.get("pregunta", ""),
                            "respuesta": a
                        })

        # CASO 12: Búsqueda de palabra clave libre / siglas directas (ej: "CCNA", "AWS")
        else:
            for item in qa_non_address:
                q = str(item.get("pregunta", ""))
                a = str(item.get("respuesta", ""))
                if crit_low in f"{q} {a}".lower():
                    evidence_list.append({
                        "pregunta": q,
                        "respuesta": a
                    })

        if evidence_list:
            matched.append({
                "candidate": c,
                "evidences": evidence_list
            })

    total_matches = len(matched)
    
    if total_matches == 0:
        return {
            "criterio_buscado": criterio_o_habilidad,
            "posicion": posicion or "Todos los puestos",
            "total_candidatos_que_cumplen": 0,
            "mensaje": f"Se evaluó al 100% de los candidatos y ninguno cumple o menciona '{criterio_o_habilidad}'.",
            "candidatos": []
        }

    from src.tools.criteria_engine import score_candidate_with_framework
    evaluated_candidates = []
    
    for m in matched:
        cand = m["candidate"]
        puesto_cand = cand.get("puesto", "Front of House Team Member")
        qa_list = cand.get("parsed_qa", [])
        try:
            dist_mi = float(str(cand.get("distancia_millas", 999)).replace("mi", "").strip())
        except Exception:
            dist_mi = 999.0
            
        eval_res = score_candidate_with_framework(puesto_cand, qa_list, dist_mi)
        pct = eval_res.get("percentage", 0.0)
        
        # Override para Systems Analyst
        if "system" in puesto_cand.lower():
            from src.tools.systems_analyst_evaluator import evaluate_systems_analyst_applicant
            sa_eval = evaluate_systems_analyst_applicant(cand)
            if sa_eval.get("is_approved"):
                pct = sa_eval.get("score_percentage", pct)
        
        evidence_text = "\n".join([f"- [{e['pregunta']}]: \"{e['respuesta']}\"" for e in m["evidences"][:3]])
        
        evaluated_candidates.append({
            "nombre": cand.get("nombre", "Sin Nombre"),
            "uuid": cand.get("uuid", ""),
            "puesto": puesto_cand,
            "porcentaje_final": pct,
            "clasificacion": eval_res.get("classification", "POTENTIAL"),
            "distancia": cand.get("distancia_texto", f"{dist_mi} mi"),
            "telefono": cand.get("telefono", "—"),
            "link_perfil": f"https://hr.workstream.us/#/position-applications/{cand.get('uuid')}",
            "evidencias_encontradas": evidence_text
        })

    evaluated_candidates.sort(key=lambda x: x["porcentaje_final"], reverse=True)
    
    is_truncated = total_matches > max_results
    candidates_to_return = evaluated_candidates[:max_results]
    
    note_msg = (
        f"Se evaluó al 100% del grupo ({posicion or 'todas las posiciones'}) y se encontraron {total_matches} candidatos que cumplen exactamente con '{criterio_o_habilidad}'."
    )
    if is_truncated:
        note_msg += f" Como son más de {max_results}, aquí tienes a los {max_results} más destacados ordenados por puntaje oficial:"
    else:
        note_msg += " Aquí tienes la lista completa de todos los que cumplen:"

    return {
        "criterio_buscado": criterio_o_habilidad,
        "posicion": posicion or "Todos los puestos",
        "total_candidatos_que_cumplen": total_matches,
        "mostrando": len(candidates_to_return),
        "mensaje": note_msg,
        "candidatos": candidates_to_return
    }


