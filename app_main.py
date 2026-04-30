import streamlit as st
from utils.theme import inject_css, inject_centrica_logo

#--- Page Setup ---

st.set_page_config(
    page_title="OTTO · Pricing Engine",
    page_icon="OTTO_Logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
         'Get Help': 'mailto:yoganath.manickavasakam@britishgas.co.uk',
         'Report a bug': 'mailto:yoganath.manickavasakam@britishgas.co.uk',
         'About': "**OTTO** — BG S&S Pricing Engine HC3.0\n\nDeveloped by Yoga Manickavasakam · yoganath.manickavasakam@britishgas.co.uk"}
)

# Inject CSS immediately after set_page_config so styles are in the first render pass
# — this prevents the unstyled flash/flicker when navigating between pages
inject_css()

about_page = st.Page(
                page = "views/about.py",
                title = "About",
                icon = ":material/info:",
                default=True,
)

upload_page = st.Page(
                page = "views/upload_section.py",
                title = "Rating & Input",
                icon = ":material/upload_file:",
)

exploration_page = st.Page(
                page = "views/exploration.py",
                title = "MI Snapshot",
                icon = ":material/analytics:",
)

reports_page = st.Page(
                page = "views/reports.py",
                title = "Reports",
                icon = ":material/insert_chart:",
)

calculation_page = st.Page(
                page = "views/calculation_section.py",
                title = "Price Engine",
                icon = ":material/tune:",
)

retention_page = st.Page(
                page = "views/retention.py",
                title = "Retention",
                icon = ":material/trending_up:",
)

download_page = st.Page(
                page = "views/download.py",
                title = "Download Results",
                icon = ":material/file_download:",
)

ask_page = st.Page(
                page = "views/ask.py",
                title = "DiagnostAIcs Lab",
                icon = ":material/smart_toy:",
)

future_projections_page = st.Page(
                page = "views/future_projections.py",
                title = "Future Projections",
                icon = ":material/trending_up:",
)


# -- NAVIGATION SETUP --

pg = st.navigation(
    {
        "Info" : [about_page],
        "Upload": [upload_page],
        "Calculate" : [calculation_page, retention_page],
        "Explore": [exploration_page, reports_page, ask_page, future_projections_page],
        "Download": [download_page]
    }
)


lines = [
    "**Developed by**",
    "Yoga Manickavasakam",
]

for line in lines:
    st.sidebar.markdown(line, unsafe_allow_html=True)

inject_centrica_logo("Centrica_home.png")

# -- Run Navigation ---
pg.run()