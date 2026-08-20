import requests
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
from src.config import WORKSTREAM_API_KEY, WORKSTREAM_BASE_URL
from src.state import CandidateAnswer
from src.tools.maps_commute import calculate_candidate_commute

def fetch_position_criteria_dynamic(position_title: str) -> Dict[str, Any]:
    """Obtiene los criterios de evaluación dinámicos delegando a criteria_engine."""
    try:
        from src.tools.criteria_engine import fetch_position_criteria
        rules = fetch_position_criteria(position_title)
        return {
            "position": position_title,
            "rules_count": len(rules),
            "rules": rules
        }
    except Exception as e:
        print(f"[fetch_position_criteria_dynamic Error] {e}")
        return {"position": position_title, "rules": []}

MOCK_CANDIDATES = {
    "candidato_01_proactivo": {
        "uuid": "cfa-cand-001",
        "name": "Mateo Hernández",
        "email": "mateo.h@example.com",
        "phone": "+1 832 555 0192",
        "language": "es",
        "application_date": "2026-08-15",
        "position_title": "Front of House Team Member",
        "candidate_info": [
            {"question": "Full Address", "answer": ["11900 Murphy Rd, Stafford, TX 77477"]},
            {"question": "Are you legally eligible to work in the United States?", "answer": ["Yes"]},
            {"question": "¿Tienes experiencia previa en restaurantes o servicio al cliente?", "answer": ["Es mi primer trabajo formal, pero siempre he colaborado como voluntario en eventos de mi iglesia."]},
            {"question": "¿Qué harías si un cliente se queja de que su pedido está incompleto o frío?", "answer": ["Lo escucharía con una sonrisa, me disculparía y le repondría de inmediato el producto caliente."]},
            {"question": "¿Cuál es tu disponibilidad de horario para trabajar?", "answer": ["Disponible tardes y fines de semana completos."]},
            {"question": "¿Tienes transporte confiable?", "answer": ["Sí, tengo vehículo propio."]}
        ]
    }
}

def extract_position_title_safe(data: Dict[str, Any]) -> str:
    """
    Extracción multicapa segura del puesto de Workstream para evitar valores nulos por anidación dinámica.
    Soporta: data.position.title, data.position_application.position.title, data.position_title, data.puesto
    """
    if not isinstance(data, dict):
        return ""
    pos = (
        (data.get("position") or {}).get("title")
        or ((data.get("position_application") or {}).get("position") or {}).get("title")
        or data.get("position_title")
        or (data.get("position_application") or {}).get("position_title")
        or data.get("puesto")
        or ""
    )
    return str(pos).strip()

def fetch_candidate_data(candidate_id: str) -> Dict[str, Any]:
    """
    Obtiene los datos completos y respuestas de un candidato por UUID o ID desde Google Sheet / Workstream.
    Incluye embed obligatorio de position y candidate_info.
    """
    # 1. Buscar primero en el Google Sheet Data Lake
    try:
        from src.tools.sheet_auditor import fetch_sheet_rows
        all_cands = fetch_sheet_rows()
        for c in all_cands:
            if c.get("uuid") == candidate_id or c.get("nombre", "").lower() == candidate_id.lower():
                parsed_qa = c.get("parsed_qa", [])
                cand_info = [{"question": item.get("pregunta", ""), "answer": [item.get("respuesta", "")]} for item in parsed_qa]
                return {
                    "uuid": c.get("uuid"),
                    "name": c.get("nombre"),
                    "email": c.get("email"),
                    "phone": c.get("telefono"),
                    "position_title": c.get("puesto", "Front of House Team Member"),
                    "application_date": c.get("fecha_postulacion"),
                    "current_stage": c.get("estado"),
                    "candidate_info": cand_info
                }
    except Exception as e:
        print(f"[fetch_candidate_data Sheet Error] {e}")

    # 2. Buscar en MOCK_CANDIDATES
    if candidate_id in MOCK_CANDIDATES:
        return MOCK_CANDIDATES[candidate_id]

    # 3. Buscar en Workstream API en vivo con embed completo
    if WORKSTREAM_API_KEY and WORKSTREAM_API_KEY != "tu_workstream_api_key_aqui":
        try:
            headers = {"Authorization": f"Bearer {WORKSTREAM_API_KEY}", "Accept": "application/json"}
            url = f"{WORKSTREAM_BASE_URL}/position_applications/{candidate_id}"
            params = {"embed": "(position,candidate_info)"}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                raw_data = resp.json()
                data = raw_data.get("data") if ("data" in raw_data and isinstance(raw_data["data"], dict)) else raw_data
                pos_title = extract_position_title_safe(data)
                if not pos_title:
                    pos_title = "Front of House Team Member"
                data["position_title"] = pos_title
                return data
        except Exception as e:
            print(f"[fetch_candidate_data Workstream Error] {e}")

    return {
        "uuid": candidate_id,
        "name": "Candidato",
        "position_title": "Front of House Team Member",
        "candidate_info": []
    }

