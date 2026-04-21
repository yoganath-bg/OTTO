import streamlit as st
import pandas as pd
from datetime import datetime

from utils.theme import page_header, section_divider, section_heading
from utils.word_report import build_run_summary_docx
from utils.constants import ENDPOINT_NAME

page_header(
    "Download Results",
    icon="&#128229;",
    subtitle="Export final premium files, SAP tables and scored data",
)

if 'premium_file' not in st.session_state:
    st.info("Please calculate prices first (Calculate page) before downloading.")
    st.stop()

premium_file   = st.session_state['premium_file']
contracts_view = st.session_state.get('contracts_view')

# Left-join retention scores onto the full files so row counts always match
premium_scored      = st.session_state.get('premium_scored')
contracts_view_scored = st.session_state.get('contracts_view_scored')

if premium_scored is not None:
    scores_product = (
        premium_scored[["business_agreement", "prob_retention", "prob_churn"]]
        .drop_duplicates("business_agreement")
    )
    premium_file_dl = premium_file.copy()
    premium_file_dl["business_agreement"] = premium_file_dl["business_agreement"].astype(str)
    scores_product["business_agreement"] = scores_product["business_agreement"].astype(str)
    premium_file_dl = premium_file_dl.merge(scores_product, on="business_agreement", how="left")
else:
    premium_file_dl = premium_file.copy()

if contracts_view is not None and contracts_view_scored is not None:
    scores_customer = (
        contracts_view_scored[["business_agreement", "prob_retention", "prob_churn"]]
        .drop_duplicates("business_agreement")
    )
    contracts_view_dl = contracts_view.copy()
    contracts_view_dl["business_agreement"] = contracts_view_dl["business_agreement"].astype(str)
    scores_customer["business_agreement"] = scores_customer["business_agreement"].astype(str)
    contracts_view_dl = contracts_view_dl.merge(scores_customer, on="business_agreement", how="left")
elif contracts_view is not None:
    contracts_view_dl = contracts_view.copy()
else:
    contracts_view_dl = None

file_labels = [
"Base_Price",
"Boiler_Type",
"Appl_Make",
"Boiler_Age",
"Rads",
"Spl_Rads",
"Claims",
"Ratearea_Boilertype",
"Ratarea_Rads",
"Rads_Claims",
"Claims_Boilertype",
"Claims_load",
"Asv_price",
"Exp_Claim_load",
"Exp_Asv_load",
"Flat_Load",
"Multi_bund_margin",
"Cap_n_Collar",
"PRD_GROUP",
"geo_pschal",
"GEO_FACHAL",
"Absolute_Capping",
"Minimum_Capping",
"Flat_Bundle_Margin"
]

col1, col2 = st.columns(2)
with col1:
    st.write("Click below to download the pricing file")
    st.download_button(
    label="Download final premium file",
    data=premium_file.to_csv(index=False),
    file_name="premium_file.csv",
    mime="text/csv"
)


with col2:
    table_name = st.selectbox("Choose SAP table to download in transformed format", options=file_labels)
    if table_name is not None:
            df = st.session_state.processed_data[table_name]
            st.download_button(
            label=f"Download {table_name} file",
            data=df.to_csv(index=False),
            file_name=f"{table_name}.csv",
            mime="text/csv"
            )

# ---------- Scored downloads ----------
section_divider()
section_heading("Download Scored Data")

if premium_scored is None:
    st.info("Run **Get Retention** on the Calculate page to enable scored downloads.")
else:
    dl1, dl2 = st.columns(2)
    with dl1:
        st.caption(f"Product file — {len(premium_file_dl):,} rows (all policies, scores joined where available)")
        st.download_button(
            label="⬇ Download Product Scored (CSV)",
            data=premium_file_dl.to_csv(index=False).encode('utf-8'),
            file_name="product_scored.csv",
            mime="text/csv",
        )
    with dl2:
        if contracts_view_dl is not None:
            st.caption(f"Customer file — {len(contracts_view_dl):,} rows (all customers, scores joined where available)")
            st.download_button(
                label="⬇ Download Customer Scored (CSV)",
                data=contracts_view_dl.to_csv(index=False).encode('utf-8'),
                file_name="customer_scored.csv",
                mime="text/csv",
            )
        else:
            st.info("No contracts view available.")

# ── Word Run Summary Report ───────────────────────────────────────────────────
section_divider()
section_heading("Run Summary Report")

st.markdown(
    "Download a Word document summarising key metrics from this pricing run — "
    "portfolio overview, price summary by pricing key, and Conduct MI results."
)

# Resolve Databricks username from the SDK (falls back gracefully if not available)
def _get_username() -> str:
    # Databricks Apps injects the authenticated user's identity via OAuth proxy
    # headers. X-Forwarded-Email carries the human-readable email; X-Forwarded-User
    # carries a numeric Databricks user ID — we use the SDK to resolve that to a name.
    user_id = None
    try:
        headers = st.context.headers  # requires Streamlit >= 1.37
        email = headers.get("X-Forwarded-Email") or headers.get("Remote-User")
        if email:
            return email
        user_id = headers.get("X-Forwarded-User")  # numeric ID e.g. "236558...@360648..."
    except AttributeError:
        pass  # older Streamlit — fall through

    try:
        from databricks.sdk import WorkspaceClient
        wc = WorkspaceClient()
        if user_id:
            # Strip the workspace segment if present (format: userId@workspaceId)
            uid = user_id.split("@")[0]
            user = wc.users.get(id=uid)
            return (
                getattr(user, "display_name", None)
                or getattr(user, "user_name",    None)
                or user_id
            )
        # Last resort: current token identity (will be service principal in Apps)
        me = wc.current_user.me()
        return getattr(me, "display_name", None) or getattr(me, "user_name", None) or "Unknown"
    except Exception:
        return user_id or "Unknown"

if st.button("Generate Run Summary (Word)", type="primary"):
    with st.spinner("Building report…"):
        try:
            username = _get_username()
            docx_bytes = build_run_summary_docx(
                premium_file     = premium_file,
                premium_scored   = premium_scored,
                processed_data   = st.session_state.get("processed_data", {}),
                endpoint_name    = ENDPOINT_NAME,
                prepared_by      = username,
                prepared_at      = datetime.now(),
            )
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label     = "⬇ Download Run Summary (.docx)",
                data      = docx_bytes,
                file_name = f"OTTO_Run_Summary_{ts}.docx",
                mime      = "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        except ImportError as e:
            st.error(f"Report generator import error: {e}")
        except Exception as e:
            st.error(f"Failed to generate report: {e}")