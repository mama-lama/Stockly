from __future__ import annotations

import pandas as pd


def add_moving_average_baseline(
    df: pd.DataFrame,
    *,
    group_col: str,
    target_col: str,
    window: int = 7,
    prediction_col: str = "pred_moving_avg_7",
) -> pd.DataFrame:
    """Add trailing moving average baseline per SKU."""
    result = df.copy()
    result[prediction_col] = (
        result.groupby(group_col, group_keys=False)[target_col]
        .rolling(window=window, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )
    return result
