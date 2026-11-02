import os
import html
import inspect
import urllib.request
from datetime import datetime
from urllib.parse import quote

import streamlit as st
import pandas as pd
import plotly.express as px
from database import init_db, create_inquiry, list_inquiries, get_inquiry, update_inquiry, seed_demo_data, metrics
from ai_engine import process_inquiry, generate_reply, AI_MODE
from utils import export_csv, validate_inquiry

st.set_page_config(page_title="CareFlow AI", page_icon="💙", layout="wide", initial_sidebar_state="expanded")
init_db()

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
PAGES = ["Dashboard", "Submit Inquiry", "Manage Inquiries", "AI Response Studio", "Analytics & Reports", "Settings"]
CATEGORIES = ["Appointments", "Clinic Hours", "Billing", "General Inquiry", "Clinical Question"]
STATUSES = ["Open", "In Progress", "Resolved"]
PRIORITIES = ["Low", "Medium", "High"]

BLUE = "#2457e6"
PRIORITY_COLORS = {"High": "#e5484d", "Medium": "#f5a524", "Low": "#2fa66a"}

PRIORITY_CLS = {"High": "p-high", "Medium": "p-med", "Low": "p-low"}
STATUS_CLS = {"Open": "s-open", "In Progress": "s-prog", "Resolved": "s-done"}

# Line icons (24x24, stroke based) used for sidebar navigation, in the same order as PAGES
NAV_ICON_BODIES = [
    "<rect x='3' y='3' width='7' height='7' rx='1.5'/><rect x='14' y='3' width='7' height='7' rx='1.5'/><rect x='14' y='14' width='7' height='7' rx='1.5'/><rect x='3' y='14' width='7' height='7' rx='1.5'/>",
    "<circle cx='12' cy='12' r='9'/><path d='M12 8v8M8 12h8'/>",
    "<path d='M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01'/>",
    "<path d='M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z'/><path d='M19 16v4M17 18h4'/>",
    "<path d='M5 20V11M12 20V4M19 20v-6'/>",
    "<path d='M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6'/>",
]


def _icon_uri(body):
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' "
           "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>" + body + "</svg>")
    return "data:image/svg+xml;utf8," + quote(svg)


NAV_CSS = "".join(
    f'section[data-testid="stSidebar"] div[role="radiogroup"] label:nth-of-type({i}):before'
    f'{{background-image:url("{_icon_uri(b)}");}}'
    for i, b in enumerate(NAV_ICON_BODIES, 1)
)

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

:root{
  --navy:#0b1a3c; --navy-2:#13285c; --blue:#2457e6; --blue-d:#1c46c2;
  --ink:#14234b; --text:#41536f; --muted:#6b7a94; --line:#e3e9f5; --bg:#f6f8fc;
}

