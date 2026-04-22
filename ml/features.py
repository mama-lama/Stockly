from __future__ import annotations

import pandas as pd

from ml.constants import GROUP_COL, HORIZONS, TARGET_COL


def add_targets(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for horizon in HORIZONS:
        result[f"target_h{horizon}"] = result.groupby(GROUP_COL)[TARGET_COL].shift(-horizon)
    return result
