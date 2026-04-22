from __future__ import annotations

from pathlib import Path

HORIZONS = (1, 7, 14, 28)

TRAIN_START = "2022-01-01"
TRAIN_END = "2024-12-31"
TEST_START = "2025-01-01"
TEST_END = "2026-04-30"

DATE_COL = "date"
GROUP_COL = "sku_id"
TARGET_COL = "sales_qty"

DEFAULT_DATASET_CANDIDATES = (
    Path("data/checks/train_dataset.csv"),
    Path("data/processed/train_dataset.csv"),
    Path("data/checks/20260419_161515/processed/train_dataset.csv"),
    Path("data/tmp_checks/processed/train_dataset.csv"),
)

DEFAULT_OUTPUT_PATH = Path("ml/artifacts/forecast_metrics.csv")
DEFAULT_FUTURE_OUTPUT_PATH = Path("ml/artifacts/future_forecast.csv")
