import streamlit as st
import pandas as pd

st.title("Upload Rating Factors ⬆️")

st.markdown("""<hr style="border: 1px solid #0093f5; margin: 20px 0;">""", unsafe_allow_html=True)

# Initialize session state containers
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'all_sheets_raw' not in st.session_state:
    # this will hold the raw read from Excel: {sheet_name: DataFrame}
    st.session_state.all_sheets_raw = {}
if 'processed_data' not in st.session_state:
    # this will hold final processed sheets (for now identical to raw)
    st.session_state.processed_data = {}

# helper to normalise column names
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # ensure columns are strings first
    df.columns = df.columns.astype(str)
    # strip, replace whitespace runs with underscore, lower-case
    df.columns = df.columns.str.strip().str.replace(r'\s+', '_', regex=True).str.lower()
    return df

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
            st.dataframe(df_to_show)
        else:
            st.dataframe(df_to_show.head(200))
            csv = df_to_show.to_csv(index=False).encode('utf-8')
            st.download_button(label=f"Download {sheet_to_view} (CSV)", data=csv, file_name=f"{sheet_to_view}_processed.csv", mime="text/csv")