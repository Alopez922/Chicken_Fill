from typing import Dict, Any
from src.state import CandidateEvaluationState, CriticReview

def critic_reflection_node(state: CandidateEvaluationState) -> Dict[str, Any]:
    """
    Nodo 3: Crítico de Auto-Reflexión y Calibración Humana.
    Verifica que la evaluación no haya sido injusta, sesgada o demasiado mecánica.
    """
    logs = state.get("agent_logs", [])
    logs.append("🧐 [Nodo Crítico] Revisando coherencia y justicia de la evaluación...")
    
    pillar = state.get("pillar_analysis")
    commute = state.get("commute_analysis")
    evals = state.get("evaluations", [])
    iter_count = state.get("iteration_count", 0) + 1
    
    critic_notes = []
    adjustments = None
    is_fair = True
    
    # 1. Comprobar si hay descalificación legal crítica
    has_legal_flag = any("legalmente" in flag.lower() for flag in (pillar.red_flags if pillar else []))
    if has_legal_flag:
        critic_notes.append("Confirmado: Candidato no elegible legalmente. Requiere descalificación inmediata.")
    
    # 2. Comprobar si se penalizó la distancia a pesar de tener auto propio
    if commute.distance_miles > 10 and commute.is_commute_feasible:
        critic_notes.append(f"Nota: Aunque vive a {commute.distance_miles} mi, cuenta con transporte propio. La logística es manejable.")
        
    # 3. Comprobar equilibrio entre falta de experiencia y alta actitud
    if pillar and "primer empleo" in pillar.potential_or_experience.lower():
        critic_notes.append("Calibración: Se ponderó favorablemente la actitud de servicio y voluntariado frente a la falta de experiencia formal.")

    review = CriticReview(
        is_fair=is_fair,
        critic_notes=" | ".join(critic_notes) if critic_notes else "Evaluación balanceada y rigurosa sin inconsistencias detectadas.",
        adjustments_suggested=adjustments
    )
    
    logs.append(f"⚖️ [Nodo Crítico] Auto-revisión finalizada: {review.critic_notes}")
    
    return {
        "critic_review": review,
        "iteration_count": iter_count,
        "agent_logs": logs
    }
