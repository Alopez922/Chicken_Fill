"""
Herramienta de Auditoría y Lectura Directa de Candidatos desde Google Sheet para LangGraph.
Incluye inferencia inteligente del puesto real a partir del cuestionario respondido en Workstream
para corregir inconsistencias del Data Lake.
"""
import os
import requests
import csv
import io
import json
import collections
from typing import Dict, Any, List, Optional
from src.tools.name_matcher import find_best_candidate_match

DEFAULT_SHEET_ID = "1hFZVyh6YwzHD13jCZDSs6zqxvJXZ_jNTHRTMh2OaqIM"

# Los 7 puestos EXACTOS y oficiales presentes en el Google Sheet
CANONICAL_POSITIONS = [
    "Front of House Team Member",
    "Back of House Team Member",
    "Front of the House Director",
    "Director of Back of House Operations – High-Volume Restaurant",
    "Shift Leader",
    "Systems Analyst",
    "Chick-fil-A Delivery Driver"
]

# Mapeo semántico directo hacia cada puesto oficial
POSITION_QUERY_MAPPING = {
    # 1. Front of House Team Member (Servicio Operativo)
    "front of house team member": "Front of House Team Member",
    "front of house": "Front of House Team Member",
    "foh": "Front of House Team Member",
    "caja": "Front of House Team Member",
    "servicio": "Front of House Team Member",
    "atencion al cliente": "Front of House Team Member",
    "drive thru": "Front of House Team Member",

    # 2. Back of House Team Member (Cocina Operativa)
    "back of house team member": "Back of House Team Member",
    "back of house": "Back of House Team Member",
    "boh": "Back of House Team Member",
    "cocina": "Back of House Team Member",
    "cocinero": "Back of House Team Member",
    "kitchen": "Back of House Team Member",
    "cook": "Back of House Team Member",

    # 3. Front of the House Director (Directivo FOH)
    "front of the house director": "Front of the House Director",
    "director foh": "Front of the House Director",
    "director front of house": "Front of the House Director",
    "director de servicio": "Front of the House Director",

    # 4. Director of Back of House Operations (Directivo BOH)
    "director of back of house operations – high-volume restaurant": "Director of Back of House Operations – High-Volume Restaurant",
    "director of back of house operations": "Director of Back of House Operations – High-Volume Restaurant",
    "director boh": "Director of Back of House Operations – High-Volume Restaurant",
    "director back of house": "Director of Back of House Operations – High-Volume Restaurant",
    "director de cocina": "Director of Back of House Operations – High-Volume Restaurant",
    "director cocina": "Director of Back of House Operations – High-Volume Restaurant",

    # 5. Shift Leader (Líder de Turno)
    "shift leader": "Shift Leader",
    "lider de turno": "Shift Leader",
    "líder de turno": "Shift Leader",

    # 6. Systems Analyst (Analista de Sistemas)
    "systems analyst": "Systems Analyst",
    "analista de sistemas": "Systems Analyst",
    "analista": "Systems Analyst",
    "sistemas": "Systems Analyst",
    "it": "Systems Analyst",

    # 7. Delivery Driver (Repartidor)
    "chick-fil-a delivery driver": "Chick-fil-A Delivery Driver",
    "delivery driver": "Chick-fil-A Delivery Driver",
    "repartidor": "Chick-fil-A Delivery Driver",
    "driver": "Chick-fil-A Delivery Driver",
    "chofer": "Chick-fil-A Delivery Driver"
}

PROCESSED_STAGES = [
    "1st interview", "2nd interview", "interview", "entrevista",
    "hired", "contratado", "oferta", "offer sent", "offer accepted",
    "rejected", "rechazado", "archived", "archivado", "no show", "declined"
]

