import streamlit as st
import time
import pandas as pd
from core.orchestrator import run_global_scraper

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="LeadGen Engine",
    page_icon="🚀",
    layout="wide"
)

# ----------------------------
# SESSION STATE
# ----------------------------
if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False

if "running" not in st.session_state:
    st.session_state.running = False

# ----------------------------
# CUSTOM CSS
# ----------------------------
st.markdown("""
<style>
.main { background-color: #0e1117; }
h1, h2, h3, h4 { color: white; }

.stButton>button {
    background: linear-gradient(90deg,#00c6ff,#0072ff);
    color: white;
    border-radius: 12px;
    height: 3em;
    width: 100%;
    font-size: 18px;
    font-weight: bold;
}
.stButton>button:hover { transform: scale(1.03); }

.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# HEADER
# ----------------------------
st.title("🚀 Global Lead Generation Engine")
st.write("Scrape business leads & extract decision-maker emails.")

# ----------------------------
# CATEGORY ICONS (WORKING)
# ----------------------------
CATEGORY_ICONS = {
    "software company": "💻",
    "bpo": "🎧",
    "it services": "🖧",
    "digital marketing": "📊",
    "real estate": "🏢",
    "default": "📁"
}

# ----------------------------
# INPUTS
# ----------------------------
col1, col2 = st.columns(2)

with col1:
    city = st.text_input("📍 City", value="Bangalore")

with col2:
    category = st.selectbox(
        "🏷 Category",
        ["software company", "bpo", "it services", "digital marketing"]
    )

icon = CATEGORY_ICONS.get(category.lower(), CATEGORY_ICONS["default"])
st.write(f"### {icon} Selected Category: **{category.upper()}**")

# ----------------------------
# CONTROL BUTTONS
# ----------------------------
colA, colB = st.columns(2)

with colA:
    start = st.button("🚀 Start Scraping")

with colB:
    stop = st.button("🛑 Cancel")

if stop:
    st.session_state.stop_requested = True
    st.warning("Stopping safely... please wait.")

# ----------------------------
# SCRAPER PROCESS
# ----------------------------
if start and not st.session_state.running:

    st.session_state.running = True
    st.session_state.stop_requested = False

    progress = st.progress(0)
    status_box = st.empty()
    log_box = st.empty()

    steps = [
        "Initializing engine...",
        "Connecting to sources...",
        "Scraping directories...",
        "Collecting websites...",
        "Extracting emails...",
        "Cleaning data...",
        "Scoring leads...",
        "Preparing export..."
    ]

    for i, step in enumerate(steps):

        if st.session_state.stop_requested:
            status_box.error("❌ Scraping stopped.")
            st.session_state.running = False
            st.stop()

        status_box.info(f"⚙ {step}")
        log_box.text(f"[LOG] {step}")
        progress.progress((i + 1) * 12)
        time.sleep(0.4)

    # run pipeline
    if not st.session_state.stop_requested:

        status_box.info("🔎 Running scraping pipeline...")

        with st.spinner("Extracting high-quality leads..."):
            leads = run_global_scraper([city], [category])

        progress.progress(100)
        status_box.success("✅ Scraping Complete!")
        st.balloons()

        if leads:

            df = pd.DataFrame(leads)

            st.success(f"🎯 {len(df)} leads generated")

            st.dataframe(df, use_container_width=True)

            st.download_button(
                label="📥 Download Leads CSV",
                data=df.to_csv(index=False),
                file_name="leads.csv",
                mime="text/csv"
            )

        else:
            st.warning("No leads found.")

        st.session_state.running = False

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.caption("Built with ❤️ using Python & Streamlit")
