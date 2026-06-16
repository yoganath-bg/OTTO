import streamlit as st
import pandas as pd
from datetime import date, timedelta

from utils.ui_helpers import normalize_columns
from utils.theme import page_header, section_divider, section_heading, render_table

page_header(
    "Rating &amp; Input",
    icon="&#128190;",
    subtitle="Upload rating factor tables and input risk data",
)

# ── Section 1: Upload Rating Factors ─────────────────────────────────────────
section_heading("1 · Upload Rating Factors")

# Initialize session state containers
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'all_sheets_raw' not in st.session_state:
    # this will hold the raw read from Excel: {sheet_name: DataFrame}
    st.session_state.all_sheets_raw = {}
if 'processed_data' not in st.session_state:
    # this will hold final processed sheets (for now identical to raw)
    st.session_state.processed_data = {}

# File uploader (single Excel file or single CSV)
uploaded = st.file_uploader("Upload an Excel file (all sheets will be listed)", type=["xls", "xlsx", "csv"])
if uploaded is not None:
    st.session_state.uploaded_file = uploaded

    # Try reading all sheets (handle CSV as single-sheet)
    try:
        name_lower = uploaded.name.lower()
        if name_lower.endswith('.csv'):
            # read single csv into a single-entry dict, sheet name = filename without extension
            sheet_name = uploaded.name.rsplit('.', 1)[0]
            df = pd.read_csv(st.session_state.uploaded_file)
            st.session_state.all_sheets_raw = {sheet_name: df}
        else:
            # read all sheets from Excel file
            all_sheets = pd.read_excel(st.session_state.uploaded_file, sheet_name=None)
            st.session_state.all_sheets_raw = all_sheets  # store raw sheets

        st.success(f"Following {len(st.session_state.all_sheets_raw)} table(s) are loaded: {list(st.session_state.all_sheets_raw.keys())}")
    except Exception as e:
        st.session_state.all_sheets_raw = {}
        st.error(f"Failed to read file: {e}")

# If we have sheets, let the user select which to process
if st.session_state.all_sheets_raw:
    sheet_names = list(st.session_state.all_sheets_raw.keys())
    selected = st.multiselect("Select sheets to process (leave empty to select all)", sheet_names, default=sheet_names)

    if st.button("Process selected sheets"):
        # Ensure we always store a DataFrame (never None)
        for sheet in selected:
            try:
                df = st.session_state.all_sheets_raw.get(sheet)
                if isinstance(df, pd.DataFrame):
                    # Normalize column headers to lowercase + underscores
                    df_normalized = normalize_columns(df)
                    # store the normalized copy into processed_data
                    st.session_state.processed_data[sheet] = df_normalized.copy()
                else:
                    # If sheet exists but isn't a DataFrame (unlikely), store empty DF
                    st.session_state.processed_data[sheet] = pd.DataFrame()
            except Exception as e:
                # On error, store an empty dataframe and report
                st.session_state.processed_data[sheet] = pd.DataFrame()
                st.error(f"Error processing sheet '{sheet}': {e}")

        st.success(f"{len(selected)} Rating table(s) are processed for further calculation")

# Preview & download processed sheets
if st.session_state.processed_data:
    sheet_to_view = st.selectbox("Preview processed sheet", ["-- none --"] + list(st.session_state.processed_data.keys()))
    if sheet_to_view != "-- none --":
        df_to_show = st.session_state.processed_data.get(sheet_to_view)
        # Defensive checks
        if df_to_show is None:
            st.warning(f"'{sheet_to_view}' has not been saved yet.")
        elif not isinstance(df_to_show, pd.DataFrame):
            st.error(f"Unexpected type for '{sheet_to_view}': {type(df_to_show)}")
        elif df_to_show.empty:
            st.info(f"'{sheet_to_view}' is saved but empty.")
            render_table(df_to_show)
        else:
            render_table(df_to_show.head(200))
            csv = df_to_show.to_csv(index=False).encode('utf-8')
            st.download_button(label=f"Download {sheet_to_view} (CSV)", data=csv, file_name=f"{sheet_to_view}_processed.csv", mime="text/csv")


section_divider()

# ── Section 2: Fetch Input Risk Data ─────────────────────────────────────────
section_heading("2 · Fetch Input Risk Data")

st.info(
    "**Performance Advisory** — For optimal query performance and accurate pricing outputs, "
    "we recommend limiting your renewal date range to a maximum of **2 months** per session. "
    "Larger datasets may result in slower load times and increased memory usage.",
    icon="ℹ️",
)

data_source = st.radio(
    "Select data source",
    options=["Fetch from Unity Catalog", "Upload CSV File"],
    horizontal=True,
)

_HTTP_PATH  = "/sql/1.0/warehouses/60555e50c3fecff0"
_TABLE_NAME = "dap_bgss_prd.ana_p_pricing.HC_renewals_model_input_test"

