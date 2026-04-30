import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.pricing_engine import calculate_future_projections
from utils.theme import page_header, render_table, section_divider, section_heading

page_header(
    "Future Projections",
    icon="&#128200;",
    subtitle="5-year projected premium outlook · adjust inflation and ASV assumptions per pricing key",
)

# ── Guard ─────────────────────────────────────────────────────────────────────
if "input_risk_clean" not in st.session_state:
    st.info(
        "Please **Calculate Prices** first (Calculate → Price Engine) to enable future projections."
    )
    st.stop()

input_risk_clean       = st.session_state["input_risk_clean"]
projection_constraints = st.session_state["projection_constraints"]
boiler_type_df         = st.session_state.get("_proj_boiler_type_df")
manufacturer_df        = st.session_state.get("_proj_manufacturer_df")
postal_sector_df       = st.session_state.get("_proj_postal_sector_df")
radiators_df           = st.session_state.get("_proj_radiators_df")
boiler_age_df          = st.session_state.get("_proj_boiler_age_df")
tenure_discount_df     = st.session_state.get("_proj_tenure_discount_df")

# ── Build default assumption tables from the constraints ──────────────────────
pricing_keys = sorted(projection_constraints["pricing_key"].dropna().unique().tolist())

# Default inflation table: one row per pricing_key, all %s = 0.0
_default_inflation = pd.DataFrame(
    {
        "pricing_key": pricing_keys,
        "Y2_%": [0.0] * len(pricing_keys),
        "Y3_%": [0.0] * len(pricing_keys),
        "Y4_%": [0.0] * len(pricing_keys),
        "Y5_%": [0.0] * len(pricing_keys),
    }
)

# Default ASV table: one row per pricing_key, current f_asv_price as Y1 default
_asv_base = (
    projection_constraints[["pricing_key", "f_asv_price"]]
    .drop_duplicates("pricing_key")
    .rename(columns={"f_asv_price": "ASV_Y1"})
)
_asv_base = _asv_base.set_index("pricing_key").reindex(pricing_keys).reset_index()
_asv_base["ASV_Y1"] = pd.to_numeric(_asv_base["ASV_Y1"], errors="coerce").fillna(0.0)
_default_asv = _asv_base.copy()
for _y in [2, 3, 4, 5]:
    _default_asv[f"ASV_Y{_y}"] = _default_asv["ASV_Y1"]

# ── Assumption editors ────────────────────────────────────────────────────────
with st.expander("Inflation & ASV Assumptions", expanded=True):
    col_l, col_r = st.columns(2)

    with col_l:
        section_heading("Inflation Schedule")
        st.caption(
            "Each year's % is compounded on top of the previous year's adjusted base. "
            "Applies to base_price, min and max premium."
        )
        inflation_pct_cols = {"Y2_%": 0.0, "Y3_%": 0.0, "Y4_%": 0.0, "Y5_%": 0.0}
        edited_inflation = st.data_editor(
            _default_inflation,
            num_rows="fixed",
            use_container_width=True,
            disabled=["pricing_key"],
            column_config={
                "pricing_key": st.column_config.TextColumn("Pricing Key"),
                "Y2_%": st.column_config.NumberColumn("Y2 Inflation %", min_value=-100.0, max_value=1000.0, step=0.1, format="%.2f"),
                "Y3_%": st.column_config.NumberColumn("Y3 Inflation %", min_value=-100.0, max_value=1000.0, step=0.1, format="%.2f"),
                "Y4_%": st.column_config.NumberColumn("Y4 Inflation %", min_value=-100.0, max_value=1000.0, step=0.1, format="%.2f"),
                "Y5_%": st.column_config.NumberColumn("Y5 Inflation %", min_value=-100.0, max_value=1000.0, step=0.1, format="%.2f"),
            },
            key="proj_inflation_editor",
        )

    with col_r:
        section_heading("ASV Price Schedule")
        st.caption(
            "ASV_Y1 shows current values (read-only). "
            "Edit Y2–Y5 to override the ASV price per pricing key per year."
        )
        edited_asv = st.data_editor(
            _default_asv,
            num_rows="fixed",
            use_container_width=True,
            disabled=["pricing_key", "ASV_Y1"],
            column_config={
                "pricing_key": st.column_config.TextColumn("Pricing Key"),
                "ASV_Y1": st.column_config.NumberColumn("ASV Y1 (current)", format="£%.2f"),
                "ASV_Y2": st.column_config.NumberColumn("ASV Y2 (£)", min_value=0.0, step=0.01, format="£%.2f"),
                "ASV_Y3": st.column_config.NumberColumn("ASV Y3 (£)", min_value=0.0, step=0.01, format="£%.2f"),
                "ASV_Y4": st.column_config.NumberColumn("ASV Y4 (£)", min_value=0.0, step=0.01, format="£%.2f"),
                "ASV_Y5": st.column_config.NumberColumn("ASV Y5 (£)", min_value=0.0, step=0.01, format="£%.2f"),
            },
            key="proj_asv_editor",
        )

