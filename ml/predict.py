from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ml.constants import (
    DATE_COL,
    DEFAULT_FUTURE_OUTPUT_PATH,
    GROUP_COL,
    HORIZONS,
    TARGET_COL,
)
from ml.features import add_targets
from ml.io import load_dataset
from ml.models import predict_from_bundle, train_lightgbm_for_horizon


def _latest_rows_per_sku(df: pd.DataFrame) -> pd.DataFrame:
    latest_idx = df.groupby(GROUP_COL)[DATE_COL].idxmax()
    return df.loc[latest_idx].copy().reset_index(drop=True)


def run(
    dataset_path: str | None = None,
    output_path: str | None = None,
    max_train_rows: int = 250_000,
) -> pd.DataFrame:
    df, source_path = load_dataset(dataset_path)
    df = add_targets(df)

    all_rows_train_mask = pd.Series(True, index=df.index)
    inference_frame = _latest_rows_per_sku(df)

    rows: list[dict[str, object]] = []
    for horizon in HORIZONS:
        bundle = train_lightgbm_for_horizon(
            df=df,
            horizon=horizon,
            train_mask=all_rows_train_mask,
            target_col=TARGET_COL,
            date_col=DATE_COL,
            max_train_rows=max_train_rows,
        )
        preds = predict_from_bundle(bundle=bundle, frame=inference_frame)

        horizon_frame = inference_frame[[GROUP_COL, DATE_COL]].copy()
        horizon_frame["horizon"] = horizon
        horizon_frame["forecast_date"] = horizon_frame[DATE_COL] + pd.to_timedelta(horizon, unit="D")
        horizon_frame["predicted_sales_qty"] = preds.clip(min=0.0)
        horizon_frame.rename(columns={DATE_COL: "base_date"}, inplace=True)

        rows.extend(horizon_frame.to_dict(orient="records"))

    forecast = pd.DataFrame(rows).sort_values([GROUP_COL, "horizon"]).reset_index(drop=True)

    final_output_path = Path(output_path) if output_path else DEFAULT_FUTURE_OUTPUT_PATH
    final_output_path.parent.mkdir(parents=True, exist_ok=True)
    forecast.to_csv(final_output_path, index=False)

    print(f"Dataset: {source_path}")
    print(f"Saved future forecast to: {final_output_path}")
    print(f"Rows: {len(forecast)} | SKUs: {forecast[GROUP_COL].nunique()} | Horizons: {len(HORIZONS)}")
    print(forecast.head(10).to_string(index=False))
    return forecast


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train LightGBM and build future demand forecast.")
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
        help="Where to save future forecast CSV (default: ml/artifacts/future_forecast.csv).",
    )
    parser.add_argument(
        "--max-train-rows",
        type=int,
        default=250000,
        help="Max rows per horizon for LightGBM training (default: 250000).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        dataset_path=args.dataset_path,
        output_path=args.output_path,
        max_train_rows=args.max_train_rows,
    )
