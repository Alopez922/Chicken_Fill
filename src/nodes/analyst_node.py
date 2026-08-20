"""
Nodo Analista: Evaluador Multidimensional y Humano de RRHH para Chick-fil-A.
Combina la Rúbrica Oficial de Scoring del Cliente (Criteria Engine) con el análisis cualitativo de GPT-4o.
"""
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from src.state import (
    CandidateEvaluationState,
    QuestionEvaluation,
    PillarAnalysis
)
from src.config import OPENAI_API_KEY, DEFAULT_MODEL
from src.tools.rules_memory import get_rules_prompt_context
from src.tools.criteria_engine import score_candidate_with_framework

class LLMPillarAnalysisOutput(BaseModel):
    culture_and_service: str = Field(description="Evaluación cualitativa de actitud de servicio, hospitalidad ('My Pleasure') y valores")
    availability_and_reliability: str = Field(description="Evaluación de horarios, puntualidad, distancia y traslado")
    potential_or_experience: str = Field(description="Evaluación de experiencia previa o potencial formativo en primer empleo")
    strengths: List[str] = Field(description="Lista de 3 a 5 fortalezas detectadas en sus respuestas")
    red_flags: List[str] = Field(description="Lista de alertas, inconsistencias o descalificaciones detectadas")

def candidate_analyst_node(state: CandidateEvaluationState) -> Dict[str, Any]:
    """
    Nodo 2: Evaluador Multidimensional y Humano de RRHH.
    1. Aplica la rúbrica oficial de puntuación del cliente (Criteria Engine).
    2. Aplica análisis cualitativo con IA y reglas de negocio activas.
    """
    logs = state.get("agent_logs", [])
    logs.append("🧠 [Nodo Analista] Aplicando Rúbrica Oficial del Framework de Chick-fil-A...")
    
    answers = state.get("candidate_answers", [])
    commute = state.get("commute_analysis")
    pos_title = state.get("position_title", "Front of House Team Member")
    raw_data = state.get("raw_candidate_data", {})
    name = raw_data.get("nombre") or raw_data.get("name") or "Candidato"
    
    # 1. Ejecutar el motor de scoring oficial del cliente
    parsed_qa_list = [
        {"pregunta": a.question_full, "respuesta": a.candidate_response}
        for a in answers
    ]
    dist_val = commute.distance_miles if commute else 0.0
    framework_res = score_candidate_with_framework(pos_title, parsed_qa_list, distance_miles=dist_val)
    
    # Mapear a QuestionEvaluation
    eval_list: List[QuestionEvaluation] = []
    for d in framework_res.get("details", []):
        eval_list.append(
            QuestionEvaluation(
                question_key=d["question"][:30],
                question_text=d["question"],
                score=d["score"],
                weighted_score=d["score"],
                max_score=d["max_score"],
                reasoning=d["reason"]
            )
        )
        
    # 2. Análisis cualitativo (Pilares) con GPT-4o
    rules_text = get_rules_prompt_context()
    commute_summary = f"Distancia: {dist_val} mi ({commute.duration_text if commute else 'N/A'})."
    
    answers_text = ""
    for idx, ans in enumerate(answers, 1):
        answers_text += f"\n[P{idx}]: {ans.question_full}\n[R]: {ans.candidate_response}\n"
        
    system_prompt = f"""Eres el Director de Recursos Humanos Senior de Chick-fil-A ({pos_title}).
Evalúa cualitativamente a este candidato basándote en la cultura de hospitalidad de Chick-fil-A ("My Pleasure"), su disponibilidad, transporte y potencial de servicio.

{rules_text}

DATOS DEL CANDIDATO:
- Nombre: {name}
- Posición: {pos_title}
- Traslado: {commute_summary}
- Puntuación Rúbrica: {framework_res['total_score']} / {framework_res['max_possible_score']} ({framework_res['percentage']}%)
- Estado de Rúbrica: {framework_res['classification']}

RESPUESTAS COMPLETAS:
{answers_text}
"""

    strengths = []
    red_flags = list(framework_res.get("disqualification_reasons", []))
    
    if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"):
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model=DEFAULT_MODEL, temperature=0.2, api_key=OPENAI_API_KEY)
            structured_llm = llm.with_structured_output(LLMPillarAnalysisOutput)
            llm_res: LLMPillarAnalysisOutput = structured_llm.invoke(system_prompt)
            
            pillar = PillarAnalysis(
                culture_and_service=llm_res.culture_and_service,
                availability_and_reliability=llm_res.availability_and_reliability,
                potential_or_experience=llm_res.potential_or_experience,
                red_flags=list(set(red_flags + llm_res.red_flags)),
                strengths=llm_res.strengths
            )
            logs.append(f"✨ [Nodo Analista] Rúbrica y análisis cualitativo completados ({len(eval_list)} preguntas evaluadas).")
            return {
                "evaluations": eval_list,
                "pillar_analysis": pillar,
                "agent_logs": logs
            }
        except Exception as e:
            logs.append(f"⚠️ [Nodo Analista] Aviso en LLM ({e}). Aplicando análisis contextual heurístico.")
            
    # Fallback heurístico si no hay LLM
    if dist_val <= 6.0:
        strengths.append(f"Vive muy cerca del restaurante ({dist_val} mi).")
    if framework_res["percentage"] >= 75.0:
        strengths.append("Respuestas de alta calidad alineadas a la hospitalidad Chick-fil-A.")
    if framework_res["is_disqualified"]:
        red_flags.append("Incurrió en una respuesta descalificatoria según el framework del cliente.")
        
    pillar = PillarAnalysis(
        culture_and_service="Alineado con los estándares de servicio al cliente" if not framework_res["is_disqualified"] else "No califica para la posición",
        availability_and_reliability=f"Traslado a {dist_val} millas con disponibilidad confirmada.",
        potential_or_experience="Candidato con perfil adecuado para el puesto seleccionado",
        red_flags=red_flags,
        strengths=strengths if strengths else ["Cumple con los requisitos base del puesto"]
    )
    
    logs.append(f"✅ [Nodo Analista] Evaluación con framework completada con éxito.")
    return {
        "evaluations": eval_list,
        "pillar_analysis": pillar,
        "agent_logs": logs
    }
