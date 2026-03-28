import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import date
import joblib

st.title("Generate Prices 📱")

st.markdown("""   
    <hr style="border: 1px solid #0093f5; margin: 20px 0;">
""", unsafe_allow_html=True)


# Defensive default
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = {}

# Helper to convert sheet name into safe python variable name + _df suffix
def sheet_to_varname(name: str) -> str:
    v = name.strip().lower()
    v = re.sub(r'\W+', '_', v)        # replace non-alnum with underscore
    v = re.sub(r'^_+', '', v)         # remove leading underscores
    v = re.sub(r'_+$', '', v)         # remove trailing underscores
    if not v:
        v = "sheet"
    return f"{v}_df"

# === Your rename mappings per sheet (edit/add as needed) ===
# Keys must match the sheet names in st.session_state.processed_data
RENAME_MAPS = {
    "Base_Price":      {"price": "f_base_price"},
    "ASV_Price":       {"price": "f_asv_price"},
    "Boiler_Type":     {"value": "f_boiler_type"},
    "Manufacturer":    {"value": "f_manufacturer"},
    "Postal_Sector":   {"value": "f_postal_sector"},
    "Radiators":       {"value": "f_radiators"},
    "Boiler_age":      {"value": "f_boiler_age"},
    "Tenure_Discount": {"value": "f_tenure_discount"},
    "Caps_Collar":     {"collar": "f_collar", "cap": "f_cap"},
    "Min_Max":         {"maximum_premium": "f_max", "minimum_premium": "f_min"}
}
# =========================================================

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

def _ci_col(df, colname):
    """Return the actual column name from df that matches colname case-insensitive, or None."""
    if df is None:
        return None
    for c in df.columns:
        if str(c).strip().lower() == colname.strip().lower():
            return c
    return None

base = _get_df('base_price_df')
asv = _get_df('asv_price_df')
caps = _get_df('caps_collar_df')
minmax = _get_df('min_max_df')

# Basic existence checks
if base is None or base.empty:
    st.error("Ensure you uploaded base price and caps and collars.")
else:
    # Ensure pricing_key exists
    if _ci_col(base, 'pricing_key') is None:
        st.error("base_price_df must contain a 'pricing_key' column.")
    else:
        # find actual column names (case-insensitive)
        pk_col = _ci_col(base, 'pricing_key')
        bundle_col = _ci_col(base, 'bundle')  # may be None

        # Start from base_price_df selecting pricing_key + f_base_price if present
        cols = [pk_col]
        base_copy = base.copy()
        # find base price col name (case-insensitive)
        base_price_col = _ci_col(base_copy, 'f_base_price') or _ci_col(base_copy, 'price')
        if base_price_col:
            # if it's 'price', rename to 'f_base_price' for uniformity
            if base_price_col != 'f_base_price':
                base_copy = base_copy.rename(columns={base_price_col: 'f_base_price'})
            cols.append('f_base_price')
        else:
            base_copy['f_base_price'] = 0.0
            cols.append('f_base_price')

        # include bundle column if present
        if bundle_col:
            # rename to 'bundle' for consistent downstream name if needed
            if bundle_col != 'bundle':
                base_copy = base_copy.rename(columns={bundle_col: 'bundle'})
            cols.append('bundle')

        # build initial constraints df
        constraints_df = base_copy[cols].drop_duplicates(subset=[pk_col,bundle_col],).copy()
        # ensure the primary pricing_key column is named 'pricing_key' consistently
        if pk_col != 'pricing_key':
            constraints_df = constraints_df.rename(columns={pk_col: 'pricing_key'})

        # Merge ASV
        if asv is not None and _ci_col(asv, 'pricing_key') is not None:
            asv_pk = _ci_col(asv, 'pricing_key')
            if _ci_col(asv, 'f_asv_price') is None and _ci_col(asv, 'price') is not None:
                asv = asv.rename(columns={_ci_col(asv, 'price'): 'f_asv_price'})
            if _ci_col(asv, 'f_asv_price') is not None:
                asv = asv.rename(columns={asv_pk: 'pricing_key'})
                constraints_df = constraints_df.merge(asv[['pricing_key', 'f_asv_price']].drop_duplicates('pricing_key'),
                                                      on='pricing_key', how='left')

        # Merge Caps & Collar
        if caps is not None and _ci_col(caps, 'pricing_key') is not None:
            caps_pk = _ci_col(caps, 'pricing_key')
            if _ci_col(caps, 'f_collar') is None and _ci_col(caps, 'collar') is not None:
                caps = caps.rename(columns={_ci_col(caps, 'collar'): 'f_collar'})
            if _ci_col(caps, 'f_cap') is None and _ci_col(caps, 'cap') is not None:
                caps = caps.rename(columns={_ci_col(caps, 'cap'): 'f_cap'})
            avail = [c for c in ['pricing_key', 'f_collar', 'f_cap'] if c in caps.columns]
            if len(avail) > 1:
                caps = caps.rename(columns={caps_pk: 'pricing_key'})
                constraints_df = constraints_df.merge(caps[avail].drop_duplicates('pricing_key'),
                                                      on='pricing_key', how='left')

        # Merge Min/Max
        if minmax is not None and _ci_col(minmax, 'pricing_key') is not None:
            mm_pk = _ci_col(minmax, 'pricing_key')
            if _ci_col(minmax, 'f_min') is None and _ci_col(minmax, 'minimum_premium') is not None:
                minmax = minmax.rename(columns={_ci_col(minmax, 'minimum_premium'): 'f_min'})
            if _ci_col(minmax, 'f_max') is None and _ci_col(minmax, 'maximum_premium') is not None:
                minmax = minmax.rename(columns={_ci_col(minmax, 'maximum_premium'): 'f_max'})
            avail = [c for c in ['pricing_key', 'f_min', 'f_max'] if c in minmax.columns]
            if len(avail) > 1:
                minmax = minmax.rename(columns={mm_pk: 'pricing_key'})
                constraints_df = constraints_df.merge(minmax[avail].drop_duplicates('pricing_key'),
                                                      on='pricing_key', how='left')

        # Ensure all expected numeric columns exist and are numeric
        expected = ['f_base_price', 'f_asv_price', 'f_collar', 'f_cap', 'f_min', 'f_max']
        for c in expected:
            if c not in constraints_df.columns:
                constraints_df[c] = 0.0
            constraints_df[c] = pd.to_numeric(constraints_df[c], errors='coerce').fillna(0.0).astype(float)

        # Reorder columns: pricing_key, bundle (if exists), then expected numeric columns
        cols_order = ['pricing_key']
        if 'bundle' in constraints_df.columns:
            cols_order.append('bundle')
        cols_order.extend(expected)
        constraints_df = constraints_df[cols_order]

        # Show and allow download
        #st.subheader("Constraints dataframe")
        #st.dataframe(constraints_df)


