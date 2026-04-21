import streamlit as st
from utils.theme import page_header, section_divider, section_heading

page_header(
    "About OTTO",
    icon="&#128202;",
    subtitle="BG S&amp;S Pricing Engine · Home Care 3.0",
)

st.markdown("""
OTTO is an **internal pricing engine** built to generate HC3.0 product prices for Home Care
products using the BG S&amp;S rating structure. Designed for pricing analysts — fast, auditable,
and integrated with retention modelling.
""", unsafe_allow_html=True)

section_divider()
section_heading("Advantages")

st.markdown("""
- **Simple workflow** — structured pages guide you from upload to download in minutes.
- **Live Exploration** — interactive MI Snapshot and Reports pages update as you calculate.
- **Retention Modelling** — integrated Databricks model endpoint scores every policy.
- **One-click Download** — final premiums, SAP tables and scored data available instantly.
- **Conduct MI** — built-in loss ratio and COR monitoring against configurable thresholds.
""")

section_divider()
section_heading("How to use")

st.markdown("""
1. **Rating &amp; Input** — Upload your unformatted SAP rating tables (Excel) and input risk file (CSV).
2. **Price Engine** — Review constraints, calculate prices, and refine with the recalculate option.
3. **Retention** — Score your book against the Databricks retention model endpoint.
4. **MI Snapshot** — View KPI scorecards by product and customer, plus Conduct MI compliance metrics.
5. **Reports** — Explore interactive price distribution, YoY movement, and retention charts.
6. **Download** — Export final premium files, SAP tables and scored data.
""", unsafe_allow_html=True)

section_divider()
section_heading("Notes")

st.markdown("""
- No cell should be left empty — fill with `0` or an appropriate default.
- Rating factor tables must be uploaded in **Excel** format.
- Input risk data must be uploaded in **CSV** format.
- Thresholds (LR, COR) in the cost sheet should be supplied as **decimals** (e.g. `0.45` = 45 %).
""")

st.markdown(
    "<p style='color:#6b7280; font-size:0.78rem; margin-top:2rem;'>"
    "Contact: <a href='mailto:yoganath.manickavasakam@britishgas.co.uk' style='color:#0f2067;'>"
    "yoganath.manickavasakam@britishgas.co.uk</a></p>",
    unsafe_allow_html=True,
)