# ── Calculate button ──────────────────────────────────────────────────────────
if st.button("Calculate Future Projections", type="primary"):
    # Rename inflation columns to match engine expectations
    infl_df = edited_inflation.rename(columns={
        "Y2_%": "Y2_pct", "Y3_%": "Y3_pct", "Y4_%": "Y4_pct", "Y5_%": "Y5_pct",
    })
    asv_df = edited_asv.copy()

    with st.spinner("Projecting premiums for Years 1–5…"):
        try:
            proj = calculate_future_projections(
                input_risk_base=input_risk_clean,
                constraints_df=projection_constraints,
                boiler_type_df=boiler_type_df,
                manufacturer_df=manufacturer_df,
                postal_sector_df=postal_sector_df,
                radiators_df=radiators_df,
                boiler_age_df=boiler_age_df,
                tenure_discount_df=tenure_discount_df,
                inflation_df=infl_df,
                asv_future_df=asv_df,
            )
            st.session_state["future_projections"] = proj
            st.success(f"Projections calculated for {len(proj):,} policies across 5 years.")
        except Exception as _e:
            st.error(f"Error calculating projections: {_e}")

# ── Results ───────────────────────────────────────────────────────────────────
if "future_projections" not in st.session_state:
    st.stop()

proj = st.session_state["future_projections"]
year_fp_cols = [f"Final_Premium_Y{y}" for y in range(1, 6) if f"Final_Premium_Y{y}" in proj.columns]

if not year_fp_cols:
    st.warning("No Final_Premium columns found in projection results.")
    st.stop()

section_divider()
section_heading("Average Final Premium by Pricing Key · Year 1 – 5")

# ── Aggregate summary table ───────────────────────────────────────────────────
agg = (
    proj.groupby("pricing_key")[year_fp_cols]
    .mean()
    .round(2)
    .reset_index()
)
agg.columns = ["Pricing Key"] + [f"Year {y}" for y in range(1, len(year_fp_cols) + 1)]

# Format as £
for c in agg.columns[1:]:
    agg[c] = agg[c].apply(lambda x: f"£{x:,.2f}" if pd.notna(x) else "—")

render_table(agg)

section_divider()
section_heading("Premium Trend · Avg Final Premium per Pricing Key")

# ── Line chart ────────────────────────────────────────────────────────────────
# Rebuild numeric agg for charting
agg_num = (
    proj.groupby("pricing_key")[year_fp_cols]
    .mean()
    .reset_index()
)
agg_num.columns = ["pricing_key"] + [f"Y{y}" for y in range(1, len(year_fp_cols) + 1)]

_PALETTE = [
    "#0f2067", "#85db9c", "#a50091", "#b999f6", "#d03e9d",
    "#1a56db", "#e74c3c", "#f39c12", "#27ae60", "#8e44ad",
]

fig = go.Figure()
for i, pk in enumerate(sorted(agg_num["pricing_key"].unique())):
    row = agg_num[agg_num["pricing_key"] == pk].iloc[0]
    years = [f"Year {y}" for y in range(1, len(year_fp_cols) + 1)]
    values = [row.get(f"Y{y}", None) for y in range(1, len(year_fp_cols) + 1)]
    fig.add_trace(go.Scatter(
        x=years,
        y=values,
        name=pk,
        mode="lines+markers",
        line=dict(color=_PALETTE[i % len(_PALETTE)], width=2),
        marker=dict(size=8),
        hovertemplate=f"<b>{pk}</b><br>%{{x}}: £%{{y:,.2f}}<extra></extra>",
    ))

fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Avg Final Premium (£)",
    yaxis_tickprefix="£",
    height=420,
    margin=dict(t=20, b=60, l=60, r=20),
    legend=dict(orientation="h", y=1.12),
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

section_divider()
section_heading("Download Detailed Projections (Policy Level)")

# ── Build download file ───────────────────────────────────────────────────────
# Include boiler_age_1..5, tenure_1..5, Final_Premium_Y1..Y5 alongside identifiers
_id_cols = [c for c in ["pricing_key", "bundle", "business_agreement", "contract_id", "contract_start_date"] if c in proj.columns]
_age_cols = [f"boiler_age_{y}" for y in range(1, 6) if f"boiler_age_{y}" in proj.columns]
_ten_cols = [f"tenure_{y}" for y in range(1, 6) if f"tenure_{y}" in proj.columns]

download_df = proj[_id_cols + _age_cols + _ten_cols + year_fp_cols].copy()

# Format £ columns in download (keep numeric — CSV is for analysis)
_csv_buffer = io.BytesIO()
download_df.to_csv(_csv_buffer, index=False)
_csv_bytes = _csv_buffer.getvalue()

st.download_button(
    label="Download Detailed Projections (CSV)",
    data=_csv_bytes,
    file_name="future_projections_detail.csv",
    mime="text/csv",
)

st.caption(
    f"File contains {len(download_df):,} rows × {len(download_df.columns)} columns — "
    "policy identifiers, boiler age & tenure per year, and Final Premium Y1–Y5."
)
