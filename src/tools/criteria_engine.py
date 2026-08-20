"""
Motor de Scoring Oficial de Chick-fil-A Stafford basado en el Framework Google Sheet:
https://docs.google.com/spreadsheets/d/1P0G_SRgOgBSnZt2zAc3W2Gj77JVUGirTmgsMngUtEEY

Pestañas y GIDs Oficiales:
- FOH (Front of House Team Member): 130754344
- BOH (Back of House Team Member): 2101082756
- DD (Chick-fil-A Delivery Driver): 72313513
- SA (Systems Analyst): 806349230
- SL (Shift Leader): 1475216791
- DFOH (Front of the House Director): 336909315
- DBOH (Director of Back of House Operations): 143582961
- CONFIG (Scoring Config): 964924413
"""
import requests
import csv
import io
import re
import difflib
from typing import Dict, Any, List, Optional, Tuple

CRITERIA_SHEET_ID = "1P0G_SRgOgBSnZt2zAc3W2Gj77JVUGirTmgsMngUtEEY"

# GIDs de cada puesto en el nuevo Google Sheet
POSITION_TABS_GID = {
    # Front of House Team Member
    "front of house team member": 130754344,
    "front of house": 130754344,
    "foh": 130754344,

    # Back of House Team Member
    "back of house team member": 2101082756,
    "back of house": 2101082756,
    "boh": 2101082756,
    "cocina": 2101082756,

    # Chick-fil-A Delivery Driver
    "chick-fil-a delivery driver": 72313513,
    "delivery driver": 72313513,
    "driver": 72313513,
    "dd": 72313513,

    # Systems Analyst
    "systems analyst": 806349230,
    "system analyst": 806349230,
    "analista de sistemas": 806349230,
    "sa": 806349230,

    # Shift Leader
    "shift leader": 1475216791,
    "lider de turno": 1475216791,
    "sl": 1475216791,

    # Front of the House Director
    "front of the house director": 336909315,
    "director foh": 336909315,
    "dfoh": 336909315,

    # Director of Back of House Operations
    "director of back of house operations – high-volume restaurant": 143582961,
    "director of back of house operations": 143582961,
    "director boh": 143582961,
    "dboh": 143582961
}

# Caché en memoria de las reglas del nuevo Sheet
_CRITERIA_CACHE: Dict[int, List[Dict[str, Any]]] = {}

SPANISH_TO_ENGLISH_CHOICES = {
    "si": "Yes",
    "sí": "Yes",
    "no": "No",
    "abierto": "Open",
    "12th grade": "12th grade",
    "some college/university": "Some college/university",
    "experienced": "Experienced",
    "limited experience": "Limited Experience",
    "whatever it takes": "Whatever it takes",
    "lo que sea necesario": "Whatever it takes",
    "you are a team player": "You are a team player",
    "you are a team player and a good leader": "You are a team player and a good leader",
    "all the time": "All the time",
    "prefer not to say": "Prefer not to say",
    "quietly tell a manager": "Quietly tell a manager"
}

def get_tab_gid_for_position(position_name: str) -> int:
    """
    Obtiene el GID exacto de la pestaña del puesto asegurando precedencia estricta.
    Evalúa directores primero para evitar colisiones con Team Members y evitar fallbacks silenciosos erróneos.
    """
    p = position_name.lower().strip()
    
    # 1. Directores primero (precedencia alta)
    if "director of back of house" in p or "director back of house" in p or "dboh" in p or ("director" in p and ("back" in p or "boh" in p or "kitchen" in p or "cocina" in p)):
        return 143582961  # DBOH
    if "front of the house director" in p or "director front of house" in p or "dfoh" in p or ("director" in p and ("front" in p or "foh" in p or "servicio" in p)):
        return 336909315  # DFOH
    if "director" in p:
        return 336909315  # DFOH default director
        
    # 2. Shift Leader
    if "shift leader" in p or "lider de turno" in p or "líder de turno" in p or "sl" in p:
        return 1475216791  # SL
        
    # 3. Systems Analyst
    if "systems analyst" in p or "system analyst" in p or "analista de sistemas" in p or "sa" in p:
        return 806349230  # SA
        
    # 4. Delivery Driver
    if "delivery driver" in p or "chick-fil-a delivery driver" in p or "repartidor" in p or "dd" in p or "driver" in p:
        return 72313513  # DD
        
    # 5. Back of House Team Member
    if "back of house" in p or "boh" in p or "cocina" in p or "kitchen" in p or "cook" in p:
        return 2101082756  # BOH
        
    # 6. Front of House Team Member (Default operativo)
    return 130754344  # FOH

