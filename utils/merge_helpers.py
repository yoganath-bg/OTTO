# ---------------------------------------------------------------------------
# merge_helpers.py
# Left-join lookup helpers used by calculate_prices.
# Each function merges a single factor column from a lookup table onto df.
# ---------------------------------------------------------------------------

import pandas as pd


def merge_lookup_bundle(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[["pricing_key", "bundle", value_to_return]],
        how="left",
        left_on=["pricing_key", "bundle"],
        right_on=["pricing_key", "bundle"],
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(0)
    return df


def merge_combi_boiler_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[["pricing_key", "combi_boiler", value_to_return]],
        how="left",
        left_on=["pricing_key", "combi_boiler"],
        right_on=["pricing_key", "combi_boiler"],
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df


def merge_manufacturer_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[["pricing_key", "manufacturer", value_to_return]],
        how="left",
        left_on=["pricing_key", "manufacturer"],
        right_on=["pricing_key", "manufacturer"],
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df


def merge_postal_sector_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[["pricing_key", "postal_sector", value_to_return]],
        how="left",
        left_on=["pricing_key", "postal_sector"],
        right_on=["pricing_key", "postal_sector"],
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df


def merge_radiators_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[["pricing_key", "radiators", value_to_return]],
        how="left",
        left_on=["pricing_key", "radiators"],
        right_on=["pricing_key", "radiators"],
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df


def merge_boiler_age_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[["pricing_key", "boiler_age", value_to_return]],
        how="left",
        left_on=["pricing_key", "boiler_age"],
        right_on=["pricing_key", "boiler_age"],
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df


def merge_simple_pricing_key_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[["pricing_key", value_to_return]],
        how="left",
        left_on=["pricing_key"],
        right_on=["pricing_key"],
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(0)
    return df


def merge_tenure_discount_lookup_value(df, value_to_return, lookup_table):
    df = df.merge(
        lookup_table[["pricing_key", "bundle", "tenure", value_to_return]],
        how="left",
        left_on=["pricing_key", "bundle", "tenure_for_discount"],
        right_on=["pricing_key", "bundle", "tenure"],
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(0)
    return df
