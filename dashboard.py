import streamlit as st
import pandas as pd
import io
from core.orchestrator import run_global_scraper

st.set_page_config(
    page_title="LeadGen Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

for key, default in {
    "stop_requested": False,
    "running": False,
    "recent_searches": [],
    "last_df": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #0e1117 !important;
    color: #e2e8f0 !important;
}
.main .block-container {
    padding: 2rem 3rem 3rem !important;
    max-width: 1260px !important;
}

/* ── Hero ── */
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 55%, #e879f9 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
    margin: 0 0 0.35rem 0;
}
.hero-sub {
    font-size: 0.92rem;
    color: #475569;
    margin-bottom: 2rem;
    font-weight: 400;
}

/* ── Section label ── */
.sec-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.66rem;
    font-weight: 700;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    margin-bottom: 1rem;
}

/* ── Form card wraps both columns ── */
.form-card {
    background: #131921;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.2rem;
}

/* ── All input labels same style ── */
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stRadio"] label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: #64748b !important;
    letter-spacing: 0.04em !important;
    margin-bottom: 0.3rem !important;
}

/* ── Text input ── */
div[data-testid="stTextInput"] input {
    background-color: #0e1520 !important;
    border: 1px solid #1e2d3d !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.94rem !important;
    height: 2.75rem !important;
    padding: 0 0.9rem !important;
    transition: border-color 0.15s !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 2px rgba(56,189,248,0.12) !important;
    outline: none !important;
}

/* ── Selectbox ── */
div[data-testid="stSelectbox"] > div > div {
    background-color: #0e1520 !important;
    border: 1px solid #1e2d3d !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.94rem !important;
    min-height: 2.75rem !important;
}

/* ── Radio buttons ── */
div[data-testid="stRadio"] > div {
    display: flex !important;
    flex-direction: row !important;
    gap: 1.2rem !important;
    margin-top: 0.2rem !important;
    margin-bottom: 0.75rem !important;
}
div[data-testid="stRadio"] > div label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    color: #94a3b8 !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
    cursor: pointer !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.04em !important;
    background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    height: 2.85rem !important;
    box-shadow: 0 4px 16px rgba(37,99,235,0.3) !important;
    transition: all 0.18s ease !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(37,99,235,0.45) !important;
}
.stButton > button[kind="primary"]:disabled {
    opacity: 0.35 !important;
    transform: none !important;
}

/* ── Secondary button (Stop) ── */
.stButton > button:not([kind="primary"]) {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    background: transparent !important;
    border: 1px solid #2d3a4a !important;
    color: #64748b !important;
    border-radius: 10px !important;
    height: 2.85rem !important;
    transition: all 0.15s !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: #ef4444 !important;
    color: #ef4444 !important;
}
.stButton > button:not([kind="primary"]):disabled {
    opacity: 0.3 !important;
}

/* ── Progress ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #2563eb, #7c3aed, #e879f9) !important;
    border-radius: 999px !important;
}
.stProgress > div > div {
    background: #1e2d3d !important;
    border-radius: 999px !important;
    height: 5px !important;
}

/* ── Log box ── */
.log-box {
    background: #0a0f1a;
    border: 1px solid #1e293b;
    border-left: 3px solid #2563eb;
    border-radius: 0 8px 8px 0;
    padding: 0.85rem 1.1rem;
    font-family: 'Courier New', monospace;
    font-size: 0.79rem;
    color: #94a3b8;
    max-height: 185px;
    overflow-y: auto;
    line-height: 1.75;
}

