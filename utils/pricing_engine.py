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


# ---------------------------------------------------------------------------
# Future Projections
# ---------------------------------------------------------------------------

_FACTOR_COLS = [
    "f_expense", "f_base_price", "f_boiler_type", "f_manufacturer",
    "f_postal_sector", "f_radiators", "f_boiler_age", "f_asv_price",
    "f_tenure_discount", "f_cap", "f_collar", "f_min", "f_max",
    "c_Risk_Premium", "c_ASV_Premium", "c_Undiscounted_Premium",
    "c_tenure_discount", "Discounted_Premium", "Min_Premium",
    "Max_Premium", "Capped_Premium", "Final_Premium",
]


def calculate_future_projections(
    input_risk_base,
    constraints_df,
    boiler_type_df,
    manufacturer_df,
    postal_sector_df,
    radiators_df,
    boiler_age_df,
    tenure_discount_df,
    inflation_df,
    asv_future_df,
):
    """Calculate projected Final_Premium for Years 1–5.

    Parameters
    ----------
    input_risk_base : DataFrame
        Clean pre-calculation input risk (no factor columns).
    constraints_df : DataFrame
        Y1 constraints keyed on (pricing_key, bundle).
    inflation_df : DataFrame
        Columns: pricing_key, Y2_pct, Y3_pct, Y4_pct, Y5_pct.
        Each Yn_pct is the compound increment applied *on top of* the
        previous year's base (i.e. Y3 base = Y2 base × (1 + Y3_pct/100)).
    asv_future_df : DataFrame
        Columns: pricing_key, ASV_Y1, ASV_Y2, ASV_Y3, ASV_Y4, ASV_Y5.

    Returns
    -------
    DataFrame with columns:
        pricing_key, bundle, [key identifiers],
        boiler_age_1..5, tenure_1..5,
        Final_Premium_Y1..Y5
    """
    # Determine caps for boiler_age and tenure from their lookup tables
    max_boiler_age = (
        int(boiler_age_df["boiler_age"].max())
        if boiler_age_df is not None and not boiler_age_df.empty
        else 99
    )
    max_tenure = (
        int(tenure_discount_df["tenure"].max())
        if tenure_discount_df is not None and not tenure_discount_df.empty
        else 99
    )

    # Base age/tenure series
    base_boiler_age = (
        pd.to_numeric(input_risk_base["boiler_age"], errors="coerce")
        if "boiler_age" in input_risk_base.columns
        else None
    )
    base_tenure = (
        pd.to_numeric(input_risk_base["tenure_for_discount"], errors="coerce")
        if "tenure_for_discount" in input_risk_base.columns
        else None
    )

    # Start result DataFrame with identifier columns
    id_cols = ["pricing_key", "bundle"] + [
        c for c in ["business_agreement", "contract_id", "contract_start_date"]
        if c in input_risk_base.columns
    ]
    result = input_risk_base[[c for c in id_cols if c in input_risk_base.columns]].copy()

    # Build per-pricing_key compound multiplier lookup from inflation_df
    # inflation_df row: pricing_key, Y2_pct, Y3_pct, Y4_pct, Y5_pct
    infl = inflation_df.set_index("pricing_key") if inflation_df is not None else pd.DataFrame()

    # Rolling ly_undiscounted_price: starts from input data, then each year
    # is replaced by the previous year's Final_Premium (for cap/collar calculation).
    rolling_ly_undiscounted = (
        pd.to_numeric(input_risk_base["ly_undiscounted_price"], errors="coerce").values.copy()
        if "ly_undiscounted_price" in input_risk_base.columns
        else None
    )

    for y in range(1, 6):
        age_offset = y - 1

        # ── boiler_age and tenure for this year ──────────────────────────
        if base_boiler_age is not None:
            boiler_age_y = (base_boiler_age + age_offset).clip(upper=max_boiler_age)
        else:
            boiler_age_y = pd.Series([pd.NA] * len(input_risk_base))

        if base_tenure is not None:
            tenure_y = (base_tenure + age_offset).clip(upper=max_tenure)
        else:
            tenure_y = pd.Series([pd.NA] * len(input_risk_base))

        result[f"boiler_age_{y}"] = boiler_age_y.values
        result[f"tenure_{y}"] = tenure_y.values

        # ── Compound inflation multiplier per pricing_key ─────────────────
        # Multiplier for year y = Π(1 + Yk_pct/100) for k = 2..y
        c_mod = constraints_df.copy()
        if y > 1 and not infl.empty:
            def _multiplier(pk):
                m = 1.0
                for k in range(2, y + 1):
                    col = f"Y{k}_pct"
                    pct = float(infl.at[pk, col]) if pk in infl.index and col in infl.columns else 0.0
                    m *= 1.0 + pct / 100.0
                return m

            mult_series = c_mod["pricing_key"].map(_multiplier).fillna(1.0)
            for col in ["f_base_price", "f_min", "f_max"]:
                if col in c_mod.columns:
                    c_mod[col] = c_mod[col] * mult_series

        # ── Override f_asv_price from asv_future_df ───────────────────────
        asv_col = f"ASV_Y{y}"
        if asv_future_df is not None and asv_col in asv_future_df.columns:
            asv_map = (
                asv_future_df[["pricing_key", asv_col]]
                .drop_duplicates("pricing_key")
                .set_index("pricing_key")[asv_col]
                .to_dict()
            )
            if "f_asv_price" in c_mod.columns:
                c_mod["f_asv_price"] = c_mod["pricing_key"].map(asv_map).fillna(c_mod["f_asv_price"])
            else:
                c_mod["f_asv_price"] = c_mod["pricing_key"].map(asv_map).fillna(0.0)
            c_mod["f_asv_price"] = pd.to_numeric(c_mod["f_asv_price"], errors="coerce").fillna(0.0)

        # ── Build modified input_risk copy for this year ──────────────────
        ir_mod = input_risk_base.copy()
        # Drop any pre-existing factor columns to avoid merge conflicts
        ir_mod = ir_mod.drop(columns=[c for c in _FACTOR_COLS if c in ir_mod.columns])

        if base_boiler_age is not None:
            ir_mod["boiler_age"] = boiler_age_y.values
        if base_tenure is not None:
            ir_mod["tenure_for_discount"] = tenure_y.values

        # Feed previous year's Final_Premium as ly_undiscounted_price (Y1 uses original)
        if rolling_ly_undiscounted is not None:
            ir_mod["ly_undiscounted_price"] = rolling_ly_undiscounted

        # ── Run pricing ───────────────────────────────────────────────────
        _pf = calculate_prices(
            ir_mod,
            c_mod,
            boiler_type_df,
            manufacturer_df,
            postal_sector_df,
            radiators_df,
            boiler_age_df,
            tenure_discount_df,
        )

        result[f"Final_Premium_Y{y}"] = _pf["Final_Premium"].values

        # Roll forward: this year's Final_Premium becomes next year's ly_undiscounted_price
        rolling_ly_undiscounted = _pf["Final_Premium"].values.copy()

    return result
