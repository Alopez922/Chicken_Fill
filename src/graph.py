"""
Construcción y orquestación del Grafo de LangGraph para la evaluación de candidatos de Chicken Fill.
"""
from langgraph.graph import StateGraph, START, END
from src.state import CandidateEvaluationState
from src.nodes.fetch_node import fetch_and_enrich_candidate_node
from src.nodes.analyst_node import candidate_analyst_node
from src.nodes.critic_node import critic_reflection_node
from src.nodes.synthesizer_node import executive_synthesizer_node

def build_candidate_screening_graph():
    """
    Construye y compila el flujo agéntico de LangGraph.
    
    Flujo:
    START -> [fetch_and_enrich] -> [analyst_evaluation] -> [critic_reflection] -> [executive_synthesis] -> END
    """
    workflow = StateGraph(CandidateEvaluationState)

    # 1. Registrar los Nodos
    workflow.add_node("fetch_and_enrich", fetch_and_enrich_candidate_node)
    workflow.add_node("analyst_evaluation", candidate_analyst_node)
    workflow.add_node("critic_reflection", critic_reflection_node)
    workflow.add_node("executive_synthesis", executive_synthesizer_node)

    # 2. Definir las transiciones y conexiones
    workflow.add_edge(START, "fetch_and_enrich")
    workflow.add_edge("fetch_and_enrich", "analyst_evaluation")
    workflow.add_edge("analyst_evaluation", "critic_reflection")
    workflow.add_edge("critic_reflection", "executive_synthesis")
    workflow.add_edge("executive_synthesis", END)

    # 3. Compilar el grafo
    app = workflow.compile()
    return app