/* ── Stat cards ── */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 1.1rem 0 1.4rem;
}
.stat-card {
    background: #131921;
    border: 1px solid #1e293b;
    border-top: 2px solid #38bdf8;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    text-align: center;
}
.stat-card.g { border-top-color: #34d399; }
.stat-card.p { border-top-color: #a78bfa; }
.stat-card.o { border-top-color: #fb923c; }
.stat-num {
    font-family: 'Syne', sans-serif;
    font-size: 2.1rem;
    font-weight: 800;
    color: #38bdf8;
    line-height: 1;
}
.stat-card.g .stat-num { color: #34d399; }
.stat-card.p .stat-num { color: #a78bfa; }
.stat-card.o .stat-num { color: #fb923c; }
.stat-lbl {
    font-size: 0.7rem;
    color: #334155;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.35rem;
    font-weight: 600;
}

/* ── Dataframe ── */
.stDataFrame {
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
}

/* ── Download ── */
.stDownloadButton > button {
    font-family: 'Syne', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    background: #0e1520 !important;
    border: 1px solid #1e293b !important;
    color: #475569 !important;
    height: 2.5rem !important;
    border-radius: 8px !important;
    transition: all 0.15s !important;
}
.stDownloadButton > button:hover {
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
}

/* ── Checkbox ── */
div[data-testid="stCheckbox"] label {
    font-size: 0.83rem !important;
    color: #64748b !important;
}

/* ── Alerts ── */
.stAlert {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.87rem !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #090e16 !important;
    border-right: 1px solid #1e293b !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid #1e293b !important;
    color: #334155 !important;
    font-size: 0.77rem !important;
    height: 2.2rem !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    text-align: left !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ── Misc ── */
hr { border-color: #1e293b !important; margin: 1.4rem 0 !important; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #090e16; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #38bdf8; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ───────────────────────────────────────────────────────────────────


def normalize_leads(leads):
    if not isinstance(leads, list):
        return []
    out = []
    for lead in leads:
        if isinstance(lead, list):
            for sub in lead:
                if isinstance(sub, dict):
                    out.append(_clean(sub))
        elif isinstance(lead, dict):
            out.append(_clean(lead))
    return out


def _clean(lead):
    fixed = {}
    for k, v in lead.items():
        if k.startswith("_"):
            continue
        fixed[k] = ", ".join(str(x) for x in v if x) if isinstance(v, list) \
                   else ("" if v is None else str(v))
    for col in ("Email", "Website", "Phone", "Name", "City", "Category", "Source", "Address"):
        fixed.setdefault(col, "")
    return fixed


def estimate_time(cities, categories):
    m = len(cities) * len(categories) * 4
    return "~1–2 min" if m < 2 else (f"~{m} min" if m < 10 else f"~{m//60}h {m%60}m")


def make_excel(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Leads")
        ws = w.sheets["Leads"]
        for cc in ws.columns:
            ws.column_dimensions[cc[0].column_letter].width = \
                min(max(len(str(c.value or "")) for c in cc) + 4, 50)
    buf.seek(0)
    return buf.getvalue()


DISPLAY_COLS = ["Name", "Email", "Phone", "Website",
                "City", "Category", "Source", "Address"]
QUICK_CATS = [
    "Digital Marketing Agency", "Software Development Company",
    "Medical Billing Company", "BPO Company", "IT Services Company",
    "Web Development Company", "Cybersecurity Services",
    "HR Outsourcing Services", "Outsourced Accounting", "Call Center Services",
]
COMMON_CATEGORIES = [
    "-- Select --",
    "Digital Marketing Agency", "SEO Agency", "Social Media Marketing",
    "Software Development Company", "Web Development Company",
    "Mobile App Development", "IT Services Company",
    "Medical Billing Company", "Revenue Cycle Management",
    "BPO Company", "Call Center Services",
    "Outsourced Accounting Services", "HR Outsourcing Services",
    "Cybersecurity Services", "Cloud Services Provider",
    "Real Estate Agency", "Construction Company",
    "Logistics Company", "Manufacturing Company",
]
STEP_MAP = {
    "engine started": 5, "city": 10, "category": 15, "searching": 25,
    "directories": 30, "raw leads": 45, "cleaning": 55, "unique": 60,
    "finding websites": 65, "extracting emails": 72, "deep crawl": 82,
    "enriching": 90, "saving": 96, "completed": 100,
}

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style='font-family:Syne,sans-serif;font-size:1rem;font-weight:800;
                color:#38bdf8;margin-bottom:0.1rem'>⚡ LeadGen Engine</div>
    <div style='font-size:0.72rem;color:#1e3a4a;margin-bottom:1.4rem'>
        Business Intelligence Platform
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.68rem;color:#334155;font-weight:600;"
                "text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.55rem'>"
                "Data Sources</div>", unsafe_allow_html=True)
    for icon, name in [("🗺️", "Google Maps"), ("🔍", "SerpAPI"), ("📒", "JustDial"),
                       ("🏭", "IndiaMART"), ("🟡", "YellowPages"), ("🟩", "BBB")]:
        st.markdown(f"<div style='font-size:0.8rem;color:#1e3a4a;padding:3px 0'>"
                    f"{icon}&nbsp;&nbsp;{name}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='font-size:0.68rem;color:#334155;font-weight:600;"
                "text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.55rem'>"
                "Quick Categories</div>", unsafe_allow_html=True)
    for cat in QUICK_CATS:
        if st.button(cat, key=f"qc_{cat}", use_container_width=True):
            st.session_state["_quick_cat"] = cat

    if st.session_state.recent_searches:
        st.markdown("---")
        st.markdown("<div style='font-size:0.68rem;color:#334155;font-weight:600;"
                    "text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.5rem'>"
                    "Recent Searches</div>", unsafe_allow_html=True)
        for item in st.session_state.recent_searches[:5]:
            st.markdown(f"<div style='font-size:0.76rem;color:#1e3a4a;"
                        f"padding:3px 0 3px 8px;border-left:2px solid #1e293b;"
                        f"margin-bottom:3px'>{item}</div>", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class='hero-title'>Global Lead Generation Engine</div>
<div class='hero-sub'>Discover verified business leads and decision-maker emails across any industry.</div>
""", unsafe_allow_html=True)

# ── SEARCH FORM ───────────────────────────────────────────────────────────────
# Wrap the whole form in a card so both columns share the same background,
# making mismatched heights invisible.

st.markdown("<div class='sec-label'>Search Parameters</div>",
            unsafe_allow_html=True)
st.markdown("<div class='form-card'>", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    city_input = st.text_input(
        "📍 Cities",
        placeholder="Chennai, Dubai, New York, London",
        help="Comma-separated cities"
    )
    cities = [c.strip() for c in city_input.split(",") if c.strip()]

with col2:
    default_cat = st.session_state.pop("_quick_cat", "")

    cat_mode = st.radio(
        "Input method",
        ["Choose from list", "Type my own"],
        horizontal=True,
        label_visibility="visible",
        key="cat_mode"
    )

    if cat_mode == "Choose from list":
        cat_select = st.selectbox(
            "🏷️ Category",
            COMMON_CATEGORIES,
            key="cat_select"
        )
        category = "" if cat_select == "-- Select --" else cat_select
    else:
        category = st.text_input(
            "🏷️ Category",
            value=default_cat,
            placeholder="e.g. solar companies, dental clinics",
            key="cat_text"
        )

st.markdown("</div>", unsafe_allow_html=True)

# ── VALIDATION ────────────────────────────────────────────────────────────────

if cities and category:
    est = estimate_time(cities, [category])
    st.info(
        f"🔍 Targeting **{category}** in **{', '.join(cities)}** "
        f"across 6 sources · estimated time: **{est}**"
    )
elif cities and not category:
    st.warning("Select or type a category to continue.")
elif category and not cities:
    st.warning("Enter at least one city to continue.")

# ── ACTION BUTTONS ────────────────────────────────────────────────────────────

st.markdown("")
bc1, bc2, bc3 = st.columns([2, 1, 4])
with bc1:
    start = st.button(
        "⚡ Start Scraping",
        disabled=st.session_state.running or not cities or not category,
        use_container_width=True,
        type="primary"
    )
with bc2:
    if st.button("⛔ Stop", use_container_width=True,
                 disabled=not st.session_state.running):
        st.session_state.stop_requested = True

# ── SCRAPER RUN ───────────────────────────────────────────────────────────────

if start and not st.session_state.running:
    st.session_state.running = True
    st.session_state.stop_requested = False

    st.markdown("---")
    st.markdown("<div class='sec-label'>Live Progress</div>",
                unsafe_allow_html=True)

    prog = st.progress(0, text="Initializing...")
    stat_box = st.empty()
    log_slot = st.empty()

    logs = []
    pct = [0]

    def upd(msg: str):
        logs.append(f"› {msg}")
        if len(logs) > 12:
            logs.pop(0)
        for kw, p in STEP_MAP.items():
            if kw in msg.lower() and p > pct[0]:
                pct[0] = p
                break
        prog.progress(pct[0], text=(msg[:78]+"..." if len(msg) > 78 else msg))
        stat_box.markdown(
            f"<div style='font-size:0.82rem;color:#334155;margin:0.2rem 0'>"
            f"⏳ {msg}</div>", unsafe_allow_html=True
        )
        rows = "".join(
            f"<div style='color:{'#94a3b8' if i==len(logs)-1 else '#1e3a4a'}'>{l}</div>"
            for i, l in enumerate(logs)
        )
        log_slot.markdown(
            f"<div class='log-box'>{rows}</div>", unsafe_allow_html=True)

    upd("🚀 Engine starting...")

    try:
        result = run_global_scraper(
            cities=cities, categories=[category],
            progress_callback=upd,
            stop_flag=lambda: st.session_state.stop_requested
        )
        leads, _ = result if isinstance(result, tuple) else (result, [])
    except Exception as e:
        st.error(f"❌ Scraper error: {e}")
        st.session_state.running = False
        st.stop()

    prog.progress(100, text="Complete!")
    stat_box.empty()

    if leads:
        leads = normalize_leads(leads)
        df = pd.DataFrame(leads)
        for col in DISPLAY_COLS:
            if col not in df.columns:
                df[col] = ""
        st.session_state.last_df = df
        label = f"{category} · {', '.join(cities)}"
        if label not in st.session_state.recent_searches:
            st.session_state.recent_searches.insert(0, label)
            st.session_state.recent_searches = st.session_state.recent_searches[:5]
    else:
        st.warning("⚠️ No leads found — try a different city or category.")

    st.session_state.running = False

# ── RESULTS ───────────────────────────────────────────────────────────────────

df = st.session_state.get("last_df")

if df is not None and not df.empty:
    st.markdown("---")

    total = len(df)
    we = int(df["Email"].apply(lambda x: bool(str(x).strip())).sum())
    wp = int(df["Phone"].apply(lambda x: bool(str(x).strip())).sum())
    ww = int(df["Website"].apply(lambda x: bool(str(x).strip())).sum())

    st.markdown(f"""
    <div class='stats-grid'>
        <div class='stat-card'>
            <div class='stat-num'>{total}</div>
            <div class='stat-lbl'>Total Leads</div>
        </div>
        <div class='stat-card g'>
            <div class='stat-num'>{we}</div>
            <div class='stat-lbl'>Emails · {int(100*we/total) if total else 0}%</div>
        </div>
        <div class='stat-card p'>
            <div class='stat-num'>{wp}</div>
            <div class='stat-lbl'>Phones · {int(100*wp/total) if total else 0}%</div>
        </div>
        <div class='stat-card o'>
            <div class='stat-num'>{ww}</div>
            <div class='stat-lbl'>Websites · {int(100*ww/total) if total else 0}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='sec-label'>Filter Results</div>",
                unsafe_allow_html=True)

    f1, f2, f3 = st.columns([3, 1, 1])
    with f1:
        q = st.text_input("Search", placeholder="Search by name, email, city...",
                          label_visibility="collapsed")
    with f2:
        oe = st.checkbox("Email only")
    with f3:
        ow = st.checkbox("Website only")

    filtered = df.copy()
    if q:
        filtered = filtered[filtered.apply(
            lambda r: q.lower() in r.to_string().lower(), axis=1)]
    if oe:
        filtered = filtered[filtered["Email"].str.strip().astype(bool)]
    if ow:
        filtered = filtered[filtered["Website"].str.strip().astype(bool)]

    st.markdown(
        f"<div style='font-size:0.76rem;color:#1e3a4a;margin-bottom:0.5rem'>"
        f"Showing {len(filtered)} of {total} leads</div>",
        unsafe_allow_html=True
    )

    st.dataframe(
        filtered[[c for c in DISPLAY_COLS if c in filtered.columns]],
        use_container_width=True,
        height=460,
        column_config={
            "Website": st.column_config.LinkColumn("Website"),
            "Email":   st.column_config.TextColumn("Email",   width="medium"),
            "Name":    st.column_config.TextColumn("Company", width="large"),
            "Phone":   st.column_config.TextColumn("Phone",   width="medium"),
        }
    )

    st.markdown("")
    st.markdown("<div class='sec-label'>Export</div>", unsafe_allow_html=True)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M")
    d1, d2, _ = st.columns([1, 1, 4])
    with d1:
        st.download_button("⬇ CSV", data=filtered.to_csv(index=False).encode(),
                           file_name=f"leads_{ts}.csv", mime="text/csv",
                           use_container_width=True)
    with d2:
        try:
            st.download_button("⬇ Excel", data=make_excel(filtered),
                               file_name=f"leads_{ts}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        except Exception:
            st.info("pip install openpyxl for Excel export")

# ── FOOTER ────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#1e293b;font-size:0.7rem'>"
    "LeadGen Engine · Built with Python & Streamlit</div>",
    unsafe_allow_html=True
)
