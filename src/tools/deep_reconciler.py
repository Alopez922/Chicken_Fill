"""
Módulo de Auditoría Profunda y Conciliación de Datos (Deep Reconciler)
Compara en tiempo real la API de Workstream con el Google Sheet de Candidatos:
- Valida UUID, Nombre, Puesto y Cuestionario Completo (Q&A JSON).
- Identifica candidatos que avanzaron a Entrevista/Contratado para eliminarlos del Sheet.
- Detecta candidatos faltantes, inconsistencias de celda y corrupción de datos.
"""
import requests
import json
import collections
from typing import Dict, Any, List, Optional
from src.config import WORKSTREAM_API_KEY, WORKSTREAM_BASE_URL
from src.tools.sheet_auditor import fetch_sheet_rows, resolve_true_position_from_qa, DEFAULT_SHEET_ID

PURGE_STAGES = [
    "1st interview", "2nd interview", "interview", "entrevista",
    "hired", "contratado", "oferta", "offer sent", "offer accepted",
    "rejected", "rechazado", "archived", "archivado", "no show", "declined"
]

def run_deep_workstream_audit(sheet_id: str = DEFAULT_SHEET_ID) -> Dict[str, Any]:
    """
    Ejecuta una auditoría profunda de 4 capas:
    1. Identidad (UUID ↔ Nombre)
    2. Puesto (Workstream Position ↔ Sheet Puesto)
    3. Respuestas completas (Workstream candidate_info ↔ Sheet respuestas_completas_json)
    4. Ciclo de Vida y Depuración (Candidatos en Entrevista/Oferta para purgar)
    """
    if not WORKSTREAM_API_KEY or WORKSTREAM_API_KEY == "tu_workstream_api_key_aqui":
        return {"error": "API Key de Workstream no configurada."}

    # 1. Descargar postulaciones en vivo de Workstream con embed completo
    headers = {'Authorization': f'Bearer {WORKSTREAM_API_KEY}', 'Accept': 'application/json'}
    url = f"{WORKSTREAM_BASE_URL}/position_applications"
    params = {"status": "in_progress", "limit": 350, "embed": "(position,candidate_info)"}
    
    try:
        ws_res = requests.get(url, headers=headers, params=params, timeout=15)
        if ws_res.status_code != 200:
            return {"error": f"Error conectando a Workstream API: HTTP {ws_res.status_code}"}
        ws_data = ws_res.json()
        ws_apps = ws_data.get("position_applications", ws_data.get("data", []))
    except Exception as e:
        return {"error": f"Excepción consultando Workstream: {str(e)}"}

    # 2. Descargar filas del Google Sheet Data Lake
    sheet_cands = fetch_sheet_rows(sheet_id)
    
    # Mapeos rápidos para cruce de datos
    sheet_by_uuid = {}
    sheet_by_row = {}
    for c in sheet_cands:
        u = str(c.get("uuid", "")).strip().lower()
        if u:
            sheet_by_uuid[u] = c
        sheet_by_row[c.get("row_number")] = c

    ws_by_uuid = {}
    for a in ws_apps:
        u = str(a.get("uuid", "")).strip().lower()
        if u:
            ws_by_uuid[u] = a

    # Contenedores de resultados de la auditoría
    candidates_to_purge = []       # En etapa de entrevista/hired que deben salir del Sheet
    position_mismatches = []       # Puesto en Sheet no coincide con Workstream / respuestas
    qa_inconsistencies = []        # Respuestas faltantes o corruptas en el Sheet
    missing_in_sheet = []          # En Workstream pero faltan en el Sheet
    perfectly_synced = []          # 100% Íntegros

    # =========================================================================
    # REVISIÓN A: De Sheet hacia Workstream (Validar lo que ya está en el Sheet)
    # =========================================================================
    for c in sheet_cands:
        u = str(c.get("uuid", "")).strip().lower()
        nombre = c.get("nombre", "Sin Nombre")
        row_num = c.get("row_number")
        sheet_puesto = c.get("puesto_raw_sheet") or c.get("puesto", "")
        sheet_qa = c.get("parsed_qa", [])
        sheet_estado = c.get("estado", "")

        ws_cand = ws_by_uuid.get(u)

        if not ws_cand:

            # Ya no está en progreso en Workstream (Archivado, Rechazado o Eliminado)
            candidates_to_purge.append({
                "row_number": row_num,
                "uuid": u,
                "nombre": nombre,
                "puesto": sheet_puesto,
                "estado_en_sheet": sheet_estado,
                "etapa_en_workstream": "Archivado / Fuera de Workstream",
                "motivo_purga": "Ya no está en etapa 'Applications' activa en Workstream (debe depurarse del Sheet)"
            })
            continue

        # 1. Regla de Ciclo de Vida (Purga por avance a Entrevista / Hired)
        ws_stage = str(ws_cand.get("stage") or ws_cand.get("current_stage") or "Review Stage").strip()
        is_in_purge_stage = any(st in ws_stage.lower() for st in PURGE_STAGES)
        
        if is_in_purge_stage:
            candidates_to_purge.append({
                "row_number": row_num,
                "uuid": u,
                "nombre": nombre,
                "puesto": sheet_puesto,
                "estado_en_sheet": sheet_estado,
                "etapa_en_workstream": ws_stage,
                "motivo_purga": f"Avanzó a '{ws_stage}' (Interviews) en Workstream (ya gestionado por RRHH, debe depurarse del Sheet)"
            })
            continue


        # 2. Regla de Puesto
        ws_pos = (ws_cand.get("position") or {}).get("title") or ws_cand.get("position_title") or ""
        true_inferred_pos = resolve_true_position_from_qa(ws_pos or sheet_puesto, sheet_qa)
        
        has_pos_issue = False
        if ws_pos and sheet_puesto and ws_pos.lower().strip() != sheet_puesto.lower().strip():
            has_pos_issue = True
            position_mismatches.append({
                "row_number": row_num,
                "uuid": u,
                "nombre": nombre,
                "puesto_actual_en_sheet": sheet_puesto,
                "puesto_correcto_workstream": ws_pos,
                "puesto_inferido_por_preguntas": true_inferred_pos
            })

        # 3. Regla de Cuestionario y Respuestas
        ws_info = ws_cand.get("candidate_info", [])
        if len(ws_info) > 0 and len(sheet_qa) == 0:
            qa_inconsistencies.append({
                "row_number": row_num,
                "uuid": u,
                "nombre": nombre,
                "problema": f"JSON de respuestas vacío en Sheet, pero en Workstream tiene {len(ws_info)} respuestas completas."
            })
        elif len(ws_info) > 0 and abs(len(ws_info) - len(sheet_qa)) > 3:
            qa_inconsistencies.append({
                "row_number": row_num,
                "uuid": u,
                "nombre": nombre,
                "problema": f"Discrepancia en cantidad de preguntas: {len(sheet_qa)} en Sheet vs {len(ws_info)} en Workstream."
            })

        if not is_in_purge_stage and not has_pos_issue and len(sheet_qa) > 0:
            perfectly_synced.append({
                "row_number": row_num,
                "uuid": u,
                "nombre": nombre,
                "puesto": sheet_puesto
            })

    # =========================================================================
    # REVISIÓN B: De Workstream hacia Sheet (Detectar Candidatos Faltantes)
    # =========================================================================
    for a in ws_apps:
        u = str(a.get("uuid", "")).strip().lower()
        ws_stage = str(a.get("stage") or a.get("current_stage") or "Review Stage").strip()
        is_purge = any(st in ws_stage.lower() for st in PURGE_STAGES)

        # Solo nos interesan los candidatos pendientes de screening (Applications)
        if not is_purge and u not in sheet_by_uuid:
            ws_pos = (a.get("position") or {}).get("title") or a.get("position_title") or "Front of House Team Member"
            missing_in_sheet.append({
                "uuid": u,
                "nombre": a.get("name", "Sin Nombre"),
                "email": a.get("email", ""),
                "telefono": a.get("phone", ""),
                "puesto": ws_pos,
                "etapa": ws_stage,
                "fecha_postulacion": a.get("application_date", "")
            })

    total_apps_ws = sum(1 for a in ws_apps if not any(st in str(a.get("current_stage") or a.get("stage") or "").lower() for st in PURGE_STAGES))
    total_interviews_ws = len(ws_apps) - total_apps_ws

    return {
        "status": "success",
        "resumen_ejecutivo": {
            "total_applications_workstream": total_apps_ws,
            "total_interviews_workstream": total_interviews_ws,
            "total_candidatos_workstream_in_progress": len(ws_apps),
            "total_filas_en_google_sheet": len(sheet_cands),
            "candidatos_perfectamente_sincronizados": len(perfectly_synced),
            "candidatos_para_depurar": len(candidates_to_purge),
            "candidatos_para_depurar_por_entrevista": len(candidates_to_purge),
            "discrepancias_de_puesto": len(position_mismatches),
            "inconsistencias_de_respuestas_json": len(qa_inconsistencies),
            "candidatos_faltantes_en_sheet": len(missing_in_sheet)
        },
        "candidatos_para_depurar": candidates_to_purge,
        "discrepancias_de_puesto": position_mismatches,
        "inconsistencias_respuestas": qa_inconsistencies,
        "candidatos_faltantes_en_sheet": missing_in_sheet
    }

