"""
RootSight Root Monitoring Dashboard
=====================================
Rezylix Root Intelligence Platform

8 tanks across 2 shelves (Upper: T1-T4, Lower: T5-T8)
One front camera per tank
Temperature + humidity sensor per shelf

Get your free Gemini API key at: https://aistudio.google.com/apikey
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import random

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="RootSight | Rezylix",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        min-width: 290px !important; width: 290px !important; transform: none !important;
    }
    section[data-testid="stSidebar"][aria-expanded="false"] {
        min-width: 290px !important; width: 290px !important;
        margin-left: 0 !important; transform: none !important; display: block !important;
    }
    button[kind="headerNoPadding"],
    [data-testid="collapsedControl"],
    [data-testid="baseButton-headerNoPadding"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONSTANTS
# ============================================================================

TANKS = {
    "upper": ["Tank 1", "Tank 2", "Tank 3", "Tank 4"],
    "lower": ["Tank 5", "Tank 6", "Tank 7", "Tank 8"],
}
ALL_TANKS = TANKS["upper"] + TANKS["lower"]
DAYS = 14

# ============================================================================
# DATA GENERATION
# ============================================================================

@st.cache_data
def generate_root_data(days=DAYS):
    records = []
    for d in range(days):
        date = (datetime.now() - timedelta(days=days - d - 1)).strftime("%Y-%m-%d")
        for tank in ALL_TANKS:
            base_vol = random.uniform(110, 135)
            gf = 1 + (d / days) * random.uniform(0.7, 0.9)
            records.append({
                "date": date,
                "tank": tank,
                "shelf": "Upper" if tank in TANKS["upper"] else "Lower",
                "root_volume":        round(base_vol * gf + random.uniform(-5, 8), 1),
                "root_length":        round(90 * gf + random.uniform(-3, 5), 1),
                "growth_rate":        round(1.5 + (d / days) * 1.5 + random.uniform(-0.3, 0.3), 2),
                "biomass":            round(6 + (d / days) * 8 + random.uniform(-0.5, 0.5), 1),
                "branching_density":  round(0.65 + (d / days) * 0.25 + random.uniform(-0.05, 0.05), 2),
            })
    return pd.DataFrame(records)


@st.cache_data
def generate_env_data(days=DAYS):
    records = []
    for d in range(days):
        date = (datetime.now() - timedelta(days=days - d - 1)).strftime("%Y-%m-%d")
        for shelf in ["Upper", "Lower"]:
            t_off = 1.5 if shelf == "Upper" else 0
            h_off = -3  if shelf == "Upper" else 0
            records.append({
                "date":        date,
                "shelf":       shelf,
                "temperature": round(22 + t_off + random.uniform(-1.2, 1.2), 1),
                "humidity":    round(68 + h_off + random.uniform(-3, 3), 1),
            })
    return pd.DataFrame(records)


def load_excel_data(uploaded_file):
    """
    Parse uploaded Excel file.
    Expected sheets:
      root_data : date, tank, root_volume, root_length, growth_rate, biomass, branching_density
      env_data  : date, shelf, temperature, humidity
    """
    try:
        xls = pd.ExcelFile(uploaded_file)
        root_df = pd.read_excel(xls, "root_data") if "root_data" in xls.sheet_names else None
        env_df  = pd.read_excel(xls, "env_data")  if "env_data"  in xls.sheet_names else None
        if root_df is not None:
            root_df["date"] = pd.to_datetime(root_df["date"]).dt.strftime("%Y-%m-%d")
            if "shelf" not in root_df.columns:
                root_df["shelf"] = root_df["tank"].apply(
                    lambda t: "Upper" if t in TANKS["upper"] else "Lower"
                )
        if env_df is not None:
            env_df["date"] = pd.to_datetime(env_df["date"]).dt.strftime("%Y-%m-%d")
        return root_df, env_df
    except Exception as e:
        st.sidebar.error(f"Could not parse file: {e}")
        return None, None

# ============================================================================
# CSS
# ============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:        #f8fafc;
    --card:      #ffffff;
    --green:     #22c55e;
    --green-lt:  #dcfce7;
    --green-dk:  #16a34a;
    --txt:       #111827;
    --txt2:      #374151;
    --txt3:      #4b5563;
    --border:    #e5e7eb;
    --shadow:    0 4px 6px -1px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 20px -4px rgba(0,0,0,0.1);
}

.stApp { background: var(--bg); }
#MainMenu, footer, header { visibility: hidden; }
.main .block-container { padding: 1rem 2rem 2rem 2rem; max-width: 1440px; }

/* Sidebar */
section[data-testid="stSidebar"] { background: var(--card); border-right: 1px solid var(--border); }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: #111827 !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* Header */
.header-bar {
    background: var(--card); border: 1px solid var(--border); border-radius: 16px;
    padding: 1rem 1.5rem; margin-bottom: 1.5rem; box-shadow: var(--shadow);
    display: flex; justify-content: space-between; align-items: center;
}
.logo-text { font-family:'Inter',sans-serif; font-size:1.5rem; font-weight:700; color:var(--green); letter-spacing:2px; }
.subtitle  { font-family:'Inter',sans-serif; font-size:0.9rem; font-weight:500; color:var(--txt2);
             margin-left:12px; padding-left:12px; border-left:2px solid var(--border); }
.pill { padding:6px 14px; border-radius:20px; font-size:0.75rem; font-weight:700; font-family:'Inter',sans-serif; }
.pill-g { background:var(--green-lt); color:var(--green-dk); border:1px solid var(--green); }
.pill-b { background:#dbeafe; color:#1d4ed8; border:1px solid #3b82f6; }

/* Section heading */
.sh {
    font-family:'Inter',sans-serif; font-size:1.05rem; font-weight:700; color:var(--txt);
    margin:1.4rem 0 0.7rem 0; padding-bottom:0.4rem;
    border-bottom:2px solid var(--green-lt);
}

/* KPI card */
.kpi {
    background:var(--card); border:1px solid var(--border); border-radius:14px;
    padding:1.1rem 1.25rem; box-shadow:var(--shadow); transition:all .2s ease;
}
.kpi:hover { box-shadow:var(--shadow-lg); transform:translateY(-2px); }
.kpi-ico { font-size:1.4rem; margin-bottom:4px; }
.kpi-lbl { font-family:'Inter',sans-serif; font-size:0.7rem; font-weight:700;
           color:var(--txt3); text-transform:uppercase; letter-spacing:.6px; margin-bottom:3px; }
.kpi-val { font-family:'JetBrains Mono',monospace; font-size:1.6rem; font-weight:700; color:var(--txt); }
.kpi-unt { font-size:0.82rem; font-weight:500; color:var(--txt2); margin-left:3px; }
.kpi-chg { font-size:0.75rem; font-weight:600; margin-top:4px; }
.pos { color:var(--green-dk); }
.neg { color:#dc2626; }
.wrn { color:#d97706; }

/* Card */
.card { background:var(--card); border:1px solid var(--border); border-radius:16px; padding:1.5rem; box-shadow:var(--shadow); }
.card-hdr { display:flex; align-items:center; justify-content:space-between;
            margin-bottom:1rem; padding-bottom:.75rem; border-bottom:1px solid var(--border); }
.card-ttl { font-family:'Inter',sans-serif; font-size:.95rem; font-weight:700; color:var(--txt); }
.card-bdg { font-size:.7rem; font-family:'JetBrains Mono',monospace; color:var(--green-dk);
            background:var(--green-lt); padding:3px 10px; border-radius:12px; font-weight:700; }

/* Shelf divider */
.sdiv {
    background:linear-gradient(90deg,var(--green-lt),#e0f2fe);
    border-left:4px solid var(--green); border-radius:0 10px 10px 0;
    padding:.6rem 1rem; margin:1.2rem 0 .8rem 0;
    font-family:'Inter',sans-serif; font-size:.9rem; font-weight:700; color:var(--txt);
}

/* Status dot */
.dot { width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:6px; animation:pulse 2s infinite; }
.dot-g { background:var(--green); }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

/* Image card */
.img-card { background:var(--card); border:1px solid var(--border); border-radius:12px; overflow:hidden; transition:all .2s; margin-bottom:1rem; }
.img-card:hover { box-shadow:var(--shadow-lg); transform:translateY(-3px); }
.img-ph { height:150px; background:linear-gradient(135deg,#d1fae5,#a7f3d0); display:flex; align-items:center; justify-content:center; font-size:2.5rem; }
.img-info { padding:.85rem 1rem; }
.img-lbl { font-weight:700; color:var(--txt); font-size:.9rem; }
.img-meta { font-size:.75rem; color:var(--txt3); margin-top:3px; }

/* Chat */
.msg-user { background:var(--green); color:white; border-radius:12px 12px 4px 12px; padding:10px 14px; margin:8px 0 8px 25%; font-size:.9rem; }
.msg-bot  { background:#f9fafb; border:1px solid var(--border); border-radius:12px 12px 12px 4px; padding:12px 16px; margin:8px 15% 8px 0; font-size:.9rem; color:var(--txt); line-height:1.6; }

/* Insight */
.insight { background:linear-gradient(135deg,var(--green-lt),#f0fdf4); border:1px solid #86efac; border-radius:14px; padding:1.25rem; margin-top:1.5rem; }
.insight-ttl { font-size:.9rem; font-weight:700; color:var(--green-dk); margin-bottom:.75rem; }
.insight-row { font-size:.85rem; color:var(--txt2); padding:7px 0; border-bottom:1px solid rgba(34,197,94,.2); }
.insight-row:last-child { border-bottom:none; }

/* Buttons */
.stButton > button {
    background:linear-gradient(135deg,var(--green),var(--green-dk)) !important;
    color:white !important; border:none !important; border-radius:10px !important;
    font-weight:600 !important; font-family:'Inter',sans-serif !important;
}
.stButton > button:hover { transform:translateY(-2px); box-shadow:0 4px 12px rgba(34,197,94,.3); }

/* Inputs */
.stTextInput > div > div > input { background:#fff !important; border:1px solid var(--border) !important; border-radius:10px !important; color:var(--txt) !important; }
.stSelectbox > div > div { background:#fff !important; color:var(--txt) !important; border-radius:10px !important; }
.stSelectbox label, .stDateInput label, .stTextInput label { color:var(--txt) !important; font-weight:500 !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================

def init_state():
    # Auto-load Gemini key from Streamlit Secrets if available
    secret_key = ""
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        pass
    for k, v in [("current_page","Overview"),("messages",[]),("api_key", secret_key)]:
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================================
# CHART DEFAULTS
# ============================================================================

CL = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#374151", family="Inter", size=12),
    margin=dict(l=10, r=10, t=30, b=50),
    hovermode="x unified",
)
GR = dict(showgrid=True, gridcolor="#e5e7eb", tickfont=dict(color="#374151", size=11))

# ============================================================================
# AI
# ============================================================================

def call_gemini(msg, root_df, env_df, api_key):
    latest = root_df.groupby("tank").last().reset_index()
    u = env_df[env_df["shelf"]=="Upper"].iloc[-1]
    l = env_df[env_df["shelf"]=="Lower"].iloc[-1]

    tank_summary = "\n".join([
        f"  {row['tank']} ({row['shelf']} shelf): volume={row['root_volume']:.1f}cm³, "
        f"length={row['root_length']:.1f}cm, growth={row['growth_rate']:.2f}cm/d, biomass={row['biomass']:.1f}g"
        for _, row in latest.iterrows()
    ])

    ctx = f"""You are RootSight AI, an expert assistant for the Rezylix hydroponic root monitoring platform.

