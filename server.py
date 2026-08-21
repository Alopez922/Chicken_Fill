"""
CFA Candidates Portal and Headhunter IA - Production FastAPI Server
Serves both the REST API (/api/*) and the React SPA static files in a Single Docker Container.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from src.config import STORE_NAME, STORE_ADDRESS
from src.tools.portal_engine import get_portal_scored_candidates
from src.agent.headhunter_agent import run_conversational_agent
from src.tools.criteria_engine import fetch_position_criteria, POSITION_TABS_GID
from src.tools.deep_reconciler import run_deep_workstream_audit
from src.tools.sheet_writer import apply_reconciliation_to_sheet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cfa_server")

app = FastAPI(
    title="CFA Candidates Portal and Headhunter IA",
    description="Plataforma Empresarial de Seleccion CFA Stafford",
    version="2.0.0"
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# AUTHENTICATION
# ==========================================
CFA_USERS = {
    "admin": "cfa2026",
    "cfa.stafford": "stafford2026",
    "operator": "chickenfill2026",
    "hr": "cfa_hr_2026"
}

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = []

@app.post("/api/auth/login")
def login(req: LoginRequest):
    uname = req.username.strip().lower()
    expected_pwd = CFA_USERS.get(uname)
    if expected_pwd and expected_pwd == req.password.strip():
        return {
            "success": True,
            "username": uname,
            "displayName": "Admin / Operator" if uname == "admin" else uname.title(),
            "token": f"cfa-token-{uname}-2026"
        }
    raise HTTPException(status_code=401, detail="Credenciales invalidas")

# ==========================================
# CANDIDATES PORTAL API (Rich Data)
# ==========================================
def format_rich_candidates(raw_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    formatted = []
    for c in raw_candidates:
        puesto = c.get("puesto", "Front of House Team Member")
        score = float(c.get("overall_score", 0.0))
        is_disq = bool(c.get("is_disqualified", False))
        clasif_raw = str(c.get("classification", "Potential")).upper()

        if is_disq or clasif_raw == "DISQUALIFIED":
            clasif_label = "DISQUALIFIED"
        elif clasif_raw == "GOLD":
            clasif_label = "GOLD"
        elif clasif_raw == "IDEAL":
            clasif_label = "IDEAL"
        else:
            clasif_label = "POTENTIAL"

        details = c.get("details", [])
        sa_details = c.get("sa_details") or {}
        qa_list = c.get("parsed_qa", [])

        open_text_items = []
        choice_items = []
        seen_q = set()

        for d in details:
            q_name = str(d.get("question", "")).strip()
            q_ans = str(d.get("answer", "")).strip()
            q_score = d.get("score", 0.0)
            q_max = d.get("max_score", 10.0)
            q_reason = str(d.get("reason", "")).strip()
            cat = str(d.get("category", "")).lower()
            is_text = d.get("is_open_text", False) or "open text" in cat or "ai" in cat or "study" in q_name.lower() or "jobs" in q_name.lower() or "tell us" in q_name.lower()

            if "distance" in cat or "commute" in q_name.lower():
                continue

            seen_q.add(q_name.lower().replace("*", "").replace("?", "").strip())

            if is_text:
                open_text_items.append({
                    "question": q_name,
                    "answer": q_ans if q_ans else "No especificado",
                    "score": q_score,
                    "max_score": q_max,
                    "reason": q_reason
                })
            else:
                pts = int(q_score) if isinstance(q_score, (int, float)) and float(q_score).is_integer() else q_score
                choice_items.append({
                    "question": q_name,
                    "answer": q_ans if q_ans else "—",
                    "score": pts,
                    "max_score": q_max
                })

        for item in qa_list:
            q_raw = str(item.get("pregunta", "")).strip()
            a_raw = str(item.get("respuesta", "")).strip()
            q_clean = q_raw.lower().replace("*", "").replace("?", "").strip()
            if q_clean not in seen_q and len(a_raw) > 2 and a_raw.lower() not in ["yes", "no", "n/a"]:
                seen_q.add(q_clean)
                open_text_items.append({
                    "question": q_raw,
                    "answer": a_raw,
                    "score": None,
                    "max_score": None,
                    "reason": ""
                })

        detected_signals = sa_details.get("detected_signals", []) if "system" in puesto.lower() else []
        competency_profile = sa_details.get("competency_profile") if "system" in puesto.lower() else None

        formatted.append({
            "uuid": c.get("uuid"),
            "nombre": c.get("nombre", "Sin Nombre"),
            "name": c.get("nombre", "Sin Nombre"),
            "puesto": puesto,
            "position": puesto,
            "clasificacion": clasif_label,
            "classification": clasif_label,
            "overall_score": score,
            "score": score,
            "is_disqualified": is_disq,
            "choice_score": c.get("choice_score", 0),
            "distance_score": c.get("distance_score", 0),
            "ai_score": c.get("ai_score", 0),
            "total_points": c.get("total_points", 0),
            "max_points": c.get("max_points", 100),
            "distance_miles": c.get("distancia_millas", 0.0),
            "distancia_texto": c.get("distancia_texto", "—"),
            "address": c.get("direccion", "Dirección no especificada"),
            "applied_date": c.get("fecha_postulacion", ""),
            "phone": c.get("telefono", "—"),
            "email": c.get("email", "—"),
            "summary": c.get("summary") or sa_details.get("disqualification_reason") or "",
            "detected_signals": detected_signals,
            "competency_profile": competency_profile,
            "open_text_items": open_text_items,
            "choice_items": choice_items,
            "sa_details": sa_details
        })
    return formatted

@app.get("/api/candidates")
def get_candidates(force_refresh: bool = False):
    try:
        data = get_portal_scored_candidates(force_refresh=force_refresh)
        raw_cands = data.get("candidatos") or data.get("candidates") or []
        rich_cands = format_rich_candidates(raw_cands)

        kpis = {
            "total": len(rich_cands),
            "gold": sum(1 for c in rich_cands if c["classification"] == "GOLD"),
            "ideal": sum(1 for c in rich_cands if c["classification"] == "IDEAL"),
            "potential": sum(1 for c in rich_cands if c["classification"] == "POTENTIAL"),
            "disqualified": sum(1 for c in rich_cands if c["classification"] == "DISQUALIFIED")
        }

        return {
            "success": True,
            "total": len(rich_cands),
            "kpis": kpis,
            "candidates": rich_cands
        }
    except Exception as e:
        logger.error(f"Error fetching candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# HEADHUNTER IA CHAT API
# ==========================================
@app.post("/api/chat")
def chat_with_headhunter(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Mensaje vacio")
    try:
        reply = run_conversational_agent(req.message, req.history)
        updated_history = list(req.history)
        updated_history.append({"role": "user", "content": req.message})
        updated_history.append({"role": "assistant", "content": reply})
        return {
            "success": True,
            "reply": reply,
            "history": updated_history
        }
    except Exception as e:
        logger.error(f"Error running conversational agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error del Agente: {str(e)}")

# ==========================================
# AUDIT & RECONCILIATION API
# ==========================================
@app.get("/api/audit/status")
def get_audit_status():
    try:
        res = run_deep_workstream_audit()
        return {
            "success": True,
            "audit": res
        }
    except Exception as e:
        logger.error(f"Error running deep audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/audit/sync")
def sync_audit_sheet():
    try:
        res = apply_reconciliation_to_sheet()
        return {
            "success": res.get("success", False),
            "result": res
        }
    except Exception as e:
        logger.error(f"Error applying sheet reconciliation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# RUBRICS API
# ==========================================
@app.get("/api/rubrics")
def get_rubrics_positions():
    canonical = [
        "Front of House Team Member",
        "Back of House Team Member",
        "Chick-fil-A Delivery Driver",
        "Systems Analyst",
        "Shift Leader",
        "Front of the House Director",
        "Director of Back of House Operations"
    ]
    return {
        "success": True,
        "positions": canonical
    }

@app.get("/api/rubrics/{position_name}")
def get_rubric_for_position(position_name: str):
    try:
        rules = fetch_position_criteria(position_name)
        if isinstance(rules, list):
            return {"success": True, "position": position_name, "criteria": rules}
        elif hasattr(rules, "to_dict"):
            return {"success": True, "position": position_name, "criteria": rules.to_dict(orient="records")}
        return {"success": True, "position": position_name, "criteria": []}
    except Exception as e:
        logger.error(f"Error fetching rubrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# SYSTEM HEALTH
# ==========================================
@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "store": STORE_NAME,
        "address": STORE_ADDRESS,
        "engine": "FastAPI + React 2.0"
    }

# ==========================================
# REACT SPA STATIC FILES & ROUTING
# ==========================================
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return JSONResponse({"detail": "Frontend dist not built yet"}, status_code=404)
