from __future__ import annotations

import pandas as pd


def add_last_value_baseline(
    df: pd.DataFrame,
    *,
    target_col: str,
    prediction_col: str = "pred_last_value",
) -> pd.DataFrame:
    result = df.copy()
    result[prediction_col] = result[target_col]
    return result
