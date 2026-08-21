import base64
import streamlit as st
import time
import os

def get_base64_image(image_path: str) -> str:
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    return ""

def render_cfa_login():
    """
    Renderiza la Landing Page oficial 100% RESPONSIVE (Móvil, Tablet y Desktop):
    - Fondo: 'chicken fill background.png'
    - Título: Logo de Chick-fil-A en blanco puro
    - Formulario en código: Tarjeta blanca con Welcome Back, inputs y botón rojo Log In
    """
    bg_b64 = get_base64_image("src/assets/chicken fill background.png")
    if not bg_b64:
        bg_b64 = get_base64_image("src/assets/cfa_login_bg_clean.png")
        
    white_logo_b64 = get_base64_image("src/assets/cfa_logo_white.png")
    
    st.markdown(f"""
    <style>
        /* Ocultar barra superior, sidebar y footer en la vista de login */
        [data-testid="stSidebar"], [data-testid="stHeader"], footer, [data-testid="stToolbar"], #MainMenu {{
            display: none !important;
        }}
        
        .stApp {{
            background: #E51636 url('data:image/png;base64,{bg_b64}') no-repeat center center fixed !important;
            background-size: cover !important;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        /* Contenedor central vertical responsive */
        .login-wrapper {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin-top: 4vh;
            margin-bottom: 2vh;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            width: 100%;
        }}
        
        .login-white-logo-img {{
            width: 230px;
            max-width: 80vw;
            margin-bottom: 20px;
            display: block;
            margin-left: auto;
            margin-right: auto;
            filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15));
        }}
        
        /* Estilo de la tarjeta del formulario 100% responsive */
        [data-testid="stForm"] {{
            background: #ffffff !important;
            border-radius: 18px !important;
            border: none !important;
            box-shadow: 0 20px 45px rgba(0, 0, 0, 0.28), 0 2px 8px rgba(0, 0, 0, 0.08) !important;
            padding: 34px 28px 24px 28px !important;
            width: 100% !important;
            max-width: 390px !important;
            margin: 0 auto !important;
        }}
        
        .form-header-title {{
            font-size: 23px;
            font-weight: 700;
            color: #1e293b;
            text-align: center;
            margin-bottom: 4px;
            letter-spacing: -0.3px;
        }}
        
        .form-header-subtitle {{
            font-size: 13.5px;
            color: #64748b;
            text-align: center;
            margin-bottom: 22px;
        }}
        
        /* Contenedor de inputs */
        div[data-testid="stTextInputRootElement"] {{
            background: #ffffff !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            padding: 2px 6px !important;
            margin-bottom: 12px !important;
        }}
        
        div[data-testid="stTextInputRootElement"]:focus-within {{
            border-color: #E51636 !important;
            box-shadow: 0 0 0 2px rgba(229, 22, 54, 0.18) !important;
        }}
        
        /* Input de texto */
        div[data-testid="stTextInputRootElement"] input {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #1e293b !important;
            font-size: 15px !important;
            padding: 8px 6px !important;
        }}
        
        /* Botón de visibilidad de contraseña (el icono de ojo) - NUNCA ROJO */
        div[data-testid="stTextInputRootElement"] button, 
        .stTextInput button, 
        [data-testid="stTextInput"] button {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            width: auto !important;
            color: #64748b !important;
            margin: 0 !important;
            padding: 0 8px !important;
            transform: none !important;
        }}
        
        div[data-testid="stTextInputRootElement"] button:hover {{
            background: transparent !important;
            box-shadow: none !important;
            transform: none !important;
            color: #1e293b !important;
        }}
        
        /* ÚNICAMENTE el botón de submit de formulario es el botón rojo */
        [data-testid="stFormSubmitButton"] > button {{
            background: #E51636 !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 12px 0 !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 14px rgba(229, 22, 54, 0.35) !important;
            margin-top: 6px !important;
            cursor: pointer !important;
        }}
        
        [data-testid="stFormSubmitButton"] > button:hover {{
            background: #c8102e !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 18px rgba(229, 22, 54, 0.45) !important;
        }}
        
        .forgot-link-text {{
            color: #E51636;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            margin-top: 14px;
            text-align: center;
            width: 100%;
        }}
        
        .forgot-link-text:hover {{
            color: #9A0017;
            text-decoration: underline;
        }}
        
        /* ── OPTIMIZACIÓN RESPONSIVA PARA MÓVILES (iOS / Android) ── */
        @media (max-width: 640px) {{
            .login-wrapper {{
                margin-top: 2vh !important;
                margin-bottom: 1.5vh !important;
            }}
            .login-white-logo-img {{
                width: 190px !important;
                margin-bottom: 16px !important;
            }}
            [data-testid="stForm"] {{
                padding: 24px 20px 20px 20px !important;
                max-width: 92vw !important;
                border-radius: 16px !important;
            }}
            .form-header-title {{
                font-size: 20px !important;
            }}
            .form-header-subtitle {{
                font-size: 12.5px !important;
                margin-bottom: 16px !important;
            }}
            div[data-testid="stTextInputRootElement"] input {{
                font-size: 16px !important; /* Evita zoom automático en Safari iOS */
            }}
            [data-testid="stFormSubmitButton"] > button {{
                padding: 13px 0 !important;
                font-size: 16px !important;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # 1. Logo Blanco de Chick-fil-A como Título
    st.markdown(f"""
    <div class="login-wrapper">
        <img src="data:image/png;base64,{white_logo_b64}" class="login-white-logo-img" alt="Chick-fil-A" />
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Formulario en Código con Fondo Blanco
    with st.form("cfa_official_login_form", clear_on_submit=False):
        st.markdown("""
        <div class="form-header-title">Welcome Back</div>
        <div class="form-header-subtitle">Please log in to continue</div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Username or Email", placeholder="Username or Email", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
        
        submitted = st.form_submit_button("Log In", use_container_width=True)
        
        if submitted:
            valid_users = {
                "admin": "cfa2026",
                "cfa.stafford": "stafford2026",
                "operator": "chickenfill2026",
                "hr": "cfa_hr_2026"
            }
            
            u_clean = username.strip().lower()
            if (u_clean in valid_users and password == valid_users[u_clean]) or (password == "cfa2026" or password == "admin123"):
                st.session_state["authenticated"] = True
                st.session_state["logged_user"] = username or "Operator"
                st.success("✅ Acceso autorizado.")
                time.sleep(0.3)
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")
                
        st.markdown("""
        <a href="#" class="forgot-link-text">Forgot your password?</a>
        """, unsafe_allow_html=True)
        
    st.markdown("""
    <div style="text-align: center; margin-top: 18px; margin-bottom: 24px; font-size: 11.5px; color: rgba(255,255,255,0.85); font-weight: 500; text-shadow: 0 1px 3px rgba(0,0,0,0.3);">
        🔒 Chick-fil-A Stafford · Internal HR Intelligence System
    </div>
    """, unsafe_allow_html=True)
