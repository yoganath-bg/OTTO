# ---------------------------------------------------------------------------
# summary.py
# YoY summary table computation used on the Calculate page.
# ---------------------------------------------------------------------------

import numpy as np
import pandas as pd


def compute_yoy(
    df,
    group_col="pricing_key",
    final_col="Final_Premium",
    ly_col="ly_customer_price",
    zero_division="nan",
):
    """For each group compute volume, avg LY price, min/max/avg renewal price,
    and YoY %.  Appends a final 'Total' row across all records.

    group_col can be a single column name (str) or a list of column names for
    multi-column groupby (e.g. ["product_bundle", "bundle_excess"]).

    Returns a formatted DataFrame ready for st.dataframe().
    """
    group_cols = [group_col] if isinstance(group_col, str) else list(group_col)
    missing = [c for c in group_cols + [final_col, ly_col] if c not in df.columns]
    if missing:
        raise ValueError(f"DataFrame must contain columns: {missing}")

    df_work = df[group_cols + [final_col, ly_col]].copy()
    df_work[final_col] = pd.to_numeric(df_work[final_col], errors="coerce").fillna(0.0)
    df_work[ly_col]    = pd.to_numeric(df_work[ly_col],    errors="coerce").fillna(0.0)

    agg_df = df_work.groupby(group_cols, dropna=False).agg(
        sum_final =(final_col, "sum"),
        sum_ly    =(ly_col,    "sum"),
        volume    =(ly_col,    "count"),
        avg_ly    =(ly_col,    "mean"),
        min_final =(final_col, "min"),
        max_final =(final_col, "max"),
        avg_final =(final_col, "mean"),
    ).reset_index()

    def _yoy_pct(a, b):
        if b == 0:
            return np.inf if zero_division == "inf" else np.nan
        return ((a / b) - 1) * 100

    agg_df["yoy_pct_raw"] = agg_df.apply(lambda r: _yoy_pct(r["avg_final"], r["avg_ly"]), axis=1)

    agg_df["Volume"]           = agg_df["volume"]
    agg_df["Last_Year_Price"]   = agg_df["avg_ly"].round(2).apply(lambda x: f"£{x:,.2f}")
    agg_df["Min_Renewal_Price"] = agg_df["min_final"].round(2).apply(lambda x: f"£{x:,.2f}")
    agg_df["Max_Renewal_Price"] = agg_df["max_final"].round(2).apply(lambda x: f"£{x:,.2f}")
    agg_df["Avg_Renewal_Price"] = agg_df["avg_final"].round(2).apply(lambda x: f"£{x:,.2f}")

    def fmt_pct(x):
        if pd.isna(x):
            return "nan"
        if np.isinf(x):
            return "inf"
        return f"{round(x, 2)}%"

    agg_df["yoy_pct"] = agg_df["yoy_pct_raw"].apply(fmt_pct)

    result = agg_df[
        group_cols + ["Volume", "Last_Year_Price", "Min_Renewal_Price",
                      "Max_Renewal_Price", "Avg_Renewal_Price", "yoy_pct"]
    ].copy()

    # --- Append TOTAL row ---
    total_volume    = int(df_work.shape[0])
    total_avg_ly    = float(df_work[ly_col].mean())    if total_volume > 0 else 0.0
    total_avg_final = float(df_work[final_col].mean()) if total_volume > 0 else 0.0
    total_min_final = float(df_work[final_col].min())  if total_volume > 0 else 0.0
    total_max_final = float(df_work[final_col].max())  if total_volume > 0 else 0.0

    total_yoy_fmt = fmt_pct(_yoy_pct(total_avg_final, total_avg_ly))

    # For multi-column groupby put "Total" in the first group column, blank in rest
    total_row_data = {col: [""] for col in group_cols}
    total_row_data[group_cols[0]] = ["Total"]
    total_row_data.update({
        "Volume":            [total_volume],
        "Last_Year_Price":   [f"£{total_avg_ly:,.2f}"],
        "Min_Renewal_Price": [f"£{total_min_final:,.2f}"],
        "Max_Renewal_Price": [f"£{total_max_final:,.2f}"],
        "Avg_Renewal_Price": [f"£{total_avg_final:,.2f}"],
        "yoy_pct":           [total_yoy_fmt],
    })

    return pd.concat([result, pd.DataFrame(total_row_data)], ignore_index=True)
