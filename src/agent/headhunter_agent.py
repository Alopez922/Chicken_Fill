"""
Agente Autónomo de Reclutamiento con Tool Calling (GPT-4o + LangGraph + Google Sheets + Memoria).
Maneja historial conversacional continuo, memoria de reglas permanente, búsquedas ad-hoc y decide autónomamente qué herramienta ejecutar.
"""
import json
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI

from src.config import OPENAI_API_KEY, STORE_NAME, STORE_ADDRESS
from src.tools.sheet_auditor import (
    audit_google_sheet, 
    find_candidate_in_sheet, 
    get_distinct_positions_from_sheet,
    get_processed_candidates,
    get_active_screening_candidates
)
from src.tools.talent_search import (
    search_and_rank_top_candidates, 
    get_best_candidate_for_every_position,
    compare_two_candidates,
    filter_candidates_by_custom_criteria,
    search_all_candidates_by_criteria
)
from src.tools.workstream_api import get_applicant_statistics, search_candidate_by_name
from src.tools.criteria_engine import fetch_position_criteria

# ========================================================
# DEFINICIÓN DE HERRAMIENTAS REALES PARA EL AGENTE
# ========================================================

@tool
def tool_auditar_google_sheet() -> str:
    """Audita el Google Sheet en tiempo real: verifica duplicados, etapas (activos vs contratados/entrevistados/rechazados) y estado general del pipeline."""
    report = audit_google_sheet()
    if not report.get("success"):
        return f"Error leyendo el Google Sheet: {report.get('error')}"
    return json.dumps(report, ensure_ascii=False)

@tool
def tool_evaluar_mejores_candidatos(posicion: str, cantidad: int = 3) -> str:
    """
    Busca, califica con el Framework Oficial de Chick-fil-A y rankea a los mejores candidatos generales (Top N) para un puesto específico (ej: Front of House, Back of House, etc.).
    NOTA: Si el usuario pide explícitamente candidatos QUE TENGAN EXPERIENCIA PREVIA o alguna condición especial, NO uses esta herramienta; usa 'tool_buscar_candidatos_con_filtros_personalizados'.
    """
    result = search_and_rank_top_candidates(position_query=posicion, top_n=cantidad, only_active=True)
    return json.dumps(result, ensure_ascii=False)

@tool
def tool_buscar_candidatos_con_filtros_personalizados(
    posicion: Optional[str] = None,
    requiere_experiencia_previa: bool = True,
    palabra_clave_experiencia: Optional[str] = None,
    distancia_maxima_millas: Optional[float] = None,
    requiere_vehiculo_transporte: bool = False,
    palabra_clave_general: Optional[str] = None,
    cantidad: int = 4
) -> str:
    """
    IMPORTANTE: Usa esta herramienta SIEMPRE que el usuario pregunte por candidatos QUE TENGAN EXPERIENCIA, o con filtros específicos (ej: 'qué candidatos tienen experiencia en back of house', 'candidatos con experiencia en cocina', 'quiénes han trabajado en comida rápida', 'quiénes viven a menos de 5 millas con carro', etc.).
    Filtra y extrae textualmente la evidencia laboral de los 296 candidatos del Google Sheet y los rankea por puntuación.
    """
    res = filter_candidates_by_custom_criteria(
        position_query=posicion,
        must_have_experience=requiere_experiencia_previa,
        experience_keyword=palabra_clave_experiencia,
        max_distance_miles=distancia_maxima_millas,
        must_have_transport=requiere_vehiculo_transporte,
        general_keyword=palabra_clave_general,
        limit=cantidad
    )
    return json.dumps(res, ensure_ascii=False)

@tool
def tool_cuadro_honor_todos_los_puestos() -> str:
    """Evalúa todos los puestos de la tienda y devuelve el mejor candidato (#1) para cada posición activa en el Google Sheet."""
    summary = get_best_candidate_for_every_position()
    return json.dumps(summary, ensure_ascii=False)

@tool
def tool_consultar_expediente_candidato(nombre_candidato: str) -> str:
    """
    Busca el expediente completo de un candidato por nombre o apellido en el Google Sheet.
    Devuelve sus respuestas completas, datos de contacto, distancia, puesto y etapa en la que se encuentra.
    """
    cand = find_candidate_in_sheet(nombre_candidato)
    if cand:
        return json.dumps(cand, ensure_ascii=False)
    cand_ws = search_candidate_by_name(nombre_candidato)
    if cand_ws:
        return json.dumps(cand_ws, ensure_ascii=False)
    return f"No se encontró ningún candidato con el nombre o apellido '{nombre_candidato}' en el sistema."

