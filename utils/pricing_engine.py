# ---------------------------------------------------------------------------
# pricing_engine.py
# Core pricing logic: constraints builder and price calculation.
# ---------------------------------------------------------------------------

import re
import pandas as pd

from utils.merge_helpers import (
    merge_lookup_bundle,
    merge_combi_boiler_lookup_value,
    merge_manufacturer_lookup_value,
    merge_postal_sector_lookup_value,
    merge_radiators_lookup_value,
    merge_boiler_age_lookup_value,
    merge_tenure_discount_lookup_value,
)


def sheet_to_varname(name: str) -> str:
    """Convert a sheet name into a safe Python variable name with a _df suffix."""
    v = name.strip().lower()
    v = re.sub(r"\W+", "_", v)
    v = re.sub(r"^_+", "", v)
    v = re.sub(r"_+$", "", v)
    if not v:
        v = "sheet"
    return f"{v}_df"


def _ci_col(df, colname):
    """Return the actual column name from df that matches colname
    case-insensitively, or None if not found."""
    if df is None:
        return None
    for c in df.columns:
        if str(c).strip().lower() == colname.strip().lower():
            return c
    return None


def build_constraints_df(base, asv, caps, minmax):
    """Build the constraints DataFrame by merging base price, ASV, caps/collars,
    and min/max tables.  Returns a DataFrame with pricing_key, bundle (if present),
    and all expected numeric factor columns.
    """
    pk_col     = _ci_col(base, "pricing_key")
    bundle_col = _ci_col(base, "bundle")  # may be None

    cols      = [pk_col]
    base_copy = base.copy()

    # Standardise base price column name
    base_price_col = _ci_col(base_copy, "f_base_price") or _ci_col(base_copy, "price")
    if base_price_col:
        if base_price_col != "f_base_price":
            base_copy = base_copy.rename(columns={base_price_col: "f_base_price"})
        cols.append("f_base_price")
    else:
        base_copy["f_base_price"] = 0.0
        cols.append("f_base_price")

    if bundle_col:
        if bundle_col != "bundle":
            base_copy = base_copy.rename(columns={bundle_col: "bundle"})
        cols.append("bundle")

    constraints_df = base_copy[cols].drop_duplicates(subset=[pk_col, bundle_col]).copy()

    if pk_col != "pricing_key":
        constraints_df = constraints_df.rename(columns={pk_col: "pricing_key"})

    # Merge ASV
    if asv is not None and _ci_col(asv, "pricing_key") is not None:
        asv_pk = _ci_col(asv, "pricing_key")
        if _ci_col(asv, "f_asv_price") is None and _ci_col(asv, "price") is not None:
            asv = asv.rename(columns={_ci_col(asv, "price"): "f_asv_price"})
        if _ci_col(asv, "f_asv_price") is not None:
            asv = asv.rename(columns={asv_pk: "pricing_key"})
            constraints_df = constraints_df.merge(
                asv[["pricing_key", "f_asv_price"]].drop_duplicates("pricing_key"),
                on="pricing_key", how="left",
            )

    # Merge Caps & Collar
    if caps is not None and _ci_col(caps, "pricing_key") is not None:
        caps_pk = _ci_col(caps, "pricing_key")
        if _ci_col(caps, "f_collar") is None and _ci_col(caps, "collar") is not None:
            caps = caps.rename(columns={_ci_col(caps, "collar"): "f_collar"})
        if _ci_col(caps, "f_cap") is None and _ci_col(caps, "cap") is not None:
            caps = caps.rename(columns={_ci_col(caps, "cap"): "f_cap"})
        avail = [c for c in ["pricing_key", "f_collar", "f_cap"] if c in caps.columns]
        if len(avail) > 1:
            caps = caps.rename(columns={caps_pk: "pricing_key"})
            constraints_df = constraints_df.merge(
                caps[avail].drop_duplicates("pricing_key"),
                on="pricing_key", how="left",
            )

    # Merge Min/Max
    if minmax is not None and _ci_col(minmax, "pricing_key") is not None:
        mm_pk = _ci_col(minmax, "pricing_key")
        if _ci_col(minmax, "f_min") is None and _ci_col(minmax, "minimum_premium") is not None:
            minmax = minmax.rename(columns={_ci_col(minmax, "minimum_premium"): "f_min"})
        if _ci_col(minmax, "f_max") is None and _ci_col(minmax, "maximum_premium") is not None:
            minmax = minmax.rename(columns={_ci_col(minmax, "maximum_premium"): "f_max"})
        avail = [c for c in ["pricing_key", "f_min", "f_max"] if c in minmax.columns]
        if len(avail) > 1:
            minmax = minmax.rename(columns={mm_pk: "pricing_key"})
            constraints_df = constraints_df.merge(
                minmax[avail].drop_duplicates("pricing_key"),
                on="pricing_key", how="left",
            )

    # Ensure all expected numeric columns exist and are numeric
    expected = ["f_base_price", "f_asv_price", "f_collar", "f_cap", "f_min", "f_max"]
    for c in expected:
        if c not in constraints_df.columns:
            constraints_df[c] = 0.0
        constraints_df[c] = pd.to_numeric(constraints_df[c], errors="coerce").fillna(0.0).astype(float)

    # Reorder columns: pricing_key, bundle (if present), then numeric factors
    cols_order = ["pricing_key"]
    if "bundle" in constraints_df.columns:
        cols_order.append("bundle")
    cols_order.extend(expected)
    constraints_df = constraints_df[cols_order]

    return constraints_df


