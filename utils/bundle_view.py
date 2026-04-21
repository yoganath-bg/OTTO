# ---------------------------------------------------------------------------
# bundle_view.py
# Builds the contract-level bundle view from premium_file.
# Replicates the Spark SQL bundle CTE logic in pandas.
# ---------------------------------------------------------------------------

import numpy as np
import pandas as pd

from utils.constants import KEY_COLS, KEYS_PLUS


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def coalesce_series(*series_list):
    """Return the first non-null value across a list of Series, element-wise."""
    valid = [s for s in series_list if s is not None]
    if not valid:
        return pd.Series(dtype=object)
    cleaned = [s.replace(r"^\s*$", np.nan, regex=True) for s in valid]
    out = cleaned[0].copy()
    for s in cleaned[1:]:
        out = out.where(out.notna(), s)
    return out


def add_prefix_except_keys(df, prefix, key_cols):
    """Prefix all columns that are not join key columns."""
    rename = {c: f"{prefix}{c}" for c in df.columns if c not in key_cols}
    return df.rename(columns=rename)


def to_string(df, cols):
    """Cast specified columns to string dtype."""
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype("string")
    return df


def to_date(df, col):
    """Parse a column to date (date only, no time)."""
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df


def clean_select(df, cols):
    """Select only existing columns, cast keys to string/date."""
    cols_present = [c for c in cols if c in df.columns]
    out = df.loc[:, cols_present].copy()
    out = to_string(out, ["business_agreement", "contract_id"])
    out = to_date(out, "contract_start_date")
    return out


def prep_for_merge(df, prefix):
    """Prefix non-key columns so product tables can be joined without collision."""
    out = df.copy()
    out = add_prefix_except_keys(out, prefix, KEY_COLS)
    return out


