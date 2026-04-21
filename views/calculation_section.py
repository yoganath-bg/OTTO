import numpy as np
import pandas as pd
import streamlit as st

from utils.constants import COLUMNS_FOR_ANALYSIS, RENAME_MAPS
from utils.pricing_engine import _ci_col, build_constraints_df, calculate_prices, sheet_to_varname
from utils.summary import compute_yoy
from utils.bundle_view import build_contracts_view
from utils.theme import page_header, section_divider, section_heading, render_table

page_header(
    "Price Engine",
    icon="&#9881;&#65039;",
    subtitle="Review constraints, calculate ratings and view summary outputs",
)


# Defensive default
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = {}

# sheet_to_varname and RENAME_MAPS are imported from utils.pricing_engine / utils.constants

created_vars = {}  # track created variable names -> original sheet name

for sheet_name, val in st.session_state.processed_data.items():
    # accept only real DataFrames that are not empty
    if not isinstance(val, pd.DataFrame):
        continue
    if val.empty:
        continue

    try:
        df = val.copy()
    except Exception:
        # best-effort conversion if copy fails
        try:
            df = pd.DataFrame(val)
        except Exception:
            continue

    # Apply rename mapping for this sheet if provided
    rename_map = RENAME_MAPS.get(sheet_name)
    if rename_map:
        # Only rename columns that actually exist (avoid KeyError)
        cols_to_rename = {old: new for old, new in rename_map.items() if old in df.columns}
        if cols_to_rename:
            try:
                df = df.rename(columns=cols_to_rename)
            except Exception as e:
                st.error(f"Failed to rename columns for sheet '{sheet_name}': {e}")

    # Build sanitized variable name
    varname = sheet_to_varname(sheet_name)

    # Avoid overwriting an existing global variable unintentionally
    if varname in globals():
        st.warning(f"Variable name collision: '{varname}' already exists in globals(). Skipping sheet '{sheet_name}'.")
        continue

    # Inject into globals and record it
    globals()[varname] = df
    created_vars[varname] = sheet_name

# UI summary of created variables
if created_vars:
    st.success(f"Loaded {len(created_vars)} Rating Table(s).")
    #with st.expander("Created DataFrame variables (var_name -> sheet_name)"):
        #st.write(created_vars)
else:
    st.info("No Rating table was loaded/ processed — please go back to 'Upload Section'")


# Helper to safely fetch a dataframe from globals() and ensure it's a DataFrame
def _get_df(varname):
    df = globals().get(varname)
    if isinstance(df, pd.DataFrame):
        return df.copy()
    return None

# _ci_col is imported from utils.pricing_engine

base   = _get_df('base_price_df')
asv    = _get_df('asv_price_df')
caps   = _get_df('caps_collar_df')
minmax = _get_df('min_max_df')

# Basic existence checks
if base is None or base.empty:
    st.error("Ensure you uploaded base price and caps and collars.")
else:
    # Ensure pricing_key exists
    if _ci_col(base, 'pricing_key') is None:
        st.error("base_price_df must contain a 'pricing_key' column.")
    else:
        constraints_df = build_constraints_df(base, asv, caps, minmax)


# First row (2 questions)
col1, col2 = st.columns(2)
with col1:
    pass
with col2:
    pass

# input_risk is uploaded on the 'Rating & Input' page and stored in session_state
input_risk = st.session_state.get('input_risk')
if input_risk is None:
    st.info("Please upload and validate your Input Risk data on the **Rating & Input** page first.")


# ---------- Editable constraints table UI with protected columns + auto-recalc ----------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Constraints Table \n (pricing_key & bundle are protected)")

    # expected numeric columns used elsewhere
    expected = ['f_base_price', 'f_asv_price', 'f_collar', 'f_cap', 'f_min', 'f_max']

    # ensure constraints_df exists
    if 'constraints_df' not in globals():
        st.info("Please upload the rating table")
    else:
        original = constraints_df.copy()

        # show editor (user can try to edit anything)
        edited = st.data_editor(
            original,
            num_rows="dynamic",
            use_container_width=True
        )

        # buttons below the editor
        col_download, _ = st.columns([1, 2])
        with col_download:
            csv = edited.to_csv(index=False).encode('utf-8')
            st.download_button("Download edited (CSV)", data=csv, file_name="constraints_edited.csv", mime="text/csv")

    # show status
    if 'constraints_df' in st.session_state:
        st.info("Constraint(s) updated and saved. Use that for downstream calculations.")
    else:
        st.write("No saved edits yet — click **Save edits** to persist changes.")