# First row (2 questions)
col1, col2 = st.columns(2)
with col1:
    #capturing the uploaded file
    st.subheader("Upload your input table")
    uploaded_file = st.file_uploader(label='', help='Upload your data', label_visibility="visible")


    if uploaded_file is not None:
        uploaded_file.seek(0)

        input_risk = pd.read_csv(uploaded_file, encoding='utf-8', sep=',')
        #input_risk = pd.read_csv(uploaded_file, encoding='utf-8', sep=',')



with col2:
    
    # --- Step 1: Let user pick dates ---
    st.subheader("SQL code for input data")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Select Renewal Start Date", value=date(2024, 11, 1))

    with col2:
        end_date = st.date_input("Select Renewal End Date", value=date(2024, 11, 30))

    # --- Step 2: Read SQL template ---
    with open("views_HC3.0/HC_3.0_data_input.sql", "r") as f:
        sql_template = f.read()


    # Replace existing dates dynamically
    sql_filled = re.sub(r"SET hivevar:start_date=\d{4}-\d{2}-\d{2};",
                        f"SET hivevar:start_date={start_date};", sql_template)
    sql_filled = re.sub(r"SET hivevar:end_date=\d{4}-\d{2}-\d{2};",
                        f"SET hivevar:end_date={end_date};", sql_filled)


    # --- Step 4: Show preview ---
    #st.subheader("Generated SQL:")
    #st.code(sql_filled, language="sql")

    # --- Step 5: Download button ---
    st.download_button(
        label="Download SQL File",
        data=sql_filled,
        file_name="dynamic_query.sql",
        mime="text/sql"
    )



def merge_lookup_bundle(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'bundle', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'bundle'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'bundle']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(0)
    return df
    

def merge_combi_boiler_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'combi_boiler', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'combi_boiler'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'combi_boiler']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df
    
def merge_manufacturer_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'manufacturer', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'manufacturer'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'manufacturer']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_postal_sector_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'postal_sector', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'postal_sector'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'postal_sector']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_radiators_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'radiators', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'radiators'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'radiators']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_boiler_age_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'boiler_age', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'boiler_age'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'boiler_age']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df


def merge_simple_pricing_key_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key'],  # Columns from the main DataFrame
        right_on=['pricing_key']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(0)
    return df

def merge_tenure_discount_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'bundle','tenure', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key','bundle','tenure_for_discount'],  # Columns from the main DataFrame
        right_on=['pricing_key','bundle','tenure']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(0)
    return df



def calculate_prices(input_risk):
    input_risk['f_expense'] = 0.01
    input_risk = merge_lookup_bundle(input_risk, 'f_base_price', constraints_df)
    input_risk = merge_combi_boiler_lookup_value(input_risk, 'f_boiler_type', boiler_type_df)
    input_risk = merge_manufacturer_lookup_value(input_risk, 'f_manufacturer', manufacturer_df)
    input_risk = merge_postal_sector_lookup_value(input_risk, 'f_postal_sector', postal_sector_df)
    input_risk = merge_radiators_lookup_value(input_risk, 'f_radiators', radiators_df)
    input_risk = merge_boiler_age_lookup_value(input_risk, 'f_boiler_age', boiler_age_df)
    input_risk = merge_lookup_bundle(input_risk, 'f_asv_price', constraints_df)
    input_risk = merge_tenure_discount_lookup_value(input_risk, 'f_tenure_discount', tenure_discount_df)
    input_risk = merge_lookup_bundle(input_risk, 'f_cap', constraints_df)
    input_risk = merge_lookup_bundle(input_risk, 'f_collar', constraints_df)
    input_risk = merge_lookup_bundle(input_risk, 'f_min', constraints_df)
    input_risk = merge_lookup_bundle(input_risk, 'f_max', constraints_df)

    


    input_risk['c_Risk_Premium'] = (input_risk['f_base_price']+input_risk['f_expense'])*input_risk['f_boiler_type']*input_risk['f_manufacturer']*input_risk['f_postal_sector']*input_risk['f_radiators']*input_risk['f_boiler_age']
    input_risk['c_ASV_Premium'] = input_risk['f_asv_price']
    input_risk['c_Undiscounted_Premium'] = (input_risk['c_Risk_Premium']+input_risk['c_ASV_Premium'])
    input_risk['c_tenure_discount'] = input_risk['c_Undiscounted_Premium'] * input_risk['f_tenure_discount']
    input_risk['Discounted_Premium'] = input_risk['c_Undiscounted_Premium'] - input_risk['c_tenure_discount']
    input_risk['Min_Premium'] = input_risk['ly_undiscounted_price']*(input_risk['f_collar'])
    input_risk['Max_Premium'] = input_risk['ly_undiscounted_price']*(input_risk['f_cap'])
    input_risk['Capped_Premium'] = input_risk.apply(lambda row: min(max(row['Min_Premium'], row['Discounted_Premium']), row['Max_Premium']),axis=1)
    input_risk['Final_Premium'] = input_risk.apply(lambda row: min(max(row['f_min'], row['Capped_Premium']), row['f_max']),axis=1)
    
    return input_risk

