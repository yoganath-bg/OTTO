# ---------------------------------------------------------------------------
# ui_helpers.py
# Reusable UI utilities shared across view pages.
# ---------------------------------------------------------------------------

import pandas as pd

HR_DIVIDER = """<div class="otto-divider"></div>"""


def hr_divider() -> str:
    """Return the standard horizontal rule HTML used across all pages."""
    return HR_DIVIDER


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column headers: strip whitespace, replace runs of spaces with
    underscores, and lowercase everything."""
    df = df.copy()
    df.columns = df.columns.astype(str)
    df.columns = df.columns.str.strip().str.replace(r"\s+", "_", regex=True).str.lower()
    return df