def fetch_position_criteria(position_name: str) -> List[Dict[str, Any]]:
    """
    Descarga y parsea la rúbrica oficial desde el nuevo Google Sheet del cliente (1P0G_SRgOgBSnZt2zAc3W2Gj77JVUGirTmgsMngUtEEY).
    Columnas: #, question_key, question_full, answer_option, score, disqualifies, ideal_answer, question_type
    """
    gid = get_tab_gid_for_position(position_name)
    if gid in _CRITERIA_CACHE:
        return _CRITERIA_CACHE[gid]
        
    url = f"https://docs.google.com/spreadsheets/d/{CRITERIA_SHEET_ID}/export?format=csv&gid={gid}"
    try:
        response = requests.get(url, timeout=12)
        if response.status_code != 200:
            print(f"[Criteria Engine] Error {response.status_code} al descargar GID {gid}")
            return []
            
        lines = list(csv.reader(io.StringIO(response.text)))
        if len(lines) < 2:
            return []
            
        rules = []
        # Header: #, question_key, question_full, answer_option, score, disqualifies, ideal_answer, question_type
        for row in lines[1:]:
            if not row or not any(row):
                continue
                
            q_num = row[0].strip() if len(row) > 0 else ""
            q_key = row[1].strip() if len(row) > 1 else ""
            q_full = row[2].strip() if len(row) > 2 else ""
            ans_opt = row[3].strip() if len(row) > 3 else ""
            score_str = row[4].strip() if len(row) > 4 else "0"
            disq_str = row[5].strip() if len(row) > 5 else "No"
            ideal_str = row[6].strip() if len(row) > 6 else ""
            q_type = row[7].strip().lower() if len(row) > 7 else "choice"
            
            try:
                score_val = float(score_str)
            except Exception:
                score_val = 0.0
                
            disqualifies = "yes" in disq_str.lower() or "si" in disq_str.lower()
            
            rules.append({
                "question_number": q_num,
                "question_key": q_key,
                "question_full": q_full,
                "question": q_full if q_full else q_key,
                "category": q_type.upper() if q_type else "GENERAL",
                "answer_option": ans_opt,
                "score": score_val,
                "disqualifies": disqualifies,
                "ideal_answer": ideal_str,
                "question_type": q_type
            })
            
        _CRITERIA_CACHE[gid] = rules
        return rules
    except Exception as e:
        print(f"[Criteria Engine Error] {e}")
        return []

def evaluate_distance_score(distance_miles: float, distance_rule: str) -> Tuple[float, float, str]:
    """Evalúa el score de distancia según la regla ideal_answer del sheet."""
    dist_max = 10.0
    if not distance_rule or "no_limit" in distance_rule.lower():
        return 10.0, dist_max, "Sin límite de distancia estricto (10/10 pts)"
        
    matches = list(re.finditer(r"([<>]=?)(\d+(?:\.\d+)?)mi=(\d+)", distance_rule))
    for m in matches:
        op, val_str, pts_str = m.groups()
        val = float(val_str)
        pts = float(pts_str)
        if op == "<=" and distance_miles <= val:
            return pts, dist_max, f"Distancia {distance_miles} mi <= {val} mi ({pts}/10 pts)"
        elif op == "<" and distance_miles < val:
            return pts, dist_max, f"Distancia {distance_miles} mi < {val} mi ({pts}/10 pts)"
        elif op == ">=" and distance_miles >= val:
            return pts, dist_max, f"Distancia {distance_miles} mi >= {val} mi ({pts}/10 pts)"
        elif op == ">" and distance_miles > val:
            return pts, dist_max, f"Distancia {distance_miles} mi > {val} mi ({pts}/10 pts)"
            
    # Fallback si no hubo match
    if distance_miles <= 10.0:
        return 10.0, dist_max, f"Excelente cercanía ({distance_miles} mi <= 10 mi) - 10/10 pts"
    elif distance_miles <= 15.0:
        return 8.0, dist_max, f"Distancia aceptable ({distance_miles} mi) - 8/10 pts"
    else:
        return 5.0, dist_max, f"Distancia lejana ({distance_miles} mi > 15 mi) - 5/10 pts"

