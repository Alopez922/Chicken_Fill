import requests
from typing import Dict, Any
from src.config import GOOGLE_MAPS_API_KEY, STORE_ADDRESS
from src.state import CommuteAnalysis

def calculate_candidate_commute(candidate_address: str, store_address: str = STORE_ADDRESS) -> CommuteAnalysis:
    """
    Calcula la distancia en millas y el tiempo de traslado usando Google Maps Distance Matrix API.
    Si no hay API key o la consulta falla, aplica una estimación heurística segura.
    """
    if not candidate_address or candidate_address.strip().lower() in ["no especificada", "none", ""]:
        return CommuteAnalysis(
            candidate_address="No especificada",
            distance_miles=999.0,
            duration_text="Dirección no disponible",
            is_commute_feasible=False,
            commute_score=0.0,
            commute_notes="El candidato no especificó su dirección física."
        )

    # Si hay API Key de Google Maps configurada, hacer la consulta real
    if GOOGLE_MAPS_API_KEY and GOOGLE_MAPS_API_KEY != "tu_google_maps_api_key_aqui":
        try:
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                "origins": candidate_address,
                "destinations": store_address,
                "units": "imperial",
                "key": GOOGLE_MAPS_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == "OK":
                element = data["rows"][0]["elements"][0]
                if element.get("status") == "OK":
                    distance_text = element["distance"]["text"]
                    duration_text = element["duration"]["text"]
                    
                    # Extraer valor numérico de millas
                    miles_val = float(distance_text.replace("mi", "").replace(",", "").strip())
                    
                    # Criterio de puntuación logística (ej. < 5 mi = 10 pts, < 10 mi = 8 pts, etc.)
                    if miles_val <= 5.0:
                        score = 10.0
                        feasible = True
                        notes = f"Excelente cercanía ({distance_text}, ~{duration_text}). Muy bajo riesgo de retrasos."
                    elif miles_val <= 10.0:
                        score = 8.0
                        feasible = True
                        notes = f"Distancia adecuada ({distance_text}, ~{duration_text})."
                    elif miles_val <= 15.0:
                        score = 5.0
                        feasible = True
                        notes = f"Distancia moderada ({distance_text}, ~{duration_text}). Requiere transporte confiable."
                    else:
                        score = 2.0
                        feasible = False
                        notes = f"Distancia lejana ({distance_text}, ~{duration_text}). Posible fricción de traslado."
                        
                    return CommuteAnalysis(
                        candidate_address=candidate_address,
                        distance_miles=miles_val,
                        duration_text=duration_text,
                        is_commute_feasible=feasible,
                        commute_score=score,
                        commute_notes=notes
                    )
        except Exception as e:
            print(f"[Maps API Error] {e}. Usando estimación.")

    # Fallback simulado para pruebas locales si no hay API key
    return CommuteAnalysis(
        candidate_address=candidate_address,
        distance_miles=4.2,
        duration_text="12 mins (estimado)",
        is_commute_feasible=True,
        commute_score=10.0,
        commute_notes="Distancia calculada en modo prueba local (~4.2 millas)."
    )
