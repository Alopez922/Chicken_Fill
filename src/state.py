from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# ==========================================
# MODELOS DE DATOS DETALLADOS (PYDANTIC)
# ==========================================

class CandidateAnswer(BaseModel):
    """Representa una respuesta dada por el candidato."""
    question_key: str = Field(description="Identificador corto de la pregunta")
    question_full: str = Field(description="Texto completo de la pregunta")
    question_type: str = Field(default="open_text", description="Tipo: choice, open_text, numeric, distance")
    candidate_response: Any = Field(description="Respuesta proporcionada por el candidato")
    ideal_criteria: Optional[str] = Field(default="", description="Criterio ideal esperado para esta pregunta")
    max_score: float = Field(default=10.0, description="Puntaje máximo asignable")

class CommuteAnalysis(BaseModel):
    """Análisis logístico de distancia y traslado hacia el local."""
    candidate_address: str = Field(default="", description="Dirección proporcionada por el candidato")
    distance_miles: float = Field(default=999.0, description="Distancia calculada en millas")
    duration_text: str = Field(default="No calculada", description="Tiempo estimado en auto/transporte")
    is_commute_feasible: bool = Field(default=True, description="Indica si la distancia es viable para el turno")
    commute_score: float = Field(default=0.0, description="Puntuación logística (0 a 10)")
    commute_notes: str = Field(default="", description="Observación sobre el traslado")

class QuestionEvaluation(BaseModel):
    """Evaluación individual de cada pregunta realizada por el nodo analista."""
    question_key: str
    question_text: str
    score: float = Field(ge=0, le=10, description="Puntaje asignado de 0 a 10")
    weighted_score: float = Field(default=0.0, description="Puntaje escalado al peso de la pregunta")
    max_score: float = Field(default=10.0, description="Puntaje máximo de la pregunta")
    reasoning: str = Field(description="Explicación humana y justificación del puntaje otorgado")
    key_evidence: Optional[str] = Field(default="", description="Cita o evidencia textual de la respuesta")

class PillarAnalysis(BaseModel):
    """Análisis por pilares fundamentales de selección de Chick-fil-A."""
    culture_and_service: str = Field(description="Evaluación de actitud, servicio al cliente y valores")
    availability_and_reliability: str = Field(description="Flexibilidad horaria, puntualidad y logística")
    potential_or_experience: str = Field(description="Valoración de experiencia previa o potencial si es primer empleo")
    red_flags: List[str] = Field(default_factory=list, description="Señales de alerta o inconsistencias detectadas")
    strengths: List[str] = Field(default_factory=list, description="Puntos fuertes más destacados")

class CriticReview(BaseModel):
    """Evaluación del nodo crítico para auto-corrección y eliminación de sesgos."""
    is_fair: bool = Field(default=True, description="¿La evaluación inicial fue justa y equilibrada?")
    critic_notes: str = Field(default="", description="Observaciones críticas sobre la evaluación")
    adjustments_suggested: Optional[str] = Field(default=None, description="Ajustes sugeridos a la puntuación o juicio")

class FinalHRReport(BaseModel):
    """Reporte ejecutivo final generado para el reclutador humano."""
    classification: str = Field(description="Clasificación: IDEAL - GOLD, CANDIDATO IDEAL, POTENCIAL, NO CALIFICA, AUTO-DESCALIFICADO")
    overall_match_percentage: float = Field(description="Porcentaje global de compatibilidad (0 a 100%)")
    total_score: float = Field(description="Puntos totales obtenidos")
    max_possible_score: float = Field(description="Puntos máximos posibles")
    human_verdict_summary: str = Field(description="Resumen ejecutivo en lenguaje humano explicando por qué contratar o no")
    tailored_interview_questions: List[str] = Field(
        default_factory=list,
        description="3 a 5 preguntas estratégicas personalizadas para que el reclutador las use en la llamada"
    )

# ==========================================
# ESTADO PRINCIPAL DEL GRAFO (LANGGRAPH)
# ==========================================

class CandidateEvaluationState(TypedDict):
    """Estado compartido que viaja entre los nodos del grafo de LangGraph."""
    # Identificadores básicos
    candidate_id: str
    position_title: str
    
    # Datos crudos obtenidos de la API
    raw_candidate_data: Dict[str, Any]
    candidate_answers: List[CandidateAnswer]
    position_criteria: Dict[str, Any]
    
    # Datos enriquecidos (Logística / Mapas)
    commute_analysis: CommuteAnalysis
    
    # Evaluaciones de los nodos especialistas
    evaluations: List[QuestionEvaluation]
    pillar_analysis: Optional[PillarAnalysis]
    
    # Nodo Crítico / Reflexión
    critic_review: Optional[CriticReview]
    iteration_count: int  # Para evitar bucles infinitos en el grafo
    
    # Reporte Final
    final_report: Optional[FinalHRReport]
    
    # Historial de logs / pensamiento del agente
    agent_logs: List[str]