def evaluate_open_text_score(
    q_key: str, 
    q_full: str, 
    candidate_answer: str, 
    ideal_answer: str, 
    max_score: float = 10.0
) -> Tuple[float, str]:
    """Evalúa respuestas de texto abierto y numéricas con heurística avanzada alineada al n8n AI Agent."""
    ans = str(candidate_answer).strip()
    ans_low = ans.lower()
    
    # 1. Expectativa salarial
    if "earnings" in q_key.lower() or "wage" in q_key.lower() or "minimum expected" in q_full.lower():
        nums = re.findall(r"\d+\.?\d*", ans)
        val = float(nums[0]) if nums else 14.0
        if val <= 14.0 or "open" in ans_low or "discutir" in ans_low or "experience" in ans_low:
            return min(9.0, max_score), f"Expectativa salarial competitiva (${val}/hr o abierta a discutir): 9/{max_score} pts"
        elif val <= 16.0:
            return min(6.0, max_score), f"Expectativa salarial moderada (${val}/hr): 6/{max_score} pts"
        else:
            return min(3.0, max_score), f"Expectativa salarial alta (${val}/hr > $16/hr): 3/{max_score} pts"
            
    # 2. Historial de trabajos y experiencia
    if "recent jobs" in q_key.lower() or "previous job" in q_full.lower():
        # Experiencia en Chick-fil-A previa
        if any(k in ans_low for k in ["chick-fil-a", "click-fil-a", "cfa"]):
            return max_score, f"Experiencia directa previa en Chick-fil-A: {max_score}/{max_score} pts"
        # Experiencia en restaurantes de servicio rápido / comida
        if any(k in ans_low for k in ["pollo campero", "subway", "arby", "carl", "mcdonald", "sonic", "burger", "wendy", "sodexo", "cook", "cocina", "kitchen", "restaurant", "paletas", "sweetwaters"]):
            return min(9.0, max_score), f"Trayectoria relevante en restaurantes / servicio de alimentos: 9/{max_score} pts"
        # Sin experiencia o primer empleo
        if any(k in ans_low for k in ["first job", "primer trabajo", "none", "ninguno", "dont have", "do not have", "n/a"]):
            return min(5.0, max_score), f"Primer empleo / sin historial previo: 5/{max_score} pts"
        # Otro trabajo general
        if len(ans) > 10:
            return min(7.5, max_score), f"Experiencia laboral en otros sectores: 7.5/{max_score} pts"
        return min(4.0, max_score), f"Información laboral muy breve: 4/{max_score} pts"

    # 3. Trabajo previo en Chick-fil-A (pregunta binaria o de texto)
    if "worked for chick-fil-a" in q_key.lower() or "worked for chick-fil-a" in q_full.lower():
        if any(k in ans_low for k in ["yes", "si", "sí", "click-fil-a", "chick-fil-a", "años", "years", "lider"]):
            return max_score, f"Experiencia previa en Chick-fil-A: {max_score}/{max_score} pts"
        return min(5.0, max_score), f"Sin experiencia previa en Chick-fil-A: 5/{max_score} pts"

    # 4. Team building / liderazgo
    if "team building" in q_key.lower() or "team building" in q_full.lower():
        if len(ans) > 30 and any(k in ans_low for k in ["equipo", "team", "lider", "leader", "ayudar", "help", "comunicacion", "support"]):
            return min(9.5, max_score), f"Excelente respuesta sobre trabajo en equipo y liderazgo: 9.5/{max_score} pts"
        elif len(ans) > 15:
            return min(7.5, max_score), f"Respuesta constructiva sobre equipo: 7.5/{max_score} pts"
        elif any(k in ans_low for k in ["na", "none", "no tengo", "no"]):
            return min(4.0, max_score), f"Sin ejemplos de liderazgo previo: 4/{max_score} pts"
        return min(6.0, max_score), f"Respuesta general: 6/{max_score} pts"

    # 5. Tell us about yourself / Por qué Chick-fil-A
    if "tell us about yourself" in q_key.lower() or "why do you" in q_key.lower():
        if len(ans) > 25:
            return min(9.0, max_score), f"Buena presentación y motivación hacia la marca: 9/{max_score} pts"
        elif len(ans) > 10:
            return min(7.0, max_score), f"Presentación adecuada: 7/{max_score} pts"
        return min(5.0, max_score), f"Presentación básica: 5/{max_score} pts"

    # Caso general
    if len(ans) > 15:
        return min(8.0, max_score), f"Respuesta clara y alineada: 8/{max_score} pts"
    return min(5.0, max_score), f"Respuesta estándar: 5/{max_score} pts"

