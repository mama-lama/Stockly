from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ml.baselines import add_last_value_baseline, add_moving_average_baseline
from ml.constants import (
    DATE_COL,
    DEFAULT_OUTPUT_PATH,
    GROUP_COL,
    HORIZONS,
    TARGET_COL,
    TEST_END,
    TEST_START,
    TRAIN_END,
    TRAIN_START,
)
from ml.evaluation import mae, wape
from ml.features import add_targets
from ml.io import load_dataset
from ml.models import predict_with_lightgbm


def _compute_baselines(df: pd.DataFrame) -> pd.DataFrame:
    with_last = add_last_value_baseline(df, target_col=TARGET_COL)
    return add_moving_average_baseline(
        with_last,
        group_col=GROUP_COL,
        target_col=TARGET_COL,
        window=7,
    )


def _evaluate(df: pd.DataFrame, *, max_train_rows: int) -> pd.DataFrame:
    train_mask = (df[DATE_COL] >= TRAIN_START) & (df[DATE_COL] <= TRAIN_END)
    test_mask = (df[DATE_COL] >= TEST_START) & (df[DATE_COL] <= TEST_END)

    if not train_mask.any():
        raise ValueError("Train split is empty. Check date range and dataset coverage.")
    if not test_mask.any():
        raise ValueError("Test split is empty. Check date range and dataset coverage.")

    rows: list[dict[str, float | int | str]] = []
    baselines = (
        ("last_value", "pred_last_value"),
        ("moving_avg_7", "pred_moving_avg_7"),
    )

    for horizon in HORIZONS:
        target_col = f"target_h{horizon}"
        horizon_frame = df.loc[test_mask & df[target_col].notna()].copy()

        for baseline_name, prediction_col in baselines:
            y_true = horizon_frame[target_col].to_numpy()
            y_pred = horizon_frame[prediction_col].to_numpy()

            rows.append(
                {
                    "horizon": horizon,
                    "model": baseline_name,
                    "mae": mae(y_true, y_pred),
                    "wape": wape(y_true, y_pred),
                    "rows": int(len(horizon_frame)),
                }
            )

        lightgbm_result = predict_with_lightgbm(
            df=df,
            horizon=horizon,
            train_mask=train_mask,
            test_mask=test_mask,
            target_col=TARGET_COL,
            date_col=DATE_COL,
            max_train_rows=max_train_rows,
        )
        rows.append(
            {
                "horizon": horizon,
                "model": "lightgbm",
                "mae": mae(lightgbm_result.y_true, lightgbm_result.y_pred),
                "wape": wape(lightgbm_result.y_true, lightgbm_result.y_pred),
                "rows": lightgbm_result.rows,
            }
        )

    return pd.DataFrame(rows).sort_values(["horizon", "model"]).reset_index(drop=True)


def run(
    dataset_path: str | None = None,
    output_path: str | None = None,
    max_train_rows: int = 250_000,
) -> pd.DataFrame:
    df, source_path = load_dataset(dataset_path)

    df = add_targets(df)
    df = _compute_baselines(df)
    metrics = _evaluate(df, max_train_rows=max_train_rows)

    final_output_path = Path(output_path) if output_path else DEFAULT_OUTPUT_PATH
    final_output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(final_output_path, index=False)

    print(f"Dataset: {source_path}")
    print(f"Saved metrics to: {final_output_path}")
    print(metrics.to_string(index=False))

    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run baseline and LightGBM demand forecasting metrics.")
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=None,
        help="Path to train_dataset.csv. If omitted, known defaults are checked.",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Where to save the metrics CSV (default: ml/artifacts/forecast_metrics.csv).",
    )
    parser.add_argument(
        "--max-train-rows",
        type=int,
        default=250000,
        help="Max rows per horizon for LightGBM train split sampling (default: 250000).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        dataset_path=args.dataset_path,
        output_path=args.output_path,
        max_train_rows=args.max_train_rows,
    )
