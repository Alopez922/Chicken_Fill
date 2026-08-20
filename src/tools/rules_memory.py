"""
Módulo de Memoria Persistente de Reglas y Criterios de Selección.
Permite al usuario 'educar' al Agente para que recuerde reglas de negocio para siempre.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any

RULES_FILE = Path(__file__).resolve().parent.parent.parent / "store_rules.json"

DEFAULT_RULES = [
    {
        "id": 1,
        "rule": "Es obligatorio e indispensable que el candidato sea legalmente elegible para trabajar en EE.UU. Si responde que no, queda auto-descalificado.",
        "category": "legal",
        "created_at": "2026-08-15"
    },
    {
        "id": 2,
        "rule": "Para el puesto de Back of House (Cocina), priorizar a candidatos con experiencia en freidoras, parrilla o ritmo rápido de comida.",
        "category": "position_specific",
        "created_at": "2026-08-15"
    },
    {
        "id": 3,
        "rule": "Para Front of House, si es primer empleo, valorar altamente la actitud de servicio ('My Pleasure'), amabilidad y voluntariado.",
        "category": "culture",
        "created_at": "2026-08-15"
    }
]

def load_rules() -> List[Dict[str, Any]]:
    """Carga todas las reglas activas de la memoria persistente."""
    if not RULES_FILE.exists():
        save_rules(DEFAULT_RULES)
        return DEFAULT_RULES
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando reglas: {e}")
        return DEFAULT_RULES

def save_rules(rules: List[Dict[str, Any]]) -> None:
    """Guarda las reglas en el archivo de memoria persistente."""
    try:
        with open(RULES_FILE, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando reglas: {e}")

def delete_rule(rule_id: int) -> bool:
    """Elimina una regla de la memoria permanente por su ID."""
    rules = load_rules()
    updated = [r for r in rules if r.get("id") != rule_id]
    if len(updated) < len(rules):
        save_rules(updated)
        return True
    return False

def add_new_rule(rule_text: str, category: str = "general") -> Dict[str, Any]:
    """Agrega una nueva regla dictada por el usuario al cerebro del agente."""
    rules = load_rules()
    new_id = max([r.get("id", 0) for r in rules] + [0]) + 1
    new_rule = {
        "id": new_id,
        "rule": rule_text.strip(),
        "category": category,
        "created_at": "2026-08-15"
    }
    rules.append(new_rule)
    save_rules(rules)
    return new_rule

def get_rules_prompt_context() -> str:
    """Genera el bloque de texto con todas las reglas aprendidas para inyectarlo en los prompts del agente."""
    rules = load_rules()
    if not rules:
        return ""
    
    text = "\nREGLAS DE SELECCIÓN APRENDIDAS (MEMORIA PERMANENTE DEL NEGOCIO):\n"
    for r in rules:
        text += f"- [{r.get('category', 'general').upper()}]: {r.get('rule')}\n"
    return text
