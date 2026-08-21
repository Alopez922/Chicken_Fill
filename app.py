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

    /* ── MOBILE CHATBOT OVERLAY ── */
    #cfa-chat-launcher {
        display: none;
        position: fixed;
        bottom: 22px;
        right: 20px;
        z-index: 99999;
        flex-direction: column;
        align-items: flex-end;
        gap: 10px;
    }
    #cfa-chat-bubble-hint {
        background: #fff;
        color: #1e293b;
        font-size: 13.5px;
        font-weight: 600;
        padding: 10px 14px;
        border-radius: 14px 14px 4px 14px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.18);
        max-width: 220px;
        line-height: 1.4;
        animation: cfaBounceIn 0.5s ease;
    }
    #cfa-chat-btn {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: #E51636;
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 6px 20px rgba(229,22,54,0.45);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        padding: 0;
    }
    #cfa-chat-btn:hover { transform: scale(1.08); box-shadow: 0 8px 24px rgba(229,22,54,0.55); }
    #cfa-chat-btn img { width: 36px; height: 36px; object-fit: contain; }

    /* Chat panel full-screen on mobile */
    #cfa-chat-panel {
        display: none;
        position: fixed;
        inset: 0;
        z-index: 100000;
        flex-direction: column;
        background: #fff;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }
    #cfa-chat-panel.open { display: flex; }
    #cfa-chat-panel-header {
        background: linear-gradient(135deg, #E51636 0%, #B80028 100%);
        padding: 14px 16px 12px;
        display: flex;
        align-items: center;
        gap: 12px;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    #cfa-chat-panel-header img { width: 38px; height: 38px; object-fit: contain; }
    .cfa-header-text { flex: 1; }
    .cfa-header-text h3 { color: #fff; font-size: 15px; font-weight: 800; margin: 0; }
    .cfa-header-text p { color: rgba(255,255,255,0.82); font-size: 11px; margin: 0; font-weight: 500; }
    #cfa-chat-close {
        background: rgba(255,255,255,0.18);
        border: none;
        color: #fff;
        width: 32px; height: 32px;
        border-radius: 50%;
        font-size: 18px;
        cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        transition: background 0.2s;
    }
    #cfa-chat-close:hover { background: rgba(255,255,255,0.3); }
    #cfa-chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px 14px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        background: #F8FAFC;
    }
    .cfa-msg-row { display: flex; gap: 8px; align-items: flex-end; }
    .cfa-msg-row.user { flex-direction: row-reverse; }
    .cfa-msg-avatar {
        width: 30px; height: 30px;
        border-radius: 50%;
        background: #E51636;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }
    .cfa-msg-avatar img { width: 18px; height: 18px; object-fit: contain; }
    .cfa-msg-bubble {
        max-width: 78%;
        padding: 10px 13px;
        border-radius: 16px 16px 16px 4px;
        font-size: 13.5px;
        line-height: 1.5;
        color: #1e293b;
        background: #fff;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        white-space: pre-wrap;
        word-break: break-word;
    }
    .cfa-msg-row.user .cfa-msg-bubble {
        background: #E51636;
        color: #fff;
        border: none;
        border-radius: 16px 16px 4px 16px;
        box-shadow: 0 2px 8px rgba(229,22,54,0.3);
    }
    .cfa-typing-dots { display: flex; gap: 4px; padding: 4px 2px; }
    .cfa-typing-dots span {
        width: 7px; height: 7px; border-radius: 50%; background: #94a3b8;
        animation: cfaDot 1.2s infinite ease-in-out;
    }
    .cfa-typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .cfa-typing-dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes cfaDot { 0%,80%,100%{transform:scale(0.8);opacity:0.5} 40%{transform:scale(1.1);opacity:1} }

    #cfa-chat-input-bar {
        display: flex;
        gap: 8px;
        padding: 10px 12px;
        background: #fff;
        border-top: 1px solid #e2e8f0;
        flex-shrink: 0;
    }
    #cfa-chat-input {
        flex: 1;
        border: 1.5px solid #e2e8f0;
        border-radius: 24px;
        padding: 10px 16px;
        font-size: 14px;
        outline: none;
        font-family: inherit;
        color: #1e293b;
        transition: border-color 0.2s;
    }
    #cfa-chat-input:focus { border-color: #E51636; }
    #cfa-chat-send {
        width: 44px; height: 44px;
        background: #E51636;
        border: none;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer;
        flex-shrink: 0;
        transition: background 0.2s, transform 0.15s;
        box-shadow: 0 3px 10px rgba(229,22,54,0.35);
    }
    #cfa-chat-send:hover { background: #c8102e; transform: scale(1.06); }
    #cfa-chat-send svg { width: 18px; height: 18px; }

    @keyframes cfaBounceIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }

    /* Only show launcher on mobile */
    @media (max-width: 768px) {
        #cfa-chat-launcher { display: flex !important; }
        /* Hide streamlit sidebar on mobile when chat panel is closed */
        [data-testid="stSidebar"] { display: none !important; }
    }
    @media (min-width: 769px) {
        #cfa-chat-launcher { display: none !important; }
        #cfa-chat-panel { display: none !important; }
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
# MOBILE FLOATING CHATBOT (Solo visible en móvil)
# ==========================================
import base64 as _b64
def _logo_b64():
    p = "src/assets/cfa_logo_white.png"
    if not __import__("os").path.exists(p):
        return ""
    return _b64.b64encode(open(p,"rb").read()).decode()

_logo = _logo_b64()
_chat_history_js = json.dumps([
    {"role": m["role"], "content": m["content"]}
    for m in st.session_state.get("headhunter_history", [])
])

# Handle mobile chat submission via query params
_qp = st.query_params
_mobile_msg = _qp.get("cfa_mobile_msg", "")
if _mobile_msg and _mobile_msg not in ["", "__clear__"]:
    # Process the message the same way as sidebar chat
    st.session_state["headhunter_history"].append({"role": "user", "content": _mobile_msg})
    with st.spinner("🍗 Consultando al Headhunter IA..."):
        reply = run_conversational_agent(_mobile_msg, st.session_state["headhunter_history"])
    st.session_state["headhunter_history"].append({"role": "assistant", "content": reply})
    st.query_params.clear()
    st.rerun()

_chat_history_js = json.dumps([
    {"role": m["role"], "content": m["content"]}
    for m in st.session_state.get("headhunter_history", [])
], ensure_ascii=False)

st.markdown(f"""
<div id="cfa-chat-launcher">
  <div id="cfa-chat-bubble-hint">¿Quieres saber algo sobre los candidatos? 🍗 ¡Pregúntame!</div>
  <button id="cfa-chat-btn" aria-label="Abrir chat Headhunter IA">
    <img src="data:image/png;base64,{_logo}" alt="CFA" />
  </button>
</div>

<div id="cfa-chat-panel">
  <div id="cfa-chat-panel-header">
    <img src="data:image/png;base64,{_logo}" alt="CFA logo" />
    <div class="cfa-header-text">
      <h3>Headhunter IA 🍗</h3>
      <p>CFA Stafford · En línea</p>
    </div>
    <button id="cfa-chat-close" aria-label="Cerrar chat">✕</button>
  </div>
  <div id="cfa-chat-messages"></div>
  <div id="cfa-chat-input-bar">
    <input id="cfa-chat-input" type="text" placeholder="Escribe una pregunta..." autocomplete="off" />
    <button id="cfa-chat-send" aria-label="Enviar">
      <svg fill="none" stroke="#fff" stroke-width="2.2" viewBox="0 0 24 24">
        <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
      </svg>
    </button>
  </div>
</div>
""", unsafe_allow_html=True)

# JS bridge: st.components.v1.html() DOES execute scripts and can access parent DOM
components.html(f"""
<script>
(function() {{
  var LOGO = "data:image/png;base64,{_logo}";
  var HISTORY = {_chat_history_js};
  var hintHidden = false;
  var doc = window.parent.document;

  function waitForEl(id, cb, tries) {{
    tries = tries || 0;
    var el = doc.getElementById(id);
    if (el) {{ cb(el); return; }}
    if (tries < 40) setTimeout(function() {{ waitForEl(id, cb, tries+1); }}, 150);
  }}

  function buildBubble(role, text) {{
    var row = doc.createElement('div');
    row.className = 'cfa-msg-row' + (role === 'user' ? ' user' : '');
    if (role !== 'user') {{
      var av = doc.createElement('div');
      av.className = 'cfa-msg-avatar';
      var img = doc.createElement('img');
      img.src = LOGO; img.alt = 'AI';
      av.appendChild(img);
      row.appendChild(av);
    }}
    var bub = doc.createElement('div');
    bub.className = 'cfa-msg-bubble';
    bub.innerHTML = text
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/[*][*](.*?)[*][*]/g,'<strong>$1</strong>')
      .replace(/[*](.*?)[*]/g,'<em>$1</em>')
      .replace(/\\n/g,'<br>');
    row.appendChild(bub);
    return row;
  }}

  function renderHistory() {{
    var box = doc.getElementById('cfa-chat-messages');
    if (!box) return;
    box.innerHTML = '';
    HISTORY.forEach(function(m) {{ box.appendChild(buildBubble(m.role, m.content)); }});
    box.scrollTop = box.scrollHeight;
  }}

  function showTyping() {{
    var box = doc.getElementById('cfa-chat-messages');
    if (!box) return;
    var row = doc.createElement('div');
    row.className = 'cfa-msg-row'; row.id = 'cfa-typing';
    var av = doc.createElement('div'); av.className = 'cfa-msg-avatar';
    var img = doc.createElement('img'); img.src = LOGO; img.alt = '';
    av.appendChild(img); row.appendChild(av);
    var bub = doc.createElement('div'); bub.className = 'cfa-msg-bubble';
    bub.innerHTML = '<div class="cfa-typing-dots"><span></span><span></span><span></span></div>';
    row.appendChild(bub); box.appendChild(row);
    box.scrollTop = box.scrollHeight;
  }}

  function openChat() {{
    var panel = doc.getElementById('cfa-chat-panel');
    if (!panel) return;
    panel.classList.add('open');
    doc.body.style.overflow = 'hidden';
    if (!hintHidden) {{
      var hint = doc.getElementById('cfa-chat-bubble-hint');
      if (hint) hint.style.display = 'none';
      hintHidden = true;
    }}
    renderHistory();
    setTimeout(function() {{
      var inp = doc.getElementById('cfa-chat-input');
      if (inp) inp.focus();
    }}, 300);
  }}

  function closeChat() {{
    var panel = doc.getElementById('cfa-chat-panel');
    if (panel) panel.classList.remove('open');
    doc.body.style.overflow = '';
  }}

  function sendMsg() {{
    var inp = doc.getElementById('cfa-chat-input');
    if (!inp) return;
    var msg = inp.value.trim();
    if (!msg) return;
    inp.value = '';
    var box = doc.getElementById('cfa-chat-messages');
    if (box) {{ box.appendChild(buildBubble('user', msg)); box.scrollTop = box.scrollHeight; }}
    showTyping();
    HISTORY.push({{role:'user', content:msg}});
    var url = window.parent.location.pathname + '?cfa_mobile_msg=' + encodeURIComponent(msg);
    window.parent.location.href = url;
  }}

  // Wire up buttons after DOM is ready
  waitForEl('cfa-chat-btn', function(btn) {{
    btn.addEventListener('click', openChat);
  }});
  waitForEl('cfa-chat-close', function(btn) {{
    btn.addEventListener('click', closeChat);
  }});
  waitForEl('cfa-chat-send', function(btn) {{
    btn.addEventListener('click', sendMsg);
  }});
  waitForEl('cfa-chat-input', function(inp) {{
    inp.addEventListener('keydown', function(e) {{ if (e.key === 'Enter') sendMsg(); }});
  }});

  // Auto-hide hint after 6s
  setTimeout(function() {{
    var hint = doc.getElementById('cfa-chat-bubble-hint');
    if (hint && !hintHidden) {{
      hint.style.transition = 'opacity 0.5s';
      hint.style.opacity = '0';
      setTimeout(function() {{ if(hint) hint.style.display='none'; }}, 500);
    }}
  }}, 6000);
}})();
</script>
""", height=0)


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