@tool
def tool_comparar_dos_candidatos(nombre_candidato_1: str, nombre_candidato_2: str) -> str:
    """Compara detalladamente a dos candidatos (puntuación del framework, fortalezas, debilidades, cercanía y preguntas de entrevista) para ayudar a decidir a quién contratar."""
    res = compare_two_candidates(nombre_candidato_1, nombre_candidato_2)
    return json.dumps(res, ensure_ascii=False)

@tool
def tool_consultar_criterios_oficiales_puesto(posicion: str) -> str:
    """Muestra la rúbrica oficial, preguntas clave, respuestas ideales y motivos de descalificación que el cliente configuró en su Google Sheet de Criterios para un puesto específico."""
    rules = fetch_position_criteria(posicion)
    if not rules:
        return f"No se encontraron criterios para el puesto '{posicion}'."
    
    summary = {
        "puesto": posicion,
        "total_preguntas_en_rubrica": len(rules),
        "descalificaciones_automaticas": [r for r in rules if r.get("disqualifies")],
        "muestra_criterios_ideales": [
            {"pregunta": r["question"], "opcion": r["answer_option"], "score": r["score"], "ideal": r["ideal_answer"]}
            for r in rules[:12] if r.get("ideal_answer")
        ]
    }
    return json.dumps(summary, ensure_ascii=False)



from src.tools.workstream_api import (
    fetch_candidate_data, 
    list_workstream_candidates, 
    search_candidate_by_name, 
    get_applicant_statistics,
    get_live_workstream_position_counts
)

from src.tools.deep_reconciler import run_deep_workstream_audit

@tool
def tool_estadisticas_postulaciones_hoy() -> str:
    """Obtiene cuántos candidatos se postularon hoy en Workstream y el total de candidatos activos en proceso."""
    stats = get_applicant_statistics()
    return json.dumps(stats, ensure_ascii=False)

@tool
def tool_conteo_candidatos_por_puesto_workstream() -> str:
    """Consulta la API de Workstream en vivo y devuelve el número exacto de candidatos que existen postulados para cada puesto y en qué etapa están."""
    stats = get_live_workstream_position_counts()
    return json.dumps(stats, ensure_ascii=False)

@tool
def tool_auditoria_profunda_workstream_vs_sheet() -> str:
    """
    Ejecuta una auditoría profunda de 4 capas entre la API en vivo de Workstream y el Google Sheet:
    1. Identifica discrepancias de Puesto, UUID y Nombre.
    2. Identifica candidatos en '1st Interview', 'Hired' u 'Oferta' que deben depurarse del Sheet.
    3. Identifica inconsistencias en las respuestas JSON y candidatos nuevos faltantes en el Sheet.
    """
    audit = run_deep_workstream_audit()
    return json.dumps(audit, ensure_ascii=False)

from src.tools.sheet_writer import apply_reconciliation_to_sheet, is_service_account_configured

@tool
def tool_aplicar_sincronizacion_y_limpieza_sheet() -> str:
    """
    Aplica las correcciones reales y la sincronización directamente en el Google Sheet:
    1. Corrige las celdas de puesto discrepantes.
    2. Inserta las filas de los candidatos nuevos faltantes desde Workstream.
    3. Elimina las filas de los candidatos que ya pasaron a Entrevista o fueron contratados.
    Solo debe ejecutarse cuando el usuario confirme explícitamente que desea aplicar los cambios.
    """
    if not is_service_account_configured():
        return "AVISO: Para modificar el Google Sheet en vivo, se requiere el archivo 'service_account.json'. Por favor proporciona las credenciales de Google Cloud o indícame si deseas configurarlo."
    
    result = apply_reconciliation_to_sheet()
    if result.get("success"):
        resumen = result.get("resumen", {})
        detalles = "\n".join(resumen.get("detalles", []))
        return (
            f"✅ Sincronización aplicada con éxito en el Google Sheet:\n"
            f"- Posiciones corregidas: {resumen.get('posiciones_corregidas', 0)}\n"
            f"- Nuevas filas insertadas: {resumen.get('filas_insertadas', 0)}\n"
            f"- Filas depuradas (candidatos que avanzaron): {resumen.get('filas_depuradas', 0)}\n\n"
            f"Detalle de cambios:\n{detalles}"
        )
    else:
        return f"❌ Error al sincronizar el Google Sheet: {result.get('error', 'Error desconocido')}"