if uploaded_file is not None:
    if st.button('Validate'):
        try:
            
            # Reset pointer in case it was read before
            uploaded_file.seek(0)

            input_risk = pd.read_csv(uploaded_file, encoding='utf-8', sep=',')
            st.session_state['input_risk'] = input_risk  # << store for later use
            st.write(f"**Number of rows in your file**: {input_risk.shape[0]}")
            st.write(f"**Number of columns in your file**: {input_risk.shape[1]}")
            st.header("Check your uploaded File:")
            st.write(input_risk.head())
        except Exception as e:
            st.error(f"Error validating the file: {e}")


# Check if input_risk is in session state before displaying the Calculate button
if st.button('Calculate'):
    try:
        premium_file = calculate_prices(input_risk)
        # Store consistently using bracket notation
        st.session_state['premium_file'] = premium_file

        # Build summary_file now so the right pane shows immediately
        columns_for_analysis = [
            "Business Agreement", "Renewal Date", "pricing_key","price_group", "combi_boiler",
            "manufacturer", "postal_sector", "radiators", "boiler_age",
            "tenure_for_discount", "bundle", "ly_customer_price",
            "c_tenure_discount", "Discounted_Premium", "Final_Premium"
        ]
        available = [c for c in columns_for_analysis if c in premium_file.columns]
        st.session_state['summary_file'] = premium_file[available].copy()

        st.success(f"Prices calculated successfully for {len(premium_file)} policies!")
        #st.header("Sample Output:")
        #st.write(premium_file.head())
    except Exception as e:
        st.error(f"Error calculating prices: {e}")


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

        # buttons for save / discard / download
        col_save, col_cancel, col_download = st.columns([1, 1, 1])

        with col_save:
            if st.button("Recalculate"):
                # ensure pricing_key exists in original and edited
                if 'pricing_key' not in original.columns or 'pricing_key' not in edited.columns:
                    st.error("pricing_key column must exist in the table.")
                else:
                    # compare protected columns: pricing_key and bundle (if present in original)
                    protected = ['pricing_key']
                    if 'bundle' in original.columns:
                        protected.append('bundle')

                    # For safety compare as strings to avoid dtype mismatches
                    changes = []
                    for col in protected:
                        orig_vals = original[col].astype(str).fillna('')
                        new_vals = edited[col].astype(str).fillna('') if col in edited.columns else pd.Series([''] * len(original))
                        if not orig_vals.equals(new_vals):
                            changes.append(col)

                    if changes:
                        # restore protected columns from original into edited copy
                        for col in changes:
                            edited[col] = original[col].values
                        st.warning(
                            f"The following protected column(s) were not editable and have been restored to original values: "
                            f"{', '.join(changes)}. Other edits were saved."
                        )

                    # normalize numeric columns and fill any missing expected numeric columns
                    for c in expected:
                        if c in edited.columns:
                            edited[c] = pd.to_numeric(edited[c], errors='coerce').fillna(0.0).astype(float)
                        else:
                            edited[c] = 0.0

                    # persist updates
                    st.session_state['constraints_df'] = edited.copy()
                    globals()['constraints_df'] = edited.copy()
                    #st.success("Edits saved to session_state['constraints_df'].")

                    # ✅ Recalculate prices if input_risk exists
                    # ✅ Recalculate prices using validated input if available; else fallback to uploaded file
                    src = st.session_state.get('input_risk')
                    if src is None and uploaded_file is not None:
                        try:
                            src = pd.read_csv(uploaded_file, encoding='utf-8', sep=',')
                        except Exception as e:
                            st.error(f"Unable to read the uploaded file for recalculation: {e}")

                    if src is not None:
                        try:
                            premium_file = calculate_prices(src)
                            st.session_state['premium_file'] = premium_file

                            columns_for_analysis = [
                                "Business Agreement", "Renewal Date", "pricing_key","price_group", "combi_boiler",
                                "manufacturer", "postal_sector", "radiators", "boiler_age",
                                "tenure_for_discount", "bundle", "ly_customer_price",
                                "c_tenure_discount", "Discounted_Premium", "Final_Premium"
                            ]
                            missing_cols = [c for c in columns_for_analysis if c not in premium_file.columns]
                            if missing_cols:
                                available = [c for c in columns_for_analysis if c in premium_file.columns]
                                summary_file = premium_file[available].copy()
                               
                            else:
                                summary_file = premium_file[columns_for_analysis].copy()

                            st.session_state['summary_file'] = summary_file
                            st.success("Prices recalculated after constraint update!")
                        except Exception as e:
                            st.error(f"Error recalculating prices: {e}")
                    else:
                        st.info("Edits saved. Upload & Validate an input file (or click Recalculate after uploading) to enable auto-recalculation.")


        with col_download:
            csv = edited.to_csv(index=False).encode('utf-8')
            st.download_button("Download edited (CSV)", data=csv, file_name="constraints_edited.csv", mime="text/csv")

    # show status
    if 'constraints_df' in st.session_state:
        st.info("Constraint(s) updated and saved. Use that for downstream calculations.")
    else:
        st.write("No saved edits yet — click **Save edits** to persist changes.")


