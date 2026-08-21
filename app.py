"""
CFA Candidates Portal & Super Agente Headhunter con IA — CFA Stafford
Plataforma Empresarial de Selección con Interfaz HTML/JS Client-Side Ultrarrápida (0ms) y Copiloto IA en Sidebar.
"""
import streamlit as st
import streamlit.components.v1 as components
import json
import time
from typing import Dict, Any, List, Optional

from src.config import WORKSTREAM_API_KEY, GOOGLE_MAPS_API_KEY, OPENAI_API_KEY, STORE_NAME, STORE_ADDRESS
from src.tools.sheet_auditor import fetch_sheet_rows, resolve_true_position_from_qa, get_distinct_positions_from_sheet
from src.tools.criteria_engine import fetch_position_criteria, POSITION_TABS_GID, score_candidate_with_framework
from src.tools.portal_engine import get_portal_scored_candidates
from src.tools.systems_analyst_evaluator import evaluate_systems_analyst_applicant, batch_evaluate_systems_analysts
from src.tools.rules_memory import load_rules, add_new_rule, delete_rule, get_rules_prompt_context
from src.tools.html_portal_builder import build_portal_html
from src.agent.headhunter_agent import run_conversational_agent
from src.tools.login_view import render_cfa_login

# ==========================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==========================================
st.set_page_config(
    page_title="CFA Candidates Portal — CFA Stafford",
    page_icon="🍗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# GESTIÓN DE AUTENTICACIÓN / LOGIN SCREEN OFICIAL
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    render_cfa_login()
    st.stop()

# ==========================================
# ESTILOS GLOBALES
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
    }
    
    .sidebar-copilot-header {
        background: linear-gradient(135deg, #DD0031 0%, #B80028 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 14.5px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 3px 8px rgba(221, 0, 49, 0.25);
    }

    /* ── FLOATING LAUNCHER BUTTON (Mobile & Desktop) ── */
    .cfa-floating-fab-container {
        position: fixed;
        bottom: 22px;
        right: 22px;
        z-index: 999999;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 8px;
        pointer-events: none;
    }
    .cfa-floating-fab-hint {
        background: #ffffff;
        color: #1e293b;
        font-size: 12.5px;
        font-weight: 700;
        padding: 8px 14px;
        border-radius: 14px 14px 2px 14px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.18);
        border: 1px solid #fee2e2;
        pointer-events: auto;
        animation: cfaPulse 3s infinite ease-in-out;
        max-width: 210px;
        line-height: 1.4;
    }
    @keyframes cfaPulse {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-4px); }
    }

    /* Target FAB button in Streamlit */
    div[data-testid="stButton"]:has(button[key="cfa_fab_trigger_btn"]) {
        position: fixed !important;
        bottom: 22px !important;
        right: 22px !important;
        z-index: 1000000 !important;
    }
    button[key="cfa_fab_trigger_btn"] {
        width: 58px !important;
        height: 58px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #E51636 0%, #B80028 100%) !important;
        color: white !important;
        font-size: 26px !important;
        border: none !important;
        box-shadow: 0 6px 20px rgba(229, 22, 54, 0.45) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        padding: 0 !important;
    }
    button[key="cfa_fab_trigger_btn"]:hover {
        transform: scale(1.08) !important;
        box-shadow: 0 8px 24px rgba(229, 22, 54, 0.55) !important;
    }

    /* ── STREAMLIT DIALOG CFA STYLING ── */
    div[data-testid="stDialog"] div[role="dialog"] {
        border-radius: 18px !important;
        overflow: hidden !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 20px 50px rgba(0,0,0,0.22) !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] > div:first-child {
        background: linear-gradient(135deg, #E51636 0%, #B80028 100%) !important;
        color: white !important;
        padding: 14px 20px !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] > div:first-child h2 {
        color: white !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
    }
    div[data-testid="stDialog"] button[aria-label="Close"] {
        color: white !important;
    }

    /* Full screen on mobile */
    @media (max-width: 768px) {
        div[data-testid="stDialog"] div[role="dialog"] {
            width: 100vw !important;
            max-width: 100vw !important;
            height: 100vh !important;
            max-height: 100vh !important;
            border-radius: 0 !important;
            margin: 0 !important;
        }
        [data-testid="stSidebar"] {
            display: none !important;
        }
    }
    @media (min-width: 769px) {
        .cfa-floating-fab-container {
            display: none !important;
        }
        div[data-testid="stButton"]:has(button[key="cfa_fab_trigger_btn"]) {
            display: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# GESTIÓN DE HISTORIAL DE CHAT DEL COPILOTO
# ==========================================
if "headhunter_history" not in st.session_state:
    st.session_state["headhunter_history"] = [
        {
            "role": "assistant",
            "content": f"¡Hola! Soy tu **Headhunter IA de Chick-fil-A**.\n\nPuedo responder cualquier consulta sobre los 313 candidatos, comparar perfiles o recomendarte a los mejores para cada puesto.\n\nPrueba preguntarme:\n- *'¿Quién es el mejor para Front of House y por qué?'*\n- *'¿Cuáles candidatos califican para Systems Analyst?'*\n- *'Audita el Google Sheet contra Workstream API'*"
        }
    ]

# ==========================================
# SIDEBAR IZQUIERDA: CHAT DEDICADO DEL AGENTE COPILOT
# ==========================================
with st.sidebar:
    st.markdown('<div class="sidebar-copilot-header">🍗 Headhunter AI Copilot</div>', unsafe_allow_html=True)
    
    col_u1, col_u2 = st.columns([3, 2])
    with col_u1:
        st.markdown(f"<div style='font-size: 12px; color: #475569; padding-top: 6px;'>👤 <b>{st.session_state.get('logged_user', 'Operator')}</b></div>", unsafe_allow_html=True)
    with col_u2:
        if st.button("🚪 Salir", key="btn_logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()
            
    st.markdown("<hr style='margin: 8px 0 12px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
    
    with st.expander("⚡ Preguntas Rápidas", expanded=False):
        if st.button("🍳 Mejor para Cocina (BOH)", use_container_width=True):
            st.session_state["headhunter_prompt"] = "¿Cuál es el mejor candidato para Back of House Team Member (Cocina) y por qué?"
        if st.button("💻 Top Systems Analyst Calificados", use_container_width=True):
            st.session_state["headhunter_prompt"] = "¿Cuáles son los mejores candidatos para Systems Analyst que cumplen con educación en TI y 2+ años de experiencia?"
        if st.button("🛎️ Top 3 Front of House", use_container_width=True):
            st.session_state["headhunter_prompt"] = "Dame el top 3 de candidatos con experiencia para Front of House Team Member."
        if st.button("🔍 Auditar Workstream vs Sheet", use_container_width=True):
            st.session_state["headhunter_prompt"] = "Audita el Google Sheet contra la API de Workstream en tiempo real y dime si hay inconsistencias."
        if st.button("🏆 Mejor Candidato por Puesto", use_container_width=True):
            st.session_state["headhunter_prompt"] = "¿Cuál es el mejor candidato para cada uno de los 7 puestos de la tienda aplicando el framework oficial?"

    # Chat Container Full Height
    chat_container = st.container(height=560)
    with chat_container:
        for msg in st.session_state["headhunter_history"]:
            with st.chat_message(msg["role"], avatar="🍗" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

    # Chat Input
    hh_prompt = st.chat_input("Escribe una consulta al Headhunter...")
    active_prompt = hh_prompt or st.session_state.pop("headhunter_prompt", None)

    if active_prompt:
        st.session_state["headhunter_history"].append({"role": "user", "content": active_prompt})
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.markdown(active_prompt)
            with st.chat_message("assistant", avatar="🍗"):
                with st.spinner("🤖 Analizando candidatos y rúbricas oficiales..."):
                    reply = run_conversational_agent(active_prompt, st.session_state["headhunter_history"])
                    st.markdown(reply)
                    st.session_state["headhunter_history"].append({"role": "assistant", "content": reply})
                    st.rerun()
    if st.button("🗑️ Limpiar Conversación", use_container_width=True):
        st.session_state["headhunter_history"] = []
        st.rerun()
# ==========================================
# DIÁLOGO NATIVO MODAL: HEADHUNTER IA COPILOT (100% WebSocket Nativo)
# ==========================================
@st.dialog("🍗 Headhunter IA — Chick-fil-A Stafford", width="large")
def render_headhunter_modal_dialog():
    st.markdown("""
    <div style="font-size: 13px; color: #64748b; margin-top: -10px; margin-bottom: 12px;">
        Asistente inteligente con acceso en tiempo real a los 313 candidatos y framework de selección.
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("⚡ Preguntas Frecuentes", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🍳 Mejor para Cocina (BOH)", key="modal_q_boh", use_container_width=True):
                st.session_state["headhunter_modal_prompt"] = "¿Cuál es el mejor candidato para Back of House Team Member (Cocina) y por qué?"
            if st.button("🛎️ Top 3 Front of House", key="modal_q_foh", use_container_width=True):
                st.session_state["headhunter_modal_prompt"] = "Dame el top 3 de candidatos con experiencia para Front of House Team Member."
        with c2:
            if st.button("💻 Top Systems Analyst", key="modal_q_sa", use_container_width=True):
                st.session_state["headhunter_modal_prompt"] = "¿Cuáles son los mejores candidatos para Systems Analyst que cumplen con educación en TI y 2+ años de experiencia?"
            if st.button("🏆 Mejor Candidato por Puesto", key="modal_q_best", use_container_width=True):
                st.session_state["headhunter_modal_prompt"] = "¿Cuál es el mejor candidato para cada uno de los 7 puestos de la tienda aplicando el framework oficial?"

    # Chat Messages Scroll Area
    chat_box = st.container(height=460)
    with chat_box:
        for msg in st.session_state["headhunter_history"]:
            with st.chat_message(msg["role"], avatar="🍗" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

    modal_input = st.chat_input("Escribe tu consulta al Headhunter...", key="modal_chat_input_val")
    active_prompt = modal_input or st.session_state.pop("headhunter_modal_prompt", None)

    if active_prompt:
        st.session_state["headhunter_history"].append({"role": "user", "content": active_prompt})
        with chat_box:
            with st.chat_message("user", avatar="👤"):
                st.markdown(active_prompt)
            with st.chat_message("assistant", avatar="🍗"):
                with st.spinner("🤖 Analizando candidatos y rúbricas oficiales..."):
                    reply = run_conversational_agent(active_prompt, st.session_state["headhunter_history"])
                    st.markdown(reply)
                    st.session_state["headhunter_history"].append({"role": "assistant", "content": reply})
                    st.rerun()

    c_clean, c_spacer = st.columns([1, 2])
    with c_clean:
        if st.button("🗑️ Limpiar Historial", key="modal_btn_clear", use_container_width=True):
            st.session_state["headhunter_history"] = []
            st.rerun()

# Floating launcher widget (HTML hint + Streamlit native button)
st.markdown("""
<div class="cfa-floating-fab-container">
    <div class="cfa-floating-fab-hint">¿Tienes preguntas sobre los candidatos? 🍗 ¡Pregúntame!</div>
</div>
""", unsafe_allow_html=True)

if st.button("🍗", key="cfa_fab_trigger_btn", help="Abrir Headhunter IA Copilot"):
    render_headhunter_modal_dialog()



# ==========================================
# LIENZO PRINCIPAL CON PESTAÑAS
# ==========================================
tab_portal, tab_audit, tab_criteria = st.tabs([
    "🗂️ Portal de Candidatos (Ultra-Rápido 0ms)",
    "🔍 Auditoría Workstream en Vivo",
    "📐 Rúbricas Oficiales (7 Puestos)"
])


# ==========================================
# PESTAÑA 1: PORTAL DE CANDIDATOS NATIVO (HTML + JS 0ms)
# ==========================================
with tab_portal:
    portal_data = get_portal_scored_candidates(force_refresh=False)
    raw_html = build_portal_html(portal_data)
    components.html(raw_html, height=1150, scrolling=True)



# ==========================================
# PESTAÑA 2: AUDITORÍA WORKSTREAM EN VIVO
# ==========================================
with tab_audit:
    st.subheader("🔍 Auditoría Profunda: Workstream API vs Google Sheet")
    st.write("Verifica la integridad de datos en 4 capas (UUID, Nombres, Puestos, Respuestas y Depuración de Entrevistas) aplicando la **Regla de Oro: Solo etapa 'Applications'**.")
    
    col_btn_diag, col_btn_sync = st.columns([1, 1])
    
    with col_btn_diag:
        btn_diag = st.button("🔍 Diagnosticar Estado (Solo Lectura)", use_container_width=True)
    with col_btn_sync:
        btn_sync = st.button("⚡ Sincronizar y Auto-Corregir Sheet (Regla de Oro)", type="primary", use_container_width=True)

    if btn_sync:
        with st.spinner("⚡ Conectando con Service Account y ejecutando reconciliación atómica en Google Sheet..."):
            from src.tools.sheet_writer import apply_reconciliation_to_sheet
            sync_res = apply_reconciliation_to_sheet()
            if not sync_res.get("success"):
                st.error(f"❌ Error en la sincronización: {sync_res.get('error')}")
            else:
                res = sync_res.get("resumen", {})
                st.success(f"✅ ¡Sincronización completada con éxito! Filas agregadas: {res.get('filas_insertadas', 0)} | Filas depuradas: {res.get('filas_depuradas', 0)} | Puestos corregidos: {res.get('posiciones_corregidas', 0)}")
                for d in res.get("detalles", []):
                    st.info(f"• {d}")
                time.sleep(1.5)
                st.rerun()

    if btn_diag:
        with st.spinner("Consultando API de Workstream y comparando con Google Sheet..."):
            from src.tools.deep_reconciler import run_deep_workstream_audit
            audit_res = run_deep_workstream_audit()
            
            if "error" in audit_res:
                st.error(audit_res["error"])
            else:
                resumen = audit_res["resumen_ejecutivo"]
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Applications (Workstream)", resumen.get("total_applications_workstream", 307), help="Candidatos activos en screening (Review Stage y Availability)")
                with c2:
                    st.metric("Total en Google Sheet", resumen["total_filas_en_google_sheet"])
                with c3:
                    st.metric("Por Depurar del Sheet", resumen.get("candidatos_para_depurar", 0), help="Candidatos en Entrevista, Contratados o Archivados que deben salir del Sheet")
                with c4:
                    st.metric("Faltantes en Sheet", resumen["candidatos_faltantes_en_sheet"], help="Nuevas postulaciones en Applications que faltan en el Sheet")

                if resumen.get("candidatos_faltantes_en_sheet", 0) == 0 and resumen.get("candidatos_para_depurar", 0) == 0:
                    st.success("✅ 100% Sincronizado. El Google Sheet coincide de forma exacta con la pestaña Applications de Workstream.")
                else:
                    st.warning("⚠️ Hay discrepancias detectadas. Haz clic en '⚡ Sincronizar y Auto-Corregir Sheet' para alinearlo automáticamente con la Regla de Oro.")

                # Tablas de detalle interactivo
                faltantes = audit_res.get("candidatos_faltantes_en_sheet", [])
                if faltantes:
                    with st.expander(f"⚠️ Candidatos en Workstream Faltantes en el Sheet ({len(faltantes)})", expanded=True):
                        st.dataframe(faltantes, use_container_width=True)

                purgar = audit_res.get("candidatos_para_depurar", [])
                if purgar:
                    with st.expander(f"📋 Candidatos en Etapa de Entrevista / Contratado ({len(purgar)})", expanded=False):
                        st.dataframe(purgar, use_container_width=True)

                mismatches = audit_res.get("discrepancias_de_puesto", [])
                if mismatches:
                    with st.expander(f"🔄 Discrepancias de Puesto ({len(mismatches)})", expanded=False):
                        st.dataframe(mismatches, use_container_width=True)

                inconsistencias = audit_res.get("inconsistencias_respuestas", [])
                if inconsistencias:
                    with st.expander(f"❓ Inconsistencias en Respuestas JSON ({len(inconsistencias)})", expanded=False):
                        st.dataframe(inconsistencias, use_container_width=True)


# ==========================================
# PESTAÑA 3: RÚBRICAS OFICIALES (7 PUESTOS)
# ==========================================
with tab_criteria:
    st.subheader("📐 Framework Oficial de Puntuación (Candidate Screening Matrix)")
    st.write("Consulta los pesos, respuestas ideales y descalificaciones directas por cada posición.")
    
    selected_pos_tab = st.selectbox("Selecciona la Posición:", list(POSITION_TABS_GID.keys()))
    if selected_pos_tab:
        rules_df = fetch_position_criteria(selected_pos_tab)
        if rules_df:
            st.dataframe(rules_df, use_container_width=True)