def resolve_true_position_from_qa(puesto_raw: str, parsed_qa: List[Dict[str, Any]]) -> str:
    """
    Retorna el puesto oficial registrado en Workstream/Sheet.
    Workstream es la única fuente de verdad: nunca se sobreescribe un puesto oficial.
    Si el puesto está vacío o no es canónico, infiere a partir del cuestionario.
    """
    if puesto_raw and puesto_raw.strip() in CANONICAL_POSITIONS:
        return puesto_raw.strip()
    
    p_low = (puesto_raw or "").lower().strip()
    for canon in CANONICAL_POSITIONS:
        if canon.lower() == p_low or canon.lower() in p_low:
            return canon
            
    qa_text = " ".join([str(q.get("pregunta", "")).lower() for q in parsed_qa])
    
    # 1. Back of House (Cocina) - pregunta distintiva
    if "preparing food in large volumes" in qa_text or "large volumes" in qa_text:
        return "Back of House Team Member"
        
    # 2. Systems Analyst - pregunta distintiva
    if "dell system expert" in qa_text or "cisco certified" in qa_text or "comptia" in qa_text:
        return "Systems Analyst"
        
    # 3. Delivery Driver - pregunta distintiva
    if "texas driver license" in qa_text or "clean driving record" in qa_text:
        return "Chick-fil-A Delivery Driver"
        
    # 4. Directores y Shift Leader
    if "hiring and/or terminating staff" in qa_text or "banking and cash deposits" in qa_text or "employee reviews" in qa_text:
        if "director" in p_low and ("back" in p_low or "boh" in p_low or "kitchen" in p_low):
            return "Director of Back of House Operations – High-Volume Restaurant"
        if "director" in p_low and ("front" in p_low or "foh" in p_low):
            return "Front of the House Director"
        if "shift" in p_low or "leader" in p_low:
            return "Shift Leader"
            
    # 5. Front of House Team Member
    if "bagging food" in qa_text or "difficult guests" in qa_text:
        return "Front of House Team Member"
        
    return puesto_raw if puesto_raw else "Front of House Team Member"

def is_valid_candidate(c: Dict[str, Any]) -> bool:
    """Descarta registros de prueba ('test applicant') o con distancias imposibles."""
    name = str(c.get("nombre", "")).lower().strip()
    if not name or "test applicant" in name or "test" == name or "prueba" in name:
        return False
    # Para Systems Analyst no hay restricción de distancia
    pos = str(c.get("puesto", "")).lower()
    if "system" in pos or "analyst" in pos:
        return True
    try:
        dist = float(str(c.get("distancia_millas", 0)).replace("mi", "").strip())
        if dist > 35.0:
            return False
    except Exception:
        pass
    return True