SYSTEM SETUP:
- 8 tanks across 2 shelves
- Upper shelf: Tanks 1-4 | Lower shelf: Tanks 5-8
- One front camera per tank
- One temperature + humidity sensor per shelf

CURRENT TANK DATA:
{tank_summary}

ENVIRONMENT:
- Upper shelf: {u['temperature']}°C, {u['humidity']}% RH
- Lower shelf: {l['temperature']}°C, {l['humidity']}% RH
- Optimal: 20-26°C temperature, 60-75% humidity

You can answer ANY question — about the data above, general hydroponics, plant science, agriculture, or anything else.
Be helpful, specific, and conversational. Reference the actual data when relevant."""

    errors = []
    for model in ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash-latest"]:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": f"{ctx}\n\nUser question: {msg}"}]}],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
                },
                timeout=30,
            )
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            elif r.status_code == 429:
                return "⏳ Rate limited — please wait 60 seconds and try again."
            else:
                # Capture the actual error for debugging
                try:
                    err_detail = r.json().get("error", {}).get("message", r.text[:200])
                except Exception:
                    err_detail = r.text[:200]
                errors.append(f"{model}: HTTP {r.status_code} — {err_detail}")
        except requests.exceptions.Timeout:
            errors.append(f"{model}: Request timed out")
        except Exception as e:
            errors.append(f"{model}: {str(e)[:100]}")

    # Show debug info so we can diagnose
    error_summary = "\n".join(errors)
    return (f"⚠️ **Gemini API Debug Info**\n\n"
            f"Key starts with: `{api_key[:8]}...`\n"
            f"Key length: {len(api_key)} characters\n\n"
            f"**Errors per model:**\n```\n{error_summary}\n```\n\n"
            f"Share this message so we can diagnose the issue.")


def fallback(msg, root_df, env_df):
    ml = msg.lower()
    avg_v = root_df.groupby("tank")["root_volume"].last().mean()
    avg_r = root_df["growth_rate"].mean()
    latest = root_df.groupby("tank").last().reset_index()

    if any(w in ml for w in ["root","growth","develop","volume","length","biomass"]):
        s = "excellent 🟢" if avg_r > 2.5 else "on track 🟡" if avg_r > 1.5 else "below target 🔴"
        best = latest.loc[latest["root_volume"].idxmax(), "tank"]
        worst = latest.loc[latest["root_volume"].idxmin(), "tank"]
        return (f"🌱 **Root Development Status**\n\n"
                f"• Avg volume across 8 tanks: **{avg_v:.1f} cm³**\n"
                f"• Avg growth rate: **{avg_r:.2f} cm/day** — {s}\n"
                f"• Best performing tank: **{best}** ({latest['root_volume'].max():.1f} cm³)\n"
                f"• Needs attention: **{worst}** ({latest['root_volume'].min():.1f} cm³)\n\n"
                f"Target root volume is ≥300 cm³. You're at {(avg_v/300*100):.0f}% of target.")

    if any(w in ml for w in ["env","temp","humid","shelf","condition","climate","upper","lower"]):
        u = env_df[env_df["shelf"]=="Upper"].iloc[-1]
        l = env_df[env_df["shelf"]=="Lower"].iloc[-1]
        u_tok = "✅" if 20<=u["temperature"]<=26 else "⚠️"
        l_tok = "✅" if 20<=l["temperature"]<=26 else "⚠️"
        u_hok = "✅" if 60<=u["humidity"]<=75 else "⚠️"
        l_hok = "✅" if 60<=l["humidity"]<=75 else "⚠️"
        return (f"🌡️ **Shelf Environment**\n\n"
                f"**🔼 Upper Shelf (Tanks 1–4)**\n"
                f"• Temperature: {u['temperature']}°C {u_tok}\n"
                f"• Humidity: {u['humidity']}% {u_hok}\n\n"
                f"**🔽 Lower Shelf (Tanks 5–8)**\n"
                f"• Temperature: {l['temperature']}°C {l_tok}\n"
                f"• Humidity: {l['humidity']}% {l_hok}\n\n"
                f"Optimal ranges: 20–26°C · 60–75% RH")

    if any(w in ml for w in ["harvest","when","ready","days","time"]):
        days = max(3, round((300 - avg_v) / max(avg_r * 7, 1)))
        pct = min(100, (avg_v/300*100))
        return (f"📅 **Harvest Prediction**\n\n"
                f"• Current avg volume: **{avg_v:.1f} cm³** ({pct:.0f}% of target)\n"
                f"• Growth rate: **{avg_r:.2f} cm/day**\n"
                f"• Estimated days to harvest: **{days} days**\n\n"
                f"{'✅ Getting close!' if days < 7 else '⏳ Keep monitoring daily.'}")

    if any(w in ml for w in ["issue","problem","wrong","bad","concern","alert","warn","check"]):
        low_tanks = latest[latest["root_volume"] < avg_v * 0.85]["tank"].tolist()
        issues = f"⚠️ Tanks underperforming: {', '.join(low_tanks)}" if low_tanks else "✅ All tanks performing within normal range"
        u = env_df[env_df["shelf"]=="Upper"].iloc[-1]
        l = env_df[env_df["shelf"]=="Lower"].iloc[-1]
        temp_warn = "⚠️ Upper shelf temperature is high" if u["temperature"] > 26 else ""
        return (f"🔍 **System Diagnostic**\n\n"
                f"**Root health:** {issues}\n"
                f"**Environment:** {'✅ Both shelves in range' if not temp_warn else temp_warn}\n"
                f"**Growth rate:** {'✅ On target' if avg_r > 1.5 else '⚠️ Below target — check nutrients and lighting'}\n\n"
                f"Avg growth: {avg_r:.2f} cm/day · Avg volume: {avg_v:.1f} cm³")

    if any(w in ml for w in ["hello","hi","hey","how are","good","morning","evening"]):
        return ("👋 Hello! I'm the RootSight AI assistant.\n\n"
                f"Quick system summary:\n"
                f"• 8 tanks running · avg volume {avg_v:.1f} cm³\n"
                f"• Growth rate: {avg_r:.2f} cm/day\n\n"
                "Ask me about root development, shelf conditions, harvest timing, or any issues!")

    if any(w in ml for w in ["tank 1","tank 2","tank 3","tank 4","tank 5","tank 6","tank 7","tank 8"]):
        for tank in ALL_TANKS:
            if tank.lower() in ml:
                row = latest[latest["tank"]==tank].iloc[0]
                return (f"🪴 **{tank} Status**\n\n"
                        f"• Root volume: **{row['root_volume']:.1f} cm³**\n"
                        f"• Root length: **{row['root_length']:.1f} cm**\n"
                        f"• Growth rate: **{row['growth_rate']:.2f} cm/day**\n"
                        f"• Biomass: **{row['biomass']:.1f} g**\n"
                        f"• Shelf: {row['shelf']}")

    # Generic helpful response
    return (f"🌿 **RootSight Assistant**\n\n"
            f"I can answer questions like:\n"
            f"• *How are my roots developing?*\n"
            f"• *What are the shelf conditions?*\n"
            f"• *When is harvest ready?*\n"
            f"• *Any issues with the tanks?*\n"
            f"• *How is Tank 3 doing?*\n\n"
            f"**Current snapshot:** {avg_v:.1f} cm³ avg · {avg_r:.2f} cm/day growth · 8 tanks active")

# ============================================================================
# SIDEBAR
# ============================================================================

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:1rem 0;border-bottom:1px solid #e5e7eb;margin-bottom:1rem;">
            <div style="font-family:'Inter',sans-serif;font-size:1.35rem;font-weight:700;color:#22c55e;">🌱 REZYLIX</div>
            <div style="font-size:.85rem;color:#374151;font-weight:600;margin-top:2px;">RootSight Project</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Navigation")
        pages = {"Overview":"📊","Root Metrics":"🌱","Environment":"🌡️","Images":"📷","AI Copilot":"🤖"}
        for page, icon in pages.items():
            t = "primary" if st.session_state.current_page == page else "secondary"
            if st.button(f"{icon}  {page}", key=f"nav_{page}", use_container_width=True, type=t):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("---")
        st.markdown("### 📂 Data Import")
        uploaded = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"],
            help="Sheets: 'root_data' and 'env_data'. See column guide in README.")
        if uploaded:
            st.success("✓ File loaded")
        else:
            st.info("Demo data active — upload your Excel file when ready.")

        st.markdown("---")
        st.markdown("### 🔑 AI Settings")
        api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...",
                                value=st.session_state.api_key, help="aistudio.google.com/apikey")
        st.session_state.api_key = api_key
        if api_key:
            st.success("✓ AI Ready")
        else:
            st.info("💡 Add key for full AI analysis")

        st.markdown("---")
        st.markdown("### 📅 Date Range")
        st.date_input("Select period",
                      value=(datetime.now() - timedelta(days=13), datetime.now()),
                      key="date_range")
        return api_key, uploaded

# ============================================================================
# HEADER
# ============================================================================

def render_header():
    st.markdown("""
    <div class="header-bar">
        <div style="display:flex;align-items:center;gap:12px;">
            <span class="logo-text">🌱 REZYLIX</span>
            <span class="subtitle">RootSight Project • Root Intelligence</span>
        </div>
        <div style="display:flex;gap:10px;">
            <div class="pill pill-g"><span class="dot dot-g"></span>System Online</div>
            <div class="pill pill-b">8 Tanks · 2 Shelves</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# OVERVIEW