def list_workstream_candidates(status: str = "in_progress", limit: int = 50) -> List[Dict[str, Any]]:
    """Obtiene la lista de candidatos recientes desde la API de Workstream o fallback al Google Sheet."""
    if WORKSTREAM_API_KEY and WORKSTREAM_API_KEY != "tu_workstream_api_key_aqui":
        try:
            headers = {"Authorization": f"Bearer {WORKSTREAM_API_KEY}", "Accept": "application/json"}
            url = f"{WORKSTREAM_BASE_URL}/position_applications"
            params = {"status": status, "limit": limit, "embed": "(position)"}
            response = requests.get(url, headers=headers, params=params, timeout=8)
            if response.status_code == 200:
                raw_data = response.json()
                items = raw_data.get("data", raw_data) if isinstance(raw_data, dict) else raw_data
                if isinstance(items, list):
                    for item in items:
                        item["position_title"] = extract_position_title_safe(item)
                    return items
            elif response.status_code == 429:
                print("[Workstream API] Rate limit alcanzado. Usando Data Lake de Google Sheet.")
        except Exception as e:
            print(f"[Workstream List API Error] {e}")
            
    # Fallback transparente al Google Sheet Data Lake
    try:
        from src.tools.sheet_auditor import fetch_sheet_rows
        sheet_rows = fetch_sheet_rows()
        fallback_list = []
        for r in sheet_rows[:limit]:
            fallback_list.append({
                "uuid": r.get("uuid"),
                "name": r.get("nombre"),
                "email": r.get("email"),
                "phone": r.get("telefono"),
                "position_title": r.get("puesto"),
                "application_date": r.get("fecha_postulacion"),
                "current_stage": r.get("estado")
            })
        return fallback_list
    except Exception:
        return []

def search_candidate_by_name(query_name: str) -> Optional[Dict[str, Any]]:
    """
    Busca a un candidato por nombre o apellido en Google Sheet o Workstream.
    """
    try:
        from src.tools.sheet_auditor import find_candidate_in_sheet
        cand_sheet = find_candidate_in_sheet(query_name)
        if cand_sheet:
            return cand_sheet
    except Exception:
        pass
        
    return None

def get_applicant_statistics(target_date: str = None) -> Dict[str, Any]:
    """Analiza las postulaciones reales leyendo del Google Sheet / Workstream."""
    if not target_date:
        target_date = datetime.now().strftime("%Y-%m-%d")
        
    try:
        from src.tools.sheet_auditor import fetch_sheet_rows
        cands = fetch_sheet_rows()
    except Exception:
        cands = []

    total_pipeline = len(cands)
    applied_today = 0
    positions = {}
    stages = {}

    for c in cands:
        app_date = str(c.get("fecha_postulacion", ""))
        if target_date in app_date:
            applied_today += 1
            
        pos = c.get("puesto", "Sin Puesto")
        positions[pos] = positions.get(pos, 0) + 1
        
        st = c.get("estado", "Review Stage")
        stages[st] = stages.get(st, 0) + 1

    return {
        "fecha_consulta": target_date,
        "postulaciones_hoy": applied_today,
        "total_candidatos_en_pipeline": total_pipeline,
        "desglose_por_puesto": positions,
        "desglose_por_etapa": stages
    }

def get_live_workstream_position_counts() -> Dict[str, Any]:
    """
    Consulta en tiempo real a la API de Workstream y devuelve el conteo exacto estructurado
    por las pestañas oficiales de Workstream:
    1. Applications (pendientes de screening/revisión inicial)
    2. Interviews (en etapa de entrevista)
    3. Total en progreso
    """
    if not WORKSTREAM_API_KEY or WORKSTREAM_API_KEY == "tu_workstream_api_key_aqui":
        return get_applicant_statistics()

    try:
        from collections import Counter
        headers = {'Authorization': f'Bearer {WORKSTREAM_API_KEY}', 'Accept': 'application/json'}
        url = f"{WORKSTREAM_BASE_URL}/position_applications"
        params = {"status": "in_progress", "limit": 350}
        res = requests.get(url, headers=headers, params=params, timeout=12)
        if res.status_code == 200:
            d = res.json()
            apps = d.get("position_applications", d.get("data", []))
            
            # Separar por las pestañas exactas de Workstream
            applications_pending = []
            interviews_list = []
            
            for a in apps:
                stage = str(a.get("stage") or a.get("current_stage") or "Review Stage").lower()
                if "interview" in stage:
                    interviews_list.append(a)
                else:
                    applications_pending.append(a)
            
            pos_applications = Counter()
            for a in applications_pending:
                pos_title = (a.get("position") or {}).get("title") or a.get("position_title") or "Sin Puesto"
                pos_applications[pos_title] += 1
                
            pos_interviews = Counter()
            for a in interviews_list:
                pos_title = (a.get("position") or {}).get("title") or a.get("position_title") or "Sin Puesto"
                pos_interviews[pos_title] += 1
                
            return {
                "fuente": "Workstream API (En Vivo)",
                "pestaña_applications_pendientes_screening": {
                    "total": len(applications_pending),
                    "descripcion": "Candidatos en la pestaña Applications (Review Stage / Availability) listos para auditar y calificar",
                    "desglose_por_puesto": dict(pos_applications.most_common())
                },
                "pestaña_interviews": {
                    "total": len(interviews_list),
                    "descripcion": "Candidatos que ya pasaron a 1st Interview",
                    "desglose_por_puesto": dict(pos_interviews.most_common())
                },
                "total_candidatos_en_progreso": len(apps)
            }
    except Exception as e:
        print(f"[get_live_workstream_position_counts Error] {e}")

    return get_applicant_statistics()
