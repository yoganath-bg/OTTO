import re
import streamlit as st
import pandas as pd
from datetime import date

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

# ── Section 2: Upload Input Risk Data ────────────────────────────────────────
section_heading("2 · Upload Input Risk Data")

upl_col1, upl_col2 = st.columns(2)

with upl_col1:
    st.markdown("**Upload your input table**")
    input_file = st.file_uploader(label='', help='Upload your input risk CSV', label_visibility="visible", key="input_risk_uploader")

    if input_file is not None:
        input_file.seek(0)
        input_risk_preview = pd.read_csv(input_file, encoding='utf-8', sep=',')

        if st.button('Validate'):
            try:
                input_file.seek(0)
                input_risk = pd.read_csv(input_file, encoding='utf-8', sep=',')
                st.session_state['input_risk'] = input_risk
                st.write(f"**Number of rows in your file**: {input_risk.shape[0]}")
                st.write(f"**Number of columns in your file**: {input_risk.shape[1]}")
                st.subheader("Check your uploaded File:")
                render_table(input_risk.head())
            except Exception as e:
                st.error(f"Error validating the file: {e}")

    if 'input_risk' in st.session_state:
        st.success(f"Input risk data loaded: {len(st.session_state['input_risk']):,} rows.")

with upl_col2:
    st.markdown("**SQL code for input data**")

    sql_col1, sql_col2 = st.columns(2)
    with sql_col1:
        start_date = st.date_input("Select Renewal Start Date", value=date(2024, 11, 1))
    with sql_col2:
        end_date = st.date_input("Select Renewal End Date", value=date(2024, 11, 30))

    with open("views/HC_3.0_data_input.sql", "r") as f:
        sql_template = f.read()

    sql_filled = re.sub(r"SET hivevar:start_date=\d{4}-\d{2}-\d{2};",
                        f"SET hivevar:start_date={start_date};", sql_template)
    sql_filled = re.sub(r"SET hivevar:end_date=\d{4}-\d{2}-\d{2};",
                        f"SET hivevar:end_date={end_date};", sql_filled)

    st.download_button(
        label="Download SQL File",
        data=sql_filled,
        file_name="dynamic_query.sql",
        mime="text/sql"
    )