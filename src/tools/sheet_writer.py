"""
Módulo de Escritura y Sincronización en Google Sheets (gspread)
Permite al Agente de IA ejecutar modificaciones atómicas, insertar nuevos candidatos
y depurar filas de candidatos que avanzaron a entrevista.
"""
import os
import json
from typing import Dict, Any, List, Optional
import gspread
from google.oauth2.service_account import Credentials
from src.tools.sheet_auditor import DEFAULT_SHEET_ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SERVICE_ACCOUNT_FILE = "service_account.json"

def get_gspread_client() -> Optional[gspread.Client]:
    """Obtiene el cliente autenticado de gspread si existe el archivo service_account.json."""
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        try:
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            return gspread.authorize(creds)
        except Exception as e:
            print(f"[gspread Auth Error] {e}")
    return None

def is_service_account_configured() -> bool:
    """Verifica si las credenciales de Service Account están configuradas."""
    return os.path.exists(SERVICE_ACCOUNT_FILE)

def apply_reconciliation_to_sheet(sheet_id: str = DEFAULT_SHEET_ID) -> Dict[str, Any]:
    """
    Ejecuta las correcciones reales identificadas por la auditoría profunda:
    1. Corrige las discrepancias de puesto en las celdas de la columna E.
    2. Agrega al final del Sheet las filas de los candidatos faltantes con sus 17 columnas.
    3. Elimina las filas de los candidatos que ya pasaron a Entrevista / Oferta.
    """
    client = get_gspread_client()
    if not client:
        return {
            "success": False,
            "error": "No se encontró el archivo 'service_account.json'. Por favor configura las credenciales de Google Cloud para habilitar la escritura."
        }

    try:
        from src.tools.deep_reconciler import run_deep_workstream_audit
        from src.tools.maps_commute import calculate_candidate_commute

        # 1. Ejecutar auditoría previa para tener el mapa exacto de cambios
        audit = run_deep_workstream_audit(sheet_id)
        if "error" in audit:
            return {"success": False, "error": audit["error"]}

        sh = client.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0)

        changes_applied = {
            "posiciones_corregidas": 0,
            "filas_insertadas": 0,
            "filas_depuradas": 0,
            "detalles": []
        }

        # 2. Corregir discrepancias de puesto (Columna E)
        for disc in audit.get("discrepancias_de_puesto", []):
            row_num = disc["row_number"]
            new_pos = disc["puesto_correcto_workstream"] or disc["puesto_inferido_por_preguntas"]
            worksheet.update_cell(row_num, 5, new_pos)  # Columna 5 = E (puesto)
            changes_applied["posiciones_corregidas"] += 1
            changes_applied["detalles"].append(f"Fila {row_num} ({disc['nombre']}): Puesto actualizado a '{new_pos}'")

        # 3. Agregar candidatos faltantes al final del Sheet
        missing_cands = audit.get("candidatos_faltantes_en_sheet", [])
        if missing_cands:
            from src.tools.workstream_api import fetch_candidate_data
            new_rows = []
            for mc in missing_cands:
                uuid = mc["uuid"]
                full_data = fetch_candidate_data(uuid)
                cand_info = full_data.get("candidate_info", [])
                
                # Extraer dirección y calcular distancia
                addr = "No especificada"
                for item in cand_info:
                    q = item.get("question", "").lower()
                    if "address" in q or "dirección" in q:
                        raw_a = item.get("answer", "")
                        addr = raw_a[0] if isinstance(raw_a, list) and raw_a else str(raw_a)
                        break

                commute = calculate_candidate_commute(addr)
                
                # Armar respuestas_completas_json
                qa_list = [{"pregunta": item.get("question", ""), "respuesta": item.get("answer", [""])[0] if isinstance(item.get("answer"), list) and item.get("answer") else str(item.get("answer", ""))} for item in cand_info]
                qa_json_str = json.dumps(qa_list, ensure_ascii=False)
                
                dist_mi = commute.distance_miles if commute.distance_miles < 900 else 0.0
                dist_txt = f"{dist_mi} mi" if dist_mi > 0 else "No especificado"

                row_values = [
                    uuid,
                    mc.get("nombre", ""),
                    mc.get("email", ""),
                    mc.get("telefono", ""),
                    mc.get("puesto", "Front of House Team Member"),
                    mc.get("fecha_postulacion", ""),
                    mc.get("etapa", "Review Stage"),
                    addr,
                    str(dist_mi),
                    dist_txt,
                    "Yes",
                    "Open",
                    "Yes",
                    "",
                    qa_json_str,
                    f"https://hr.workstream.us/#/position-applications/{uuid}",
                    ""
                ]
                new_rows.append(row_values)

            if new_rows:
                worksheet.append_rows(new_rows)
                changes_applied["filas_insertadas"] = len(new_rows)
                for mc in missing_cands:
                    changes_applied["detalles"].append(f"Nuevo candidato agregado: {mc['nombre']} ({mc['puesto']})")

        # 4. Depurar candidatos que pasaron a entrevista (borrar desde la fila más alta hacia abajo)
        to_purge = audit.get("candidatos_para_depurar", [])
        if to_purge:
            # Ordenar descendente por número de fila para no desfasar índices
            to_purge_sorted = sorted(to_purge, key=lambda x: x["row_number"], reverse=True)
            for p in to_purge_sorted:
                worksheet.delete_rows(p["row_number"])
                changes_applied["filas_depuradas"] += 1
                changes_applied["detalles"].append(f"Fila {p['row_number']} depurada: {p['nombre']} (Avanzó a '{p['etapa_en_workstream']}')")

        # 5. Invalidar cachés locales para que el Portal y el Agente se sincronicen de inmediato
        for cache_path in [
            "src/tools/portal_scored_cache.json",
            "src/tools/sheet_local_cache.json",
            "src/tools/candidate_cache.json",
            "candidate_cache.json"
        ]:
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                except Exception:
                    pass

        return {
            "success": True,
            "resumen": changes_applied
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error al escribir en Google Sheet: {str(e)}"
        }