with col2:
    # ---------- Summary Table ----------
    st.subheader("Summary Table \n (product level)")

    def compute_yoy(df,
                    group_col='pricing_key',
                    final_col='Final_Premium',
                    ly_col='ly_customer_price',
                    price_group = 'price_group',
                    zero_division='nan'):
        """
        For each group (group_col) compute:
        - avg_ly        : mean(ly_customer_price)
        - min_final     : min(Final_Premium)
        - max_final     : max(Final_Premium)
        - avg_final     : mean(Final_Premium)
        - yoy_pct       : ((sum(Final_Premium) / sum(ly_customer_price)) - 1) * 100,
                            rounded to 2 decimals and formatted with a '%' sign.

        Appends a final 'Total' row with:
        - Volume: total count
        - Last_Year_Price: overall mean(ly_customer_price)
        - Avg_Renewal_Price: overall mean(Final_Premium)
        - yoy_pct: ((sum(Final_Premium) / sum(ly_customer_price)) - 1) * 100

        Returns a DataFrame with:
        [group_col, 'Volume', 'Last_Year_Price', 'Min_Renewal_Price',
        'Max_Renewal_Price', 'Avg_Renewal_Price', 'yoy_pct']
        """
        # Basic checks
        if group_col not in df.columns or final_col not in df.columns or ly_col not in df.columns:
            raise ValueError(f"DataFrame must contain columns: {group_col}, {final_col}, {ly_col}")

        # Work on a copy and coerce to numeric
        df_work = df[[group_col, final_col, ly_col,price_group]].copy()
        df_work[final_col] = pd.to_numeric(df_work[final_col], errors='coerce').fillna(0.0)
        df_work[ly_col] = pd.to_numeric(df_work[ly_col], errors='coerce').fillna(0.0)

        # Group-level aggregation
        agg_df = df_work.groupby(group_col, dropna=False).agg(
            sum_final=(final_col, 'sum'),
            sum_ly=(ly_col, 'sum'), 
            volume=(ly_col, 'count'),
            avg_ly=(ly_col, lambda x: x[df_work.loc[x.index, 'price_group'] == 51].mean()),
            min_final=(final_col, 'min'),
            max_final=(final_col, 'max'),
            avg_final=(final_col, 'mean')
        ).reset_index()

        # YoY per group
        def _yoy_pct(a, b):
            if b == 0:
                return np.inf if zero_division == 'inf' else np.nan
            return ((a / b) - 1) * 100

        agg_df['yoy_pct_raw'] = agg_df.apply(lambda r: _yoy_pct(r['avg_final'], r['avg_ly']), axis=1)

        # Format columns
        agg_df['Volume'] = agg_df['volume']
        agg_df['Last_Year_Price']   = agg_df['avg_ly'].round(2).apply(lambda x: f"£{x:,.2f}")
        agg_df['Min_Renewal_Price'] = agg_df['min_final'].round(2).apply(lambda x: f"£{x:,.2f}")
        agg_df['Max_Renewal_Price'] = agg_df['max_final'].round(2).apply(lambda x: f"£{x:,.2f}")
        agg_df['Avg_Renewal_Price'] = agg_df['avg_final'].round(2).apply(lambda x: f"£{x:,.2f}")

        def fmt_pct(x):
            if pd.isna(x):
                return 'nan'
            if np.isinf(x):
                return 'inf'
            return f"{round(x, 2)}%"

        agg_df['yoy_pct'] = agg_df['yoy_pct_raw'].apply(fmt_pct)

        # Select output columns
        result = agg_df[[group_col, 'Volume', 'Last_Year_Price', 'Min_Renewal_Price',
                        'Max_Renewal_Price', 'Avg_Renewal_Price', 'yoy_pct']].copy()

        # ---------- Append TOTAL row ----------
        # Totals computed across all records (not mean of means)
        total_volume = int(df_work.shape[0])
        if 'price_group' in df_work.columns:
            total_avg_ly = float(df_work.loc[df_work['price_group'] == 51, ly_col].mean())
        else:
            total_avg_ly = float(df_work[ly_col].mean()) if total_volume > 0 else 0.0
        total_avg_final = float(df_work[final_col].mean()) if total_volume > 0 else 0.0
        total_min_final = float(df_work[final_col].min()) if total_volume > 0 else 0.0
        total_max_final = float(df_work[final_col].max()) if total_volume > 0 else 0.0

        total_sum_final = float(df_work[final_col].sum())
        total_sum_ly = float(df_work[ly_col].sum())
        total_yoy_raw = _yoy_pct(total_avg_final, total_avg_ly)
        total_yoy_fmt = fmt_pct(total_yoy_raw)

        total_row = pd.DataFrame({
            group_col: ['Total'],
            'Volume': [total_volume],
            'Last_Year_Price': [f"£{total_avg_ly:,.2f}"],
            'Min_Renewal_Price': [f"£{total_min_final:,.2f}"],
            'Max_Renewal_Price': [f"£{total_max_final:,.2f}"],
            'Avg_Renewal_Price': [f"£{total_avg_final:,.2f}"],
            'yoy_pct': [total_yoy_fmt],
        })

        result = pd.concat([result, total_row], ignore_index=True)
        # --------------------------------------

        return result

    # Display summary based on session_state
    if 'summary_file' in st.session_state and isinstance(st.session_state['summary_file'], pd.DataFrame) and not st.session_state['summary_file'].empty:
        try:
            st.dataframe(
                compute_yoy(st.session_state['summary_file']),
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generating summary: {e}")
    else:
        st.info("Summary will appear after calculation.")
# ---------- end protected editable block + summary ----------



#--------Converting to bundle view ---------------

# -----------------------------
# 0) Helpers
# -----------------------------
KEY_COLS = ["business_agreement", "contract_id", "contract_start_date"]
KEYS_PLUS = ["business_agreement", "contract_id", "contract_start_date", "contract_end_date"]


def coalesce_series(*series_list):
    valid = [s for s in series_list if s is not None]
    if not valid:
        return pd.Series(dtype=object)

    cleaned = [
        s.replace(r"^\s*$", np.nan, regex=True)
        for s in valid
    ]

    out = cleaned[0].copy()
    for s in cleaned[1:]:
        out = out.where(out.notna(), s)

    return out


def add_prefix_except_keys(df, prefix, key_cols):
    rename = {c: f"{prefix}{c}" for c in df.columns if c not in key_cols}
    return df.rename(columns=rename)

def to_string(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype("string")
    return df

def to_date(df, col):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df

if 'premium_file' in st.session_state:
    premium_file = st.session_state['premium_file']
    
# -----------------------------
# 1) Split premium_file into product dfs
# -----------------------------
# premium_file is pandas df
bcc = premium_file[premium_file["pricing_key"].isin(["BNI1", "BNI2"])].copy()
chc = premium_file[premium_file["pricing_key"].isin(["CNI1", "CNI2"])].copy()
pad = premium_file[premium_file["pricing_key"].isin(["DNI1", "DNI2"])].copy()
hec = premium_file[premium_file["pricing_key"].isin(["HNI1", "HNI2"])].copy()


# -----------------------------
# 2) "Clean" each table (casts + date parsing + select same columns as Spark SQL CTEs)
# -----------------------------
# Columns per your SQL CTEs:
pad_cols = [
    "business_agreement","contract_id","contract_start_date","contract_end_date","policy_tenure_at_renewal",
    "postal_sector","pricing_key","excess","campaign_disc","actual_policy_discount","ly_customer_price",
    "autoconsent_renewal_ind","Final_Premium","gack_kac"
]


bcc_cols = [
    "business_agreement","contract_id","contract_start_date","contract_end_date",
    "policy_tenure_at_renewal","postal_sector",
    "boiler_age",
    "manufacturer",
    "combi_boiler",
    "installedby_bg",
    "boiler_size",
    "radiators",
    "claim_count",
    "pricing_key","excess","campaign_disc","actual_policy_discount",
    "ly_customer_price","autoconsent_renewal_ind","Final_Premium","gack_kac"
]

chc_cols = bcc_cols.copy()


hec_cols = [
    "business_agreement","contract_id","contract_start_date","contract_end_date","policy_tenure_at_renewal",
    "postal_sector","pricing_key","excess","campaign_disc","actual_policy_discount","ly_customer_price",
    "autoconsent_renewal_ind","Final_Premium","gack_kac"]

def clean_select(df, cols):
    # Keep only cols that exist (defensive)
    cols_present = [c for c in cols if c in df.columns]
    out = df.loc[:, cols_present].copy()

    # Cast business_agreement & contract_id to string like SQL CAST(... AS STRING)
    out = to_string(out, ["business_agreement", "contract_id"])

    # contract_start_date -> date (SQL TO_DATE(..., 'yyyy-MM-dd'))
    out = to_date(out, "contract_start_date")

    # Keep contract_end_date as-is (your SQL doesn’t TO_DATE it)
    # If you want it as date too, uncomment:
    # out = to_date(out, "contract_end_date")

    return out

pad_clean = clean_select(pad, pad_cols)
bcc_clean = clean_select(bcc, bcc_cols)
chc_clean = clean_select(chc, chc_cols)
hec_clean = clean_select(hec, hec_cols)


# -----------------------------
# 3) keys = UNION distinct of the 4 sources (business_agreement, contract_id, start, end)
# -----------------------------
keys = pd.concat(
    [
        pad_clean[KEYS_PLUS],
        bcc_clean[KEYS_PLUS],
        chc_clean[KEYS_PLUS],
        hec_clean[KEYS_PLUS],
    ],
    axis=0,
    ignore_index=True
).drop_duplicates()


# -----------------------------
# 4) Prefix columns to match your final SELECT naming
#    Then apply the same specific renames you used in SQL aliases
# -----------------------------
def prep_for_merge(df, prefix):
    out = df.copy()
    out = add_prefix_except_keys(out, prefix, KEY_COLS)  # note: contract_end_date is NOT a join key in your SQL joins
    return out

bcc_p = prep_for_merge(bcc_clean, "bcc_")
chc_p = prep_for_merge(chc_clean, "chc_")
pad_p = prep_for_merge(pad_clean, "pad_")
hec_p = prep_for_merge(hec_clean, "hec_")

# Now replicate your SQL aliasing for boiler-related columns and gack/kac naming:
bcc_alias_map = {
    "bcc_combi_boiler": "bcc_combi",
    "bcc_installedby_bg": "bcc_bg_installed",  # already same
    "bcc_radiators": "bcc_rads",
    "bcc_claim_count": "bcc_claims",
    "bcc_gack_kac": "bcc_gackkac",
    "bcc_policy_tenure_at_renewal": "bcc_tenure",
}
bcc_p = bcc_p.rename(columns={k: v for k, v in bcc_alias_map.items() if k in bcc_p.columns})

chc_alias_map = {
    "chc_combi_boiler": "chc_combi",
    "chc_installedby_bg": "chc_bg_installed",  # already same
    "chc_radiators": "chc_rads",
    "chc_claim_count": "chc_claims",
    "chc_gack_kac": "chc_gackkac",
    "chc_policy_tenure_at_renewal": "chc_tenure",
}
chc_p = chc_p.rename(columns={k: v for k, v in chc_alias_map.items() if k in chc_p.columns})

pad_alias_map = {
    "pad_gack_kac": "pad_gackkac",
    "pad_policy_tenure_at_renewal": "pad_tenure",
    "pad_postal_sector": "pad_postal_sector",
}
pad_p = pad_p.rename(columns={k: v for k, v in pad_alias_map.items() if k in pad_p.columns})

hec_alias_map = {
    "hec_gack_kac": "hec_gackkac",
    "hec_policy_tenure_at_renewal": "hec_tenure",
    "hec_postal_sector": "hec_postal_sector",
}
hec_p = hec_p.rename(columns={k: v for k, v in hec_alias_map.items() if k in hec_p.columns})


# -----------------------------
# 5) Left-join all product tables to keys on (business_agreement, contract_id, contract_start_date)
#    (matching your SQL join conditions)
# -----------------------------
contracts_view = keys.copy()

contracts_view = contracts_view.merge(
    bcc_p, how="left", on=KEY_COLS
).merge(
    chc_p, how="left", on=KEY_COLS
).merge(
    pad_p, how="left", on=KEY_COLS
).merge(
    hec_p, how="left", on=KEY_COLS
)


# -----------------------------
# 6) Indicator flags (same as SQL CASE WHEN pricing_key is not null)
# -----------------------------
contracts_view["bcc"] = np.where(contracts_view["bcc_pricing_key"].notna(), 1, 0)
contracts_view["chc"] = np.where(contracts_view["chc_pricing_key"].notna(), 1, 0)
contracts_view["pad"] = np.where(contracts_view["pad_pricing_key"].notna(), 1, 0)
contracts_view["hec"] = np.where(contracts_view["hec_pricing_key"].notna(), 1, 0)


# -----------------------------
# 7) product_bundle logic (replicates your SQL CASE)
# -----------------------------
b = contracts_view["bcc"].eq(1)
c = contracts_view["chc"].eq(1)
p = contracts_view["pad"].eq(1)
h = contracts_view["hec"].eq(1)

conds = [
    b & ~c & ~p & ~h,
    ~b & c & ~p & ~h,
    ~b & c & p & ~h,
    ~b & c & p & h,
    b & ~c & p & ~h,
    b & ~c & ~p & h,
    b & ~c & p & h,
    ~b & ~c & p & h,
    ~b & c & ~p & h,
    ~b & ~c & p & ~h,
    ~b & ~c & ~p & h,
]
choices = [
    "HC1",
    "HC2",
    "HC3",
    "HC4",
    "BCC+PAD",
    "BCC+HEC",
    "BCC+PAD+HEC",
    "PAD+HEC",
    "CHC+HEC",
    "PAD Standalone",
    "HEC Standalone",
]
contracts_view["product_bundle"] = np.select(conds, choices, default="Others")




# -----------------------------
# 9) bundle_excess logic
#    Spark version checks: if all products share same excess and it's "0" -> "0"
#                           else if all share same and it's "60" -> "60"
#                           else "Mixed"
# -----------------------------
excess_cols = ["bcc_excess", "chc_excess", "pad_excess", "hec_excess"]

product_flags = ["bcc", "chc", "pad", "hec"]
excess_df = contracts_view[excess_cols].where(
    contracts_view[product_flags].values == 1
)

distinct_excess = excess_df.nunique(axis=1, dropna=True)



contracts_view["bundle_excess"] = np.select(
    [
        (distinct_excess == 1) & (excess_df.max(axis=1) == 0),
        (distinct_excess == 1) & (excess_df.max(axis=1) == 60),
    ],
    ["0", "60"],
    default="Mixed"
)




# autoconsent_renewal_ind = coalesce
contracts_view["autoconsent_renewal_ind"] = coalesce_series(
    contracts_view.get("bcc_autoconsent_renewal_ind"),
    contracts_view.get("chc_autoconsent_renewal_ind"),
    contracts_view.get("pad_autoconsent_renewal_ind"),
    contracts_view.get("hec_autoconsent_renewal_ind"),
)

# bundle_tenure = greatest (max) of product tenures
tenure_cols = ["bcc_tenure", "chc_tenure", "pad_tenure", "hec_tenure"]
for ccol in tenure_cols:
    if ccol in contracts_view.columns:
        contracts_view[ccol] = pd.to_numeric(contracts_view[ccol], errors="coerce")
contracts_view["bundle_tenure"] = contracts_view[tenure_cols].max(axis=1, skipna=True)

# bundle_gack_kac = greatest (max) of product gack/kac
gack_cols = ["bcc_gackkac", "chc_gackkac", "pad_gackkac", "hec_gackkac"]
for ccol in gack_cols:
    if ccol in contracts_view.columns:
        contracts_view[ccol] = pd.to_numeric(contracts_view[ccol], errors="coerce")
contracts_view["bundle_gack_kac"] = contracts_view[gack_cols].max(axis=1, skipna=True)

# postal_sector = coalesce
contracts_view["postal_sector"] = coalesce_series(
    contracts_view.get("bcc_postal_sector"),
    contracts_view.get("chc_postal_sector"),
    contracts_view.get("pad_postal_sector"),
    contracts_view.get("hec_postal_sector"),
)

# boiler attributes only from bcc/chc (as in your code)
contracts_view["boiler_age"] = coalesce_series(
    contracts_view.get("bcc_boiler_age"),
    contracts_view.get("chc_boiler_age"),
)

contracts_view["manufacturer"] = coalesce_series(
    contracts_view.get("bcc_manufacturer"),
    contracts_view.get("chc_manufacturer"),
)

contracts_view["combi"] = coalesce_series(
    contracts_view.get("bcc_combi"),
    contracts_view.get("chc_combi"),
)

contracts_view["bg_installed"] = coalesce_series(
    contracts_view.get("bcc_bg_installed"),
    contracts_view.get("chc_bg_installed"),
)

contracts_view["boiler_size"] = coalesce_series(
    contracts_view.get("bcc_boiler_size"),
    contracts_view.get("chc_boiler_size"),
)

contracts_view["rads"] = coalesce_series(
    contracts_view.get("bcc_rads"),
    contracts_view.get("chc_rads"),
)

contracts_view["claims"] = coalesce_series(
    contracts_view.get("bcc_claims"),
    contracts_view.get("chc_claims"),
)

# bundle sums (campaign disc, retention disc, customer price, quoted prices, discounts)
def sum_fill0(cols):
    existing = [c for c in cols if c in contracts_view.columns]
    return contracts_view[existing].fillna(0).sum(axis=1) if existing else 0

contracts_view["bundle_campaign_disc"] = sum_fill0(
    ["bcc_campaign_disc","chc_campaign_disc","pad_campaign_disc","hec_campaign_disc"]
)

contracts_view["bundle_retention_disc"] = sum_fill0(
    ["bcc_actual_policy_discount","chc_actual_policy_discount","pad_actual_policy_discount","hec_actual_policy_discount"]
)

contracts_view["bundle_customer_price"] = sum_fill0(
    ["bcc_ly_customer_price","chc_ly_customer_price","pad_ly_customer_price","hec_ly_customer_price"]
)

contracts_view["bundle_Final_Premium"] = sum_fill0(
    ["bcc_Final_Premium","chc_Final_Premium","pad_Final_Premium","hec_Final_Premium"]
)

req_columns = [
    "business_agreement", "contract_start_date", "contract_end_date","product_bundle",
     "bundle_excess","autoconsent_renewal_ind", "bundle_tenure", "bundle_gack_kac",
    "boiler_age", "manufacturer", "combi", "bg_installed", "boiler_size", "rads", "claims",
    "bundle_campaign_disc", "bundle_retention_disc", "bundle_customer_price", "bundle_Final_Premium"
]

df_for_model = contracts_view[req_columns]

# contracts_view is now your pandas equivalent

#st.dataframe(df_for_model, use_container_width=True)


import numpy as np
import pandas as pd

# --- constants copied from your training logic ---
BUNDLES_NOT_APPLICABLE = ['PAD+HEC', 'PAD Standalone', 'HEC Standalone']

FIXED_TOP10_MANUFACTURERS = {
    'Alpha Therm Ltd',
    'Baxi Heating Ltd',
    'Default',
    'Glow Worm',
    'Ideal Boilers',
    'MAIN GAS APPLIANCES LTD',
    'Potterton Myson Ltd',
    'Vaillant',
    'Vokera',
    'Worcester Heat Systems Ltd'
}

def engineer_features_for_scoring(df_in: pd.DataFrame) -> pd.DataFrame:
    """
    Recreates your training-time feature engineering in pandas for scoring.
    Assumes df_in is your contracts_view bundle dataframe.
    Does NOT require 'target' or 'final_status'.
    Uses Final_Premium instead of quoted-price columns.
    """
    df = df_in.copy()

    # ----------------------------
    # 0) Basic flags from discounts
    # ----------------------------
    # These require bundle_campaign_disc & bundle_retention_disc to exist.
    if "bundle_campaign_disc" in df.columns:
        df["campaign_discounted"] = np.where(df["bundle_campaign_disc"] < 0, 1, 0).astype("int8")
        df["campaign_discounted"] = df["campaign_discounted"].astype("category")

    if "bundle_retention_disc" in df.columns:
        df["retention_discounted"] = np.where(df["bundle_retention_disc"] < 0, 1, 0).astype("int8")
        df["retention_discounted"] = df["retention_discounted"].astype("category")

    # ----------------------------
    # 1) Applicability flags
    # ----------------------------
    features = ['boiler_age', 'manufacturer', 'combi', 'bg_installed', 'boiler_size', 'rads']
    for feat in features:
        flag_col = f"{feat}_applicable"
        if "product_bundle" in df.columns:
            df[flag_col] = np.where(df["product_bundle"].isin(BUNDLES_NOT_APPLICABLE), 0, 1).astype("int8")
        else:
            # if product_bundle missing, assume applicable
            df[flag_col] = 1

    # ----------------------------
    # 2) Categorical flags: combi/bg_installed -> add 'not_applicable'
    # ----------------------------
    for cat_col in ["combi", "bg_installed"]:
        if cat_col in df.columns:
            # keep NaN as NaN; but make sure we can write 'not_applicable'
            s = df[cat_col].astype("string")
            s = s.replace(r"^\s*$", pd.NA, regex=True)
            s[df[f"{cat_col}_applicable"] == 0] = "not_applicable"
            df[cat_col] = s.astype("category")

    # ----------------------------
    # 3) Numerical missingness indicators (no x_applicable interactions)
    # ----------------------------
    num_feats = ["boiler_age", "boiler_size", "rads"]
    for num in num_feats:
        if num in df.columns:
            df[f"{num}_is_missing"] = df[num].isna().astype("int8")

    # ----------------------------
    # 4) Manufacturer: 'manufacturer_cat' with fixed top-10 + Others + not_applicable
    # ----------------------------
    if "manufacturer" in df.columns:
        m = df["manufacturer"].astype("string").str.strip()
        m = m.replace({"nan": pd.NA, "NaN": pd.NA, "None": pd.NA, "": pd.NA})

        # mark non-applicable bundles
        m[df["manufacturer_applicable"] == 0] = "not_applicable"

        is_not_app = m.eq("not_applicable")
        is_na = m.isna()
        is_in_top = m.isin(list(FIXED_TOP10_MANUFACTURERS))
        applicable_mask = ~is_not_app

        # Missing applicable -> Others
        m[applicable_mask & is_na] = "Others"
        # Non-top applicable -> Others
        m[applicable_mask & ~is_na & ~is_in_top] = "Others"

        frozen_levels = list(FIXED_TOP10_MANUFACTURERS) + ["Others", "not_applicable"]
        df["manufacturer_cat"] = pd.Categorical(m, categories=frozen_levels)

    # ----------------------------
    # 5) YoY feature (adapted)
    # ----------------------------
    # Original training used: yoy = bundle_quoted_price_initial / bundle_customer_price
    # Now you don't have quoted columns; use Final_Premium as proxy.
    if "Final_Premium" in df.columns and "bundle_customer_price" in df.columns:
        safe_div = df["bundle_customer_price"].replace(0, np.nan)
        df["yoy"] = df["Final_Premium"] / safe_div
        df["yoy"] = df["yoy"].clip(lower=-1, upper=3.0)

    # Drop price-related columns (updated list)
    drop_cols = [
        # in your original drop list:
        "bundle_customer_price",
        "bundle_campaign_disc",
        "bundle_retention_disc",
        # quoted columns no longer present, but safe to include
        "bundle_quoted_price_initial",
        "bundle_quoted_price",
        "bundle_retn_discount_initial",
        "bundle_retn_discount_final",
        # and Final_Premium if you want the model to rely on yoy not raw premium:
        "Final_Premium",
    ]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    # ----------------------------
    # 6) Dates -> month cyclical features
    # ----------------------------
    for col in ["contract_start_date", "contract_end_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "contract_start_date" in df.columns:
        df["contract_start_month"] = df["contract_start_date"].dt.month
        df["contract_start_month_sin"] = np.sin(2 * np.pi * df["contract_start_month"] / 12)
        df["contract_start_month_cos"] = np.cos(2 * np.pi * df["contract_start_month"] / 12)

    # ----------------------------
    # 7) Ensure categorical dtypes (as in training)
    # ----------------------------
    categorical_features = ["product_bundle", "manufacturer_cat", "combi", "bg_installed"]
    for c in categorical_features:
        if c in df.columns:
            df[c] = df[c].astype("category")

    # ----------------------------
    # 8) Clip numeric ranges (same as training)
    # ----------------------------
    clip_rules = {
        "bundle_tenure": (0, 40),
        "boiler_age": (1, 40),
        "boiler_size": (10, 50),
        "rads": (0, 20),
        "claims": (0, 10),
    }
    for col, (lo, hi) in clip_rules.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").clip(lower=lo, upper=hi)

    # Remove rows where bundle_tenure == 0 (same as training)
    if "bundle_tenure" in df.columns:
        df = df[df["bundle_tenure"] != 0].copy()

    return df

def get_expected_feature_names(calibrated_model):
    """
    Robustly extract feature names from a CalibratedClassifierCV
    wrapping a LightGBM model.
    """
    # CalibratedClassifierCV case
    if hasattr(calibrated_model, "calibrated_classifiers_"):
        cc = calibrated_model.calibrated_classifiers_[0]
        if hasattr(cc, "base_estimator"):
            est = cc.base_estimator
            if hasattr(est, "feature_name_"):
                return list(est.feature_name_)
            if hasattr(est, "booster_"):
                return est.booster_.feature_name()

    # Plain LGBMClassifier fallback
    if hasattr(calibrated_model, "feature_name_"):
        return list(calibrated_model.feature_name_)

    raise ValueError("Could not infer feature names from model")




import joblib
import numpy as np

# Load model
model = joblib.load("views_HC3.0/model_compressed.joblib")

# Feature engineering
df_feat = engineer_features_for_scoring(df_for_model)

# Get expected feature order
feature_cols = get_expected_feature_names(model)

# Ensure all columns exist
for c in feature_cols:
    if c not in df_feat.columns:
        df_feat[c] = np.nan

X = df_feat[feature_cols]

# Score
contracts_view_scored = df_for_model.loc[df_feat.index].copy()
contracts_view_scored["pred_retention_prob"] = model.predict_proba(X)[:, 1]
contracts_view_scored["pred_churn_prob"] = 1 - contracts_view_scored["pred_retention_prob"]


st.dataframe(contracts_view_scored.head(), use_container_width=True)