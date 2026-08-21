"""
Constructor del Portal HTML/JS de Alta Velocidad (0ms Client-Side)
Inyecta los 313 candidatos calificados de Python directamente en el template HTML/JavaScript del cliente.
"""
import json
from typing import Dict, Any, List

def build_portal_html(portal_data: Dict[str, Any]) -> str:
    all_cards = portal_data.get("candidatos", [])
    kpis = portal_data.get("kpis", {})

    formatted_candidates = []
    
    for c in all_cards:
        puesto = c.get("puesto", "Front of House Team Member")
        score = float(c.get("overall_score", 0.0))
        is_disq = bool(c.get("is_disqualified", False))
        clasif_raw = str(c.get("classification", "Potential")).upper()
        
        # Mapeo exacto a las etiquetas del template
        if is_disq or clasif_raw == "DISQUALIFIED":
            clasif_label = "DESCALIFICADO"
        elif clasif_raw == "GOLD":
            clasif_label = "GOLD"
        elif clasif_raw == "IDEAL":
            clasif_label = "CANDIDATO IDEAL"
        else:
            clasif_label = "POTENCIAL"

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

        # Añadir preguntas abiertas del formulario que no estaban en la rúbrica (como College name, Tell us about yourself)
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

        formatted_candidates.append({
            "uuid": c.get("uuid"),
            "nombre": c.get("nombre", "Sin Nombre"),
            "puesto_aplicado": puesto,
            "clasificacion": clasif_label,
            "porcentaje_final": score,
            "prioridad": 0 if is_disq else 1,
            "puntaje_total": c.get("total_points", 0),
            "maximo_posible": c.get("max_points", 100),
            "puntaje_choice": c.get("choice_score", 0),
            "puntaje_distancia": c.get("distance_score", 0),
            "puntaje_ia": c.get("ai_score", 0),
            "distancia_millas": c.get("distancia_millas", 0.0),
            "distancia_texto": c.get("distancia_texto", "—"),
            "direccion": c.get("direccion", "Dirección no especificada"),
            "fecha_aplicacion": c.get("fecha_postulacion", ""),
            "telefono": c.get("telefono", "—"),
            "descalificado": "TRUE" if is_disq else "FALSE",
            "motivo_descalificacion": c.get("summary") or sa_details.get("disqualification_reason") or "",
            "detected_signals": detected_signals,
            "competency_profile": competency_profile,
            "open_text_items": open_text_items,
            "choice_items": choice_items
        })


    # Resumen para el Banner Superior de KPIs
    resumen_data = {
        "total": len(formatted_candidates),
        "clasificaciones": {
            "gold": sum(1 for c in formatted_candidates if c["clasificacion"] == "GOLD"),
            "ideal": sum(1 for c in formatted_candidates if c["clasificacion"] == "CANDIDATO IDEAL"),
            "potencial": sum(1 for c in formatted_candidates if c["clasificacion"] == "POTENCIAL"),
            "descalificado": sum(1 for c in formatted_candidates if c["clasificacion"] == "DESCALIFICADO")
        }
    }

    candidates_json = json.dumps(formatted_candidates, ensure_ascii=False)
    resumen_json = json.dumps(resumen_data, ensure_ascii=False)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Candidates Portal — CFA Stafford</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --cfa-red:       #DD0031;
      --cfa-red-hover: #B80028;
      --bg:            #F8F9FA;
      --surface:       #FFFFFF;
      --card:          #FFFFFF;
      --card-hover:    #F1F5F9;
      --border:        #E2E8F0;
      --text:          #0F172A;
      --muted:         #64748B;
      
      --gold:          #D97706;
      --ideal:         #0D9488;
      --potencial:     #2563EB;
      --nocalifica:    #6B7280;
      --desc:          #DC2626;
    }}

    body {{
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
      overflow-x: hidden;
    }}

    /* ── HEADER ── */
    header {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      gap: 16px;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }}
    .header-brand {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .brand-badge {{
      width: 36px;
      height: 36px;
      background: var(--cfa-red);
      color: #fff;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 0.9rem;
      letter-spacing: -0.5px;
    }}
    header h1 {{ font-size: 1.05rem; font-weight: 800; letter-spacing: -0.3px; color: var(--text); }}
    header h1 span {{ color: var(--cfa-red); }}
    
    .header-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-left: auto;
    }}

    .header-search {{
      width: 300px;
      position: relative;
    }}
    .header-search input {{
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 14px 8px 36px;
      color: var(--text);
      font-size: 0.85rem;
      outline: none;
      transition: all 0.2s;
    }}
    .header-search input:focus {{ border-color: var(--cfa-red); background: #fff; box-shadow: 0 0 0 3px rgba(221,0,49,0.08); }}
    .header-search svg {{ position: absolute; left: 11px; top: 50%; transform: translateY(-50%); color: var(--muted); }}
    
    .btn-guide {{
      background: var(--bg);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s;
    }}
    .btn-guide:hover {{ background: #E2E8F0; }}

    .btn-refresh {{
      background: var(--cfa-red);
      color: #fff;
      border: none;
      border-radius: 8px;
      padding: 8px 14px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: background 0.2s;
    }}
    .btn-refresh:hover {{ background: var(--cfa-red-hover); }}
    #last-update {{ font-size: 0.75rem; color: var(--muted); white-space: nowrap; }}

    /* ── STATS BAR ── */
    .stats-bar {{
      display: flex;
      gap: 12px;
      padding: 16px 24px 8px;
      overflow-x: auto;
    }}
    .stat-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 18px;
      min-width: 130px;
      flex: 1;
      cursor: pointer;
      transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
    }}
    .stat-card:hover {{ transform: translateY(-1px); border-color: #CBD5E1; }}
    .stat-card.active {{ border-color: var(--cfa-red); box-shadow: 0 0 0 1px var(--cfa-red); }}
    .stat-card .stat-label {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); margin-bottom: 4px; font-weight: 700; }}
    .stat-card .stat-val {{ font-size: 1.6rem; font-weight: 800; line-height: 1; }}
    .stat-card .stat-sub {{ font-size: 0.72rem; color: var(--muted); margin-top: 3px; }}
    .color-gold     {{ color: var(--gold); }}
    .color-ideal    {{ color: var(--ideal); }}
    .color-potencial{{ color: var(--potencial); }}
    .color-desc     {{ color: var(--desc); }}
    .color-total    {{ color: var(--text); }}

    /* ── MAIN LAYOUT ── */
    .main {{ display: flex; gap: 0; }}

    /* ── SIDEBAR ── */
    .sidebar {{
      width: 240px;
      min-width: 240px;
      background: var(--surface);
      border-right: 1px solid var(--border);
      padding: 16px 14px;
      min-height: calc(100vh - 120px);
      display: flex;
      flex-direction: column;
    }}
    .sidebar h3 {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin-bottom: 10px; font-weight: 700; }}
    .filter-section {{ margin-bottom: 18px; }}
    .filter-section label {{ display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 6px; cursor: pointer; font-size: 0.82rem; color: var(--text); transition: background 0.15s; }}
    .filter-section label:hover {{ background: var(--bg); }}
    .filter-section input[type="checkbox"] {{ accent-color: var(--cfa-red); width: 15px; height: 15px; }}
    select.filter-select {{
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      padding: 8px 10px;
      font-size: 0.82rem;
      outline: none;
      cursor: pointer;
      font-weight: 500;
    }}
    .btn-reset {{
      width: 100%;
      background: transparent;
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--muted);
      padding: 8px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      margin-top: 2px;
    }}
    .btn-reset:hover {{ background: var(--bg); color: var(--text); }}

    .sidebar-guide-box {{
      margin-top: auto;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
    }}
    .sidebar-guide-box h4 {{
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--text);
      font-weight: 800;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .guide-item {{ margin-bottom: 6px; }}
    .guide-item:last-child {{ margin-bottom: 0; }}
    .guide-item-title {{ font-size: 0.75rem; font-weight: 700; color: var(--text); }}
    .guide-item-desc {{ font-size: 0.7rem; color: var(--muted); line-height: 1.3; margin-top: 1px; }}

    /* ── CANDIDATES AREA ── */
    .candidates-area {{ flex: 1; padding: 16px 20px; }}
    .results-info {{ font-size: 0.82rem; color: var(--muted); margin-bottom: 12px; }}
    .results-info strong {{ color: var(--text); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
      gap: 14px;
    }}

    /* ── UNIFIED CANDIDATE CARD ── */
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
      position: relative;
    }}
    .card:hover {{ 
      transform: translateY(-2px); 
      border-color: #CBD5E1; 
      box-shadow: 0 4px 12px rgba(0,0,0,0.04); 
    }}

    .card-top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }}
    
    .card-badge {{
      font-size: 0.65rem; 
      font-weight: 700; 
      text-transform: uppercase;
      letter-spacing: 0.6px; 
      padding: 3px 8px; 
      border-radius: 20px;
      white-space: nowrap;
      flex-shrink: 0;
    }}
    .badge-gold     {{ background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }}
    .badge-ideal    {{ background: #F0FDF4; color: #166534; border: 1px solid #BBF7D0; }}
    .badge-potencial{{ background: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; }}
    .badge-nocalif  {{ background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; }}
    .badge-desc     {{ background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }}

    .card-name {{ font-size: 0.98rem; font-weight: 700; line-height: 1.2; color: var(--text); }}
    .card-puesto-full {{ 
      font-size: 0.78rem; 
      color: var(--muted); 
      font-weight: 500;
      margin-top: 3px;
      line-height: 1.3;
    }}

    /* ── SOFT SCORE PROGRESS BAR ── */
    .score-block {{
      display: flex;
      flex-direction: column;
      gap: 5px;
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      padding: 10px;
      border-radius: 9px;
    }}
    .score-header-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .score-title-lbl {{
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--muted);
    }}
    .score-val-txt {{
      font-size: 1.1rem;
      font-weight: 800;
      line-height: 1;
    }}
    .score-progress-track {{
      width: 100%;
      height: 6px;
      background: #E2E8F0;
      border-radius: 99px;
      overflow: hidden;
    }}
    .score-progress-fill {{
      height: 100%;
      border-radius: 99px;
      transition: width 0.4s ease;
    }}

    /* ── SCORE BREAKDOWN GRID ── */
    .score-breakdown {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 4px;
      text-align: center;
      padding-top: 6px;
      border-top: 1px solid #E2E8F0;
      margin-top: 2px;
    }}
    .score-item {{ cursor: help; }}
    .score-item .score-item-val {{ 
      font-size: 0.9rem; 
      font-weight: 700; 
      color: var(--text);
    }}
    .score-item .score-item-lbl {{ 
      font-size: 0.6rem; 
      color: var(--muted); 
      margin-top: 2px; 
      font-weight: 600; 
      text-transform: uppercase;
    }}

    /* ── META INFO ── */
    .card-meta {{ display: flex; flex-direction: column; gap: 5px; }}
    .meta-row {{ display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: var(--muted); }}
    .meta-row svg {{ flex-shrink: 0; color: var(--muted); }}

    .desc-reason {{
      background: #FEF2F2;
      border: 1px solid #FECACA;
      border-radius: 8px;
      padding: 7px 10px;
      font-size: 0.72rem;
      color: var(--desc);
      line-height: 1.35;
      font-weight: 500;
    }}

    .card-actions {{ display: flex; gap: 8px; margin-top: auto; padding-top: 2px; }}
    .btn-action {{
      flex: 1;
      width: 100%;
      padding: 8px 10px;
      border-radius: 8px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      display: flex; align-items: center; justify-content: center; gap: 6px;
      text-decoration: none;
    }}
    .btn-secondary {{ background: var(--bg); color: var(--text); border: 1px solid var(--border); }}
    .btn-secondary:hover {{ background: #E2E8F0; }}

    /* ── SCROLLBARS ── */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: #CBD5E1; border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #94A3B8; }}

    /* ── MODAL ── */
    .modal-overlay {{
      display: none; position: fixed; inset: 0;
      background: rgba(15, 23, 42, 0.6); z-index: 1000;
      align-items: center; justify-content: center;
      padding: 16px;
      backdrop-filter: blur(4px);
    }}
    .modal-overlay.open {{ display: flex; }}
    .modal {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      max-width: 880px;
      width: 94%;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      animation: fadeUp 0.15s ease;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
      overflow: hidden;
    }}
    @keyframes fadeUp {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}

    .modal-header {{
      padding: 20px 28px 16px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
      flex-shrink: 0;
    }}
    .modal-title {{ font-size: 1.3rem; font-weight: 800; color: var(--text); }}
    .modal-subtitle {{ font-size: 0.85rem; color: var(--muted); margin-top: 5px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
    .btn-close {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--muted);
      width: 32px; height: 32px;
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; flex-shrink: 0;
      transition: all 0.2s;
    }}
    .btn-close:hover {{ color: var(--text); background: var(--border); }}

    .modal-body {{
      padding: 22px 28px 28px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      overflow-y: auto;
      flex: 1;
    }}

    .modal-scores {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
    }}
    .score-box {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 10px;
      text-align: center;
    }}
    .score-box .big {{ font-size: 1.5rem; font-weight: 800; line-height: 1.1; }}
    .score-box .lbl {{ font-size: 0.7rem; color: var(--muted); margin-top: 4px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
    .score-box .max {{ font-size: 0.72rem; color: var(--muted); margin-top: 2px; }}

    /* ── SYSTEMS ANALYST COMPETENCY PROFILE (JOSEPH ANGELO STYLE) ── */
    .competency-profile-card {{
      background: #FEFCE8;
      border: 1px solid #FEF08A;
      border-radius: 12px;
      padding: 16px 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}
    .competency-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px dashed #FDE047;
    }}
    .comp-title {{
      font-size: 0.8rem;
      font-weight: 800;
      letter-spacing: 0.8px;
      color: #854D0E;
      text-transform: uppercase;
    }}
    .comp-score {{
      font-size: 0.9rem;
      font-weight: 800;
      color: #15803D;
      background: #DCFCE7;
      border: 1px solid #86EFAC;
      padding: 3px 10px;
      border-radius: 6px;
    }}
    .comp-body {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .comp-row {{
      display: flex;
      align-items: baseline;
      gap: 8px;
      font-size: 0.85rem;
      line-height: 1.45;
    }}
    .comp-icon {{
      font-size: 0.95rem;
      flex-shrink: 0;
    }}
    .comp-label {{
      font-weight: 700;
      color: #1E293B;
      min-width: 120px;
      flex-shrink: 0;
    }}
    .comp-value {{
      color: #0F172A;
      font-weight: 500;
    }}
    .cert-pill {{
      display: inline-block;
      background: #FEF08A;
      color: #854D0E;
      border: 1px solid #FACC15;
      font-weight: 800;
      font-size: 0.76rem;
      padding: 2px 8px;
      border-radius: 5px;
      margin-right: 4px;
    }}
    .comp-divider {{
      border-top: 1px dashed #FDE047;
      margin: 4px 0;
    }}
    .comp-analysis {{
      display: flex;
      align-items: flex-start;
      gap: 8px;
      font-size: 0.84rem;
      color: #334155;
      line-height: 1.5;
      background: rgba(255, 255, 255, 0.6);
      border-radius: 8px;
      padding: 10px 12px;
      border: 1px solid rgba(253, 224, 71, 0.4);
    }}
    .comp-analysis-icon {{
      font-size: 1rem;
      flex-shrink: 0;
    }}

    /* Highlights / Signals Panel */
    .signals-panel {{
      background: #F0FDF4;
      border: 1px solid #BBF7D0;
      border-radius: 12px;
      padding: 16px;
    }}
    .signals-panel-title {{
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #047857;
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 12px;
    }}
    .signals-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 10px;
    }}
    .signal-card {{
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 9px;
      padding: 12px 14px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }}
    .sig-badge {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 0.78rem;
      font-weight: 800;
      padding: 3px 10px;
      border-radius: 6px;
    }}
    .sig-badge-cert {{ background: #FEF3C7; color: #B45309; border: 1px solid #FCD34D; }}
    .sig-badge-exp  {{ background: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }}
    .sig-badge-edu  {{ background: #EDE9FE; color: #6D28D9; border: 1px solid #DDD6FE; }}
    .sig-q-title {{ font-size: 0.78rem; color: #64748B; margin-top: 6px; font-weight: 600; }}
    .sig-q-val   {{ font-size: 0.84rem; color: #0F172A; margin-top: 3px; font-weight: 500; line-height: 1.4; }}

    .detected-inline-pill {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: #FEF3C7;
      color: #92400E;
      border: 1px solid #FDE68A;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      margin-top: 6px;
    }}

    .modal-section-title {{
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
      margin-bottom: 10px;
      font-weight: 800;
    }}
    .ia-evaluation {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    .ia-question {{ border-bottom: 1px solid var(--border); padding-bottom: 14px; }}
    .ia-question:last-child {{ border-bottom: none; padding-bottom: 0; }}
    .ia-q-text {{ font-size: 0.85rem; font-weight: 700; color: var(--text); margin-bottom: 6px; }}
    .ia-q-answer {{
      font-size: 0.82rem;
      color: var(--text);
      background: var(--surface);
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid var(--border);
      line-height: 1.45;
      font-style: normal;
    }}
    .ia-reason {{ font-size: 0.78rem; color: var(--muted); line-height: 1.4; margin-top: 6px; }}

    .choice-detail {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .choice-row {{ display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; padding: 4px 0; border-bottom: 1px dashed var(--border); }}
    .choice-row:last-child {{ border-bottom: none; }}
    .choice-row .q-name {{ color: #475569; flex: 1; margin-right: 12px; }}
    .choice-row .q-answer {{ color: var(--text); font-weight: 600; text-align: right; }}
    .choice-row .q-pts {{ font-weight: 800; margin-left: 12px; min-width: 32px; text-align: right; }}

    /* ── SCORING GUIDE MODAL ── */
    .guide-modal-body {{
      padding: 20px 24px 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    .guide-section {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 9px;
      padding: 14px;
    }}
    .guide-section h4 {{
      font-size: 0.82rem;

      font-weight: 700;
      color: var(--text);
      margin-bottom: 5px;
    }}
    .guide-section p {{
      font-size: 0.78rem;
      color: var(--muted);
      line-height: 1.4;
    }}
    /* ── PAGINATION BAR ── */
    .pagination-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 24px;
      padding: 14px 20px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: var(--shadow-sm);
      flex-wrap: wrap;
      gap: 12px;
    }}
    .pagination-info {{
      font-size: 0.82rem;
      color: var(--muted);
      font-weight: 600;
    }}
    .pagination-pages {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .page-btn {{
      padding: 6px 12px;
      font-size: 0.8rem;
      font-weight: 700;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 32px;
    }}
    .page-btn:hover:not(:disabled) {{
      background: #F1F5F9;
      border-color: #CBD5E1;
    }}
    .page-btn.active {{
      background: var(--cfa-red);
      color: #fff;
      border-color: var(--cfa-red);
    }}
    .page-btn:disabled {{
      opacity: 0.4;
      cursor: not-allowed;
    }}
    .page-size-selector {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.82rem;
      color: var(--muted);
      font-weight: 600;
    }}
    .page-size-selector select {{
      padding: 5px 10px;
      border-radius: 6px;
      border: 1px solid var(--border);
      font-size: 0.82rem;
      background: var(--surface);
      color: var(--text);
      font-weight: 600;
      cursor: pointer;
    }}

    /* ── OPTIMIZACIÓN RESPONSIVA (TABLETS Y MÓVILES) ── */
    @media (max-width: 960px) {{
      header {{
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
        padding: 12px 16px;
      }}
      .header-actions {{
        width: 100%;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-left: 0;
      }}
      .header-search {{
        width: 100%;
        flex: 1 1 100%;
      }}
      .stats-bar {{
        padding: 10px 14px 4px;
        gap: 8px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(105px, 1fr));
      }}
      .stat-card {{
        padding: 8px 10px;
        min-width: 0;
      }}
      .stat-card .stat-val {{
        font-size: 1.25rem;
      }}
      .main {{
        flex-direction: column;
      }}
      .sidebar {{
        width: 100%;
        min-width: 100%;
        min-height: auto;
        border-right: none;
        border-bottom: 1px solid var(--border);
        padding: 12px 14px;
      }}
      .sidebar-guide-box {{
        display: none;
      }}
      .content {{
        padding: 12px 14px;
      }}
      .cards-grid {{
        grid-template-columns: 1fr;
        gap: 12px;
      }}
      .modal {{
        width: 96%;
        max-height: 92vh;
      }}
      .modal-header {{
        padding: 14px 16px 10px;
      }}
      .modal-body {{
        padding: 14px 16px 18px;
        gap: 14px;
      }}
      .modal-scores {{
        grid-template-columns: 1fr;
        gap: 10px;
      }}
      .sa-profile-grid {{
        grid-template-columns: 1fr;
      }}
      .pagination-bar {{
        flex-direction: column;
        align-items: center;
        gap: 10px;
        padding: 12px 14px;
      }}
      .pagination-pages {{
        flex-wrap: wrap;
        justify-content: center;
      }}
    }}

    @media (max-width: 480px) {{
      .header-brand h1 {{
        font-size: 0.95rem;
      }}
      .card-stats {{
        grid-template-columns: 1fr 1fr 1fr;
        padding: 6px;
      }}
      .card-stat-val {{
        font-size: 0.9rem;
      }}
      .card-stat-label {{
        font-size: 0.55rem;
      }}
      .modal-title {{
        font-size: 1.05rem;
      }}
      .modal-score-badge {{
        font-size: 1.2rem;
      }}
    }}
  </style>
</head>
<body>

<!-- HEADER -->
<header>
  <div class="header-brand">
    <div class="brand-badge">CFA</div>
    <h1>Candidates Portal — <span>CFA Stafford</span></h1>
  </div>
  
  <div class="header-actions">
    <div class="header-search">
      <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
      <input type="text" id="searchInput" placeholder="Search by name, email or position..." oninput="paginaActual=1; filtrarYMostrar()">
    </div>

    <button class="btn-guide" onclick="abrirGuideModal()">
      <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
      </svg>
      <span>Scoring Guide</span>
    </button>

    <div id="last-update">Updated: live</div>

    <button class="btn-refresh" id="btnRefresh" onclick="resetFiltros()">
      <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
        <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"/>
      </svg>
      <span>Reset</span>
    </button>
  </div>
</header>

<!-- STATS -->
<div class="stats-bar" id="statsBar">
  <div class="stat-card active" id="stat-all" onclick="filtrarPorClasif('')">
    <div class="stat-label">Total</div>
    <div class="stat-val color-total" id="s-total">{resumen_data['total']}</div>
    <div class="stat-sub">candidates</div>
  </div>
  <div class="stat-card" id="stat-gold" onclick="filtrarPorClasif('GOLD')">
    <div class="stat-label">GOLD</div>
    <div class="stat-val color-gold" id="s-gold">{resumen_data['clasificaciones']['gold']}</div>
    <div class="stat-sub">≥ 97%</div>
  </div>
  <div class="stat-card" id="stat-ideal" onclick="filtrarPorClasif('CANDIDATO IDEAL')">
    <div class="stat-label">Ideal</div>
    <div class="stat-val color-ideal" id="s-ideal">{resumen_data['clasificaciones']['ideal']}</div>
    <div class="stat-sub">75%–96%</div>
  </div>
  <div class="stat-card" id="stat-potencial" onclick="filtrarPorClasif('POTENCIAL')">
    <div class="stat-label">Potential</div>
    <div class="stat-val color-potencial" id="s-potencial">{resumen_data['clasificaciones']['potencial']}</div>
    <div class="stat-sub">50%–74%</div>
  </div>
  <div class="stat-card" id="stat-desc" onclick="filtrarPorClasif('DESCALIFICADO')">
    <div class="stat-label">Disqualified</div>
    <div class="stat-val color-desc" id="s-desc">{resumen_data['clasificaciones']['descalificado']}</div>
    <div class="stat-sub">auto-disqualified</div>
  </div>
</div>

<!-- MAIN -->
<div class="main">
  <!-- SIDEBAR -->
  <aside class="sidebar">
    <div class="filter-section">
      <h3>Sort by</h3>
      <select class="filter-select" id="sortSelect" onchange="paginaActual=1; filtrarYMostrar()">
        <option value="prioridad">Priority (best first)</option>
        <option value="porcentaje_desc">% Score (high to low)</option>
        <option value="porcentaje_asc">% Score (low to high)</option>
        <option value="fecha_desc">Date (most recent)</option>
        <option value="distancia">Distance (closest)</option>
      </select>
    </div>

    <div class="filter-section">
      <h3>Position</h3>
      <div id="filtrosPuestos"></div>
    </div>

    <div class="filter-section">
      <h3>Classification</h3>
      <label><input type="checkbox" value="GOLD" onchange="paginaActual=1; filtrarYMostrar()" class="chk-clasif"> GOLD</label>
      <label><input type="checkbox" value="CANDIDATO IDEAL" onchange="paginaActual=1; filtrarYMostrar()" class="chk-clasif"> Ideal</label>
      <label><input type="checkbox" value="POTENCIAL" onchange="paginaActual=1; filtrarYMostrar()" class="chk-clasif"> Potential</label>
      <label><input type="checkbox" value="DESCALIFICADO" onchange="paginaActual=1; filtrarYMostrar()" class="chk-clasif"> Disqualified</label>
    </div>

    <button class="btn-reset" onclick="resetFiltros()">Clear filters</button>

    <div class="sidebar-guide-box">
      <h4>Scoring Legend</h4>
      <div class="guide-item">
        <div class="guide-item-title">Choice</div>
        <div class="guide-item-desc">Multiple-choice score.</div>
      </div>
      <div class="guide-item">
        <div class="guide-item-title">Distance</div>
        <div class="guide-item-desc">Commute proximity score.</div>
      </div>
      <div class="guide-item">
        <div class="guide-item-title">AI Score</div>
        <div class="guide-item-desc">AI open-text answer rating.</div>
      </div>
    </div>
  </aside>

  <!-- CANDIDATES -->
  <div class="candidates-area">
    <div class="results-info" id="resultsInfo"></div>
    <div class="grid" id="grid"></div>
    <div class="pagination-bar" id="paginationBar">
      <div class="pagination-info" id="paginationInfo"></div>
      <div class="pagination-pages" id="paginationPages"></div>
      <div class="page-size-selector">
        <span>Cards per page:</span>
        <select id="pageSizeSelect" onchange="cambiarPageSize()">
          <option value="12" selected>12</option>
          <option value="24">24</option>
          <option value="48">48</option>
          <option value="all">All</option>
        </select>
      </div>
    </div>
  </div>
</div>

<!-- MODAL EVALUACION -->
<div class="modal-overlay" id="modal" onclick="closeModal(event)">
  <div class="modal" id="modalContent">
    <div class="modal-header">
      <div>
        <div class="modal-title" id="modal-name"></div>
        <div class="modal-subtitle" id="modal-sub"></div>
      </div>
      <button class="btn-close" onclick="cerrarModal()">✕</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>

<!-- MODAL SCORING GUIDE -->
<div class="modal-overlay" id="guideModal" onclick="closeGuideModal(event)">
  <div class="modal">
    <div class="modal-header">
      <div>
        <div class="modal-title">Candidate Scoring Methodology</div>
        <div class="modal-subtitle">Official evaluation and scoring framework for CFA Stafford</div>
      </div>
      <button class="btn-close" onclick="cerrarGuideModal()">✕</button>
    </div>
    <div class="guide-modal-body">
      <div class="guide-section">
        <h4>1. Overall Score (%)</h4>
        <p>The total candidate percentage represents the weighted sum of all evaluation modules (Choice + Distance + AI Evaluation) against the total maximum possible points.</p>
      </div>
      <div class="guide-section">
        <h4>2. Systems Analyst Gatekeeper</h4>
        <p>Must have formal studies in Computer Science, Systems, or IT and at least 2.0 years of verifiable technical experience.</p>
      </div>
      <div class="guide-section">
        <h4>3. Classification Tiers</h4>
        <p><strong>GOLD:</strong> ≥ 97% | <strong>IDEAL:</strong> 75%–96% | <strong>POTENTIAL:</strong> 50%–74% | <strong>DISQUALIFIED:</strong> Failed minimum requirements.</p>
      </div>
    </div>
  </div>
</div>

<script>
  let todosLosCandidatos = {candidates_json};
  let filtroClasif = '';

  function construirFiltrosPuestos() {{
    const puestos = [...new Set(todosLosCandidatos.map(c => String(c.puesto_aplicado || 'Unknown position').trim()).filter(Boolean))].sort();
    const wrap = document.getElementById('filtrosPuestos');
    wrap.innerHTML = puestos.map(p => {{
      const short = p.length > 28 ? p.substring(0, 26) + '…' : p;
      return `<label title="${{esc(p)}}"><input type="checkbox" value="${{esc(p)}}" onchange="filtrarYMostrar()" class="chk-puesto"> ${{esc(short)}}</label>`;
    }}).join('');
  }}

  function filtrarYMostrar() {{
    const search = document.getElementById('searchInput').value.toLowerCase();
    const sort = document.getElementById('sortSelect').value;
    const puestosActivos = [...document.querySelectorAll('.chk-puesto:checked')].map(c => c.value);
    const clasifActivos = [...document.querySelectorAll('.chk-clasif:checked')].map(c => c.value.toUpperCase());

    // 1. Universo base según búsqueda y puestos seleccionados (base para los KPIs superiores)
    let baseFiltrados = todosLosCandidatos.filter(c => {{
      if (search) {{
        const match = (c.nombre || '').toLowerCase().includes(search) ||
                      (c.puesto_aplicado || '').toLowerCase().includes(search) ||
                      (c.telefono || '').toLowerCase().includes(search);
        if (!match) return false;
      }}
      if (puestosActivos.length > 0) {{
        if (!puestosActivos.includes(String(c.puesto_aplicado || '').trim())) return false;
      }}
      return true;
    }});

    // 2. Calcular métricas dinámicas para los puestos seleccionados
    const totalPuesto = baseFiltrados.length;
    let goldCount = 0, idealCount = 0, potencialCount = 0, descCount = 0;

    baseFiltrados.forEach(c => {{
      const cl = String(c.clasificacion || '').toUpperCase();
      if (cl === 'GOLD') goldCount++;
      else if (cl.includes('IDEAL')) idealCount++;
      else if (cl.includes('POTENCIAL') || cl.includes('POTENTIAL')) potencialCount++;
      else if (cl.includes('DESCALIFICADO') || cl.includes('DISQUALIFIED')) descCount++;
    }});

    // Actualizar los números en los stat-cards superiores
    const sTotal = document.getElementById('s-total');
    const sGold = document.getElementById('s-gold');
    const sIdeal = document.getElementById('s-ideal');
    const sPotencial = document.getElementById('s-potencial');
    const sDesc = document.getElementById('s-desc');

    if (sTotal) sTotal.textContent = totalPuesto;
    if (sGold) sGold.textContent = goldCount;
    if (sIdeal) sIdeal.textContent = idealCount;
    if (sPotencial) sPotencial.textContent = potencialCount;
    if (sDesc) sDesc.textContent = descCount;

    // 3. Aplicar filtro de clasificación para las tarjetas de candidatos
    let filtrados = baseFiltrados.filter(c => {{
      if (filtroClasif) {{
        if (!String(c.clasificacion || '').toUpperCase().includes(filtroClasif)) return false;
      }}
      if (clasifActivos.length > 0) {{
        const clas = String(c.clasificacion || '').toUpperCase();
        if (!clasifActivos.some(a => clas.includes(a))) return false;
      }}
      return true;
    }});

    // 4. Ordenar instantáneamente
    filtrados.sort((a, b) => {{
      if (sort === 'prioridad') {{
        const pa = Number(a.prioridad) || 0, pb = Number(b.prioridad) || 0;
        if (pb !== pa) return pb - pa;
        const sa = Number(a.porcentaje_final) || 0, sb = Number(b.porcentaje_final) || 0;
        if (sb !== sa) return sb - sa;
        // Desempate por menor distancia en caso de empate en puntuación
        return (Number(a.distancia_millas) || 999) - (Number(b.distancia_millas) || 999);
      }}
      if (sort === 'porcentaje_desc') return (Number(b.porcentaje_final) || 0) - (Number(a.porcentaje_final) || 0);
      if (sort === 'porcentaje_asc')  return (Number(a.porcentaje_final) || 0) - (Number(b.porcentaje_final) || 0);
      if (sort === 'fecha_desc') return new Date(b.fecha_aplicacion || 0) - new Date(a.fecha_aplicacion || 0);
      if (sort === 'distancia')  return (Number(a.distancia_millas) || 9999) - (Number(b.distancia_millas) || 9999);
      return 0;
    }});

    // 5. Mensaje de conteo de candidatos
    const resInfo = document.getElementById('resultsInfo');
    if (resInfo) {{
      if (filtrados.length === todosLosCandidatos.length) {{
        resInfo.innerHTML = `Showing all <strong>${{todosLosCandidatos.length}}</strong> candidates`;
      }} else if (filtrados.length === totalPuesto) {{
        resInfo.innerHTML = `Showing <strong>${{filtrados.length}}</strong> of <strong>${{todosLosCandidatos.length}}</strong> candidates`;
      }} else {{
        resInfo.innerHTML = `Showing <strong>${{filtrados.length}}</strong> of <strong>${{totalPuesto}}</strong> filtered candidates`;
      }}
    }}

    renderCards(filtrados);
  }}


  function filtrarPorClasif(clasif) {{
    filtroClasif = clasif;
    document.querySelectorAll('.stat-card').forEach(s => s.classList.remove('active'));
    const map = {{ '': 'stat-all', 'GOLD': 'stat-gold', 'CANDIDATO IDEAL': 'stat-ideal', 'POTENCIAL': 'stat-potencial', 'DESCALIFICADO': 'stat-desc' }};
    if (map[clasif]) document.getElementById(map[clasif])?.classList.add('active');
    filtrarYMostrar();
  }}

  function resetFiltros() {{
    document.getElementById('searchInput').value = '';
    document.querySelectorAll('.chk-puesto, .chk-clasif').forEach(c => c.checked = false);
    document.getElementById('sortSelect').value = 'prioridad';
    filtroClasif = '';
    document.querySelectorAll('.stat-card').forEach(s => s.classList.remove('active'));
    document.getElementById('stat-all')?.classList.add('active');
    paginaActual = 1;
    filtrarYMostrar();
  }}

  let paginaActual = 1;
  let pageSize = 12;
  let candidatosFiltradosGlobal = [];

  function cambiarPageSize() {{
    const val = document.getElementById('pageSizeSelect').value;
    pageSize = val === 'all' ? 99999 : parseInt(val, 10);
    paginaActual = 1;
    renderCards(candidatosFiltradosGlobal);
  }}

  function irAPagina(p) {{
    paginaActual = p;
    renderCards(candidatosFiltradosGlobal);
    document.querySelector('.candidates-area')?.scrollIntoView({{ behavior: 'smooth' }});
  }}

  function renderCards(lista) {{
    candidatosFiltradosGlobal = lista;
    const grid = document.getElementById('grid');
    const pagBar = document.getElementById('paginationBar');
    const pagInfo = document.getElementById('paginationInfo');
    const pagPages = document.getElementById('paginationPages');

    if (!lista.length) {{
      grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:60px; color:var(--muted);">No candidates found with these filters.</div>';
      if (pagBar) pagBar.style.display = 'none';
      return;
    }}

    if (pagBar) pagBar.style.display = 'flex';

    const totalCandidatos = lista.length;
    const totalPages = Math.ceil(totalCandidatos / pageSize) || 1;
    if (paginaActual > totalPages) paginaActual = totalPages;
    if (paginaActual < 1) paginaActual = 1;

    const startIdx = (paginaActual - 1) * pageSize;
    const endIdx = Math.min(startIdx + pageSize, totalCandidatos);
    const visibles = lista.slice(startIdx, endIdx);

    grid.innerHTML = visibles.map((c, idx) => cardHTML(c, startIdx + idx)).join('');

    if (pagInfo) {{
      pagInfo.innerHTML = `Showing <strong>${{startIdx + 1}}–${{endIdx}}</strong> of <strong>${{totalCandidatos}}</strong> candidates`;
    }}

    if (pagPages) {{
      if (totalPages <= 1) {{
        pagPages.innerHTML = '';
      }} else {{
        let pagesHtml = '';
        pagesHtml += `<button class="page-btn" onclick="irAPagina(${{paginaActual - 1}})" ${{paginaActual === 1 ? 'disabled' : ''}}>« Prev</button>`;
        
        let startP = Math.max(1, paginaActual - 2);
        let endP = Math.min(totalPages, paginaActual + 2);
        
        if (startP > 1) {{
          pagesHtml += `<button class="page-btn ${{paginaActual === 1 ? 'active' : ''}}" onclick="irAPagina(1)">1</button>`;
          if (startP > 2) pagesHtml += `<span style="color:var(--muted); padding:0 4px;">...</span>`;
        }}

        for (let p = startP; p <= endP; p++) {{
          pagesHtml += `<button class="page-btn ${{p === paginaActual ? 'active' : ''}}" onclick="irAPagina(${{p}})">${{p}}</button>`;
        }}

        if (endP < totalPages) {{
          if (endP < totalPages - 1) pagesHtml += `<span style="color:var(--muted); padding:0 4px;">...</span>`;
          pagesHtml += `<button class="page-btn ${{paginaActual === totalPages ? 'active' : ''}}" onclick="irAPagina(${{totalPages}})">${{totalPages}}</button>`;
        }}

        pagesHtml += `<button class="page-btn" onclick="irAPagina(${{paginaActual + 1}})" ${{paginaActual === totalPages ? 'disabled' : ''}}>Next »</button>`;
        pagPages.innerHTML = pagesHtml;
      }}
    }}
  }}

  function clasifInfo(clas) {{
    const c = String(clas || '').toUpperCase();
    if (c.includes('GOLD'))          return {{ cls: 'badge-gold',     color: '#D97706', label: 'GOLD' }};
    if (c.includes('IDEAL'))         return {{ cls: 'badge-ideal',    color: '#0D9488', label: 'IDEAL' }};
    if (c.includes('POTENCIAL'))     return {{ cls: 'badge-potencial', color: '#2563EB', label: 'POTENTIAL' }};
    if (c.includes('DESCALIFICADO')) return {{ cls: 'badge-desc',     color: '#DC2626', label: 'DISQUALIFIED' }};
    return {{ cls: 'badge-nocalif', color: '#6B7280', label: clas || '—' }};
  }}

  function scoreColor(pct) {{
    if (pct >= 97) return '#D97706';
    if (pct >= 75) return '#0D9488';
    if (pct >= 50) return '#2563EB';
    return '#DC2626';
  }}

  function cardHTML(c, idx) {{
    const pct = Math.min(100, Math.max(0, Number(c.porcentaje_final) || 0));
    const info = clasifInfo(c.clasificacion);
    const color = scoreColor(pct);
    const desc = String(c.descalificado || '').toUpperCase() === 'TRUE';
    const puestoCompleto = String(c.puesto_aplicado || 'Unknown position');
    const dist = c.distancia_texto || '—';
    const fecha = c.fecha_aplicacion ? String(c.fecha_aplicacion).substring(0, 10) : '—';

    return `<div class="card" id="card-${{idx}}">
      <div class="card-top">
        <div>
          <div class="card-name">${{esc(c.nombre || '—')}}</div>
          <div class="card-puesto-full">${{esc(puestoCompleto)}}</div>
        </div>
        <span class="card-badge ${{info.cls}}">${{info.label}}</span>
      </div>

      <div class="score-block">
        <div class="score-header-row">
          <span class="score-title-lbl">Overall Score</span>
          <span class="score-val-txt" style="color:${{color}}">${{pct}}%</span>
        </div>
        <div class="score-progress-track">
          <div class="score-progress-fill" style="width:${{pct}}%; background-color:${{color}}"></div>
        </div>
        <div class="score-breakdown">
          <div class="score-item" title="Multiple-choice score">
            <div class="score-item-val">${{c.puntaje_choice || 0}}</div>
            <div class="score-item-lbl">Choice</div>
          </div>
          <div class="score-item" title="Proximity score">
            <div class="score-item-val">${{c.puntaje_distancia || 0}}</div>
            <div class="score-item-lbl">Distance</div>
          </div>
          <div class="score-item" title="AI evaluation score">
            <div class="score-item-val">${{c.puntaje_ia || 0}}</div>
            <div class="score-item-lbl">AI Score</div>
          </div>
        </div>
      </div>

      <div class="card-meta">
        <div class="meta-row">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
          <div>${{esc(dist)}} — ${{esc(String(c.direccion || 'No address'))}}</div>
        </div>
        <div class="meta-row">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          <div>Applied: ${{fecha}}</div>
        </div>
        <div class="meta-row">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-3.07-8.63A2 2 0 0 1 5.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L9.09 9.91a16 16 0 0 0 5.94 5.94l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
          <div>${{esc(String(c.telefono || '—'))}}</div>
        </div>
      </div>

      ${{desc && c.motivo_descalificacion ? `<div class="desc-reason">${{esc(String(c.motivo_descalificacion))}}</div>` : ''}}

      <div class="card-actions">
        <button class="btn-action btn-secondary" onclick="abrirModal('${{esc(String(c.uuid || ''))}}')">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
          View Evaluation
        </button>
      </div>
    </div>`;
  }}

  function abrirModal(uuid) {{
    const c = todosLosCandidatos.find(cand => String(cand.uuid) === String(uuid));
    if (!c) return;

    const pct = Number(c.porcentaje_final) || 0;
    const info = clasifInfo(c.clasificacion);
    const color = scoreColor(pct);

    document.getElementById('modal-name').textContent = c.nombre || '—';
    document.getElementById('modal-sub').innerHTML = `
      <span class="card-badge ${{info.cls}}">${{info.label}}</span>
      <span style="font-weight:700; color:var(--text);">${{esc(String(c.puesto_aplicado || ''))}}</span>
      <span>·</span>
      <span>📍 ${{esc(String(c.distancia_texto || '—'))}}</span>
      <span>·</span>
      <span>📞 ${{esc(String(c.telefono || '—'))}}</span>
    `;

    let bodyHTML = `
      <div class="modal-scores">
        <div class="score-box">
          <div class="big" style="color:${{color}}">${{pct}}%</div>
          <div class="lbl">Final Score</div>
          <div class="max">${{c.puntaje_total || 0}} / ${{c.maximo_posible || 0}} pts</div>
        </div>
        <div class="score-box">
          <div class="big">${{c.puntaje_choice || 0}}</div>
          <div class="lbl">Choice Score</div>
          <div class="max">multiple choice</div>
        </div>
        <div class="score-box">
          <div class="big">${{c.puntaje_ia || 0}}</div>
          <div class="lbl">AI Score</div>
          <div class="max">open-text eval</div>
        </div>
        <div class="score-box">
          <div class="big">${{c.puntaje_distancia || 0}}</div>
          <div class="lbl">Distance</div>
          <div class="max">${{esc(c.distancia_texto || '—')}}</div>
        </div>
      </div>
    `;

    // 1. Panel de Perfil de Competencias de Systems Analyst (Estilo Joseph Angelo)
    if (c.competency_profile) {{
      const prof = c.competency_profile;
      const certsHTML = prof.certifications && prof.certifications.length > 0 
        ? prof.certifications.map(crt => `<span class="cert-pill">🛡️ ${{esc(crt)}}</span>`).join(' ') 
        : '<span style="color:#64748B; font-style:italic; font-size:0.82rem;">Ninguna detectada</span>';
      
      bodyHTML += `
        <div class="competency-profile-card">
          <div class="competency-header">
            <span class="comp-title">💼 SYSTEMS ANALYST COMPETENCY PROFILE</span>
            <span class="comp-score">${{esc(prof.score_badge)}}</span>
          </div>
          <div class="comp-body">
            <div class="comp-row">
              <span class="comp-icon">💼</span>
              <span class="comp-label">IT Experience:</span>
              <span class="comp-value">${{esc(prof.it_experience)}}</span>
            </div>
            <div class="comp-row">
              <span class="comp-icon">🎓</span>
              <span class="comp-label">Field of Study:</span>
              <span class="comp-value">${{esc(prof.field_of_study)}}</span>
            </div>
            <div class="comp-row">
              <span class="comp-icon">📜</span>
              <span class="comp-label">Certifications:</span>
              <span class="comp-value">${{certsHTML}}</span>
            </div>
            <div class="comp-divider"></div>
            <div class="comp-analysis">
              <span class="comp-analysis-icon">💡</span>
              <div><strong>AI Analysis:</strong> ${{esc(prof.ai_analysis)}}</div>
            </div>
          </div>
        </div>
      `;
    }} else if (c.detected_signals && c.detected_signals.length > 0) {{
      const sigs = c.detected_signals;
      bodyHTML += `
        <div class="signals-panel">
          <div class="signals-panel-title">🎓 Credenciales y Pistas Detectadas (${{sigs.length}})</div>
          <div class="signals-grid">
            ${{sigs.map(s => {{
              const icon = s.type === 'CERTIFICATION' ? '🛡️' : (s.type === 'EXPERIENCE' ? '💼' : '📚');
              const badgeCls = s.type === 'CERTIFICATION' ? 'sig-badge-cert' : (s.type === 'EXPERIENCE' ? 'sig-badge-exp' : 'sig-badge-edu');
              return `
                <div class="signal-card">
                  <div><span class="sig-badge ${{badgeCls}}">${{icon}} ${{esc(s.label)}}</span></div>
                  <div class="sig-q-title">Respondido en: <em>"${{esc(s.question)}}"</em></div>
                  <div class="sig-q-val"><strong>Respuesta:</strong> "${{esc(s.answer)}}"</div>
                </div>
              `;
            }}).join('')}}
          </div>
        </div>
      `;
    }}

    // 2. Motivo de Descalificación si aplica
    const desc = String(c.descalificado || '').toUpperCase() === 'TRUE';
    if (desc && c.motivo_descalificacion) {{
      bodyHTML += `
        <div>
          <div class="modal-section-title" style="color:#DC2626;">Motivo de Auto-Descalificación</div>
          <div class="desc-reason" style="font-size:0.85rem; padding:12px 16px;">${{esc(String(c.motivo_descalificacion))}}</div>
        </div>
      `;
    }}

    // 3. Respuestas Abiertas del Candidato
    const openItems = c.open_text_items || [];
    if (openItems.length > 0) {{
      bodyHTML += `
        <div>
          <div class="modal-section-title">💬 Respuestas a Preguntas Abiertas (${{openItems.length}})</div>
          <div class="ia-evaluation">
            ${{openItems.map(it => {{
              const sigMatch = (c.detected_signals || []).filter(s => String(s.question).toLowerCase() === String(it.question).toLowerCase());
              const sigBadge = sigMatch.length > 0 ? `
                <div class="detected-inline-pill">
                  ✨ <strong>Pista detectada en esta pregunta:</strong> ${{sigMatch.map(s => esc(s.label)).join(', ')}}
                </div>
              ` : '';
              return `
                <div class="ia-question">
                  <div class="ia-q-text">${{esc(it.question)}}</div>
                  <div class="ia-q-answer">${{esc(it.answer)}}</div>
                  ${{sigBadge}}
                  ${{it.reason ? `<div class="ia-reason"><strong>Evaluación:</strong> ${{esc(it.reason)}}</div>` : ''}}
                </div>
              `;
            }}).join('')}}
          </div>
        </div>
      `;
    }}

    // 4. Cuestionario de Opción Múltiple
    const choiceItems = c.choice_items || [];
    if (choiceItems.length > 0) {{
      bodyHTML += `
        <div>
          <div class="modal-section-title">📋 Cuestionario de Selección Múltiple (${{choiceItems.length}})</div>
          <div class="choice-detail">
            ${{choiceItems.map(it => `
              <div class="choice-row">
                <span class="q-name">${{esc(it.question)}}</span>
                <span class="q-answer">${{esc(it.answer)}}</span>
                <span class="q-pts" style="color:${{Number(it.score) > 0 ? '#0D9488' : '#DC2626'}}">${{it.score}} pts</span>
              </div>
            `).join('')}}
          </div>
        </div>
      `;
    }}

    document.getElementById('modal-body').innerHTML = bodyHTML;
    document.getElementById('modal').classList.add('open');
    document.body.style.overflow = 'hidden';
  }}

  function abrirGuideModal() {{
    document.getElementById('guideModal').classList.add('open');
    document.body.style.overflow = 'hidden';
  }}
  function cerrarGuideModal() {{
    document.getElementById('guideModal').classList.remove('open');
    document.body.style.overflow = '';
  }}
  function closeGuideModal(e) {{ if (e.target === document.getElementById('guideModal')) cerrarGuideModal(); }}

  function cerrarModal() {{
    document.getElementById('modal').classList.remove('open');
    document.body.style.overflow = '';
  }}
  function closeModal(e) {{ if (e.target === document.getElementById('modal')) cerrarModal(); }}

  document.addEventListener('keydown', e => {{
    if (e.key === 'Escape') {{ cerrarModal(); cerrarGuideModal(); }}
  }});


  function esc(str) {{
    return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }}

  // Inicialización instantánea
  construirFiltrosPuestos();
  filtrarYMostrar();
</script>
</body>
</html>"""

    return html_template
