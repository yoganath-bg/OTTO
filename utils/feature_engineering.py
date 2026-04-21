# ---------------------------------------------------------------------------
# feature_engineering.py
# Prepares features from the bundle contracts view for retention model scoring.
# ---------------------------------------------------------------------------

import numpy as np
import pandas as pd

from utils.constants import BUNDLES_NOT_APPLICABLE, FIXED_TOP10_MANUFACTURERS


def engineer_features_for_scoring(df_in: pd.DataFrame) -> pd.DataFrame:
    """Transform df_for_model into the feature set expected by the retention model."""
    df = df_in.copy()

    # --- 0) Discount flags ---
    if "bundle_campaign_disc" in df.columns:
        df["campaign_discounted"] = np.where(df["bundle_campaign_disc"] < 0, 1, 0).astype("int8")

    if "bundle_retention_disc" in df.columns:
        df["retention_discounted"] = np.where(df["bundle_retention_disc"] < 0, 1, 0).astype("int8")

    # --- 1) Applicability flags ---
    features = ["boiler_age", "manufacturer", "combi", "bg_installed", "boiler_size", "rads"]
    for feat in features:
        flag_col = f"{feat}_applicable"
        if "product_bundle" in df.columns:
            df[flag_col] = np.where(df["product_bundle"].isin(BUNDLES_NOT_APPLICABLE), 0, 1).astype("int8")
        else:
            df[flag_col] = 1

    # Force numeric fields to NaN when not applicable
    for col in ["boiler_age", "boiler_size", "rads"]:
        app = f"{col}_applicable"
        if col in df.columns and app in df.columns:
            df.loc[df[app] == 0, col] = np.nan

    # --- 2) Categorical flags: combi / bg_installed -> add 'not_applicable' level ---
    for cat_col in ["combi", "bg_installed"]:
        if cat_col in df.columns:
            s = df[cat_col].astype("string")
            s = s.replace(r"^\s*$", pd.NA, regex=True)
            s[df[f"{cat_col}_applicable"] == 0] = "not_applicable"
            df[cat_col] = s.astype("category")

    # --- 3) Numerical missingness indicators (only when applicable == 1) ---
    for num in ["boiler_age", "boiler_size", "rads"]:
        if num in df.columns:
            df[f"{num}_is_missing"] = (
                df[num].isna() & (df[f"{num}_applicable"] == 1)
            ).astype("int8")

    # --- 4) Manufacturer: 'manufacturer_cat' with fixed top-10 + Others + not_applicable ---
    if "manufacturer" in df.columns:
        m = df["manufacturer"].astype("string").str.strip()
        m = m.replace({"nan": pd.NA, "NaN": pd.NA, "None": pd.NA, "": pd.NA})

        m[df["manufacturer_applicable"] == 0] = "not_applicable"

        is_not_app  = m.eq("not_applicable")
        is_na       = m.isna()
        is_in_top   = m.isin(list(FIXED_TOP10_MANUFACTURERS))
        applicable  = ~is_not_app

        m[applicable & is_na]             = "Others"
        m[applicable & ~is_na & ~is_in_top] = "Others"

        frozen_levels = list(FIXED_TOP10_MANUFACTURERS) + ["Others", "not_applicable"]
        df["manufacturer_cat"] = pd.Categorical(m, categories=frozen_levels)

    # --- 5) YoY feature ---
    premium_col = "bundle_Final_Premium" if "bundle_Final_Premium" in df.columns else "Final_Premium"

    if premium_col in df.columns and "bundle_customer_price" in df.columns:
        safe_div = pd.to_numeric(df["bundle_customer_price"], errors="coerce").replace(0, np.nan)
        numer    = pd.to_numeric(df[premium_col], errors="coerce")
        df["yoy"] = numer / safe_div
        df["yoy"] = df["yoy"].replace([np.inf, -np.inf], np.nan)
        df["yoy"] = df["yoy"].clip(lower=-1, upper=3.0)

    # --- 5a) YoY missingness flag ---
    df["yoy_is_missing"] = df["yoy"].isna().astype("int8") if "yoy" in df.columns else 1

    # --- 5b) Claims cleanup (NaN -> 0) ---
    if "claims" in df.columns:
        df["claims"] = pd.to_numeric(df["claims"], errors="coerce").fillna(0).clip(0, 10)

    # --- 6) Dates -> month cyclical encoding ---
    for col in ["contract_start_date", "contract_end_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "contract_start_date" in df.columns:
        df["contract_start_month"]     = df["contract_start_date"].dt.month
        df["contract_start_month_sin"] = np.sin(2 * np.pi * df["contract_start_month"] / 12)
        df["contract_start_month_cos"] = np.cos(2 * np.pi * df["contract_start_month"] / 12)

    # --- 7) Ensure categorical dtypes ---
    for col in ["product_bundle", "manufacturer_cat", "combi", "bg_installed"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # --- 8) Clip numeric ranges ---
    clip_rules = {
        "bundle_tenure": (0, 40),
        "boiler_age":    (1, 40),
        "boiler_size":   (10, 50),
        "rads":          (0, 20),
        "claims":        (0, 10),
        "yoy":           (-1, 3.0),
    }
    for col, (lo, hi) in clip_rules.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").clip(lower=lo, upper=hi)

    # Remove rows where bundle_tenure == 0 (matches training filter)
    if "bundle_tenure" in df.columns:
        df = df[df["bundle_tenure"] != 0].copy()

    # Drop raw pricing columns AFTER yoy is created
    drop_cols = [
        "bundle_customer_price",
        "bundle_campaign_disc",
        "bundle_retention_disc",
        "bundle_quoted_price_initial",
        "bundle_quoted_price",
        "bundle_retn_discount_initial",
        "bundle_retn_discount_final",
        "bundle_Final_Premium",
        "Final_Premium",
    ]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    return df
