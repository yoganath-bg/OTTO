# ---------------------------------------------------------------------------
# scoring.py
# Databricks model serving utilities for the retention scoring endpoint.
# ---------------------------------------------------------------------------

import math

import numpy as np
import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import DataframeSplitInput

from utils.constants import ENDPOINT_NAME, FEATURE_COLS, SENTINELS


@st.cache_resource
def get_ws_client():
    """Return a cached Databricks WorkspaceClient."""
    return WorkspaceClient()


def enforce_dtypes_for_serving(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce all columns to numeric so the JSON payload stays numeric."""
    X = df.copy()
    for c in X.columns:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    return X


def fill_sentinels_for_transport(X: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN in selected numeric columns with sentinel values to avoid
    JSON null -> object dtype at the serving boundary."""
    X = X.copy()
    for c in ["boiler_age", "boiler_size", "rads", "yoy"]:
        if c in X.columns:
            X[c] = X[c].replace([np.inf, -np.inf], np.nan)
            X[c] = X[c].fillna(SENTINELS.get(c, 0.0))
    for c in ["boiler_age", "boiler_size", "rads", "yoy"]:
        if c in X.columns:
            X[c] = pd.to_numeric(X[c], errors="coerce").fillna(SENTINELS.get(c, 0.0))
    return X


def dataframe_split_payload(df: pd.DataFrame):
    """Serialise a DataFrame into the dataframe_split format expected by the
    Databricks serving endpoint.  Returns (columns, data)."""
    cols = list(df.columns)
    data = []
    for row in df.itertuples(index=False, name=None):
        clean_row = []
        for v in row:
            if isinstance(v, np.generic):
                v = v.item()
            if v is pd.NA:
                v = None
            if isinstance(v, float) and not math.isfinite(v):
                v = 0.0
            clean_row.append(v)
        data.append(clean_row)
    return cols, data


def extract_predictions(resp):
    """Extract the predictions list from a serving endpoint response object."""
    if isinstance(resp, dict):
        return resp.get("predictions")
    if hasattr(resp, "predictions"):
        return resp.predictions
    if hasattr(resp, "as_dict"):
        return resp.as_dict().get("predictions")
    return None


def score_via_endpoint(df_feat: pd.DataFrame, chunk_size: int = 2000, endpoint_name: str | None = None) -> pd.DataFrame:
    """Score df_feat against the retention calibrated model endpoint in chunks.

    Parameters
    ----------
    df_feat       : DataFrame containing at least all FEATURE_COLS.
    chunk_size    : Number of rows per API call (default 2000).
    endpoint_name : Databricks serving endpoint to call. Defaults to ENDPOINT_NAME
                    from constants if not provided.

    Returns df_feat with two extra columns: prob_retention, prob_churn.
    """
    target_endpoint = endpoint_name or ENDPOINT_NAME
    missing = set(FEATURE_COLS) - set(df_feat.columns)
    if missing:
        raise ValueError(f"Missing required features: {sorted(missing)}")

    w = get_ws_client()
    X = df_feat[FEATURE_COLS].copy()
    X = enforce_dtypes_for_serving(X)
    X = fill_sentinels_for_transport(X)

    all_preds = []
    for start in range(0, len(X), chunk_size):
        chunk = X.iloc[start : start + chunk_size]
        cols, data = dataframe_split_payload(chunk)
        dfs = DataframeSplitInput(columns=cols, data=data)

        resp  = w.serving_endpoints.query(name=target_endpoint, dataframe_split=dfs)
        preds = extract_predictions(resp)
        if preds is None:
            raise RuntimeError(f"No predictions returned: {resp}")
        all_preds.extend(preds)

    proba_ret = np.asarray(all_preds, dtype=float)
    out = df_feat.copy()
    out["prob_retention"] = proba_ret
    out["prob_churn"]     = 1.0 - proba_ret
    return out