def calculate_prices(
    input_risk,
    constraints_df,
    boiler_type_df,
    manufacturer_df,
    postal_sector_df,
    radiators_df,
    boiler_age_df,
    tenure_discount_df,
):
    """Apply all rating factors to input_risk and return file with premium columns."""
    input_risk["f_expense"] = 0.01
    input_risk = merge_lookup_bundle(input_risk, "f_base_price", constraints_df)
    input_risk = merge_combi_boiler_lookup_value(input_risk, "f_boiler_type", boiler_type_df)
    input_risk = merge_manufacturer_lookup_value(input_risk, "f_manufacturer", manufacturer_df)
    input_risk = merge_postal_sector_lookup_value(input_risk, "f_postal_sector", postal_sector_df)
    input_risk = merge_radiators_lookup_value(input_risk, "f_radiators", radiators_df)
    input_risk = merge_boiler_age_lookup_value(input_risk, "f_boiler_age", boiler_age_df)
    input_risk = merge_lookup_bundle(input_risk, "f_asv_price", constraints_df)
    input_risk = merge_tenure_discount_lookup_value(input_risk, "f_tenure_discount", tenure_discount_df)
    input_risk = merge_lookup_bundle(input_risk, "f_cap", constraints_df)
    input_risk = merge_lookup_bundle(input_risk, "f_collar", constraints_df)
    input_risk = merge_lookup_bundle(input_risk, "f_min", constraints_df)
    input_risk = merge_lookup_bundle(input_risk, "f_max", constraints_df)

    input_risk["c_Risk_Premium"] = (
        (input_risk["f_base_price"] + input_risk["f_expense"])
        * input_risk["f_boiler_type"]
        * input_risk["f_manufacturer"]
        * input_risk["f_postal_sector"]
        * input_risk["f_radiators"]
        * input_risk["f_boiler_age"]
    )
    input_risk["c_ASV_Premium"]        = input_risk["f_asv_price"]
    input_risk["c_Undiscounted_Premium"] = input_risk["c_Risk_Premium"] + input_risk["c_ASV_Premium"]
    input_risk["c_tenure_discount"]    = input_risk["c_Undiscounted_Premium"] * input_risk["f_tenure_discount"]
    input_risk["Discounted_Premium"]   = input_risk["c_Undiscounted_Premium"] - input_risk["c_tenure_discount"]
    input_risk["Min_Premium"]          = input_risk["ly_undiscounted_price"] * input_risk["f_collar"]
    input_risk["Max_Premium"]          = input_risk["ly_undiscounted_price"] * input_risk["f_cap"]
    input_risk["Capped_Premium"]       = input_risk.apply(
        lambda row: min(max(row["Min_Premium"], row["Discounted_Premium"]), row["Max_Premium"]), axis=1
    )
    input_risk["Final_Premium"]        = input_risk.apply(
        lambda row: min(max(row["f_min"], row["Capped_Premium"]), row["f_max"]), axis=1
    )

    return input_risk
