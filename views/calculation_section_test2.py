import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt


st.title("Validate and Generate Prices 📱")
st.markdown('<hr style="border: 1px solid #0093f5; margin: 20px 0;">', unsafe_allow_html=True)

# ---------------------------
# 1) NORMALIZATION UTILITIES
# ---------------------------
def _to_str_clean(s: pd.Series) -> pd.Series:
    # Convert to string, strip whitespace, uppercase, and convert literal "nan" to real NaN
    out = s.astype(str).str.strip().str.upper()
    out = out.replace({"NAN": None})
    return out

def _to_int_safe(s: pd.Series) -> pd.Series:
    # Convert to nullable Int64 (keeps NaN)
    return pd.to_numeric(s, errors="coerce").astype("Int64")

def _to_float_safe(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def normalize_join_keys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize all likely join keys on a copy of df.
    Adjust the lists below to match your schema exactly.
    """
    out = df.copy()

    # String/categorical keys
    str_like = [
        "pricing_key", "exec_rule", "appliance_type", "manufacturer_code",
        "change_in_circumstan", "geo_code", "logical_bundle_key",
        "post_sector", "geo_groupid"
    ]
    for c in str_like:
        if c in out.columns:
            out[c] = _to_str_clean(out[c])

    # Integer keys
    int_like = ["price_group", "boiler_age", "radiators", "spl_radiators", "jobs_completed", "product_tenure"]
    for c in int_like:
        if c in out.columns:
            out[c] = _to_int_safe(out[c])

    # Booleans / flags: normalize is_combi_boiler to Y/N
    if "is_combi_boiler" in out.columns:
        col = out["is_combi_boiler"]
        if pd.api.types.is_bool_dtype(col):
            out["is_combi_boiler"] = col.map({True: "Y", False: "N"})
        else:
            out["is_combi_boiler"] = (
                _to_str_clean(col).replace({"TRUE": "Y", "FALSE": "N", "1": "Y", "0": "N"})
            )

    # Geo/postal formatting: remove spaces from post_sector if present
    if "post_sector" in out.columns and out["post_sector"].dtype == object:
        out["post_sector"] = out["post_sector"].str.replace(" ", "", regex=False)

    return out

# Helpful diagnostics (optional)
def assert_no_nan_keys(df: pd.DataFrame, keys: list, frame_name: str):
    bad = df[keys].isna().any(axis=1)
    if bad.any():
        rows = bad.sum()
        sample = df.loc[bad, keys].head(5)
        raise ValueError(
            f"{frame_name}: Found {rows} rows with NaNs in join keys {keys}.\n"
            f"Example rows:\n{sample}"
        )

def assert_unique_keys(df: pd.DataFrame, keys: list, frame_name: str):
    dup = df.duplicated(subset=keys, keep=False)
    if dup.any():
        sample = df.loc[dup, keys].value_counts().head(5)
        raise ValueError(
            f"{frame_name}: Keys not unique for {keys}. "
            f"Found {dup.sum()} duplicate rows. Top duplicates:\n{sample}"
        )

def diagnostic_merge(left: pd.DataFrame, right: pd.DataFrame,
                     left_on: list, right_on: list,
                     value_col: str,
                     how: str = "left",
                     neutral=None,
                     frame_label: str = "") -> pd.DataFrame:
    """
    Merges with pre-checks and fills a value column to a neutral default if provided.
    Adds a '{value_col}__matched' indicator (1 matched / 0 defaulted) when neutral is not None.
    """
    n_before = len(left)

    # Pre-merge checks
    try:
        assert_no_nan_keys(left, left_on, f"LEFT {frame_label}")
    except Exception as e:
        st.warning(str(e))
    try:
        assert_unique_keys(right, right_on, f"RIGHT {frame_label}")
    except Exception as e:
        st.warning(str(e))

    # Keep only needed columns on right to prevent suffix collisions
    cols_needed = list(dict.fromkeys(right_on + [value_col]))
    right_slim = right[cols_needed].copy()

    out = left.merge(
        right_slim,
        how=how,
        left_on=left_on,
        right_on=right_on,
        suffixes=("", "_lkp")
    )

    if neutral is not None:
        out[value_col] = pd.to_numeric(out[value_col], errors="coerce").fillna(neutral)
        out[f"{value_col}__matched"] = (out[value_col] != neutral).astype(int)
    else:
        # Keep NaNs to allow strict checks later
        pass

    # Optional: confirm row count did not explode
    if len(out) != n_before:
        st.warning(
            f"[{frame_label}] Row count changed from {n_before} to {len(out)}. "
            f"This suggests a many-to-many join; check lookup uniqueness for keys {right_on}."
        )

    return out

# ---------------------------
# 2) UI CONTROLS
# ---------------------------
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader(
        label='Upload your input table (CSV)',
        type=['csv'],
        help='Upload your risk input CSV with required columns',
        label_visibility="visible"
    )
with col2:
    pricing_date = st.date_input(
        label='Generate Prices as on',
        help="Prices will be calculated as per the factors active on this date",
        max_value=dt.date.today()
    )

# ---------------------------
# 3) LOOKUP TABLES FROM SESSION
# ---------------------------
# Assumes the calling page has populated st.session_state.processed_data and st.session_state.geo_pschal
try:
    # Base lookups (raw)
    base_price_df       = st.session_state.processed_data['Base_Price'].rename(columns={'base_price_claims': 'f_base_price'})
    boiler_Type_df      = st.session_state.processed_data['Boiler_Type'].rename(columns={'factor': 'f_boiler_type'})
    appl_make_df        = st.session_state.processed_data['Appl_Make'].rename(columns={'factor': 'f_appl_make'})
    PRD_GROUP_df        = st.session_state.processed_data['PRD_GROUP']
    geo_pschal_df       = st.session_state.geo_pschal
    geo_fachal_df       = st.session_state.processed_data['GEO_FACHAL'].rename(columns={'factor': 'f_geo_factor'})
    boiler_age_df       = st.session_state.processed_data['Boiler_Age'].rename(columns={'boiler_age_factor': 'f_boiler_age'})
    rads_df             = st.session_state.processed_data['Rads'].rename(columns={'factor': 'f_rads'})
    spl_rads_df         = st.session_state.processed_data['Spl_Rads'].rename(columns={'factor': 'f_spl_rads'})
    Claims_df           = st.session_state.processed_data['Claims'].rename(columns={'claims_tenure_factor': 'f_claims'})
    ratearea_boilertype_df = st.session_state.processed_data['Ratearea_Boilertype'].rename(columns={'geo_region': 'geo_code', 'factor': 'f_int_geo_boiler'})
    ratarea_rads_df     = st.session_state.processed_data['Ratarea_Rads'].rename(columns={'geo_region': 'geo_code', 'factor': 'f_int_geo_rads'})
    rads_claims_df      = st.session_state.processed_data['Rads_Claims'].rename(columns={'factor': 'f_int_rads_claims'})
    claims_boilertype_df= st.session_state.processed_data['Claims_Boilertype'].rename(columns={'factor': 'f_int_claims_boiler'})
    claims_load_df      = st.session_state.processed_data['Claims_load'].rename(columns={'factor': 'f_Claims_load'})
    asv_df              = st.session_state.processed_data['Asv_price'].rename(columns={'asv_base_price': 'f_Asv_price'})
    exp_claim_df        = st.session_state.processed_data['Exp_Claim_load'].rename(columns={'expense_claims_load': 'f_Exp_Claim_load'})
    exp_asv_load        = st.session_state.processed_data['Exp_Asv_load'].rename(columns={'expense_asv_load': 'f_Exp_Asv_Load'})  # note: capitalized L for uniqueness
    flat_load_df        = st.session_state.processed_data['Flat_Load'].rename(columns={'flat_load_expense': 'f_Flat_Load'})
    multi_margin_df     = st.session_state.processed_data['Multi_bund_margin'].rename(columns={'factor': 'f_Multi_bund_margin'})
    cap_collar_df       = st.session_state.processed_data['Cap_n_Collar'].rename(columns={'cap_percentage_value': 'f_Cap', 'col_percentage_value': 'f_Collar'})
    cap_collar_df['change_in_circumstan'] = cap_collar_df['change_in_circumstan'].apply(lambda x: x.upper() if isinstance(x, str) else x)
    absolute_capping_df = st.session_state.processed_data['Absolute_Capping'].rename(columns={'absolute_cap_amount': 'absolute_Max_Premium'})
    minimum_capping_df  = st.session_state.processed_data['Minimum_Capping'].rename(columns={'price': 'absolute_Min_Premium'})
    flat_bundle_df      = st.session_state.processed_data['Flat_Bundle_Margin'].rename(columns={'flat_load_bundle_exp': 'f_flat_margin'})
    bundle_tenure_df    = st.session_state.processed_data['Bundle_Tenure'].rename(columns={'factor': 'f_bundle_adj'})
except Exception as e:
    st.info("Waiting for lookup tables in session state (processed_data / geo_pschal). "
            "Make sure they are populated before running this page.")
    # You can return or continue; merges will fail without these tables.

# ---------------------------
# 4) APPLY NORMALIZATION TO LOOKUPS
# ---------------------------
def normalize_all_lookups():
    lookups = {}

    # Normalize each lookup table (if present)
    for name, df in [
        ("base_price_df", base_price_df),
        ("boiler_Type_df", boiler_Type_df),
        ("appl_make_df", appl_make_df),
        ("PRD_GROUP_df", PRD_GROUP_df),
        ("geo_pschal_df", geo_pschal_df),
        ("geo_fachal_df", geo_fachal_df),
        ("boiler_age_df", boiler_age_df),
        ("rads_df", rads_df),
        ("spl_rads_df", spl_rads_df),
        ("Claims_df", Claims_df),
        ("ratearea_boilertype_df", ratearea_boilertype_df),
        ("ratarea_rads_df", ratarea_rads_df),
        ("rads_claims_df", rads_claims_df),
        ("claims_boilertype_df", claims_boilertype_df),
        ("claims_load_df", claims_load_df),
        ("asv_df", asv_df),
        ("exp_claim_df", exp_claim_df),
        ("exp_asv_load", exp_asv_load),
        ("flat_load_df", flat_load_df),
        ("multi_margin_df", multi_margin_df),
        ("cap_collar_df", cap_collar_df),
        ("absolute_capping_df", absolute_capping_df),
        ("minimum_capping_df", minimum_capping_df),
        ("flat_bundle_df", flat_bundle_df),
        ("bundle_tenure_df", bundle_tenure_df),
    ]:
        if df is not None:
            lookups[name] = normalize_join_keys(df)

    return lookups

normalized_lookups = {}
try:
    normalized_lookups = normalize_all_lookups()
except Exception as e:
    st.warning(f"Normalization of lookups failed: {e}")

# ---------------------------
# 5) MERGE HELPERS (use diagnostic_merge)
# ---------------------------
def merge_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule'],
        right_on=['pricing_key', 'price_group', 'exec_rule'],
        value_col=value_to_return,
        neutral=0.0,  # additive-like? If factor, use 1.0. For base price loads we typically use 0.0
        frame_label=f"{value_to_return} (generic)"
    )

def merge_lookup_value_loads(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule'],
        right_on=['pricing_key', 'price_group', 'exec_rule'],
        value_col=value_to_return,
        neutral=1.0,  # multiplicative factor load default
        frame_label=f"{value_to_return} (loads)"
    )

def merge_appl_level_lookup_value(df, value_to_return, lookup_table):
    df_kac = df[df['pricing_key'].isin(['KAI1', 'KAI2'])]
    df_others = df[~df['pricing_key'].isin(['KAI1', 'KAI2'])]

    df_kac = diagnostic_merge(
        df_kac, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule', 'appliance_type'],
        right_on=['pricing_key', 'price_group', 'exec_rule', 'appliance_type'],
        value_col=value_to_return,
        neutral=None,  # base price: be strict; let NaN surface
        frame_label=f"{value_to_return} (KAC)"
    )

    df_others = diagnostic_merge(
        df_others, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule'],
        right_on=['pricing_key', 'price_group', 'exec_rule'],
        value_col=value_to_return,
        neutral=None,
        frame_label=f"{value_to_return} (OTHERS)"
    )

    merged = pd.concat([df_kac, df_others], ignore_index=True)

    # Strict check for base-like values
    if merged[value_to_return].isna().any():
        missing_rows = merged[merged[value_to_return].isna()].head(10)
        raise ValueError(
            f"Missing {value_to_return} for {merged[value_to_return].isna().sum()} rows.\n"
            f"Example rows:\n{missing_rows[['pricing_key','price_group','exec_rule','appliance_type']]}"
        )

    merged[value_to_return] = _to_float_safe(merged[value_to_return])
    return merged

def merge_combi_boiler_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler'],
        right_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (is_combi_boiler)"
    )

def merge_appl_make_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule', 'manufacturer_code'],
        right_on=['pricing_key', 'price_group', 'exec_rule', 'manufacturer_code'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (manufacturer)"
    )

def merge_geo_group_lookup_value(df, value_to_return, lookup_table):
    out = diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key'],
        right_on=['pricing_key'],
        value_col=value_to_return,
        neutral=None,
        frame_label=f"{value_to_return} (geo_groupid)"
    )
    # Default if missing
    out[value_to_return] = out[value_to_return].fillna('G0001')
    return out

def merge_geo_code_lookup_value(df, value_to_return, lookup_table):
    out = diagnostic_merge(
        df, lookup_table,
        left_on=['geo_groupid', 'post_sector', 'price_group', 'exec_rule'],
        right_on=['geo_groupid', 'post_sector', 'price_group', 'exec_rule'],
        value_col=value_to_return,
        neutral=None,
        frame_label=f"{value_to_return} (geo_code)"
    )
    out[value_to_return] = out[value_to_return].astype(str)
    out[value_to_return] = out[value_to_return].fillna(
        out['price_group'].map({51: "ZZ", 50: "ZY"}).fillna("1")
    )
    return out

def merge_geo_factor_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'exec_rule', 'geo_code'],
        right_on=['pricing_key', 'exec_rule', 'geo_code'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (geo_factor)"
    )

def merge_boiler_age_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule', 'boiler_age'],
        right_on=['pricing_key', 'price_group', 'exec_rule', 'boiler_age'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (boiler_age)"
    )

def merge_radiators_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule', 'radiators'],
        right_on=['pricing_key', 'price_group', 'exec_rule', 'radiators'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (radiators)"
    )

def merge_spl_radiators_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule', 'spl_radiators'],
        right_on=['pricing_key', 'price_group', 'exec_rule', 'spl_radiators'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (spl_radiators)"
    )

def merge_claims_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule', 'jobs_completed'],
        right_on=['pricing_key', 'price_group', 'exec_rule', 'jobs_completed'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (claims tenure)"
    )

def merge_ratarea_boilertype_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', 'geo_code'],
        right_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', 'geo_code'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (ratearea_boilertype)"
    )

def merge_ratarea_rads_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule', 'radiators', 'geo_code'],
        right_on=['pricing_key', 'price_group', 'exec_rule', 'radiators', 'geo_code'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (ratearea_rads)"
    )

def merge_rads_claims_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule', 'radiators', 'jobs_completed'],
        right_on=['pricing_key', 'price_group', 'exec_rule', 'radiators', 'jobs_completed'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (rads_claims)"
    )

def merge_claims_boilertype_lookup_value(df, value_to_return, lookup_table):
    return diagnostic_merge(
        df, lookup_table,
        left_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', 'jobs_completed'],
        right_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', 'jobs_completed'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (claims_boilertype)"
    )

def merge_bundle_adj_lookup_value(df, value_to_return, lookup_table):
    df_pad = df[df['pricing_key'].isin(['DNI1', 'DNI2','2PDI','2PFI'])]
    df_others = df[~df['pricing_key'].isin(['DNI1', 'DNI2','2PDI','2PFI'])]

    df_pad = diagnostic_merge(
        df_pad, lookup_table,
        left_on=['pricing_key', 'exec_rule', 'price_group', 'logical_bundle_key', 'geo_code'],
        right_on=['pricing_key', 'exec_rule', 'price_group', 'logical_bundle_key', 'geo_code'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (bundle_adj - PAD)"
    )

    df_others = diagnostic_merge(
        df_others, lookup_table,
        left_on=['pricing_key', 'exec_rule', 'price_group', 'logical_bundle_key'],
        right_on=['pricing_key', 'exec_rule', 'price_group', 'logical_bundle_key'],
        value_col=value_to_return,
        neutral=1.0,
        frame_label=f"{value_to_return} (bundle_adj - OTHERS)"
    )

    merged = pd.concat([df_pad, df_others], ignore_index=True)
    return merged

def merge_cap_collar_lookup_value(df, value_to_return, lookup_table):
    df_kac = df[df['pricing_key'].isin(['KAI1', 'KAI2'])]
    df_others = df[~df['pricing_key'].isin(['KAI1', 'KAI2'])]

    df_kac = diagnostic_merge(
        df_kac, lookup_table,
        left_on=['pricing_key', 'exec_rule','jobs_completed', 'product_tenure'],
        right_on=['pricing_key', 'exec_rule','jobs_completed', 'product_tenure'],
        value_col=value_to_return,
        neutral=None,
        frame_label=f"{value_to_return} (cap/collar - KAC)"
    )

    df_others = diagnostic_merge(
        df_others, lookup_table,
        left_on=['pricing_key', 'exec_rule', 'boiler_age', 'jobs_completed', 'change_in_circumstan'],
        right_on=['pricing_key', 'exec_rule', 'boiler_age', 'jobs_completed', 'change_in_circumstan'],
        value_col=value_to_return,
        neutral=None,
        frame_label=f"{value_to_return} (cap/collar - OTHERS)"
    )

    merged = pd.concat([df_kac, df_others], ignore_index=True)

    # Previous code forced 100% except price_group==51; we avoid that.
    # Instead, if missing, you can set defaults or raise error. Here we set sensible defaults.
    default_pct = 100.0 if value_to_return == "f_Collar" else 100.0  # Adjust to your policy
    merged[value_to_return] = _to_float_safe(merged[value_to_return]).fillna(default_pct)

    return merged

def merge_absolute_cap(df, value_to_return, lookup_table):
    lookup_single = lookup_table.drop_duplicates(subset=['pricing_key'])
    return diagnostic_merge(
        df, lookup_single,
        left_on=['pricing_key'],
        right_on=['pricing_key'],
        value_col=value_to_return,
        neutral=0.0,  # absolute cap default 0 means no upper bound unless set (adjust as policy)
        frame_label=f"{value_to_return} (absolute cap)"
    )

def merge_minimum_cap(df, value_to_return, lookup_table):
    lookup_single = lookup_table.drop_duplicates(subset=['pricing_key', 'exec_rule'])
    return diagnostic_merge(
        df, lookup_single,
        left_on=['pricing_key', 'exec_rule'],
        right_on=['pricing_key', 'exec_rule'],
        value_col=value_to_return,
        neutral=0.0,
        frame_label=f"{value_to_return} (absolute min)"
    )

# ---------------------------
# 6) CALCULATION PIPELINE
# ---------------------------
def calculate_prices(input_risk: pd.DataFrame) -> pd.DataFrame:
    # Normalize input first
    input_risk = normalize_join_keys(input_risk)

    # Pull normalized lookups locally
    n = normalized_lookups

    # Required columns check (minimal set; extend as needed)
    required_cols = [
        "pricing_key","price_group","exec_rule","is_combi_boiler","manufacturer_code",
        "appliance_type","boiler_age","radiators","spl_radiators","jobs_completed",
        "logical_bundle_key","post_sector","ly_price"
    ]
    missing = [c for c in required_cols if c not in input_risk.columns]
    if missing:
        raise ValueError(f"Input missing required columns: {missing}")

    # Pipeline of merges
    df = input_risk.copy()
    df = merge_appl_level_lookup_value(df, 'f_base_price', n['base_price_df'])
    df = merge_combi_boiler_lookup_value(df, 'f_boiler_type', n['boiler_Type_df'])
    df = merge_appl_make_lookup_value(df, 'f_appl_make', n['appl_make_df'])
    df = merge_geo_group_lookup_value(df, 'geo_groupid', n['PRD_GROUP_df'])
    df = merge_geo_code_lookup_value(df, 'geo_code', n['geo_pschal_df'])
    df = merge_geo_factor_lookup_value(df, 'f_geo_factor', n['geo_fachal_df'])
    df = merge_bundle_adj_lookup_value(df, 'f_bundle_adj', n['bundle_tenure_df'])
    df = merge_boiler_age_lookup_value(df, 'f_boiler_age', n['boiler_age_df'])
    df = merge_radiators_lookup_value(df, 'f_rads', n['rads_df'])
    df = merge_spl_radiators_lookup_value(df, 'f_spl_rads', n['spl_rads_df'])
    df = merge_claims_lookup_value(df, 'f_claims', n['Claims_df'])
    df = merge_ratarea_boilertype_lookup_value(df, 'f_int_geo_boiler', n['ratearea_boilertype_df'])
    df = merge_ratarea_rads_lookup_value(df, 'f_int_geo_rads', n['ratarea_rads_df'])
    df = merge_rads_claims_lookup_value(df, 'f_int_rads_claims', n['rads_claims_df'])
    df = merge_claims_boilertype_lookup_value(df, 'f_int_claims_boiler', n['claims_boilertype_df'])
    df = merge_lookup_value_loads(df, 'f_Claims_load', n['claims_load_df'])
    df = merge_lookup_value(df, 'f_Asv_price', n['asv_df'])
    df = diagnostic_merge(df, n['exp_claim_df'],
                          left_on=['pricing_key', 'price_group', 'exec_rule', 'appliance_type'],
                          right_on=['pricing_key', 'price_group', 'exec_rule', 'appliance_type'],
                          value_col='f_Exp_Claim_load', neutral=0.0, frame_label='f_Exp_Claim_load')  # additive
    df = merge_lookup_value_loads(df, 'f_Exp_Asv_Load', n['exp_asv_load'])  # multiplicative
    df = merge_appl_level_lookup_value(df, 'f_Flat_Load', n['flat_load_df'])  # additive strict
    df = merge_appl_level_lookup_value(df, 'f_flat_margin', n['flat_bundle_df'])  # additive strict
    df = merge_appl_level_lookup_value(df, 'f_Multi_bund_margin', n['multi_margin_df'])  # treat as factor but strict
    df = merge_cap_collar_lookup_value(df, 'f_Cap', n['cap_collar_df'])
    df = merge_cap_collar_lookup_value(df, 'f_Collar', n['cap_collar_df'])

    # Calculations (ensure numeric)
    num_cols = [
        'f_base_price','f_bundle_adj','f_boiler_type','f_appl_make','f_geo_factor',
        'f_boiler_age','f_rads','f_spl_rads','f_claims',
        'f_int_geo_boiler','f_int_geo_rads','f_int_rads_claims','f_int_claims_boiler',
        'f_Claims_load','f_Asv_price','f_Exp_Claim_load','f_Exp_Asv_Load','f_Flat_Load',
        'f_flat_margin','f_Multi_bund_margin','f_Cap','f_Collar','ly_price'
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = _to_float_safe(df[c])

    # Core premium computation
    df['c_Risk_Premium'] = (
        df['f_base_price'] * df['f_bundle_adj'] * df['f_boiler_type'] * df['f_appl_make'] *
        df['f_geo_factor'] * df['f_boiler_age'] * df['f_rads'] * df['f_spl_rads'] *
        df['f_claims'] * df['f_int_geo_boiler'] * df['f_int_geo_rads'] *
        df['f_int_rads_claims'] * df['f_int_claims_boiler'] * df['f_Claims_load']
    )

    df['c_ASV_Premium'] = df['f_Asv_price']

    df['c_Expense_Premium'] = (
        (df['f_Exp_Claim_load'] * df['c_Risk_Premium']) +
        (df['f_Exp_Asv_Load'] * df['c_ASV_Premium']) +
        df['f_Flat_Load']
    )

    df['Pre_Margin_Premium'] = df['c_Risk_Premium'] + df['c_ASV_Premium'] + df['c_Expense_Premium']

    # If f_Multi_bund_margin is a margin rate (e.g., 0.25 for 25%)
    df['Margin'] = df['Pre_Margin_Premium'] * df['f_Multi_bund_margin']

    # Flat bundle margin assumed additive currency
    df['Pre_Cap_Premium'] = df['Pre_Margin_Premium'] + df['Margin'] + df['f_flat_margin']

    # Cap/Collar % applied to last year price
    df['Min_Premium'] = df['ly_price'] * (df['f_Collar'] / 100.0)
    df['Max_Premium'] = df['ly_price'] * (df['f_Cap'] / 100.0)

    # Collar/Cap application
    df['Capped_Premium'] = df.apply(
        lambda row: min(max(row['Min_Premium'], row['Pre_Cap_Premium']), row['Max_Premium']),
        axis=1
    )

    # Absolute caps
    df = merge_absolute_cap(df, 'absolute_Max_Premium', n['absolute_capping_df'])
    df = merge_minimum_cap(df, 'absolute_Min_Premium', n['minimum_capping_df'])

    df['Final_Premium'] = df.apply(
        lambda row: min(max(row['absolute_Min_Premium'], row['Capped_Premium']), row['absolute_Max_Premium'])
        if (pd.notna(row['absolute_Min_Premium']) and pd.notna(row['absolute_Max_Premium']))
        else row['Capped_Premium'],
        axis=1
    )

    return df

# ---------------------------
# 7) VALIDATE & CALCULATE
# ---------------------------
def load_input_df(file):
    return pd.read_csv(file)

required_cols_min = [
    "pricing_key","price_group","exec_rule","is_combi_boiler","manufacturer_code",
    "appliance_type","boiler_age","radiators","spl_radiators","jobs_completed",
    "logical_bundle_key","post_sector","ly_price"
]

# VALIDATE
if uploaded_file and st.button('Validate'):
    try:
        st.session_state.input_risk = load_input_df(uploaded_file)
        df = st.session_state.input_risk
        missing = [c for c in required_cols_min if c not in df.columns]
        if missing:
            st.error(f"Missing required columns: {missing}")
        else:
            st.success(f"File looks good. Rows: {df.shape[0]}, Columns: {df.shape[1]}")
            st.header("Preview:")
            st.write(df.head())
    except Exception as e:
        st.error(f"Error validating the file: {e}")

# CALCULATE
can_calc = ('input_risk' in st.session_state) and (pricing_date is not None)
if st.button('Calculate', disabled=not can_calc):
    if not can_calc:
        st.warning("Please upload and validate a file, and select a pricing date.")
    else:
        try:
            premium_file = calculate_prices(st.session_state.input_risk)
            st.session_state.premium_file = premium_file
            st.success("Prices calculated successfully!!")
            st.header("Sample Output:")
            st.write(premium_file.head())

            # Optional: surface which factors are fully neutral (all 1.0)
            factor_cols = [c for c in premium_file.columns if c.startswith("f_")]
            neutrals = []
            for c in factor_cols:
                if pd.api.types.is_numeric_dtype(premium_file[c]) and (premium_file[c].fillna(1.0) == 1.0).all():
                    neutrals.append(c)
            if neutrals:
                st.info(f"These factor columns are entirely neutral (likely join misses or defaults): {neutrals}")

        except Exception as e:
            st.error(f"Error calculating prices: {e}")