def score_candidate_with_framework(
    position_title: str,
    parsed_qa: List[Dict[str, Any]],
    distance_miles: float = 0.0
) -> Dict[str, Any]:
    """
    Motor de evaluación completo y exacto basado en la configuración del nuevo Google Sheet (1P0G_SRgOgBSnZt2zAc3W2Gj77JVUGirTmgsMngUtEEY).
    Calcula:
    - Choice Score
    - Distance Score
    - AI / Open Text Score
    - Total Score y Porcentaje Final exacto.
    """
    rules = fetch_position_criteria(position_title)
    if not rules:
        return {
            "position": position_title,
            "total_score": 0.0,
            "max_possible_score": 100.0,
            "percentage": 0.0,
            "classification": "NO CALIFICA",
            "verdict_badge": "❌ NO CALIFICA",
            "action_recommendation": "Error cargando reglas de scoring.",
            "is_disqualified": False,
            "disqualification_reasons": [],
            "evaluated_questions_count": 0,
            "details": []
        }

    # Separar reglas por tipo
    choice_rules = [r for r in rules if r["question_type"] == "choice"]
    open_text_rules = [r for r in rules if r["question_type"] in ["open_text", "numeric"]]
    distance_rules = [r for r in rules if r["question_type"] == "distance"]

    # Mapa de respuestas del candidato
    cand_qa_map = {}
    for item in parsed_qa:
        q_text = str(item.get("pregunta", "")).strip()
        a_text = str(item.get("respuesta", "")).strip()
        cand_qa_map[q_text] = a_text

    scored_details = []
    choice_score = 0.0
    choice_max = 0.0
    open_text_score = 0.0
    open_text_max = 0.0
    is_disqualified = False
    disqualify_reasons = []

    # 1. EVALUAR CHOICE QUESTIONS
    # Agrupar opciones por question_key
    unique_choice_keys = list(dict.fromkeys([r["question_key"] for r in choice_rules]))
    for qk in unique_choice_keys:
        opts = [r for r in choice_rules if r["question_key"] == qk]
        q_full = opts[0]["question_full"]
        max_q_score = max([r["score"] for r in opts]) if opts else 10.0
        choice_max += max_q_score

        # Buscar respuesta del candidato
        cand_ans = None
        for q_candidate, a_candidate in cand_qa_map.items():
            if qk.lower() in q_candidate.lower() or q_candidate.lower() in q_full.lower() or q_full.lower() in q_candidate.lower():
                cand_ans = a_candidate
                break

        # Fallbacks de elegibilidad legal
        if cand_ans is None and ("eligible" in qk.lower() or "authorized" in qk.lower()):
            cand_ans = "Yes"

        if cand_ans is None:
            continue

        cand_ans_str = str(cand_ans).strip()
        cand_ans_norm = cand_ans_str.lower()
        if cand_ans_norm in SPANISH_TO_ENGLISH_CHOICES:
            cand_ans_norm = SPANISH_TO_ENGLISH_CHOICES[cand_ans_norm].lower()

        # Coincidencia con las opciones del framework
        matched_opt = None
        for r in opts:
            opt_norm = str(r["answer_option"]).strip().lower()
            if opt_norm == cand_ans_norm or opt_norm in cand_ans_norm or cand_ans_norm in opt_norm:
                matched_opt = r
                break

        if matched_opt:
            pts = float(matched_opt["score"])
            choice_score += pts
            if matched_opt["disqualifies"]:
                is_disqualified = True
                disqualify_reasons.append(f"Pregunta '{q_full}': Respuesta '{cand_ans_str}' descalifica automáticamente.")
            scored_details.append({
                "question": q_full,
                "answer": cand_ans_str,
                "score": pts,
                "max_score": max_q_score,
                "category": "Choice",
                "disqualifies": matched_opt["disqualifies"],
                "reason": f"Opción seleccionada: '{matched_opt['answer_option']}' ({pts}/{max_q_score} pts)"
            })
        else:
            min_pts = min([r["score"] for r in opts]) if opts else 0.0
            choice_score += min_pts
            scored_details.append({
                "question": q_full,
                "answer": cand_ans_str,
                "score": min_pts,
                "max_score": max_q_score,
                "category": "Choice",
                "disqualifies": False,
                "reason": f"Respuesta no estándar: '{cand_ans_str}' (puntaje base: {min_pts}/{max_q_score} pts)"
            })

    # 2. EVALUAR DISTANCE
    dist_rule_str = distance_rules[0]["ideal_answer"] if distance_rules else "<=10mi=10, >10mi=5"
    dist_score, dist_max, dist_reason = evaluate_distance_score(distance_miles, dist_rule_str)
    
    if distance_miles > 30.0:
        is_disqualified = True
        disqualify_reasons.append(f"Distancia inviable: {distance_miles} millas.")

    scored_details.append({
        "question": "Full Address / Commute Analysis",
        "answer": f"{distance_miles} millas",
        "score": dist_score,
        "max_score": dist_max,
        "category": "Distance",
        "disqualifies": distance_miles > 30.0,
        "reason": dist_reason
    })

    # 3. EVALUAR OPEN TEXT / NUMERIC
    unique_open_keys = list(dict.fromkeys([r["question_key"] for r in open_text_rules]))
    for qk in unique_open_keys:
        sample_r = next(r for r in open_text_rules if r["question_key"] == qk)
        q_full = sample_r["question_full"]
        ideal_ans = sample_r["ideal_answer"]
        max_q_score = float(sample_r["score"]) if sample_r["score"] > 0 else 10.0
        open_text_max += max_q_score

        cand_ans = ""
        for q_candidate, a_candidate in cand_qa_map.items():
            if qk.lower() in q_candidate.lower() or q_candidate.lower() in q_full.lower() or q_full.lower() in q_candidate.lower():
                cand_ans = a_candidate
                break

        if not cand_ans:
            continue

        pts, reason_txt = evaluate_open_text_score(qk, q_full, cand_ans, ideal_ans, max_q_score)
        open_text_score += pts
        scored_details.append({
            "question": q_full,
            "answer": cand_ans,
            "score": pts,
            "max_score": max_q_score,
            "category": "Open Text / AI",
            "disqualifies": False,
            "reason": reason_txt
        })

    total_obtained = choice_score + dist_score + open_text_score
    max_total = choice_max + dist_max + open_text_max
    if max_total == 0:
        max_total = 100.0

    percentage = round((total_obtained / max_total) * 100, 1)

    if is_disqualified:
        classification = "AUTO-DESCALIFICADO"
        verdict_badge = "⛔ RECHAZADO (Auto-Descalificado)"
        if disqualify_reasons:
            reasons_str = " · ".join(disqualify_reasons[:2])
            action_recommendation = f"Auto-descalificado: {reasons_str}"
        else:
            action_recommendation = "No llamar. Incurrió en causa descalificatoria o distancia inviable."

    elif percentage >= 97.0:
        classification = "IDEAL - GOLD"
        verdict_badge = "🌟 CANDIDATO IDEAL (Gold - Top Priority)"
        action_recommendation = "Llamar de inmediato · Máxima prioridad de contratación."
    elif percentage >= 75.0:
        classification = "CANDIDATO IDEAL"
        verdict_badge = "✅ CANDIDATO IDEAL (High Quality)"
        action_recommendation = "Alta calidad · Agendar entrevista presencial/telefónica."
    elif percentage >= 50.0:
        classification = "POTENCIAL"
        verdict_badge = "⚠️ CANDIDATO POTENCIAL"
        action_recommendation = "Considerar en caso de que el pipeline esté bajo."
    else:
        classification = "NO CALIFICA"
        verdict_badge = "❌ NO CALIFICA"
        action_recommendation = "No llamar · Puntuación insuficiente para los estándares del local."

    return {
        "position": position_title,
        "total_score": round(total_obtained, 1),
        "max_possible_score": round(max_total, 1),
        "percentage": percentage,
        "choice_score": round(choice_score, 1),
        "distance_score": round(dist_score, 1),
        "open_text_score": round(open_text_score, 1),
        "classification": classification,
        "verdict_badge": verdict_badge,
        "action_recommendation": action_recommendation,
        "summary": action_recommendation,
        "is_disqualified": is_disqualified,
        "disqualification_reasons": disqualify_reasons,
        "evaluated_questions_count": len(scored_details),
        "details": scored_details
    }
