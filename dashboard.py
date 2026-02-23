import streamlit as st
import time
import pandas as pd
import io
from core.orchestrator import run_global_scraper

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="LeadGen Engine",
    layout="wide"
)

# ----------------------------
# SESSION STATE
# ----------------------------
if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False

if "running" not in st.session_state:
    st.session_state.running = False

if "recent_searches" not in st.session_state:
    st.session_state.recent_searches = []

# ----------------------------
# NORMALIZE DATA
# ----------------------------


def normalize_leads(leads):
    normalized = []

    for lead in leads:
        fixed = {}

        for k, v in lead.items():
            if isinstance(v, list):
                fixed[k] = ", ".join(str(x) for x in v if x)
            elif v is None:
                fixed[k] = ""
            else:
                fixed[k] = str(v)

        fixed["Email"] = fixed.get("Email", "")
        fixed["UndeliverableEmails"] = fixed.get("UndeliverableEmails", "")
        fixed["Website"] = fixed.get("Website", "")

        normalized.append(fixed)

    return normalized


# ----------------------------
# DARK UI + CURSOR FIX
# ----------------------------
st.markdown("""
<style>
.main { background-color: #0e1117; }
h1, h2, h3 { color: #ffffff; }

/* Buttons */
.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 8px;
    height: 3em;
    font-weight: 600;
}
.stButton>button:hover {
    background-color: #1e40af;
}

/* Inputs */
.stTextInput input {
    background-color: #1c1f26;
    color: white;
}

/* Selectbox styling */
.stSelectbox div[data-baseweb="select"] {
    background-color: #1c1f26;
    cursor: pointer !important;
}

/* Fix text cursor bug */
.stSelectbox * {
    cursor: pointer !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# HEADER
# ----------------------------
st.title("Global Lead Generation Engine")
st.write("Discover verified business leads and decision-maker emails.")

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.title("Tools")

TRENDING_NICHES = [
    "AI automation agencies",
    "Shopify development",
    "Cybersecurity consulting",
    "EV infrastructure companies",
    "Solar installation companies",
    "Drone surveying services"
]

if st.sidebar.button("Find Profitable Niches"):
    st.sidebar.success("Trending Niches:")
    for niche in TRENDING_NICHES:
        st.sidebar.write("• " + niche)

st.sidebar.title("Recent Searches")
for item in st.session_state.recent_searches:
    if st.sidebar.button(item):
        st.experimental_rerun()

# ----------------------------
# INPUTS
# ----------------------------
col1, col2 = st.columns(2)

with col1:
    city = st.text_input("Cities (comma separated)", value="Bangalore")
    cities = [c.strip() for c in city.split(",") if c.strip()]

with col2:
    COMMON_CATEGORIES = [
        "software company", "it services", "digital marketing", "seo agency",
        "web development", "mobile app development", "saas company",
        "real estate", "construction company", "interior designers",
        "chartered accountant", "law firm", "hospital", "clinic",
        "manufacturers", "exporters", "hotel", "travel agency",
        "logistics company", "security services"
    ]

    category_choice = st.selectbox(
        "Choose Category",
        ["-- Select --"] + COMMON_CATEGORIES,
        index=0
    )

category_input = st.text_input(
    "Or type your own category",
    placeholder="Example: solar companies"
)

if category_input.strip():
    category = category_input.strip()
elif category_choice != "-- Select --":
    category = category_choice
else:
    category = ""

if category:
    st.subheader(f"Searching: {category.title()}")
    st.info(f"Engine will search sources for: {category}")
else:
    st.warning("Please select or enter a category.")

# ----------------------------
# CONTROL BUTTONS
# ----------------------------
colA, colB = st.columns(2)

with colA:
    start = st.button(
        "Start Scraping",
        disabled=st.session_state.running or not category
    )

with colB:
    if st.button("Cancel"):
        st.session_state.stop_requested = True
        st.warning("Stopping safely… finishing current task.")

# ----------------------------
# SCRAPER PROCESS
# ----------------------------
if start and not st.session_state.running:

    st.session_state.running = True
    st.session_state.stop_requested = False

    progress_bar = st.progress(0)
    status_box = st.empty()
    log_box = st.empty()

    logs = []

    def update_progress(message):
        logs.append(message)
        if len(logs) > 8:
            logs.pop(0)

        log_box.code("\n".join(logs))
        status_box.info(message)

    update_progress("🚀 Initializing engine")

    # simulate step progress
    steps = [
        "Connecting to sources",
        "Collecting company websites",
        "Extracting emails & contacts",
        "Removing duplicates",
        "Scoring leads",
        "Preparing results"
    ]

    for i, step in enumerate(steps):
        if st.session_state.stop_requested:
            status_box.error("Scraping stopped.")
            st.session_state.running = False
            st.stop()

        update_progress(step)
        progress_bar.progress((i + 1) * 10)
        time.sleep(0.2)

    # run scraper with LIVE log updates
    leads = run_global_scraper(
        cities,
        [category],
        progress_callback=update_progress,
        stop_flag=lambda: st.session_state.stop_requested
    )

    progress_bar.progress(100)
    status_box.success("✅ Scraping Complete!")

    if leads:
        leads = normalize_leads(leads)
        df = pd.DataFrame(leads)

        for col in ["Email", "Website", "UndeliverableEmails"]:
            if col not in df:
                df[col] = ""

        total_leads = len(df)

        valid_email_count = df["Email"].apply(
            lambda x: bool(str(x).strip())).sum()
        undeliverable_count = df["UndeliverableEmails"].apply(
            lambda x: bool(str(x).strip())).sum()
        website_count = df["Website"].apply(
            lambda x: bool(str(x).strip())).sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Leads", total_leads)
        c2.metric("Valid Emails ✅", valid_email_count)
        c3.metric("Undeliverable ⚠️", undeliverable_count)
        c4.metric("Websites Found 🌐", website_count)

        st.dataframe(df, use_container_width=True)

        st.download_button("Download CSV", df.to_csv(index=False), "leads.csv")

        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button("Download Excel", buffer, "leads.xlsx")

        st.session_state.recent_searches.insert(
            0, f"{category} in {', '.join(cities)}"
        )
        st.session_state.recent_searches = st.session_state.recent_searches[:5]

    else:
        st.warning("No leads found.")

    st.session_state.running = False

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.caption("Built with Python & Streamlit")
