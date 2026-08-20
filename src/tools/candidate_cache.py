"""
Módulo de Caché Ultrarrápido de Candidatos y Evaluaciones.
Evita hacer peticiones lentas repetitivas a la API de Workstream y Google Maps.
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

CACHE_FILE = Path(__file__).resolve().parent.parent.parent / "candidate_cache.json"

def load_cache() -> Dict[str, Any]:
    """Carga los candidatos y evaluaciones guardadas en caché local."""
    if not CACHE_FILE.exists():
        return {"candidates": {}, "evaluations": {}, "last_sync": 0}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"candidates": {}, "evaluations": {}, "last_sync": 0}

def save_cache(cache_data: Dict[str, Any]) -> None:
    """Guarda el estado actualizado en el archivo de caché local."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando caché: {e}")

def get_cached_candidate(uuid: str) -> Optional[Dict[str, Any]]:
    """Obtiene los datos completos de un candidato desde la caché si existe."""
    cache = load_cache()
    return cache.get("candidates", {}).get(uuid)

def set_cached_candidate(uuid: str, candidate_data: Dict[str, Any]) -> None:
    """Guarda los datos de un candidato en la caché local."""
    cache = load_cache()
    if "candidates" not in cache:
        cache["candidates"] = {}
    cache["candidates"][uuid] = candidate_data
    save_cache(cache)

def get_cached_evaluation(uuid: str) -> Optional[Dict[str, Any]]:
    """Obtiene la evaluación previa de un candidato para evitar volver a llamar a la IA."""
    cache = load_cache()
    return cache.get("evaluations", {}).get(uuid)

def set_cached_evaluation(uuid: str, evaluation_data: Dict[str, Any]) -> None:
    """Guarda el resultado de evaluación de un candidato en la caché."""
    cache = load_cache()
    if "evaluations" not in cache:
        cache["evaluations"] = {}
    cache["evaluations"][uuid] = evaluation_data
    save_cache(cache)

def bulk_save_candidates_from_sheet_or_api(candidates_list: List[Dict[str, Any]]) -> int:
    """Guarda una lista masiva de candidatos (por ejemplo sincronizados desde Google Sheets o n8n)."""
    cache = load_cache()
    if "candidates" not in cache:
        cache["candidates"] = {}
    count = 0
    for c in candidates_list:
        uuid = c.get("uuid")
        if uuid:
            cache["candidates"][uuid] = c
            count += 1
    cache["last_sync"] = time.time()
    save_cache(cache)
    return count
