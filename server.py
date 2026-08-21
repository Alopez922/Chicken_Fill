"""
CFA Candidates Portal and Headhunter IA - Production FastAPI Server
Serves both the REST API (/api/*) and the React SPA static files in a Single Docker Container.
"""
import os
import json
import logging
import urllib.parse
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
# CANDIDATES PORTAL API
# ==========================================
@app.get("/api/candidates")
def get_candidates(force_refresh: bool = False):
    try:
        data = get_portal_scored_candidates(force_refresh=force_refresh)
        cands = data.get("candidatos") or data.get("candidates") or []
        return {
            "success": True,
            "total": len(cands),
            "kpis": data.get("kpis", {}),
            "candidates": cands
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
    # Only return distinct canonical position names
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