# ============================================================================

def render_overview(root_df, env_df):
    latest = root_df.groupby("tank").last().reset_index()
    prev   = root_df.groupby("tank").nth(-2).reset_index()
    lenv   = env_df.groupby("shelf").last().reset_index()

    avg_v  = latest["root_volume"].mean()
    prev_v = prev["root_volume"].mean() if len(prev) else avg_v
    avg_r  = latest["growth_rate"].mean()
    avg_l  = latest["root_length"].mean()
    delta  = ((avg_v - prev_v) / prev_v * 100) if prev_v > 0 else 0

    def sv(df, sh, col):
        row = df.loc[df["shelf"]==sh, col]
        return row.values[0] if len(row) else 0

    ut = sv(lenv,"Upper","temperature"); lt = sv(lenv,"Lower","temperature")
    uh = sv(lenv,"Upper","humidity");    lh = sv(lenv,"Lower","humidity")

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:1rem;margin-bottom:1.5rem;">
        <div class="kpi"><div class="kpi-ico">🌱</div><div class="kpi-lbl">Avg Root Volume</div>
            <div class="kpi-val">{avg_v:.1f}<span class="kpi-unt">cm³</span></div>
            <div class="kpi-chg {'pos' if delta>=0 else 'neg'}">{'↑' if delta>=0 else '↓'} {abs(delta):.1f}% vs yesterday</div></div>
        <div class="kpi"><div class="kpi-ico">📏</div><div class="kpi-lbl">Avg Root Length</div>
            <div class="kpi-val">{avg_l:.1f}<span class="kpi-unt">cm</span></div>
            <div class="kpi-chg pos">8 tanks combined</div></div>
        <div class="kpi"><div class="kpi-ico">📈</div><div class="kpi-lbl">Avg Growth Rate</div>
            <div class="kpi-val">{avg_r:.2f}<span class="kpi-unt">cm/d</span></div>
            <div class="kpi-chg {'pos' if avg_r>2 else 'wrn'}">{'✓ Above target' if avg_r>2 else 'Near target'}</div></div>
        <div class="kpi"><div class="kpi-ico">🔼</div><div class="kpi-lbl">Upper Shelf Temp</div>
            <div class="kpi-val">{ut:.1f}<span class="kpi-unt">°C</span></div>
            <div class="kpi-chg {'pos' if 20<=ut<=26 else 'neg'}">{'✓ Optimal' if 20<=ut<=26 else '⚠ Adjust'}</div></div>
        <div class="kpi"><div class="kpi-ico">🔽</div><div class="kpi-lbl">Lower Shelf Temp</div>
            <div class="kpi-val">{lt:.1f}<span class="kpi-unt">°C</span></div>
            <div class="kpi-chg {'pos' if 20<=lt<=26 else 'neg'}">{'✓ Optimal' if 20<=lt<=26 else '⚠ Adjust'}</div></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="card"><div class="card-hdr"><span class="card-ttl">📈 Avg Root Volume — All Tanks</span><span class="card-bdg">14 days</span></div>', unsafe_allow_html=True)
        dv = root_df.groupby("date")["root_volume"].mean().reset_index()
        fig = go.Figure(go.Scatter(x=dv["date"], y=dv["root_volume"],
            fill="tozeroy", fillcolor="rgba(34,197,94,.12)",
            line=dict(color="#22c55e",width=3), marker=dict(size=7,color="#22c55e")))
        fig.update_layout(**CL, height=290, yaxis_title="Volume (cm³)")
        fig.update_xaxes(**GR); fig.update_yaxes(**GR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card"><div class="card-hdr"><span class="card-ttl">🌡️ Temperature by Shelf</span><span class="card-bdg">Live</span></div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        for sh, c in [("Upper","#f59e0b"),("Lower","#3b82f6")]:
            s = env_df[env_df["shelf"]==sh].sort_values("date")
            fig2.add_trace(go.Scatter(x=s["date"],y=s["temperature"],name=f"{sh} Shelf",
                line=dict(color=c,width=2.5),mode="lines+markers"))
        fig2.update_layout(**CL, height=290, yaxis_title="°C",
            legend=dict(orientation="h",yanchor="bottom",y=1.02,font=dict(color="#374151")))
        fig2.update_xaxes(**GR); fig2.update_yaxes(**GR)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sh">🪴 Current Root Volume per Tank</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    colors = ["#22c55e" if t in TANKS["upper"] else "#3b82f6" for t in latest["tank"]]
    fig3 = go.Figure(go.Bar(x=latest["tank"], y=latest["root_volume"], marker_color=colors,
        text=latest["root_volume"].round(1), textposition="outside",
        textfont=dict(color="#374151",size=12)))
    fig3.update_layout(**CL, height=270, yaxis_title="Root Volume (cm³)", showlegend=False)
    fig3.update_xaxes(**GR); fig3.update_yaxes(**GR)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
    st.markdown("<div style='font-size:.8rem;color:#4b5563;padding:0 4px 6px;'>🟢 Upper shelf &nbsp; 🔵 Lower shelf</div></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="insight">
        <div class="insight-ttl">💡 System Insights</div>
        <div class="insight-row">✅ All 8 tanks reporting. Average growth rate is on track.</div>
        <div class="insight-row">🌡️ Upper shelf runs ~1.5°C warmer than lower — monitor if it approaches 26°C.</div>
        <div class="insight-row">💧 Humidity in both shelves within optimal range (60–75%).</div>
        <div class="insight-row">📂 Upload your Excel data file via the sidebar to see real readings.</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# ROOT METRICS
# ============================================================================

def render_root_metrics(root_df):
    st.markdown('<div class="sh">🌱 Root Development — All Tanks</div>', unsafe_allow_html=True)
    latest = root_df.groupby("tank").last().reset_index()
    avg_v = latest["root_volume"].mean()
    avg_l = latest["root_length"].mean()
    avg_r = root_df["growth_rate"].mean()

    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="kpi"><div class="kpi-ico">📊</div><div class="kpi-lbl">Avg Root Volume</div><div class="kpi-val">{avg_v:.1f}<span class="kpi-unt">cm³</span></div><div class="kpi-chg pos">Target: 200–300 cm³</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi"><div class="kpi-ico">📏</div><div class="kpi-lbl">Avg Root Length</div><div class="kpi-val">{avg_l:.1f}<span class="kpi-unt">cm</span></div><div class="kpi-chg pos">Across 8 tanks</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi"><div class="kpi-ico">⚡</div><div class="kpi-lbl">Avg Growth Rate</div><div class="kpi-val">{avg_r:.2f}<span class="kpi-unt">cm/d</span></div><div class="kpi-chg {"pos" if avg_r>1.5 else "neg"}">{"✓ Healthy" if avg_r>1.5 else "⚠ Low"}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown('<div class="card"><div class="card-hdr"><span class="card-ttl">📈 Volume Timeline by Shelf</span></div>', unsafe_allow_html=True)
        sd = root_df.groupby(["date","shelf"])["root_volume"].mean().reset_index()
        fig = go.Figure()
        for sh,c,da in [("Upper","#22c55e","solid"),("Lower","#3b82f6","dot")]:
            d = sd[sd["shelf"]==sh]
            fig.add_trace(go.Scatter(x=d["date"],y=d["root_volume"],name=f"{sh} Shelf",
                line=dict(color=c,width=2.5,dash=da),mode="lines+markers"))
        fig.update_layout(**CL,height=330,yaxis_title="Avg Volume (cm³)",
            legend=dict(orientation="h",yanchor="bottom",y=1.02,font=dict(color="#374151")))
        fig.update_xaxes(**GR); fig.update_yaxes(**GR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card"><div class="card-hdr"><span class="card-ttl">📊 Growth Rate per Tank</span></div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Bar(
            x=latest["tank"], y=latest["growth_rate"],
            marker_color=latest["growth_rate"].apply(lambda v: "#22c55e" if v>2.5 else "#fbbf24" if v>1.5 else "#ef4444"),
            text=latest["growth_rate"].round(2), textposition="outside",
            textfont=dict(color="#374151",size=11),
        ))
        fig2.update_layout(**CL,height=330,yaxis_title="cm/day",showlegend=False)
        fig2.update_xaxes(**GR); fig2.update_yaxes(**GR)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sh">🪴 Per-Tank Summary Table</div>', unsafe_allow_html=True)
    disp = latest[["tank","shelf","root_volume","root_length","growth_rate","biomass","branching_density"]].copy()
    disp.columns = ["Tank","Shelf","Volume (cm³)","Length (cm)","Growth (cm/d)","Biomass (g)","Branching"]
    st.dataframe(disp.set_index("Tank"), use_container_width=True)

# ============================================================================
# ENVIRONMENT
# ============================================================================

def render_environment(env_df):
    st.markdown('<div class="sh">🌡️ Environmental Monitoring — One Sensor per Shelf</div>', unsafe_allow_html=True)

    for shelf in ["Upper","Lower"]:
        tank_names = ", ".join(TANKS["upper"] if shelf=="Upper" else TANKS["lower"])
        sdf = env_df[env_df["shelf"]==shelf].sort_values("date")
        lat = sdf.iloc[-1] if len(sdf) else None

        st.markdown(f"""<div class="sdiv">{'🔼' if shelf=='Upper' else '🔽'} {shelf} Shelf — {tank_names}</div>""", unsafe_allow_html=True)

        k1,k2,k3,k4 = st.columns(4)
        if lat is not None:
            t_ok = 20<=lat["temperature"]<=26
            h_ok = 60<=lat["humidity"]<=75
            with k1:
                st.markdown(f'<div class="kpi"><div class="kpi-ico">🌡️</div><div class="kpi-lbl">Temperature</div><div class="kpi-val">{lat["temperature"]:.1f}<span class="kpi-unt">°C</span></div><div class="kpi-chg {"pos" if t_ok else "neg"}">{"✓ Optimal (20–26°C)" if t_ok else "⚠ Outside range"}</div></div>', unsafe_allow_html=True)
            with k2:
                st.markdown(f'<div class="kpi"><div class="kpi-ico">💧</div><div class="kpi-lbl">Humidity</div><div class="kpi-val">{lat["humidity"]:.1f}<span class="kpi-unt">%</span></div><div class="kpi-chg {"pos" if h_ok else "neg"}">{"✓ Optimal (60–75%)" if h_ok else "⚠ Outside range"}</div></div>', unsafe_allow_html=True)
            with k3:
                st.markdown(f'<div class="kpi"><div class="kpi-ico">📉</div><div class="kpi-lbl">Temp Range (14d)</div><div class="kpi-val" style="font-size:1.2rem;">{sdf["temperature"].min():.1f}–{sdf["temperature"].max():.1f}<span class="kpi-unt">°C</span></div><div class="kpi-chg pos">14-day span</div></div>', unsafe_allow_html=True)
            with k4:
                st.markdown(f'<div class="kpi"><div class="kpi-ico">📉</div><div class="kpi-lbl">Humidity Range (14d)</div><div class="kpi-val" style="font-size:1.2rem;">{sdf["humidity"].min():.1f}–{sdf["humidity"].max():.1f}<span class="kpi-unt">%</span></div><div class="kpi-chg pos">14-day span</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns([3,1])
        with col1:
            st.markdown(f'<div class="card"><div class="card-hdr"><span class="card-ttl">📊 {shelf} Shelf — Temp & Humidity Trend</span></div>', unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=sdf["date"],y=sdf["temperature"],name="Temperature (°C)",
                line=dict(color="#f59e0b",width=2.5),mode="lines+markers"))
            fig.add_trace(go.Scatter(x=sdf["date"],y=sdf["humidity"],name="Humidity (%)",
                line=dict(color="#3b82f6",width=2.5),mode="lines+markers",yaxis="y2"))
            fig.add_hrect(y0=20,y1=26,fillcolor="rgba(34,197,94,.06)",line_width=0,
                annotation_text="Temp target",annotation_font_color="#16a34a",annotation_font_size=11)
            fig.update_layout(**CL, height=290,
                yaxis=dict(title="Temperature (°C)",**GR),
                yaxis2=dict(title="Humidity (%)",overlaying="y",side="right",**GR),
                legend=dict(orientation="h",yanchor="bottom",y=1.02,font=dict(color="#374151")))
            fig.update_xaxes(**GR)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="card" style="padding:1.2rem;">
                <div class="card-ttl" style="margin-bottom:.8rem;">🎯 Optimal Ranges</div>
                <div style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
                    <div style="font-size:.78rem;color:#4b5563;font-weight:700;">Temperature</div>
                    <div style="font-size:.95rem;font-weight:700;color:#16a34a;">20 – 26 °C</div>
                </div>
                <div style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
                    <div style="font-size:.78rem;color:#4b5563;font-weight:700;">Humidity</div>
                    <div style="font-size:.95rem;font-weight:700;color:#16a34a;">60 – 75 %</div>
                </div>
                <div style="padding:8px 0;">
                    <div style="font-size:.78rem;color:#4b5563;font-weight:700;">Sensor config</div>
                    <div style="font-size:.88rem;font-weight:600;color:#374151;">1 × Temp + Humidity per shelf</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# IMAGES — 8 tanks, 1 front camera each
# ============================================================================

def render_images():
    st.markdown('<div class="sh">📷 Tank Camera Gallery — Front View per Tank</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#374151;font-size:.9rem;margin-bottom:1rem;">Each tank has one front-facing camera. Upload images directly from the cards below (JPG, PNG, WEBP).</p>', unsafe_allow_html=True)

    for shelf_label, tank_list in [("🔼 Upper Shelf", TANKS["upper"]), ("🔽 Lower Shelf", TANKS["lower"])]:
        st.markdown(f'<div class="sdiv">{shelf_label}</div>', unsafe_allow_html=True)
        cols = st.columns(4)
        for i, tank in enumerate(tank_list):
            with cols[i]:
                img_file = st.file_uploader(
                    f"📷 {tank}",
                    type=["jpg","jpeg","png","webp"],
                    key=f"img_{tank}",
                )
                if img_file:
                    st.image(img_file, caption=f"{tank} · {datetime.now().strftime('%Y-%m-%d %H:%M')}", use_container_width=True)
                    st.markdown(f"""
                    <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:8px;margin-top:4px;">
                        <div style="font-size:.75rem;font-weight:700;color:#16a34a;">✓ Image loaded</div>
                        <div style="font-size:.72rem;color:#374151;">{img_file.name}</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="img-card">
                        <div class="img-ph">🪴</div>
                        <div class="img-info">
                            <div class="img-lbl">{tank}</div>
                            <div class="img-meta">No image uploaded yet</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

# ============================================================================
# AI COPILOT
# ============================================================================

def render_ai_copilot(root_df, env_df, api_key):
    st.markdown('<div class="sh">🤖 AI Copilot — RootSight Assistant</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown('<div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:1.5rem;min-height:380px;">', unsafe_allow_html=True)

        if not st.session_state.messages:
            st.markdown("""
            <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:12px;padding:16px;color:#111827;">
                <b>👋 Welcome to RootSight Intelligence!</b><br><br>
                I can help you with:<br>
                • 📊 Root development across all 8 tanks<br>
                • 🌡️ Shelf environment analysis (upper &amp; lower)<br>
                • 📅 Harvest predictions<br>
                • 🔍 Issue detection<br><br>
                <i style="color:#4b5563;">Ask me anything about your grow system!</i>
            </div>""", unsafe_allow_html=True)

        for msg in st.session_state.messages[-8:]:
            css = "msg-user" if msg["role"]=="user" else "msg-bot"
            st.markdown(f'<div class="{css}">{msg["content"]}</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        ic, bc = st.columns([5,1])
        with ic:
            user_input = st.text_input("Message", placeholder="Ask about tanks, environment, harvest...", label_visibility="collapsed")
        with bc:
            send = st.button("Send", use_container_width=True)

        st.markdown("**Suggested questions:**")
        qc = st.columns(4)
        prompts = ["🌱 Root status?","🌡️ Shelf conditions?","📅 Harvest ETA?","🔍 Any issues?"]
        for i, p in enumerate(prompts):
            with qc[i]:
                if st.button(p, key=f"qp_{i}", use_container_width=True):
                    user_input = p; send = True

        if send and user_input:
            st.session_state.messages.append({"role":"user","content":user_input})
            if api_key and api_key.startswith("AIza"):
                with st.spinner("🤖 Analysing..."):
                    resp = call_gemini(user_input, root_df, env_df, api_key)
            else:
                resp = fallback(user_input, root_df, env_df)
            st.session_state.messages.append({"role":"assistant","content":resp})
            st.rerun()

    with col2:
        lr = root_df.groupby("tank").last().reset_index()
        le = env_df.groupby("shelf").last().reset_index()
        ut = le.loc[le["shelf"]=="Upper","temperature"].values[0] if "Upper" in le["shelf"].values else 0
        lt = le.loc[le["shelf"]=="Lower","temperature"].values[0] if "Lower" in le["shelf"].values else 0

        for label, val, unit in [
            ("Avg Root Volume", f"{lr['root_volume'].mean():.1f}", "cm³"),
            ("Avg Growth Rate", f"{lr['growth_rate'].mean():.2f}", "cm/d"),
            ("Upper Shelf Temp", f"{ut:.1f}", "°C"),
            ("Lower Shelf Temp", f"{lt:.1f}", "°C"),
        ]:
            st.markdown(f"""
            <div style="background:#f9fafb;border-radius:10px;padding:12px;margin-bottom:8px;">
                <div style="font-size:.7rem;color:#4b5563;font-weight:700;text-transform:uppercase;">{label}</div>
                <div style="font-size:1.35rem;font-weight:700;color:#111827;font-family:'JetBrains Mono',monospace;">{val} <span style="font-size:.82rem;color:#374151;">{unit}</span></div>
            </div>""", unsafe_allow_html=True)

        if api_key:
            st.success("✓ Gemini AI connected")
        else:
            st.warning("Add API key for full AI")
            st.markdown("[Get free key →](https://aistudio.google.com/apikey)")

# ============================================================================
# MAIN
# ============================================================================

def main():
    api_key, uploaded_file = render_sidebar()

    if uploaded_file:
        root_df, env_df = load_excel_data(uploaded_file)
        if root_df is None: root_df = generate_root_data()
        if env_df  is None: env_df  = generate_env_data()
    else:
        root_df = generate_root_data()
        env_df  = generate_env_data()

    render_header()
    page = st.session_state.current_page

    if   page == "Overview":     render_overview(root_df, env_df)
    elif page == "Root Metrics": render_root_metrics(root_df)
    elif page == "Environment":  render_environment(env_df)
    elif page == "Images":       render_images()
    elif page == "AI Copilot":   render_ai_copilot(root_df, env_df, api_key)

    st.markdown(f"""
    <div style="text-align:center;padding:2rem 0;color:#6b7280;font-size:.75rem;">
        <span class="dot dot-g"></span>
        RootSight · Rezylix Platform · {datetime.now().strftime('%Y-%m-%d %H:%M')} · 8 tanks · 2 shelves
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
