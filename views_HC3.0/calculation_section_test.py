import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import date

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
    with open("views_HC3.0\HC_3.0_data_input.sql", "r") as f:
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

