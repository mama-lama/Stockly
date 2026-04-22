from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor


@dataclass
class LightGBMForecastResult:
    y_true: np.ndarray
    y_pred: np.ndarray
    rows: int


@dataclass
class LightGBMModelBundle:
    model: LGBMRegressor
    feature_columns: list[str]
    categorical_columns: list[str]
    numeric_fill_values: dict[str, float]


def _build_feature_columns(df: pd.DataFrame, *, target_col: str, date_col: str) -> list[str]:
    target_h_columns = {column for column in df.columns if column.startswith("target_h")}
    excluded = {date_col, *target_h_columns}
    return [column for column in df.columns if column not in excluded and column != target_col]


def _prepare_features(
    frame: pd.DataFrame,
    *,
    feature_columns: list[str],
    categorical_columns: list[str],
    numeric_fill_values: dict[str, float],
) -> pd.DataFrame:
    x = frame[feature_columns].copy()
    for column in categorical_columns:
        x[column] = x[column].astype("category")
    for column, fill_value in numeric_fill_values.items():
        x[column] = x[column].fillna(fill_value)
    return x


def _fit_model(
    x_train: pd.DataFrame,
    y_train: np.ndarray,
    *,
    categorical_columns: list[str],
    random_state: int,
) -> LGBMRegressor:
    model = LGBMRegressor(
        objective="mae",
        n_estimators=180,
        learning_rate=0.07,
        num_leaves=31,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_samples=40,
        random_state=random_state,
        n_jobs=-1,
        verbosity=-1,
    )
    model.fit(x_train, y_train, categorical_feature=categorical_columns)
    return model


def train_lightgbm_for_horizon(
    *,
    df: pd.DataFrame,
    horizon: int,
    train_mask: pd.Series,
    target_col: str,
    date_col: str,
    random_state: int = 42,
    max_train_rows: int = 250_000,
) -> LightGBMModelBundle:
    target_horizon_column = f"target_h{horizon}"
    train_frame = df.loc[train_mask & df[target_horizon_column].notna()].copy()
    if len(train_frame) > max_train_rows:
        train_frame = train_frame.sample(n=max_train_rows, random_state=random_state)

    feature_columns = _build_feature_columns(df, target_col=target_col, date_col=date_col)
    categorical_columns = [
        column
        for column in feature_columns
        if train_frame[column].dtype == "object" or str(train_frame[column].dtype) == "category"
    ]
    numeric_columns = [column for column in feature_columns if column not in categorical_columns]

    numeric_fill_values = {
        column: float(train_frame[column].median())
        for column in numeric_columns
    }

    x_train = _prepare_features(
        train_frame,
        feature_columns=feature_columns,
        categorical_columns=categorical_columns,
        numeric_fill_values=numeric_fill_values,
    )
    y_train = train_frame[target_horizon_column].to_numpy()

    model = _fit_model(
        x_train,
        y_train,
        categorical_columns=categorical_columns,
        random_state=random_state,
    )

    return LightGBMModelBundle(
        model=model,
        feature_columns=feature_columns,
        categorical_columns=categorical_columns,
        numeric_fill_values=numeric_fill_values,
    )


def predict_from_bundle(
    *,
    bundle: LightGBMModelBundle,
    frame: pd.DataFrame,
) -> np.ndarray:
    x = _prepare_features(
        frame,
        feature_columns=bundle.feature_columns,
        categorical_columns=bundle.categorical_columns,
        numeric_fill_values=bundle.numeric_fill_values,
    )
    return bundle.model.predict(x)


def predict_with_lightgbm(
    *,
    df: pd.DataFrame,
    horizon: int,
    train_mask: pd.Series,
    test_mask: pd.Series,
    target_col: str,
    date_col: str,
    random_state: int = 42,
    max_train_rows: int = 250_000,
) -> LightGBMForecastResult:
    bundle = train_lightgbm_for_horizon(
        df=df,
        horizon=horizon,
        train_mask=train_mask,
        target_col=target_col,
        date_col=date_col,
        random_state=random_state,
        max_train_rows=max_train_rows,
    )

    target_horizon_column = f"target_h{horizon}"
    test_frame = df.loc[test_mask & df[target_horizon_column].notna()].copy()
    y_true = test_frame[target_horizon_column].to_numpy()
    y_pred = predict_from_bundle(
        bundle=bundle,
        frame=test_frame,
    )

    return LightGBMForecastResult(
        y_true=y_true,
        y_pred=y_pred,
        rows=int(len(test_frame)),
    )