with col2:
    pass  # constraints table occupies col1; summaries are shown below
# ---------- end constraints block ----------

# ---------- Calculate Prices button ----------
_src = st.session_state.get('input_risk')
_cdf = globals().get('constraints_df')
if _cdf is None:
    _cdf = st.session_state.get('constraints_df')

if st.button('Calculate Prices', type='primary'):
    if _src is None:
        st.error("Upload and validate your Input Risk data first (Rating & Input page).")
    elif _cdf is None:
        st.error("No constraints table found. Upload the rating table first.")
    else:
        # Enforce protected columns from current editor state
        _edited = globals().get('edited')
        if _edited is not None:
            _protected = ['pricing_key']
            if 'bundle' in _cdf.columns:
                _protected.append('bundle')
            _changes = []
            for _c in _protected:
                _ov = _cdf[_c].astype(str).fillna('')
                _nv = _edited[_c].astype(str).fillna('') if _c in _edited.columns else pd.Series(['']*len(_cdf))
                if not _ov.equals(_nv):
                    _changes.append(_c)
            if _changes:
                for _c in _changes:
                    _edited[_c] = _cdf[_c].values
                st.warning(f"Protected column(s) restored to original values: {', '.join(_changes)}")
            _expected = ['f_base_price', 'f_asv_price', 'f_collar', 'f_cap', 'f_min', 'f_max']
            for _c in _expected:
                if _c in _edited.columns:
                    _edited[_c] = pd.to_numeric(_edited[_c], errors='coerce').fillna(0.0).astype(float)
                else:
                    _edited[_c] = 0.0
            st.session_state['constraints_df'] = _edited.copy()
            globals()['constraints_df'] = _edited.copy()
            _cdf = _edited.copy()

        with st.spinner('Calculating prices…'):
            try:
                _pf = calculate_prices(
                    _src,
                    _cdf,
                    globals().get('boiler_type_df'),
                    globals().get('manufacturer_df'),
                    globals().get('postal_sector_df'),
                    globals().get('radiators_df'),
                    globals().get('boiler_age_df'),
                    globals().get('tenure_discount_df'),
                )
                st.session_state['premium_file'] = _pf
                _avail = [c for c in COLUMNS_FOR_ANALYSIS if c in _pf.columns]
                st.session_state['summary_file'] = _pf[_avail].copy()
                st.session_state['contracts_view'] = build_contracts_view(_pf)
                st.session_state.pop('retention_summary', None)
                st.session_state.pop('premium_scored', None)
                st.session_state.pop('contracts_view_scored', None)
                st.success(f"Prices calculated successfully for {len(_pf):,} policies!")
            except Exception as _e:
                st.error(f"Error calculating prices: {_e}")

# ---------- Summary Tables (Product Summary | Customer Summary) ----------
smry_col1, smry_col2 = st.columns(2)

with smry_col1:
    st.subheader("Product Summary")

    # compute_yoy is imported from utils.summary
    if 'summary_file' in st.session_state and isinstance(st.session_state['summary_file'], pd.DataFrame) and not st.session_state['summary_file'].empty:
        try:
            render_table(compute_yoy(st.session_state['summary_file']))
        except Exception as e:
            st.error(f"Error generating Product Summary: {e}")
    else:
        st.info("Product Summary will appear after calculation.")

with smry_col2:
    st.subheader("Customer Summary")

    # build_contracts_view is imported from utils.bundle_view
    if 'contracts_view' in st.session_state and isinstance(st.session_state['contracts_view'], pd.DataFrame) and not st.session_state['contracts_view'].empty:
        try:
            render_table(
                compute_yoy(
                    st.session_state['contracts_view'],
                    group_col=["product_bundle", "bundle_excess"],
                    final_col="bundle_Final_Premium",
                    ly_col="bundle_customer_price",
                ),
            )
        except Exception as e:
            st.error(f"Error generating Customer Summary: {e}")
    else:
        st.info("Customer Summary will appear after calculation.")



# --- END OF PAGE ---
st.stop()