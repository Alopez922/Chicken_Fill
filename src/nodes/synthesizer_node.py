"""
Nodo Síntesis: Generación de Veredicto Ejecutivo Final y Guía de Entrevista.
Alineado con los estándares oficiales de clasificación de Chick-fil-A.
"""
from typing import Dict, Any, List
from src.state import CandidateEvaluationState, FinalHRReport

def executive_synthesizer_node(state: CandidateEvaluationState) -> Dict[str, Any]:
    """
    Nodo 4: Síntesis Ejecutiva y Plan de Entrevista Telefónica.
    Calcula el puntaje global, redacta el veredicto en lenguaje humano y genera las preguntas clave.
    """
    logs = state.get("agent_logs", [])
    logs.append("📝 [Nodo Síntesis] Consolidando informe ejecutivo según Framework Chick-fil-A...")
    
    evals = state.get("evaluations", [])
    commute = state.get("commute_analysis")
    pillar = state.get("pillar_analysis")
    raw_data = state.get("raw_candidate_data", {})
    name = raw_data.get("nombre") or raw_data.get("name") or "Candidato"
    pos_title = state.get("position_title", "Team Member")
    
    # Calcular totales directos de las evaluaciones del framework
    total_score = sum(e.score for e in evals)
    max_possible = sum(e.max_score for e in evals)
    
    if max_possible == 0:
        max_possible = 100.0
        
    percentage = round((total_score / max_possible) * 100, 1)
    
    # Determinar si existe descalificación
    is_disqualified = False
    if pillar and pillar.red_flags:
        for rf in pillar.red_flags:
            if any(k in rf.lower() for k in ["descalificación", "descalificado", "legalmente", "stealing", "felony", "no elegible"]):
                is_disqualified = True
                break
                
    # Clasificación oficial del Framework de Chick-fil-A
    if is_disqualified:
        classification = "AUTO-DESCALIFICADO"
        summary = (
            f"⛔ VEREDICTO: AUTO-DESCALIFICADO (NO LLAMAR).\n"
            f"{name} incurrió en una respuesta descalificatoria automática según el framework de selección de {pos_title}. "
            f"Alertas detectadas: {'; '.join(pillar.red_flags if pillar else [])}."
        )
    elif percentage >= 97.0:
        classification = "IDEAL - GOLD"
        summary = (
            f"🌟 VEREDICTO: CANDIDATO IDEAL GOLD — PRIORIDAD MÁXIMA (LLAMAR DE INMEDIATO).\n"
            f"{name} alcanzó una puntuación excepcional de {percentage}% ({total_score}/{max_possible} pts) para {pos_title}. "
            f"Cumple y supera los estándares más altos de hospitalidad ('My Pleasure'), disponibilidad y cercanía ({commute.distance_miles if commute else 'N/A'} mi)."
        )
    elif percentage >= 75.0:
        classification = "CANDIDATO IDEAL"
        summary = (
            f"✅ VEREDICTO: CANDIDATO IDEAL — AGENDAR ENTREVISTA.\n"
            f"{name} presenta un perfil de alta calidad con {percentage}% de compatibilidad para {pos_title}. "
            f"Demuestra actitud positiva, transporte confiable y respuestas sólidas en los criterios clave del puesto."
        )
    elif percentage >= 50.0:
        classification = "POTENCIAL"
        summary = (
            f"⚠️ VEREDICTO: CANDIDATO POTENCIAL (CONSIDERAR SI EL PIPELINE ESTÁ BAJO).\n"
            f"{name} obtuvo un {percentage}% de compatibilidad. Cumple con requisitos esenciales, pero se recomienda "
            f"profundizar en entrevista sobre áreas de oportunidad o disponibilidad horaria."
        )
    else:
        classification = "NO CALIFICA"
        summary = (
            f"❌ VEREDICTO: NO CALIFICA (NO LLAMAR).\n"
            f"{name} obtuvo un {percentage}% de compatibilidad, ubicándose por debajo del estándar mínimo requerido para {pos_title}."
        )

    # Generación de preguntas estratégicas para la llamada
    interview_questions: List[str] = []
    if commute and commute.distance_miles > 8.0:
        interview_questions.append(f"Tu domicilio está a {commute.distance_miles} millas; ¿cuál es tu método habitual de transporte para turnos tempranos o de cierre?")
    if pillar and any("primer" in s.lower() for s in pillar.strengths):
        interview_questions.append("Al ser uno de tus primeros empleos, ¿cómo te organizas para aprender rápido y trabajar bajo presión durante las horas pico?")
    
    interview_questions.append("Cuéntanos sobre una ocasión en la que fuiste más allá para ayudar a un compañero o cliente ('My Pleasure').")
    interview_questions.append("Si tienes un pedido pendiente y un cliente se acerca con una duda, ¿cómo priorizas la atención?")

    report = FinalHRReport(
        classification=classification,
        overall_match_percentage=percentage,
        total_score=round(total_score, 1),
        max_possible_score=round(max_possible, 1),
        human_verdict_summary=summary,
        tailored_interview_questions=interview_questions
    )
    
    logs.append(f"🏁 [Nodo Síntesis] Reporte oficial emitido: {classification} ({percentage}%)")
    
    return {
        "final_report": report,
        "agent_logs": logs
    }