if data_source == "Fetch from Unity Catalog":
    # Default date range: previous calendar month
    _today      = date.today()
    _first_prev = (_today.replace(day=1) - timedelta(days=1)).replace(day=1)
    _last_prev  = _today.replace(day=1) - timedelta(days=1)

    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("Renewal Start Date", value=_first_prev)
    with date_col2:
        end_date = st.date_input("Renewal End Date", value=_last_prev)

    if st.button("Fetch", type="primary"):
        if start_date > end_date:
            st.error("Start date must be on or before the end date.")
        else:
            try:
                from databricks import sql as dbsql
                from databricks.sdk import WorkspaceClient

                w    = WorkspaceClient()  # picks up Databricks Apps OAuth automatically
                host = w.config.host.replace("https://", "").rstrip("/")
                # Resolve auth headers and extract the Bearer token
                auth_headers  = w.config.authenticate()
                access_token  = auth_headers.get("Authorization", "").replace("Bearer ", "")

                with st.spinner("Fetching data from Unity Catalog…"):
                    with dbsql.connect(
                        server_hostname=host,
                        http_path=_HTTP_PATH,
                        access_token=access_token,
                    ) as conn:
                        with conn.cursor() as cursor:
                            query = f"""
                                SELECT *
                                FROM {_TABLE_NAME}
                                WHERE renewal_Date BETWEEN '{start_date}' AND '{end_date}'
                            """
                            cursor.execute(query)
                            rows    = cursor.fetchall()
                            columns = [desc[0] for desc in cursor.description]

                    input_risk = pd.DataFrame(rows, columns=columns)
                    # Databricks SQL connector returns decimal.Decimal for numeric cols;
                    # convert all such columns to native float so downstream arithmetic works.
                    input_risk = input_risk.apply(lambda s: pd.to_numeric(s, errors='ignore'))
                    st.session_state['input_risk'] = input_risk

                    st.success(
                        f"Data fetched successfully — **{len(input_risk):,} rows** "
                        f"for renewal dates {start_date} to {end_date}."
                    )

                    # Summary by pricing_key
                    summary = (
                        input_risk
                        .groupby("pricing_key", as_index=False)
                        .agg(
                            Volume=("pricing_key", "count"),
                            current_customer_price=("ly_customer_price", "mean"),
                            current_undiscounted_price=("ly_undiscounted_price", "mean"),
                        )
                        .round({"current_customer_price": 2, "current_undiscounted_price": 2})
                        .sort_values("pricing_key")
                        .reset_index(drop=True)
                    )
                    summary["current_customer_price"]      = summary["current_customer_price"].map(lambda v: f"£{v:,.2f}")
                    summary["current_undiscounted_price"] = summary["current_undiscounted_price"].map(lambda v: f"£{v:,.2f}")
                    st.markdown("**Renewal Portfolio Overview · by Pricing Key**")
                    render_table(summary)

                    st.markdown("**Data Preview**")
                    st.caption("A snapshot of the fetched dataset to verify data quality before proceeding to the Price Engine.")
                    render_table(input_risk.head(5))

                    st.download_button(
                        label="Download input data (CSV)",
                        data=input_risk.to_csv(index=False).encode("utf-8"),
                        file_name=f"input_risk_{start_date}_to_{end_date}.csv",
                        mime="text/csv",
                    )

            except Exception as exc:
                import traceback
                st.error(f"Failed to fetch data: {exc}")
                st.code(traceback.format_exc(), language="text")

elif data_source == "Upload CSV File":
    risk_csv = st.file_uploader(
        "Upload input risk data as a flat CSV file",
        type=["csv"],
        key="input_risk_csv",
    )
    if risk_csv is not None:
        try:
            with st.spinner("Loading CSV…"):
                input_risk = pd.read_csv(risk_csv)
                input_risk = input_risk.apply(lambda s: pd.to_numeric(s, errors='ignore'))
                st.session_state['input_risk'] = input_risk

            st.success(f"CSV loaded successfully — **{len(input_risk):,} rows**.")

            # Summary by pricing_key
            summary = (
                input_risk
                .groupby("pricing_key", as_index=False)
                .agg(
                    Volume=("pricing_key", "count"),
                    current_customer_price=("ly_customer_price", "mean"),
                    current_undiscounted_price=("ly_undiscounted_price", "mean"),
                )
                .round({"current_customer_price": 2, "current_undiscounted_price": 2})
                .sort_values("pricing_key")
                .reset_index(drop=True)
            )
            summary["current_customer_price"]      = summary["current_customer_price"].map(lambda v: f"£{v:,.2f}")
            summary["current_undiscounted_price"] = summary["current_undiscounted_price"].map(lambda v: f"£{v:,.2f}")
            st.markdown("**Renewal Portfolio Overview · by Pricing Key**")
            render_table(summary)

            st.markdown("**Data Preview**")
            st.caption("A snapshot of the uploaded dataset to verify data quality before proceeding to the Price Engine.")
            render_table(input_risk.head(5))

        except Exception as exc:
            import traceback
            st.error(f"Failed to load CSV: {exc}")
            st.code(traceback.format_exc(), language="text")

if 'input_risk' in st.session_state:
    st.info(f"Input risk data currently loaded: {len(st.session_state['input_risk']):,} rows.")