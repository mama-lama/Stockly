from __future__ import annotations

from pathlib import Path

import pandas as pd

from ml.constants import DATE_COL, DEFAULT_DATASET_CANDIDATES, GROUP_COL, TARGET_COL


def resolve_dataset_path(explicit_path: str | None) -> Path:
    if explicit_path:
        candidate = Path(explicit_path)
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"Dataset not found: {candidate}")

    for candidate in DEFAULT_DATASET_CANDIDATES:
        if candidate.exists():
            return candidate

    searched = ", ".join(str(path) for path in DEFAULT_DATASET_CANDIDATES)
    raise FileNotFoundError(f"Dataset not found. Checked: {searched}")


def load_dataset(dataset_path: str | None = None) -> tuple[pd.DataFrame, Path]:
    source_path = resolve_dataset_path(dataset_path)
    df = pd.read_csv(source_path, low_memory=False)

    required = {DATE_COL, GROUP_COL, TARGET_COL}
    missing = required.difference(df.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise ValueError(f"Dataset missing required columns: {missing_columns}")

    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df = df.sort_values([GROUP_COL, DATE_COL]).reset_index(drop=True)
    return df, source_path
