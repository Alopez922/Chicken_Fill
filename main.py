"""
Punto de entrada principal para ejecutar y probar el Súper Agente de Selección con LangGraph.
"""
import sys
import os

# Forzar codificación UTF-8 en Windows para caracteres especiales y emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from src.graph import build_candidate_screening_graph
from src.tools.workstream_api import MOCK_CANDIDATES, list_workstream_candidates

console = Console(force_terminal=True, legacy_windows=False)

def run_evaluation(candidate_id: str, candidate_display_name: str = ""):
    display_title = candidate_display_name if candidate_display_name else candidate_id
    console.print(Panel.fit(
        f"[bold yellow]🍗 AGENTE DE SELECCIÓN INTELIGENTE (CHICKEN FILL)[/bold yellow]\n"
        f"[cyan]Evaluando candidato:[/cyan] [bold white]{display_title}[/bold white]",
        border_style="yellow"
    ))

    # 1. Compilar el Grafo
    graph = build_candidate_screening_graph()

    # 2. Inicializar el Estado
    initial_state = {
        "candidate_id": candidate_id,
        "position_title": "Team Member",
        "raw_candidate_data": {},
        "candidate_answers": [],
        "position_criteria": {},
        "commute_analysis": None,
        "evaluations": [],
        "pillar_analysis": None,
        "critic_review": None,
        "iteration_count": 0,
        "final_report": None,
        "agent_logs": []
    }

    # 3. Ejecutar el Grafo
    with console.status("[bold green]El Agente está pensando y analizando al candidato...", spinner="dots"):
        final_state = graph.invoke(initial_state)

    # 4. Mostrar el rastro de pensamiento del Agente (Logs)
    console.print("\n[bold cyan]🧠 Proceso de Razonamiento del Grafo:[/bold cyan]")
    for log in final_state["agent_logs"]:
        console.print(f"  {log}")

    # 5. Mostrar tabla de preguntas evaluadas
    console.print("\n[bold cyan]📊 Desglose de Evaluación de Preguntas:[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Pregunta", style="dim", width=35)
    table.add_column("Score", justify="center", width=10)
    table.add_column("Justificación y Evidencia", width=55)

    for ev in final_state["evaluations"]:
        score_color = "green" if ev.score >= 8 else ("yellow" if ev.score >= 5 else "red")
        table.add_row(
            ev.question_text[:35] + ("..." if len(ev.question_text) > 35 else ""),
            f"[{score_color}]{ev.score}/10[/{score_color}]",
            ev.reasoning
        )
    console.print(table)

    # 6. Mostrar el Veredicto Ejecutivo Final
    report = final_state["final_report"]
    if report:
        verdict_color = "green" if "IDEAL" in report.classification else ("yellow" if "POTENCIAL" in report.classification else "red")
        
        verdict_text = (
            f"[bold {verdict_color}]CLASIFICACIÓN:[/] [bold white]{report.classification}[/]\n"
            f"[bold cyan]COMPATIBILIDAD GLOBAL:[/] [bold white]{report.overall_match_percentage}%[/] "
            f"({report.total_score} / {report.max_possible_score} pts)\n\n"
            f"[bold white]{report.human_verdict_summary}[/bold white]\n\n"
            f"[bold yellow]📞 Preguntas personalizadas recomendadas para la llamada de RRHH:[/bold yellow]\n"
        )
        
        for idx, q in enumerate(report.tailored_interview_questions, 1):
            verdict_text += f"  [bold cyan]{idx}.[/bold cyan] {q}\n"

        console.print(Panel(verdict_text, title="[bold]📋 INFORME EJECUTIVO DE RRHH[/bold]", border_style=verdict_color))

def main():
    console.clear()
    console.print("[bold yellow]Selecciona una opción para probar el Agente LangGraph:[/bold yellow]\n")
    
    candidates = list(MOCK_CANDIDATES.keys())
    for i, cand_key in enumerate(candidates, 1):
        cand = MOCK_CANDIDATES[cand_key]
        console.print(f"[{i}] [bold cyan]{cand['name']}[/bold cyan] — {cand['position_title']} ({cand_key})")
    
    console.print(f"[{len(candidates)+1}] [bold green]Probar todos los perfiles de prueba en lote[/bold green]")
    console.print(f"[{len(candidates)+2}] [bold magenta]🔥 Consultar y evaluar el candidato MÁS RECIENTE de Workstream en vivo[/bold magenta]\n")

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = "1"

    if choice == "1":
        run_evaluation("candidato_01_proactivo")
    elif choice == "2":
        run_evaluation("candidato_02_lejos_pero_comprometido")
    elif choice == "3":
        run_evaluation("candidato_03_desinteresado")
    elif choice == "4":
        for cand_key in candidates:
            run_evaluation(cand_key)
            console.print("\n" + "="*80 + "\n")
    elif choice == "5":
        with console.status("[bold cyan]Consultando Workstream API...[/bold cyan]"):
            live_cands = list_workstream_candidates(status="in_progress", limit=5)
        if live_cands:
            first = live_cands[0]
            cand_uuid = first.get("uuid")
            cand_name = first.get("name") or "Candidato Workstream"
            run_evaluation(cand_uuid, candidate_display_name=f"{cand_name} (En vivo)")
        else:
            console.print("[bold red]No se pudieron obtener candidatos en vivo de Workstream.[/bold red]")

if __name__ == "__main__":
    main()