def _sum_fill0(df, cols):
    """Sum specified columns across axis=1, treating NaN as 0."""
    existing = [c for c in cols if c in df.columns]
    return df[existing].fillna(0).sum(axis=1) if existing else 0


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def build_contracts_view(premium_file: pd.DataFrame) -> pd.DataFrame:
    """Split premium_file by product, build a bundle-level contracts view,
    and return df_for_model ready for feature engineering.

    Replicates the Spark SQL CTE bundle logic in pandas.
    """
    # --- 1) Split into product DataFrames ---
    bcc = premium_file[premium_file["pricing_key"].isin(["BNI1", "BNI2"])].copy()
    chc = premium_file[premium_file["pricing_key"].isin(["CNI1", "CNI2"])].copy()
    pad = premium_file[premium_file["pricing_key"].isin(["DNI1", "DNI2"])].copy()
    hec = premium_file[premium_file["pricing_key"].isin(["HNI1", "HNI2"])].copy()

    # --- 2) Column selections per product (matching SQL CTEs) ---
    pad_cols = [
        "business_agreement", "contract_id", "contract_start_date", "contract_end_date",
        "policy_tenure_at_renewal", "postal_sector", "pricing_key", "excess",
        "campaign_disc", "actual_policy_discount", "ly_customer_price",
        "autoconsent_renewal_ind", "Final_Premium", "gack_kac",
    ]
    bcc_cols = [
        "business_agreement", "contract_id", "contract_start_date", "contract_end_date",
        "policy_tenure_at_renewal", "postal_sector", "boiler_age", "manufacturer",
        "combi_boiler", "installedby_bg", "boiler_size", "radiators", "claim_count",
        "pricing_key", "excess", "campaign_disc", "actual_policy_discount",
        "ly_customer_price", "autoconsent_renewal_ind", "Final_Premium", "gack_kac",
    ]
    chc_cols = bcc_cols.copy()
    hec_cols = [
        "business_agreement", "contract_id", "contract_start_date", "contract_end_date",
        "policy_tenure_at_renewal", "postal_sector", "pricing_key", "excess",
        "campaign_disc", "actual_policy_discount", "ly_customer_price",
        "autoconsent_renewal_ind", "Final_Premium", "gack_kac",
    ]

    # --- 3) Clean + select ---
    pad_clean = clean_select(pad, pad_cols)
    bcc_clean = clean_select(bcc, bcc_cols)
    chc_clean = clean_select(chc, chc_cols)
    hec_clean = clean_select(hec, hec_cols)

    # --- 4) Build distinct contract keys (UNION of all 4 sources) ---
    keys = pd.concat(
        [pad_clean[KEYS_PLUS], bcc_clean[KEYS_PLUS], chc_clean[KEYS_PLUS], hec_clean[KEYS_PLUS]],
        axis=0, ignore_index=True,
    ).drop_duplicates()

    # --- 5) Prefix non-key columns + apply SQL alias renames ---
    bcc_p = prep_for_merge(bcc_clean, "bcc_")
    chc_p = prep_for_merge(chc_clean, "chc_")
    pad_p = prep_for_merge(pad_clean, "pad_")
    hec_p = prep_for_merge(hec_clean, "hec_")

    bcc_p = bcc_p.rename(columns={k: v for k, v in {
        "bcc_combi_boiler":            "bcc_combi",
        "bcc_installedby_bg":          "bcc_bg_installed",
        "bcc_radiators":               "bcc_rads",
        "bcc_claim_count":             "bcc_claims",
        "bcc_gack_kac":                "bcc_gackkac",
        "bcc_policy_tenure_at_renewal":"bcc_tenure",
    }.items() if k in bcc_p.columns})

    chc_p = chc_p.rename(columns={k: v for k, v in {
        "chc_combi_boiler":            "chc_combi",
        "chc_installedby_bg":          "chc_bg_installed",
        "chc_radiators":               "chc_rads",
        "chc_claim_count":             "chc_claims",
        "chc_gack_kac":                "chc_gackkac",
        "chc_policy_tenure_at_renewal":"chc_tenure",
    }.items() if k in chc_p.columns})

    pad_p = pad_p.rename(columns={k: v for k, v in {
        "pad_gack_kac":                "pad_gackkac",
        "pad_policy_tenure_at_renewal":"pad_tenure",
    }.items() if k in pad_p.columns})

    hec_p = hec_p.rename(columns={k: v for k, v in {
        "hec_gack_kac":                "hec_gackkac",
        "hec_policy_tenure_at_renewal":"hec_tenure",
    }.items() if k in hec_p.columns})

    # --- 6) Left-join all product tables to the key set ---
    contracts_view = (
        keys.copy()
        .merge(bcc_p, how="left", on=KEY_COLS)
        .merge(chc_p, how="left", on=KEY_COLS)
        .merge(pad_p, how="left", on=KEY_COLS)
        .merge(hec_p, how="left", on=KEY_COLS)
    )

    # --- 7) Product presence indicator flags ---
    contracts_view["bcc"] = np.where(contracts_view["bcc_pricing_key"].notna(), 1, 0)
    contracts_view["chc"] = np.where(contracts_view["chc_pricing_key"].notna(), 1, 0)
    contracts_view["pad"] = np.where(contracts_view["pad_pricing_key"].notna(), 1, 0)
    contracts_view["hec"] = np.where(contracts_view["hec_pricing_key"].notna(), 1, 0)

    # --- 8) product_bundle label (replicates SQL CASE) ---
    b = contracts_view["bcc"].eq(1)
    c = contracts_view["chc"].eq(1)
    p = contracts_view["pad"].eq(1)
    h = contracts_view["hec"].eq(1)

    contracts_view["product_bundle"] = np.select(
        [
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
        ],
        ["HC1", "HC2", "HC3", "HC4",
         "BCC+PAD", "BCC+HEC", "BCC+PAD+HEC",
         "PAD+HEC", "CHC+HEC", "PAD Standalone", "HEC Standalone"],
        default="Others",
    )

    # --- 9) bundle_excess logic ---
    excess_cols   = ["bcc_excess", "chc_excess", "pad_excess", "hec_excess"]
    product_flags = ["bcc", "chc", "pad", "hec"]
    excess_df     = contracts_view[excess_cols].where(contracts_view[product_flags].values == 1)
    distinct_excess = excess_df.nunique(axis=1, dropna=True)

    contracts_view["bundle_excess"] = np.select(
        [
            (distinct_excess == 1) & (excess_df.max(axis=1) == 0),
            (distinct_excess == 1) & (excess_df.max(axis=1) == 60),
        ],
        ["0", "60"],
        default="Mixed",
    )

    # --- 10) Coalesced attributes ---
    contracts_view["autoconsent_renewal_ind"] = coalesce_series(
        contracts_view.get("bcc_autoconsent_renewal_ind"),
        contracts_view.get("chc_autoconsent_renewal_ind"),
        contracts_view.get("pad_autoconsent_renewal_ind"),
        contracts_view.get("hec_autoconsent_renewal_ind"),
    )

    for col in ["bcc_tenure", "chc_tenure", "pad_tenure", "hec_tenure"]:
        if col in contracts_view.columns:
            contracts_view[col] = pd.to_numeric(contracts_view[col], errors="coerce")
    contracts_view["bundle_tenure"] = contracts_view[
        ["bcc_tenure", "chc_tenure", "pad_tenure", "hec_tenure"]
    ].max(axis=1, skipna=True)

    for col in ["bcc_gackkac", "chc_gackkac", "pad_gackkac", "hec_gackkac"]:
        if col in contracts_view.columns:
            contracts_view[col] = pd.to_numeric(contracts_view[col], errors="coerce")
    contracts_view["bundle_gack_kac"] = contracts_view[
        ["bcc_gackkac", "chc_gackkac", "pad_gackkac", "hec_gackkac"]
    ].max(axis=1, skipna=True)

    contracts_view["postal_sector"] = coalesce_series(
        contracts_view.get("bcc_postal_sector"),
        contracts_view.get("chc_postal_sector"),
        contracts_view.get("pad_postal_sector"),
        contracts_view.get("hec_postal_sector"),
    )
    contracts_view["boiler_age"]  = coalesce_series(
        contracts_view.get("bcc_boiler_age"),  contracts_view.get("chc_boiler_age"),
    )
    contracts_view["manufacturer"] = coalesce_series(
        contracts_view.get("bcc_manufacturer"), contracts_view.get("chc_manufacturer"),
    )
    contracts_view["combi"] = coalesce_series(
        contracts_view.get("bcc_combi"), contracts_view.get("chc_combi"),
    )
    contracts_view["bg_installed"] = coalesce_series(
        contracts_view.get("bcc_bg_installed"), contracts_view.get("chc_bg_installed"),
    )
    contracts_view["boiler_size"] = coalesce_series(
        contracts_view.get("bcc_boiler_size"), contracts_view.get("chc_boiler_size"),
    )
    contracts_view["rads"] = coalesce_series(
        contracts_view.get("bcc_rads"), contracts_view.get("chc_rads"),
    )
    contracts_view["claims"] = coalesce_series(
        contracts_view.get("bcc_claims"), contracts_view.get("chc_claims"),
    )

    # --- 11) Bundle-level sums ---
    contracts_view["bundle_campaign_disc"] = _sum_fill0(
        contracts_view, ["bcc_campaign_disc", "chc_campaign_disc", "pad_campaign_disc", "hec_campaign_disc"],
    )
    contracts_view["bundle_retention_disc"] = _sum_fill0(
        contracts_view,
        ["bcc_actual_policy_discount", "chc_actual_policy_discount",
         "pad_actual_policy_discount", "hec_actual_policy_discount"],
    )
    contracts_view["bundle_customer_price"] = _sum_fill0(
        contracts_view,
        ["bcc_ly_customer_price", "chc_ly_customer_price",
         "pad_ly_customer_price", "hec_ly_customer_price"],
    )
    contracts_view["bundle_Final_Premium"] = _sum_fill0(
        contracts_view,
        ["bcc_Final_Premium", "chc_Final_Premium", "pad_Final_Premium", "hec_Final_Premium"],
    )

    # --- 12) Select output columns for model ---
    req_columns = [
        "business_agreement", "contract_start_date", "contract_end_date", "product_bundle",
        "bundle_excess", "autoconsent_renewal_ind", "bundle_tenure", "bundle_gack_kac",
        "boiler_age", "manufacturer", "combi", "bg_installed", "boiler_size", "rads", "claims",
        "bundle_campaign_disc", "bundle_retention_disc", "bundle_customer_price", "bundle_Final_Premium",
    ]
    return contracts_view[req_columns]