def fetch_sheet_rows(sheet_id: str = DEFAULT_SHEET_ID, gid: int = 0) -> List[Dict[str, Any]]:
    """Descarga y parsea todas las filas del Google Sheet como una lista de diccionarios con puesto real inferido."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []
        
        rows = list(csv.reader(io.StringIO(response.text)))
        if len(rows) < 2:
            return []
            
        headers = [h.strip() for h in rows[0]]
        candidates = []
        
        for idx, row in enumerate(rows[1:], start=2):
            if not row or not any(row):
                continue
            row_dict = {}
            for col_idx, h in enumerate(headers):
                row_dict[h] = row[col_idx].strip() if col_idx < len(row) else ""
            row_dict["row_number"] = idx
            
            raw_qa = row_dict.get("respuestas_completas_json", "")
            qa_list = []
            if raw_qa:
                try:
                    qa_list = json.loads(raw_qa)
                except Exception:
                    qa_list = []
            row_dict["parsed_qa"] = qa_list
            
            # Puesto real inferido a partir del cuestionario para máxima precisión
            raw_puesto = row_dict.get("puesto", "Front of House Team Member")
            true_puesto = resolve_true_position_from_qa(raw_puesto, qa_list)
            row_dict["puesto"] = true_puesto
            row_dict["puesto_raw_sheet"] = raw_puesto
            
            candidates.append(row_dict)
            
        # Guardar en caché local si obtuvimos candidatos
        if candidates:
            try:
                os.makedirs("src/tools", exist_ok=True)
                with open("src/tools/sheet_local_cache.json", "w", encoding="utf-8") as f:
                    json.dump(candidates, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return candidates

        # Si no hubo candidatos, intentar leer de la caché local
        if os.path.exists("src/tools/sheet_local_cache.json"):
            with open("src/tools/sheet_local_cache.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        # Intentar con gspread si existe service_account.json
        if os.path.exists("service_account.json"):
            try:
                import gspread
                gc = gspread.service_account(filename="service_account.json")
                sh = gc.open_by_key(sheet_id)
                ws = sh.sheet1
                raw_records = ws.get_all_records()
                candidates = []
                for idx, r in enumerate(raw_records, start=2):
                    row_dict = dict(r)
                    row_dict["row_number"] = idx
                    raw_qa = str(row_dict.get("respuestas_completas_json", ""))
                    qa_list = []
                    if raw_qa.startswith("["):
                        try:
                            qa_list = json.loads(raw_qa)
                        except Exception:
                            qa_list = []
                    row_dict["parsed_qa"] = qa_list
                    raw_puesto = str(row_dict.get("puesto", "Front of House Team Member"))
                    row_dict["puesto"] = resolve_true_position_from_qa(raw_puesto, qa_list)
                    row_dict["puesto_raw_sheet"] = raw_puesto
                    st_low = str(row_dict.get("estado", "")).lower().strip()
                    row_dict["is_already_managed"] = any(p in st_low for p in PROCESSED_STAGES)
                    candidates.append(row_dict)
                if candidates:
                    with open("src/tools/sheet_local_cache.json", "w", encoding="utf-8") as f:
                        json.dump(candidates, f, ensure_ascii=False, indent=2)
                    return candidates
            except Exception as ge:
                print(f"[gspread fetch error] {ge}")

        print(f"[Sheet Reader Warning] {e} - Intentando cargar desde caché local...")
        if os.path.exists("src/tools/sheet_local_cache.json"):
            try:
                with open("src/tools/sheet_local_cache.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

def get_active_screening_candidates() -> List[Dict[str, Any]]:
    """Devuelve únicamente los candidatos válidos y pendientes de evaluación."""
    all_cands = fetch_sheet_rows()
    return [c for c in all_cands if not c.get("is_already_managed") and is_valid_candidate(c)]

def get_processed_candidates() -> List[Dict[str, Any]]:
    """Devuelve los candidatos que ya fueron procesados o pasaron a etapas manuales."""
    all_cands = fetch_sheet_rows()
    return [c for c in all_cands if c.get("is_already_managed")]

def get_distinct_positions_from_sheet(only_active: bool = True) -> List[str]:
    """Obtiene los nombres únicos de todos los puestos reales presentes en el Sheet."""
    return CANONICAL_POSITIONS

def find_candidate_in_sheet(query_name: str) -> Optional[Dict[str, Any]]:
    """
    Busca a un candidato específico por nombre y apellido con coincidencia estricta.
    """
    all_cands = fetch_sheet_rows()
    return find_best_candidate_match(query_name, all_cands)

def resolve_canonical_position(query: str) -> str:
    """Traduce cualquier consulta de usuario hacia el nombre EXACTO del puesto en el Google Sheet con prioridad estricta."""
    q_low = query.lower().strip()
    
    # 1. Coincidencia exacta directa
    if q_low in POSITION_QUERY_MAPPING:
        return POSITION_QUERY_MAPPING[q_low]
        
    # 2. Manejo explícito de directores para evitar colisión con roles operativos (Team Members)
    if "director" in q_low:
        if any(w in q_low for w in ["back", "boh", "cocina", "kitchen", "operations", "operaciones"]):
            return "Director of Back of House Operations – High-Volume Restaurant"
        if any(w in q_low for w in ["front", "foh", "servicio", "house"]):
            return "Front of the House Director"

    # 3. Priorizar frases más largas primero (ej. 'director of back of house' antes que 'back of house')
    sorted_keys = sorted(POSITION_QUERY_MAPPING.keys(), key=len, reverse=True)
    for k in sorted_keys:
        if k in q_low:
            return POSITION_QUERY_MAPPING[k]
            
    for k in sorted_keys:
        if q_low in k:
            return POSITION_QUERY_MAPPING[k]
            
    return "Front of House Team Member"

def get_candidates_from_sheet_by_position(position_query: str = "Front of House", only_active: bool = True) -> List[Dict[str, Any]]:
    """
    Filtra candidatos del Google Sheet con coincidencia ESTRICTA por puesto exacto.
    """
    all_cands = get_active_screening_candidates() if only_active else [c for c in fetch_sheet_rows() if is_valid_candidate(c)]
    target_pos = resolve_canonical_position(position_query)
    
    matched = []
    for c in all_cands:
        cand_pos = c.get("puesto", "").strip()
        
        if target_pos == "Front of House Team Member":
            if "front of house team member" in cand_pos.lower():
                matched.append(c)
        elif target_pos == "Back of House Team Member":
            if "back of house team member" in cand_pos.lower():
                matched.append(c)
        elif target_pos == "Front of the House Director":
            if "front of the house director" in cand_pos.lower() or ("director" in cand_pos.lower() and "front" in cand_pos.lower()):
                matched.append(c)
        elif target_pos == "Director of Back of House Operations – High-Volume Restaurant":
            if "director of back of house" in cand_pos.lower() or ("director" in cand_pos.lower() and "back" in cand_pos.lower()):
                matched.append(c)
        elif target_pos == "Shift Leader":
            if "shift leader" in cand_pos.lower():
                matched.append(c)
        elif target_pos == "Systems Analyst":
            if "system" in cand_pos.lower() or "analyst" in cand_pos.lower():
                matched.append(c)
        elif target_pos == "Chick-fil-A Delivery Driver":
            if "driver" in cand_pos.lower() or "delivery" in cand_pos.lower():
                matched.append(c)
                
    return matched

def audit_google_sheet(sheet_id: str = DEFAULT_SHEET_ID, gid: int = 0) -> Dict[str, Any]:
    """Audita el Google Sheet en tiempo real, incluyendo conteo por etapas y duplicados."""
    all_cands = fetch_sheet_rows(sheet_id, gid)
    if not all_cands:
        return {"success": False, "error": "No se pudieron cargar datos del Google Sheet."}
        
    uuid_map = collections.defaultdict(list)
    positions = collections.Counter()
    stages = collections.Counter()
    missing_fields = []
    managed_cands = []
    
    for c in all_cands:
        u = c.get("uuid", "")
        p = c.get("puesto", "Sin Puesto")
        st = c.get("estado", "Review Stage")
        dist = c.get("distancia_millas", "")
        
        if u:
            uuid_map[u].append(c)
        positions[p] += 1
        stages[st] += 1
        
        if c.get("is_already_managed"):
            managed_cands.append({
                "nombre": c.get("nombre"),
                "puesto": p,
                "estado": st,
                "row_number": c.get("row_number")
            })
        
        issues = []
        if not c.get("telefono"):
            issues.append("Sin teléfono")
        if not c.get("email"):
            issues.append("Sin email")
        if not dist or dist == "999":
            issues.append("Distancia no calculada")
        if issues:
            missing_fields.append({
                "row_number": c["row_number"],
                "nombre": c.get("nombre", "(Sin nombre)"),
                "issues": issues
            })
            
    dup_uuids = []
    for u, entries in uuid_map.items():
        if len(entries) > 1:
            dup_uuids.append({
                "uuid": u,
                "nombre": entries[0]["nombre"],
                "puesto": entries[0]["puesto"],
                "count": len(entries),
                "row_numbers": [e["row_number"] for e in entries]
            })
            
    active_count = len(all_cands) - len(managed_cands)
            
    return {
        "success": True,
        "total_rows": len(all_cands),
        "total_unique_candidates": len(uuid_map),
        "active_candidates_for_screening": active_count,
        "managed_candidates_count": len(managed_cands),
        "managed_candidates_sample": managed_cands[:10],
        "stages_breakdown": dict(stages),
        "duplicate_uuids_count": len(dup_uuids),
        "duplicate_candidates": dup_uuids,
        "positions_breakdown": dict(positions),
        "inconsistencies_count": len(missing_fields),
        "inconsistencies": missing_fields[:10]
    }
