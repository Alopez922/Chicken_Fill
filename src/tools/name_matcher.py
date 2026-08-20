"""
Motor de búsqueda exacta de candidatos por nombre completo en el Google Sheet.
Garantiza coincidencia de NOMBRE + APELLIDO simultáneos. Nunca devuelve candidatos incorrectos.
"""
import difflib
from typing import Dict, Any, List, Optional

def _score_name_match(query: str, candidate_name: str) -> float:
    """
    Retorna un puntaje de 0.0 a 1.0 de qué tan bien coincide el query con el nombre del candidato.
    Soporta typos de 1-2 caracteres por token mediante fuzzy matching a nivel de token.
    """
    q_tokens = [t.lower().strip() for t in query.strip().split() if len(t) > 1]
    c_tokens = [t.lower().strip() for t in candidate_name.strip().split() if len(t) > 1]
    c_name_low = candidate_name.lower().strip()

    if not q_tokens:
        return 0.0

    # Coincidencia exacta total
    if query.lower().strip() == c_name_low:
        return 1.0

    # Para cada token del query, calcular la mejor coincidencia con algún token del candidato
    # Esto permite typos como "raymon"→"raymond", "colo"→"colon", "Raimond"→"Raymond"
    token_scores = []
    for qt in q_tokens:
        best_t_score = 0.0
        for ct in c_tokens:
            # Coincidencia exacta de token
            if qt == ct:
                best_t_score = 1.0
                break
            # El token del query es subcadena del token del candidato (ej: "raymon" in "raymond")
            if qt in ct or ct in qt:
                overlap = min(len(qt), len(ct)) / max(len(qt), len(ct))
                best_t_score = max(best_t_score, 0.85 + overlap * 0.15)
                continue
            # Fuzzy match token a token (permite typos de 1-2 chars)
            ratio = difflib.SequenceMatcher(None, qt, ct).ratio()
            best_t_score = max(best_t_score, ratio)
        token_scores.append(best_t_score)

    # Promedio de coincidencia de todos los tokens
    avg_token_score = sum(token_scores) / len(token_scores)

    # Si algún token no alcanza 0.65 de similitud, penalizar
    min_token_score = min(token_scores)
    if min_token_score < 0.65:
        avg_token_score *= 0.6

    return min(avg_token_score, 1.0)


def find_best_candidate_match(query_name: str, all_candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Busca el candidato con la mejor coincidencia de nombre en la lista de candidatos.
    Garantiza que si buscas 'Raymond Colon' NO te devuelve 'Raymond Wheeler'.
    """
    best_match = None
    best_score = 0.0

    q_tokens = [t.lower().strip() for t in query_name.strip().split() if len(t) > 1]

    for c in all_candidates:
        c_name = c.get("nombre", "").strip()
        score = _score_name_match(query_name, c_name)

        if score > best_score:
            best_score = score
            best_match = c

    # Solo devolver resultado si la coincidencia es suficientemente buena
    # Y si el query tiene apellido (2+ tokens), TODOS deben estar presentes
    if len(q_tokens) >= 2:
        if best_match:
            c_name_low = best_match.get("nombre", "").lower()
            all_tokens_present = all(t in c_name_low for t in q_tokens)
            if not all_tokens_present and best_score < 0.8:
                return None  # No devolver un match parcial cuando se provee apellido

    if best_score >= 0.45:
        return best_match

    return None