from src.tools.systems_analyst_evaluator import evaluate_systems_analyst_applicant, batch_evaluate_systems_analysts
from src.tools.sheet_auditor import fetch_sheet_rows

@tool
def tool_evaluar_systems_analyst_estricto(solo_aprobados: bool = True) -> str:
    """
    Usa esta herramienta ÚNICAMENTE cuando el usuario pida la evaluación general o lista de aprobados/descartados
    del puesto Systems Analyst según los 2 requisitos mínimos obligatorios de RRHH (carrera en TI + 2 años de experiencia técnica).
    
    NOTA: NO uses esta herramienta si el usuario pregunta por CERTIFICACIONES (certificados, CCNA, CompTIA, Azure), SALARIOS, UNIVERSIDADES o HABILIDADES PUNTUALES. Para cualquier búsqueda de certificaciones o requisitos específicos usa 'tool_buscar_todos_los_candidatos_por_criterio'.
    """
    cands = fetch_sheet_rows()
    batch_res = batch_evaluate_systems_analysts(cands)
    
    if solo_aprobados:
        return json.dumps({
            "total_evaluados": batch_res["total_systems_analysts"],
            "total_aprobados": batch_res["total_aprobados"],
            "candidatos_aprobados": batch_res["candidatos_aprobados"][:10]
        }, ensure_ascii=False)
    else:
        return json.dumps(batch_res, ensure_ascii=False)

@tool
def tool_buscar_todos_los_candidatos_por_criterio(criterio_o_habilidad: str, posicion: Optional[str] = None) -> str:
    """
    HERRAMIENTA PRINCIPAL DE BÚSQUEDA Y FILTRADO:
    Usa esta herramienta OBLIGATORIAMENTE siempre que el usuario pregunte por:
    - CERTIFICACIONES (ej: 'certificaciones', 'certificados', 'certs', 'CCNA', 'CompTIA', 'Azure', 'AWS', 'Dell', 'Cisco', etc.).
    - EXPECTATIVA SALARIAL (ej: 'menos de $30/hr', 'sueldo', 'hourly rate', 'salario').
    - UNIVERSIDADES O TÍTULOS (ej: 'University of Houston', 'UH', 'Bachelor degree', 'Licenciatura', 'UTSA', 'HCC').
    - DISPONIBILIDAD (ej: 'fines de semana', 'turnos flexibles', 'noches').
    - HABILIDADES OPERACIONALES (ej: 'freidoras', 'cocina', 'caja', 'drive-thru', 'comida rápida', 'liderazgo').
    
    Escanea al 100% de los candidatos (bilingüe español/inglés) y devuelve a todos los que cumplen con sus evidencias y links de Workstream.
    """
    res = search_all_candidates_by_criteria(criterio_o_habilidad=criterio_o_habilidad, posicion=posicion)
    return json.dumps(res, ensure_ascii=False)

# Lista de herramientas conectadas al Agente
AGENT_TOOLS = [
    tool_auditar_google_sheet,
    tool_auditoria_profunda_workstream_vs_sheet,
    tool_aplicar_sincronizacion_y_limpieza_sheet,
    tool_buscar_todos_los_candidatos_por_criterio,
    tool_evaluar_systems_analyst_estricto,
    tool_evaluar_mejores_candidatos,
    tool_buscar_candidatos_con_filtros_personalizados,
    tool_cuadro_honor_todos_los_puestos,
    tool_consultar_expediente_candidato,
    tool_comparar_dos_candidatos,
    tool_consultar_criterios_oficiales_puesto,
    tool_estadisticas_postulaciones_hoy,
    tool_conteo_candidatos_por_puesto_workstream
]

TOOL_MAP = {t.name: t for t in AGENT_TOOLS}

