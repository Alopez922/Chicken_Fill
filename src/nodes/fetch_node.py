from typing import Dict, Any, List
from src.state import CandidateEvaluationState, CandidateAnswer
from src.tools.workstream_api import fetch_candidate_data, fetch_position_criteria_dynamic
from src.tools.maps_commute import calculate_candidate_commute

def fetch_and_enrich_candidate_node(state: CandidateEvaluationState) -> Dict[str, Any]:
    """
    Nodo 1: Ingesta y enriquecimiento de datos.
    Descarga la postulación de Workstream, extrae preguntas/respuestas y analiza la logística de transporte.
    """
    cand_id = state.get("candidate_id", "candidato_01_proactivo")
    logs = state.get("agent_logs", [])
    logs.append(f"🔍 [Nodo Ingestión] Consultando datos del candidato: {cand_id}")
    
    # 1. Obtener datos crudos
    raw_data = fetch_candidate_data(cand_id)
    pos_title = raw_data.get("position_title", "Team Member")
    logs.append(f"📋 [Nodo Ingestión] Puesto aplicado: '{pos_title}'")
    
    # 2. Extraer respuestas estructuradas
    extracted_answers: List[CandidateAnswer] = []
    cand_info_list = raw_data.get("candidate_info", [])
    
    candidate_address = "No especificada"
    for item in cand_info_list:
        q_text = item.get("question", "")
        raw_ans = item.get("answer", "")
        clean_ans = raw_ans[0] if isinstance(raw_ans, list) and len(raw_ans) > 0 else str(raw_ans)
        
        # Identificar dirección
        if "address" in q_text.lower() or "dirección" in q_text.lower():
            candidate_address = clean_ans
            
        extracted_answers.append(
            CandidateAnswer(
                question_key=q_text[:30].strip(),
                question_full=q_text,
                question_type="open_text" if len(clean_ans) > 15 else "choice",
                candidate_response=clean_ans,
                max_score=10.0
            )
        )
    
    # 3. Analizar distancia y logística
    commute_info = calculate_candidate_commute(candidate_address)
    logs.append(f"🚗 [Nodo Logística] Distancia: {commute_info.distance_miles} mi ({commute_info.duration_text})")
    
    # 4. Criterios dinámicos por puesto
    criteria = fetch_position_criteria_dynamic(pos_title)
    
    return {
        "candidate_id": cand_id,
        "position_title": pos_title,
        "raw_candidate_data": raw_data,
        "candidate_answers": extracted_answers,
        "position_criteria": criteria,
        "commute_analysis": commute_info,
        "iteration_count": 0,
        "agent_logs": logs
    }