/* ---------- Base ---------- */
.stApp{background:var(--bg);color:var(--text);font-family:'DM Sans',system-ui,-apple-system,'Segoe UI',sans-serif;}
.stApp p,.stApp label,.stApp li,.stApp input,.stApp textarea,.stApp button,.stApp td,.stApp th,
.stApp div[data-testid="stMarkdownContainer"],.stApp [data-baseweb="select"]{font-family:'DM Sans',system-ui,-apple-system,'Segoe UI',sans-serif;}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu,footer{visibility:hidden;}
.block-container{padding:1rem 2rem 2rem;max-width:1400px;}
div[data-testid="stHorizontalBlock"]{align-items:stretch;}
h1,h2,h3,h4{font-family:'Manrope','DM Sans',sans-serif !important;color:var(--ink) !important;letter-spacing:-.01em;}
h3{font-size:1.02rem !important;font-weight:700 !important;}
p,label,[data-testid="stCaptionContainer"]{color:var(--text);}
[data-testid="stCaptionContainer"]{color:var(--muted);}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"]{background:var(--navy);border-right:none;}
section[data-testid="stSidebar"] > div{background:var(--navy);}
section[data-testid="stSidebar"] .block-container{padding:1.5rem 1rem;}
/* Keep Streamlit's own sidebar toggle controls visible and readable (never hidden) */
[data-testid="stSidebarCollapseButton"],[data-testid="stSidebarCollapseButton"] button{visibility:visible !important;opacity:1 !important;color:#cdd8f2 !important;}
[data-testid="stSidebarCollapseButton"] svg{color:#cdd8f2 !important;fill:#cdd8f2 !important;}
[data-testid="stExpandSidebarButton"],[data-testid="stSidebarCollapsedControl"] button,[data-testid="collapsedControl"] button{
  visibility:visible !important;opacity:1 !important;background:var(--navy) !important;color:#fff !important;border-radius:10px !important;}
[data-testid="stExpandSidebarButton"] svg,[data-testid="stSidebarCollapsedControl"] svg,[data-testid="collapsedControl"] svg{color:#fff !important;fill:#fff !important;}

.brand{display:flex;align-items:center;gap:.7rem;margin:.2rem .3rem 1.4rem;}
.brand-logo{width:38px;height:38px;border-radius:11px;background:var(--blue);display:flex;align-items:center;justify-content:center;flex:none;}
.brand-name{font-family:'Manrope',sans-serif;font-weight:800;font-size:1.2rem;color:#fff;letter-spacing:-.02em;line-height:1.1;}
.brand-sub{font-size:.72rem;color:#9fb0d6;margin-top:2px;}
.side-label{font-size:.68rem;font-weight:700;letter-spacing:.12em;color:#7f92bd;margin:0 .4rem .5rem;}

section[data-testid="stSidebar"] div[role="radiogroup"]{display:flex;flex-direction:column;gap:.2rem;}
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  width:100%;margin:0;padding:.62rem .85rem;border-radius:10px;cursor:pointer;
  display:flex;align-items:center;gap:.75rem;transition:background .15s ease;}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child{display:none;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:before{
  content:"";width:18px;height:18px;flex:none;background-size:contain;background-repeat:no-repeat;background-position:center;opacity:.65;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:rgba(255,255,255,.07);}
section[data-testid="stSidebar"] div[role="radiogroup"] label:focus-within{outline:2px solid rgba(255,255,255,.35);outline-offset:1px;}
section[data-testid="stSidebar"] div[role="radiogroup"] label p{margin:0;font-size:.92rem;font-weight:500;color:#cdd8f2 !important;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){background:var(--blue);box-shadow:0 4px 12px rgba(36,87,230,.35);}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked):before{opacity:1;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p{color:#fff !important;font-weight:600;}

.side-card{margin:1.6rem .1rem 0;padding:.9rem 1rem;border-radius:12px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);}
.side-card-h{display:flex;align-items:center;gap:.5rem;font-size:.78rem;font-weight:700;color:#fff;}
.side-card-mode{margin-top:.4rem;font-size:.82rem;color:#cdd8f2;word-break:break-word;}
.side-card-t{margin-top:.35rem;font-size:.72rem;color:#8fa2cc;line-height:1.45;}
.side-foot{margin:1rem .4rem 0;font-size:.7rem;color:#7f92bd;line-height:1.5;}
.dot{width:8px;height:8px;border-radius:50%;background:#35c98a;display:inline-block;flex:none;}
.dot-warn{background:#f5a524;}
.dot-off{background:#9aa7c2;}

/* ---------- Page header ---------- */
.crumb{font-size:.78rem;color:var(--muted);font-weight:500;margin-bottom:.35rem;}
.crumb span{margin:0 .3rem;color:#a9b5cb;}
.ph{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;margin-bottom:1rem;}
.ph h1{font-size:1.65rem !important;font-weight:800 !important;margin:0 0 .25rem !important;padding:0 !important;line-height:1.2;}
.ph p{margin:0;color:var(--muted);font-size:.92rem;max-width:720px;}
.ph-date{flex:none;font-size:.8rem;font-weight:600;color:var(--text);background:#fff;border:1px solid var(--line);border-radius:999px;padding:.4rem .85rem;}

.sec{display:flex;align-items:baseline;justify-content:space-between;margin:.2rem 0 .7rem;}
.sec h3{margin:0 !important;padding:0 !important;}
.sec span{font-size:.78rem;color:var(--muted);}

/* ---------- Cards ---------- */
.kpi{background:#fff;border:1px solid var(--line);border-radius:14px;padding:.85rem 1.1rem;box-shadow:0 1px 2px rgba(15,30,69,.04);height:100%;}
.kpi-top{display:flex;align-items:center;gap:.5rem;font-size:.8rem;font-weight:600;color:var(--muted);}
.kpi-dot{width:8px;height:8px;border-radius:50%;display:inline-block;}
.kpi-value{font-family:'Manrope',sans-serif;font-size:1.9rem;font-weight:800;color:var(--ink);margin:.3rem 0 .1rem;line-height:1.1;}
.kpi-note{font-size:.75rem;color:var(--muted);}

.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:1.1rem 1.25rem;box-shadow:0 1px 2px rgba(15,30,69,.04);margin-bottom:1rem;}
.card h4{margin:0 0 .6rem !important;font-size:.95rem !important;}
.card p{margin:.25rem 0;font-size:.88rem;}
div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:14px;}

.ai-card{background:#eef3ff;border:1px solid #d9e4fc;border-radius:14px;padding:1rem 1.15rem;margin-bottom:1rem;}
.ai-top{display:flex;align-items:center;gap:.5rem;font-size:.85rem;color:var(--ink);}
.ai-mode{font-family:'Manrope',sans-serif;font-weight:700;font-size:1.02rem;color:var(--ink);margin:.45rem 0 .25rem;word-break:break-word;}
.ai-card p{margin:0;font-size:.82rem;color:var(--text);line-height:1.5;}
.ai-card{height:100%;margin-bottom:0;}
.ai-status{font-size:.82rem;color:var(--text);margin:.1rem 0 .6rem;}
.ai-warn{margin-top:.7rem;padding:.6rem .8rem;border-radius:10px;background:#fff6e5;border:1px solid #f6dfae;color:#7a4b04;font-size:.8rem;line-height:1.45;}
.ai-warn b{color:#7a4b04;}

.msgbox{background:#f7f9fd;border:1px solid var(--line);border-left:3px solid var(--blue);border-radius:10px;padding:.85rem 1rem;font-size:.92rem;line-height:1.6;color:var(--ink);white-space:pre-wrap;word-break:break-word;}
.meta-row{display:flex;flex-wrap:wrap;gap:.45rem;align-items:center;margin:.2rem 0 .8rem;}
.chip{display:inline-flex;align-items:center;padding:.2rem .65rem;border-radius:999px;font-size:.74rem;font-weight:600;background:#eef2fa;color:#32456b;border:1px solid #e0e8f6;}
.lead-name{font-family:'Manrope',sans-serif;font-weight:700;font-size:1.02rem;color:var(--ink);}
.kv{font-size:.82rem;color:var(--muted);margin-top:.7rem;}
.kv b{color:var(--ink);}

.steps{margin:0;padding-left:1.1rem;font-size:.88rem;line-height:1.7;color:var(--text);}
.steps li{margin-bottom:.25rem;}

.empty{background:#fff;border:1px dashed #cbd7ea;border-radius:14px;padding:2rem 1.5rem;text-align:center;margin-bottom:1rem;}
.empty-ic{width:46px;height:46px;border-radius:12px;background:#eef3ff;color:var(--blue);display:inline-flex;align-items:center;justify-content:center;margin-bottom:.6rem;}
.empty h4{margin:0 0 .3rem !important;font-size:1rem !important;}
.empty p{margin:0;color:var(--muted);font-size:.88rem;}

/* ---------- Tables & badges ---------- */
.tbl-wrap{background:#fff;border:1px solid var(--line);border-radius:14px;overflow-x:auto;box-shadow:0 1px 2px rgba(15,30,69,.04);}
table.tbl{width:100%;border-collapse:collapse;font-size:.84rem;}
.tbl th{text-align:left;font-size:.68rem;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:700;padding:.75rem .9rem;background:#f9fbfe;border-bottom:1px solid var(--line);white-space:nowrap;}
table.tbl{min-width:860px;}
.tbl td{padding:.7rem .9rem;border-bottom:1px solid #eef2f9;color:var(--text);vertical-align:middle;}
.tbl .cat{white-space:nowrap;}
.tbl tbody tr:last-child td{border-bottom:none;}
.tbl tbody tr:hover td{background:#f8faff;}
.tbl .id{font-weight:700;color:var(--ink);white-space:nowrap;}
.tbl .nm{font-weight:600;color:var(--ink);white-space:nowrap;}
.tbl .dt{white-space:nowrap;color:var(--muted);}
.tbl .sum{min-width:260px;color:var(--muted);line-height:1.45;}

.badge{display:inline-flex;align-items:center;gap:.38rem;padding:.2rem .62rem;border-radius:999px;font-size:.74rem;font-weight:600;white-space:nowrap;}
.badge:before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor;}
.p-high{background:#fdecec;color:#b42318;}
.p-med{background:#fff3dc;color:#9a5b04;}
.p-low{background:#e5f6ec;color:#17744a;}
.s-open{background:#e8efff;color:#1f4fd6;}
.s-prog{background:#f0eaff;color:#6a3fd1;}
.s-done{background:#e2f4f3;color:#0e6b68;}
.b-neutral{background:#eef2fa;color:#41536f;}


/* ---------- Inputs: readable styling ---------- */

.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stMultiSelect label {
    color: #2c3e5f !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
}

/* Input backgrounds and borders */
div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border: 1px solid #d5deee !important;
    border-radius: 10px !important;
}

/* Entered text */
.stTextInput input,
.stTextArea textarea,
div[data-baseweb="select"] input {
    color: #1b2b4d !important;
    -webkit-text-fill-color: #1b2b4d !important;
    background-color: transparent !important;
    caret-color: #2457e6 !important;
}

/* Dropdown selected value */
div[data-baseweb="select"] span {
    color: #1b2b4d !important;
}

/* Placeholder text */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #71809a !important;
    -webkit-text-fill-color: #71809a !important;
    opacity: 1 !important;
}

/* Focus effect */
div[data-baseweb="input"]:focus-within,
div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="select"] > div:focus-within {
    border-color: #2457e6 !important;
    box-shadow: 0 0 0 3px rgba(36, 87, 230, 0.14) !important;
}

/* Forms */
div[data-testid="stForm"] {
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 1.3rem 1.4rem;
    box-shadow: 0 1px 2px rgba(15, 30, 69, 0.04);
}

/* Expandable sections */
div[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: 12px;
}

/* ---------- FIX: readable Streamlit input fields ---------- */
.stTextInput div[data-baseweb="base-input"],
.stTextArea div[data-baseweb="base-input"],
div[data-baseweb="input"],
div[data-baseweb="textarea"] {
    background-color: #ffffff !important;
    border-color: #d5deee !important;
    border-radius: 10px !important;
}

.stTextInput input,
.stTextArea textarea,
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    background-color: #ffffff !important;
    color: #1b2b4d !important;
    -webkit-text-fill-color: #1b2b4d !important;
    caret-color: #2457e6 !important;
    opacity: 1 !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #71809a !important;
    -webkit-text-fill-color: #71809a !important;
    opacity: 1 !important;
}

/* ---------- Buttons ---------- */

.stButton > button,.stDownloadButton > button,.stFormSubmitButton > button{
  border-radius:10px;font-weight:600;min-height:2.6rem;border:1px solid #d5deee;background:#fff;color:var(--ink);
  transition:border-color .15s ease,box-shadow .15s ease,background .15s ease,transform .05s ease;}
.stButton > button p,.stDownloadButton > button p,.stFormSubmitButton > button p{color:inherit;font-weight:600;font-size:.9rem;white-space:normal !important;overflow:visible !important;text-overflow:clip !important;line-height:1.25;text-align:center;}
.stButton > button,.stDownloadButton > button,.stFormSubmitButton > button{padding:.4rem .75rem;height:auto;}
.stButton > button:hover,.stDownloadButton > button:hover,.stFormSubmitButton > button:hover{border-color:var(--blue);color:var(--blue);background:#f6f9ff;}
.stButton > button:focus-visible,.stDownloadButton > button:focus-visible,.stFormSubmitButton > button:focus-visible{outline:2px solid rgba(36,87,230,.4);outline-offset:2px;}
.stButton > button[kind="primary"],.stButton > button[data-testid="stBaseButton-primary"],
.stDownloadButton > button[kind="primary"],.stDownloadButton > button[data-testid="stBaseButton-primary"],
.stFormSubmitButton > button[kind="primaryFormSubmit"],.stFormSubmitButton > button[data-testid="stBaseButton-primaryFormSubmit"]{
  background:var(--blue);border-color:var(--blue);color:#fff;box-shadow:0 2px 6px rgba(36,87,230,.25);}
.stButton > button[kind="primary"]:hover,.stButton > button[data-testid="stBaseButton-primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover,.stDownloadButton > button[data-testid="stBaseButton-primary"]:hover,
.stFormSubmitButton > button[kind="primaryFormSubmit"]:hover,.stFormSubmitButton > button[data-testid="stBaseButton-primaryFormSubmit"]:hover{
  background:var(--blue-d);border-color:var(--blue-d);color:#fff;}

/* ---------- Alerts, tables ---------- */
div[data-testid="stAlert"]{border-radius:12px;border:1px solid rgba(20,35,75,.08);}
div[data-testid="stAlert"] p{color:inherit;}
div[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden;}

/* ---------- Small screens ---------- */
@media (max-width: 1100px){
  .block-container{padding:1rem 1.2rem 2rem;}
  .kpi-value{font-size:1.6rem;}
}
@media (max-width: 768px){
  .block-container{padding:1rem 1rem 2rem;}
  .ph{flex-direction:column;}
  .ph h1{font-size:1.35rem !important;}
  .ph-date{display:none;}
  .kpi-value{font-size:1.5rem;}
  table.tbl{font-size:.78rem;}
}
"""
st.markdown("<style>" + CSS + NAV_CSS + "</style>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def esc(v):
    if v is None or (isinstance(v, float) and v != v):
        return ""
    return html.escape(str(v))


def badge(kind, value):
    mapping = PRIORITY_CLS if kind == "priority" else STATUS_CLS
    cls = mapping.get(value, "b-neutral")
    return "<span class='badge " + cls + "'>" + esc(value) + "</span>"


def fmt_date(v, fmt="%d %b %Y"):
    ts = pd.to_datetime(v, errors="coerce")
    if pd.isna(ts):
        return esc(v)
    return ts.strftime(fmt)


def idx(options, value):
    return options.index(value) if value in options else 0


def go(page_name):
    """Callback used by navigation buttons (runs before the next rerun)."""
    st.session_state["page"] = page_name


def flash(msg):
    st.session_state["_flash"] = msg


def show_flash():
    msg = st.session_state.pop("_flash", None)
    if msg:
        st.success(msg)


def page_header(crumb, title, desc):
    today = datetime.now().strftime("%a, %d %b %Y")
    st.markdown(
        "<div class='crumb'>CareFlow AI <span>›</span> " + esc(crumb) + "</div>"
        "<div class='ph'><div><h1>" + esc(title) + "</h1><p>" + esc(desc) + "</p></div>"
        "<div class='ph-date'>" + today + "</div></div>",
        unsafe_allow_html=True,
    )


def section(title, sub=None):
    right = "<span>" + esc(sub) + "</span>" if sub else ""
    st.markdown("<div class='sec'><h3>" + esc(title) + "</h3>" + right + "</div>", unsafe_allow_html=True)


def empty_state(title, text):
    icon = ("<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
            "stroke-linecap='round' stroke-linejoin='round'><path d='M22 12h-6l-2 3h-4l-2-3H2'/>"
            "<path d='M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z'/></svg>")
    st.markdown("<div class='empty'><div class='empty-ic'>" + icon + "</div><h4>" + esc(title) + "</h4><p>" + esc(text) + "</p></div>",
                unsafe_allow_html=True)


def kpi(label, value, note, color):
    st.markdown(
        "<div class='kpi'><div class='kpi-top'><span class='kpi-dot' style='background:" + color + "'></span>" + esc(label) + "</div>"
        "<div class='kpi-value'>" + esc(value) + "</div><div class='kpi-note'>" + esc(note) + "</div></div>",
        unsafe_allow_html=True,
    )


def inquiry_table(rows, limit=None, empty_title="No inquiries found", empty_text="Nothing matches yet."):
    """Readable HTML table with priority/status badges. All values are HTML-escaped."""
    if not rows:
        empty_state(empty_title, empty_text)
        return
    shown = rows[:limit] if limit else rows
    body = []
    for r in shown:
        summary = str(r.get("summary") or "")
        if len(summary) > 120:
            summary = summary[:117].rstrip() + "…"
        body.append(
            "<tr>"
            "<td class='id'>#" + esc(r.get("id")) + "</td>"
            "<td class='nm'>" + esc(r.get("patient_name")) + "</td>"
            "<td class='cat'>" + esc(r.get("category")) + "</td>"
            "<td>" + badge("priority", r.get("priority")) + "</td>"
            "<td>" + badge("status", r.get("status")) + "</td>"
            "<td class='dt'>" + fmt_date(r.get("created_at")) + "</td>"
            "<td class='sum'>" + esc(summary) + "</td>"
            "</tr>"
        )
    head = "".join("<th>" + h + "</th>" for h in ["ID", "Patient", "Category", "Priority", "Status", "Created", "Summary"])
    st.markdown("<div class='tbl-wrap'><table class='tbl'><thead><tr>" + head + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>",
                unsafe_allow_html=True)
    if limit and len(rows) > limit:
        st.caption(f"Showing the first {limit} of {len(rows)} inquiries.")


def style_fig(fig, height=260):
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", size=12, color="#41536f"),
        showlegend=False,
    )
    return fig


PLOT_CONFIG = {"displayModeBar": False}


def stretch(fn):
    """Full-width kwarg that works on both newer (width='stretch') and older (use_container_width) Streamlit."""
    try:
        if "width" in inspect.signature(fn).parameters:
            return {"width": "stretch"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": True}


def spacer(rem=0.6):
    st.markdown("<div style='height:" + str(rem) + "rem'></div>", unsafe_allow_html=True)


@st.cache_data(ttl=20, show_spinner=False)
def check_ollama(base_url):
    """Read-only GET to the local Ollama model-list endpoint. Does not touch the app's AI integration."""
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/api/tags", timeout=0.8) as resp:
            return resp.status == 200
    except Exception:
        return False


def ai_status():
    """Returns (dot css class, short status text, detail text) for the AI status panels."""
    mode = str(AI_MODE)
    if "ollama" in mode.lower():
        base = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        if not base.startswith("http"):
            base = "http://" + base
        host = base.split("://", 1)[1].rstrip("/")
        if check_ollama(base):
            return "", "Ollama reachable", "Local Ollama service responded at " + host + "."
        return "dot-warn", "Ollama not detected", "No response from " + host + ". Start Ollama to generate live drafts."
    return "dot-off", "Status check unavailable", "Live connection status is only checked for Ollama modes."


AI_DOT, AI_STATE, AI_DETAIL = ai_status()

# ----------------------------------------------------------------------------
# Sidebar & navigation
# ----------------------------------------------------------------------------
if "page" not in st.session_state or st.session_state["page"] not in PAGES:
    st.session_state["page"] = "Dashboard"

with st.sidebar:
    st.markdown(
        "<div class='brand'><div class='brand-logo'>"
        "<svg width='20' height='20' viewBox='0 0 24 24' fill='white'><path d='M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z'/></svg>"
        "</div><div><div class='brand-name'>CareFlow AI</div><div class='brand-sub'>Healthcare Inquiry Automation</div></div></div>"
        "<div class='side-label'>WORKSPACE</div>",
        unsafe_allow_html=True,
    )
    page = st.radio("Navigation", PAGES, key="page", label_visibility="collapsed")
    st.markdown(
        "<div class='side-card'><div class='side-card-h'><span class='dot " + AI_DOT + "'></span>AI Assistant</div>"
        "<div class='side-card-mode'>Mode: " + esc(AI_MODE) + "<br>" + esc(AI_STATE) + "</div>"
        "<div class='side-card-t'>Helps organise inquiries and draft administrative replies. Drafts always need staff review.</div></div>"
        "<div class='side-foot'>Prototype for administrative workflows. Not a medical advice tool.</div>",
        unsafe_allow_html=True,
    )

# ----------------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------------
if page == "Dashboard":
    data = list_inquiries()
    m = metrics()
    page_header("Dashboard", "Welcome back", "A clear view of your patient inquiry queue, recent activity and AI assistant status.")
    show_flash()

    k1, k2, k3, k4 = st.columns(4, gap="small")
    with k1:
        kpi("Total Inquiries", m.get("total", 0), "All recorded requests", "#14234b")
    with k2:
        kpi("Open Queue", m.get("open", 0), "Needs attention", "#2457e6")
    with k3:
        kpi("In Progress", m.get("in_progress", 0), "Being handled", "#8a5cf0")
    with k4:
        kpi("Resolved", m.get("resolved", 0), "Completed requests", "#14a39e")

    spacer()
    section("Quick actions")
    q1, q2, q3, q4 = st.columns(4, gap="small")
    q1.button("New Inquiry", type="primary", **stretch(st.button), key="qa_new", on_click=go, args=("Submit Inquiry",))
    q2.button("Manage Inquiries", **stretch(st.button), key="qa_manage", on_click=go, args=("Manage Inquiries",))
    q3.button("AI Response Studio", **stretch(st.button), key="qa_studio", on_click=go, args=("AI Response Studio",))
    q4.button("Analytics & Reports", **stretch(st.button), key="qa_analytics", on_click=go, args=("Analytics & Reports",))

    spacer()
    section("Recent inquiries", "Latest 6 requests")
    if not data:
        empty_state("Your workspace is empty", "Submit an inquiry, or load fictional sample records to explore the dashboard.")
        if st.button("Load fictional demo data", type="primary", key="seed_dash"):
            seed_demo_data()
            flash("Fictional demo data loaded.")
            st.rerun()
    else:
        inquiry_table(data[:6])

    spacer()
    chart_col, ai_col = st.columns([1.4, 1], gap="medium")
    with chart_col:
        with st.container(border=True):
            section("Inquiries by category")
            df = pd.DataFrame(data)
            if not df.empty and "category" in df:
                counts = df["category"].value_counts().rename_axis("Category").reset_index(name="Inquiries")
                counts = counts.sort_values("Inquiries", ascending=True)
                fig = px.bar(counts, x="Inquiries", y="Category", orientation="h")
                fig.update_traces(marker_color=BLUE, marker_line_width=0)
                fig.update_xaxes(showgrid=True, gridcolor="#eef2f9", zeroline=False, title="", dtick=1)
                fig.update_yaxes(title="")
                st.plotly_chart(style_fig(fig, 230), **stretch(st.plotly_chart), config=PLOT_CONFIG)
            else:
                st.caption("Charts will appear when inquiries are added.")
    with ai_col:
        st.markdown(
            "<div class='ai-card'><div class='ai-top'><span class='dot " + AI_DOT + "'></span><b>AI assistant</b></div>"
            "<div class='ai-mode'>" + esc(AI_MODE) + "</div>"
            "<div class='ai-status'><b>" + esc(AI_STATE) + "</b><br>" + esc(AI_DETAIL) + "</div>"
            "<p>Classifies inquiries and drafts administrative replies.</p>"
            "<div class='ai-warn'><b>Human review required.</b> AI-generated drafts must be checked by staff before use.</div></div>",
            unsafe_allow_html=True,
        )

    st.caption("All figures are calculated from the current local database; sample records are fictional.")

# ----------------------------------------------------------------------------
# Submit Inquiry
# ----------------------------------------------------------------------------
elif page == "Submit Inquiry":
    page_header("Submit Inquiry", "Submit an inquiry", "Capture the request, classify it, and prepare a response for staff review.")
    form_col, info_col = st.columns([1.8, 1], gap="large")
    with form_col:
        with st.form("inquiry_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Patient name *", placeholder="e.g. Priya Sharma")
            email = c2.text_input("Email (optional)", placeholder="name@example.com")
            category = st.selectbox("Inquiry category", CATEGORIES)
            message = st.text_area("Inquiry message *", height=170, placeholder="Write the inquiry in the patient's own words...")
            submitted = st.form_submit_button("Process inquiry", type="primary", **stretch(st.form_submit_button))

        if submitted:
            error = validate_inquiry(name, email, message)
            if error:
                st.error(error)
            else:
                result = process_inquiry(message, category)
                record = create_inquiry(name.strip(), email.strip(), category, message.strip(), result["summary"], result["priority"], result["draft_response"], "Open")
                st.success(f"Inquiry #{record['id']} saved. AI processing mode: {AI_MODE}.")
                st.session_state["selected_inquiry_id"] = record["id"]
                st.info("The generated response is a draft. A staff member must review it before use.")
                st.button("Open in Manage Inquiries", key="after_submit_manage", on_click=go, args=("Manage Inquiries",))
    with info_col:
        st.markdown(
            "<div class='card'><h4>What happens next</h4><ol class='steps'>"
            "<li>The inquiry is summarised and given a priority.</li>"
            "<li>A draft administrative reply is generated.</li>"
            "<li>Staff review and update the inquiry. Nothing is sent automatically.</li></ol></div>"
            "<div class='card'><h4>Data guidance</h4>"
            "<p>Use fictional data for demonstrations and avoid entering real patient health information.</p></div>",
            unsafe_allow_html=True,
        )

# ----------------------------------------------------------------------------
# Manage Inquiries
# ----------------------------------------------------------------------------
elif page == "Manage Inquiries":
    page_header("Manage Inquiries", "Manage inquiries", "Search, filter, review and update requests in one place.")
    show_flash()
    data = list_inquiries()
    df = pd.DataFrame(data)
    if not df.empty:
        a, b, c, d = st.columns([2.2, 1, 1, 1])
        q = a.text_input("Search", placeholder="Patient, message, or summary")
        cats = ["All"] + sorted(df["category"].dropna().unique().tolist())
        cat = b.selectbox("Category", cats)
        status = c.selectbox("Status", ["All"] + STATUSES)
        prio = d.selectbox("Priority", ["All"] + PRIORITIES[::-1])
        if q:
            df = df[df.apply(lambda row: q.lower() in " ".join(map(str, row.values)).lower(), axis=1)]
        if cat != "All":
            df = df[df["category"] == cat]
        if status != "All":
            df = df[df["status"] == status]
        if prio != "All":
            df = df[df["priority"] == prio]

        spacer()
        inquiry_table(df.to_dict("records"), limit=100, empty_title="No inquiries match your filters", empty_text="Try clearing the search or changing a filter.")

        spacer()
        section("Review an inquiry")
        ids = df["id"].tolist()
        if ids:
            preset = st.session_state.get("selected_inquiry_id")
            start = ids.index(preset) if preset in ids else 0
            selected = st.selectbox("Choose inquiry", ids, index=start,
                                    format_func=lambda x: f"#{x} — {df.loc[df.id == x, 'patient_name'].iloc[0]}")
            item = get_inquiry(int(selected))
            if item:
                lc, rc = st.columns([1.2, 1], gap="large")
                with lc:
                    st.markdown(
                        "<div class='card'><div class='lead-name'>" + esc(item.get("patient_name")) + "</div>"
                        "<div class='meta-row'><span class='chip'>" + esc(item.get("category")) + "</span>"
                        + badge("priority", item.get("priority")) + badge("status", item.get("status")) + "</div>"
                        "<div class='msgbox'>" + esc(item.get("message")) + "</div>"
                        "<div class='kv'><b>Summary:</b> " + esc(item.get("summary")) + "</div></div>",
                        unsafe_allow_html=True,
                    )
                with rc:
                    with st.form(f"edit_{selected}"):
                        new_status = st.selectbox("Status", STATUSES, index=idx(STATUSES, item["status"]))
                        new_priority = st.selectbox("Priority", PRIORITIES, index=idx(PRIORITIES, item["priority"]))
                        new_draft = st.text_area("Response draft", value=item["draft_response"], height=150)
                        if st.form_submit_button("Save changes", type="primary", **stretch(st.form_submit_button)):
                            update_inquiry(int(selected), status=new_status, priority=new_priority, draft_response=new_draft)
                            flash("Inquiry updated.")
                            st.rerun()
    else:
        empty_state("No inquiries yet", "Submit one, or load fictional demo data to explore the workspace.")
        if st.button("Load fictional demo data", type="primary", key="seed_manage"):
            seed_demo_data()
            st.rerun()

# ----------------------------------------------------------------------------
# AI Response Studio
# ----------------------------------------------------------------------------
elif page == "AI Response Studio":
    page_header("AI Response Studio", "AI Response Studio", "Experiment with structured prompts and create human-reviewed administrative reply drafts.")
    data = list_inquiries()
    if not data:
        empty_state("No inquiries to work with", "Add an inquiry first, or load fictional demo data from the Dashboard.")
    else:
        ids = [x["id"] for x in data]
        preset = st.session_state.get("selected_inquiry_id")
        start = ids.index(preset) if preset in ids else 0
        selected = st.selectbox("Select inquiry", ids, index=start,
                                format_func=lambda x: f"#{x} — {next((i['patient_name'] for i in data if i['id'] == x), 'Inquiry')}")
        item = get_inquiry(int(selected))
        st.warning("**Human review required.** AI-generated drafts can be inaccurate or incomplete. A staff member must review and approve every draft before it is used.")

        if item:
            left, right = st.columns([1, 1.15], gap="large")
            with left:
                section("Incoming inquiry")
                st.markdown(
                    "<div class='card'><div class='lead-name'>" + esc(item.get("patient_name")) + "</div>"
                    "<div class='meta-row'><span class='chip'>" + esc(item.get("category")) + "</span>"
                    + badge("priority", item.get("priority")) + badge("status", item.get("status")) + "</div>"
                    "<div class='msgbox'>" + esc(item.get("message")) + "</div></div>",
                    unsafe_allow_html=True,
                )
                with st.expander("Prompt configuration"):
                    system_prompt = st.text_area(
                        "System prompt",
                        value="You are a helpful clinic administrative assistant. Classify inquiries and draft concise, empathetic administrative replies. Never diagnose, recommend treatment, or provide medication advice. Escalate clinical questions to a qualified healthcare professional.",
                        height=150,
                    )
                    st.caption(f"Execution mode: {AI_MODE}")
            with right:
                section("Response draft")
                if st.button("Generate response draft", type="primary", **stretch(st.button), key="studio_generate"):
                    result = generate_reply(item["message"], item["category"], system_prompt)
                    st.session_state["studio_result"] = result
                    st.session_state["studio_for"] = int(selected)
                    st.session_state["studio_gen"] = st.session_state.get("studio_gen", 0) + 1

                if "studio_result" in st.session_state and st.session_state.get("studio_for") == int(selected):
                    result = st.session_state["studio_result"]
                    st.markdown(
                        "<div class='meta-row'><span class='chip'>" + esc(result["category"]) + "</span>"
                        + badge("priority", result["priority"]) + "</div>"
                        "<div class='kv' style='margin-top:0;margin-bottom:.6rem'><b>Summary:</b> " + esc(result["summary"]) + "</div>",
                        unsafe_allow_html=True,
                    )
                    edited = st.text_area("Review and edit before saving", value=result["draft_response"], height=210,
                                          key=f"studio_edit_{selected}_{st.session_state.get('studio_gen', 0)}")
                    if st.button("Save draft to inquiry", key="studio_save", **stretch(st.button)):
                        update_inquiry(int(selected), category=result["category"], priority=result["priority"], summary=result["summary"], draft_response=edited)
                        st.success("Draft saved for staff review.")
                else:
                    empty_state("No draft yet", "Generate a response draft to review and edit it here.")

# ----------------------------------------------------------------------------
# Analytics & Reports
# ----------------------------------------------------------------------------
elif page == "Analytics & Reports":
    page_header("Analytics & Reports", "Analytics & reports", "Explore inquiry patterns and export operational data.")
    data = list_inquiries()
    df = pd.DataFrame(data)
    if df.empty:
        empty_state("No data to analyze yet", "Charts and exports will appear once inquiries are added.")
    else:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            with st.container(border=True):
                section("Category volume")
                catdf = df["category"].value_counts().rename_axis("Category").reset_index(name="Inquiries")
                fig = px.bar(catdf, x="Category", y="Inquiries")
                fig.update_traces(marker_color=BLUE, marker_line_width=0)
                fig.update_yaxes(gridcolor="#eef2f9", zeroline=False, title="", dtick=1)
                fig.update_xaxes(title="")
                st.plotly_chart(style_fig(fig, 300), **stretch(st.plotly_chart), config=PLOT_CONFIG)
        with c2:
            with st.container(border=True):
                section("Priority breakdown")
                pr = df["priority"].value_counts().rename_axis("Priority").reset_index(name="Inquiries")
                fig = px.pie(pr, names="Priority", values="Inquiries", hole=0.62, color="Priority", color_discrete_map=PRIORITY_COLORS)
                fig.update_traces(textinfo="value", marker=dict(line=dict(color="#ffffff", width=2)))
                fig = style_fig(fig, 300)
                fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center", title_text=""))
                st.plotly_chart(fig, **stretch(st.plotly_chart), config=PLOT_CONFIG)

        spacer()
        section("Export & data")
        st.download_button("Download inquiries as CSV", data=export_csv(data), file_name="careflow_inquiries.csv", mime="text/csv", type="primary")
        spacer()
        st.dataframe(df[["id", "patient_name", "category", "priority", "status", "created_at"]], **stretch(st.dataframe), hide_index=True)

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
elif page == "Settings":
    page_header("Settings", "Settings & project information", "Manage the local prototype configuration and understand how its AI workflow operates.")
    show_flash()
    key_present = bool(os.getenv("OPENAI_API_KEY"))
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            "<div class='card'><h4>AI configuration</h4>"
            "<p><b>Current mode:</b> " + esc(AI_MODE) + "</p>"
            "<p><b>API key present:</b> " + ("Yes" if key_present else "No") + "</p>"
            "<p style='color:#6b7a94;font-size:.82rem'>Configure an API key in a local .env file to enable live AI responses. Never commit secrets.</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='card'><h4>Safety</h4>"
            "<p>Clinical questions receive a safe escalation message. The app does not diagnose, recommend treatment, or send messages automatically.</p></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            "<div class='card'><h4>Data storage</h4>"
            "<p>SQLite database stored locally in <code>data/careflow.db</code>.</p>"
            "<p>Use fictional data for demonstrations. Avoid entering real patient health information.</p></div>",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown("<h4 style='margin:0 0 .4rem'>Demo controls</h4>", unsafe_allow_html=True)
            st.caption("Adds fictional sample inquiries to the local database.")
            if st.button("Add fictional sample inquiries", key="seed_settings"):
                seed_demo_data()
                flash("Fictional sample inquiries added.")
                st.rerun()
    st.caption("CareFlow AI is an assessment prototype for administrative workflow automation, not a certified healthcare product.")