def run_conversational_agent(user_message: str, chat_history: List[Dict[str, str]]) -> str:
    """
    Ejecuta el Agente Autónomo con GPT-4o, Tool Calling y Búsqueda Exhaustiva.
    """
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-TU_CLAVE"):
        return "Error: Clave de OpenAI no configurada en el archivo .env."

    system_prompt = f"""Eres el Super Agente Headhunter y Reclutador Senior con IA de Chick-fil-A ({STORE_NAME} en {STORE_ADDRESS}).

TIENES ACCESO TOTAL Y HERRAMIENTAS DIRECTAS A:
1. Google Sheet Data Lake (tu base de datos centralizada con 307 candidatos, respuestas y etapas).
2. Google Sheet de Criterios Oficiales (Candidate Screening Framework con las 7 posiciones oficiales).
3. API de Workstream (postulaciones en vivo y estadísticas).
4. Google Maps (distancias reales y cálculo de traslados).

DIRECTRICES CLAVE DE OPERACIÓN:
- BÚSQUEDA EXHAUSTIVA DE HABILIDADES, CERTIFICACIONES, SALARIO, UNIVERSIDAD Y EXPERIENCIA:
  * Si el usuario pregunta por CUALQUIER certificación (general como 'certificaciones', 'certificados', 'certs' o específicas como CCNA, CNA, Cisco, CompTIA, Azure, AWS, Dell, etc.), expectativa salarial ('menos de $30/hr'), universidades (UH, UTSA, HCC, Bachelor's degree), disponibilidad (fines de semana, turnos), o habilidades operacionales (freidoras, caja, drive-thru, fast food), DEBES LLAMAR OBLIGATORIAMENTE a 'tool_buscar_todos_los_candidatos_por_criterio(criterio_o_habilidad=..., posicion=...)'.
  * NUNCA asumas que nadie cumple un criterio basándote en un top general; esta herramienta escanea al 100% de los candidatos y te devuelve a todos los que coinciden con sus evidencias textuales y enlaces a Workstream.
- EVALUACIÓN ESTRICTA DE SYSTEMS ANALYST: Si el usuario pregunta por el puesto general de Systems Analyst (ej: 'quiénes califican para Systems Analyst', 'evalúa a los analistas de sistemas', 'quiénes tienen carrera y 2 años de experiencia en IT', 'cuál es el mejor candidato de systems analyst'), DEBES LLAMAR A 'tool_evaluar_systems_analyst_estricto'.
  * Detalla con precisión qué carrera de TI estudió cada candidato aprobado y cuántos años de experiencia técnica en IT tiene demostrables.
  * NOTA METODOLÓGICA OBLIGATORIA PARA SYSTEMS ANALYST:
    Siempre que evalúes, listes o recomiendes candidatos para Systems Analyst, DEBES INCLUIR al final de tu respuesta el siguiente bloque de transparencia metodológica:
    - Si respondes en ESPAÑOL:
      > 💡 **Nota Metodológica del Headhunter IA:**
      > *Esta calificación se genera relacionando las respuestas del formulario oficial (carrera en TI, historial laboral y certificaciones mencionadas). Debido a que no descargamos la hoja de vida en PDF de forma automática, este análisis es una **estimación aproximada basada en lo que el candidato declaró por escrito y puede presentar variaciones**. Te recomendamos abrir el enlace de Workstream para verificar el currículum adjunto y corroborar los datos durante la entrevista.*
    - Si respondes en INGLÉS:
      > 💡 **AI Evaluation Methodology Note:**
      > *This rating is generated by correlating the candidate's questionnaire responses (IT degree, work history, and mentioned certifications). Since attached PDF resumes are not downloaded automatically, this analysis is an **approximation based on the applicant's self-reported statements and may vary**. We recommend clicking the Workstream link to review the attached PDF resume and confirm their credentials during the interview.*
- AUDITORÍA PROFUNDA Y RECONCILIACIÓN (WORKSTREAM VS SHEET): Si el usuario te pide auditar, conciliar o comparar la API de Workstream con el Google Sheet (ej: 'audita el sheet contra workstream', 'compara los candidatos de la api con el sheet', 'revisa si hay inconsistencias o candidatos que ya pasaron a entrevista'), DEBES LLAMAR OBLIGATORIAMENTE a 'tool_auditoria_profunda_workstream_vs_sheet'.
  * Presenta siempre la tabla 'Antes vs Después' de forma clara.
  * Muestra claramente qué candidatos ya avanzaron a '1st Interview' o 'Hired' y deben depurarse del Sheet de screening activo.
  * Pregunta siempre al usuario si desea que se apliquen las correcciones sugeridas (Modo Consultivo con Aprobación).
- ESTRUCTURA DE RESPUESTA OFICIAL PARA PUESTOS REGULARES (FOH, BOH, Drivers, Shift Leaders, Directores):
  Cuando el usuario pregunte por el mejor candidato o recomendación de un puesto (ej: 'cuál es el mejor candidato para Front of House', 'quién es el mejor para Back of House'):
  1. NIVEL 1 - PUNTAJE OFICIAL DEL FRAMEWORK (Fuente de la Verdad):
     Inicia SIEMPRE tu respuesta confirmando de forma ejecutiva y profesional el candidato #1 según la calificación oficial de Recursos Humanos en el Google Sheet:
     "Basado en la calificación oficial seleccionada por Recursos Humanos en el Framework de Chick-fil-A Stafford, el mejor candidato para [Puesto] es **[Nombre del #1]** con una puntuación de **[Score]%** ([Total Pts]/[Max Pts] pts). Cuenta con [Disponibilidad] y se ubica a [Distancia] millas de la tienda."
  2. NIVEL 2 - PERSPECTIVA CUALITATIVA DEL HEADHUNTER IA (Opinión Opcional / Complementaria):
     A continuación, añade una sección constructiva con tu análisis cualitativo de antecedentes:
     "💡 **Perspectiva del Headhunter IA:** Si deseas una opinión cualitativa más allá del puntaje numérico, analizando las respuestas abiertas e historial de trabajo previo, también te sugiero considerar a **[Candidato 2 o perfil con experiencia relevante]**, debido a su experiencia previa en [Sonic, restaurante, atención al cliente, etc.]."
- REGLA DE ORO DE FILTRADO: Si el usuario pregunta específicamente por candidatos CON EXPERIENCIA en un puesto (ej: 'qué candidatos tienen experiencia en back of house', 'candidatos con experiencia en cocina', 'quiénes han trabajado antes en restaurantes'), DEBES LLAMAR OBLIGATORIAMENTE a 'tool_buscar_candidatos_con_filtros_personalizados(posicion=..., requiere_experiencia_previa=True)'.
- NUNCA incluyas a un candidato sin experiencia previa cuando el usuario te haya pedido candidatos con experiencia.
- En tu respuesta, cita siempre el historial de trabajo exacto del candidato con sus enlaces a Workstream.
- Si el usuario pide el ranking general del puesto sin filtros de experiencia, usa 'tool_evaluar_mejores_candidatos'.
- Si el usuario pregunta por el conteo en vivo de postulaciones en Workstream, usa 'tool_conteo_candidatos_por_puesto_workstream'.

IDIOMA Y ESTILO BILINGÜE:
- AUTO-DETECCIÓN DE IDIOMA:
  * Si el usuario te escribe en ESPAÑOL, responde completamente en ESPAÑOL profesional, cálido, ágil y ejecutivo de Recursos Humanos de Chick-fil-A.
  * If the user writes in ENGLISH, respond completely in professional, warm, executive ENGLISH suitable for Chick-fil-A Leadership and HR Recruiters (*"It's my pleasure to assist you..."*).
- Sé estructurado, preciso y cita siempre los hechos reales de las respuestas del candidato con sus enlaces a Workstream.
"""

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2, api_key=OPENAI_API_KEY)
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)

    messages = [SystemMessage(content=system_prompt)]
    
    for msg in chat_history[-14:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
            
    if not messages or messages[-1].content != user_message:
        messages.append(HumanMessage(content=user_message))

    try:
        ai_response = llm_with_tools.invoke(messages)
        
        if ai_response.tool_calls:
            messages.append(ai_response)
            for tool_call in ai_response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                if tool_name in TOOL_MAP:
                    tool_func = TOOL_MAP[tool_name]
                    tool_output = tool_func.invoke(tool_args)
                    messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
                    
            final_response = llm.invoke(messages)
            return final_response.content
        else:
            return ai_response.content
            
    except Exception as e:
        return f"Ocurrió un error al procesar tu solicitud con el Agente: {e}"
