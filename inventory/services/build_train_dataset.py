import os
from dataclasses import dataclass

import holidays
import numpy as np
import pandas as pd

from .exceptions import ValidationError


@dataclass
class BuildTrainDatasetParams:
    daily_sales_file: str = "data/processed/daily_sales.csv"
    sku_status_file: str = "data/processed/sku_status.csv"
    daily_stock_file: str = "data/processed/daily_stock.csv"
    products_file: str = "data/exports/products.csv"
    categories_file: str = "data/categorized_products_filled.xlsx"
    output_file: str = "data/processed/train_dataset.csv"
    min_history_days: int = 35


@dataclass
class BuildTrainDatasetResult:
    output_file: str
    rows_count: int
    sku_count: int


def require_columns(df: pd.DataFrame, required: set[str], file_name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValidationError(f"В файле {file_name} отсутствуют колонки: {sorted(missing)}")


def normalize_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def build_train_dataset(params: BuildTrainDatasetParams) -> BuildTrainDatasetResult:
    for path in [params.daily_sales_file, params.sku_status_file, params.daily_stock_file, params.products_file]:
        if not os.path.exists(path):
            raise ValidationError(f"Файл не найден: {path}")

    categories_file = params.categories_file if os.path.exists(params.categories_file) else None

    output_dir = os.path.dirname(params.output_file) or "."
    os.makedirs(output_dir, exist_ok=True)

    daily = pd.read_csv(params.daily_sales_file, low_memory=False)
    status = pd.read_csv(params.sku_status_file, low_memory=False)
    daily_stock = pd.read_csv(params.daily_stock_file, low_memory=False)
    products = pd.read_csv(params.products_file, low_memory=False)

    require_columns(daily, {"date", "sku_id", "sales_qty"}, "daily_sales.csv")
    require_columns(status, {"sku_id", "first_activity_date", "last_activity_date"}, "sku_status.csv")
    require_columns(daily_stock, {"date", "sku_id", "stock_on_day"}, "daily_stock.csv")
    require_columns(products, {"uuid"}, "products.csv")

    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    daily["sku_id"] = normalize_text(daily["sku_id"])
    daily["sales_qty"] = pd.to_numeric(daily["sales_qty"], errors="coerce").fillna(0.0)
    daily = daily.dropna(subset=["date"])
    daily = daily[daily["sku_id"] != ""].copy()

    status["sku_id"] = normalize_text(status["sku_id"])
    status["first_activity_date"] = pd.to_datetime(status["first_activity_date"], errors="coerce")
    status["last_activity_date"] = pd.to_datetime(status["last_activity_date"], errors="coerce")
    status = status.dropna(subset=["sku_id", "first_activity_date", "last_activity_date"]).copy()

    status["history_days"] = (status["last_activity_date"] - status["first_activity_date"]).dt.days + 1
    status = status[status["history_days"] >= int(params.min_history_days)].copy()
    if status.empty:
        raise ValidationError("После фильтра min-history-days не осталось SKU")

    daily_stock["date"] = pd.to_datetime(daily_stock["date"], errors="coerce")
    daily_stock["sku_id"] = normalize_text(daily_stock["sku_id"])
    daily_stock["stock_on_day"] = pd.to_numeric(daily_stock["stock_on_day"], errors="coerce")
    daily_stock = daily_stock.dropna(subset=["date", "sku_id"]).copy()

    products["sku_id"] = normalize_text(products["uuid"])
    products_meta = products[["sku_id"]].copy()
    products_meta["product_code_from_catalog"] = normalize_text(products["code"]) if "code" in products.columns else ""
    products_meta["product_name"] = normalize_text(products["name"]) if "name" in products.columns else ""
    products_meta["measure_name"] = normalize_text(products["measure_name"]) if "measure_name" in products.columns else ""
    products_meta = products_meta.drop_duplicates(subset=["sku_id"])

    pieces = []
    for row in status.itertuples(index=False):
        calendar = pd.DataFrame({"date": pd.date_range(row.first_activity_date, row.last_activity_date, freq="D")})
        calendar["sku_id"] = row.sku_id
        pieces.append(calendar)

    train_df = pd.concat(pieces, ignore_index=True)

    train_df = train_df.merge(daily[["date", "sku_id", "sales_qty"]], on=["date", "sku_id"], how="left")
    train_df["sales_qty"] = train_df["sales_qty"].fillna(0.0)

    train_df = train_df.merge(daily_stock[["date", "sku_id", "stock_on_day"]], on=["date", "sku_id"], how="left")
    train_df = train_df.sort_values(["sku_id", "date"]).reset_index(drop=True)
    train_df["stock_on_day"] = train_df.groupby("sku_id")["stock_on_day"].ffill().fillna(0.0)
    train_df["stock_available_flag"] = (train_df["stock_on_day"] > 0).astype(int)

    train_df = train_df.merge(products_meta, on="sku_id", how="left")

    if "product_name" in daily.columns:
        names = daily[["sku_id", "product_name"]].dropna().drop_duplicates(subset=["sku_id"], keep="last")
        train_df = train_df.merge(names, on="sku_id", how="left", suffixes=("", "_daily"))
        train_df["product_name"] = train_df["product_name"].replace("", pd.NA).fillna(train_df["product_name_daily"])
        train_df = train_df.drop(columns=["product_name_daily"])

    if "measure_name" in daily.columns:
        measures = daily[["sku_id", "measure_name"]].dropna().drop_duplicates(subset=["sku_id"], keep="last")
        train_df = train_df.merge(measures, on="sku_id", how="left", suffixes=("", "_daily"))
        train_df["measure_name"] = train_df["measure_name"].replace("", pd.NA).fillna(train_df["measure_name_daily"])
        train_df = train_df.drop(columns=["measure_name_daily"])

    if categories_file is not None:
        categories = pd.read_excel(categories_file)
        require_columns(categories, {"uuid", "Категории для списка"}, "categories excel")
        categories = categories[["uuid", "Категории для списка"]].copy()
        categories["sku_id"] = normalize_text(categories["uuid"])
        categories["category"] = normalize_text(categories["Категории для списка"])
        categories = categories[["sku_id", "category"]].drop_duplicates(subset=["sku_id"])
        train_df = train_df.merge(categories, on="sku_id", how="left")
    else:
        train_df["category"] = np.nan

    train_df["category"] = train_df["category"].fillna("прочее")
    train_df["is_other_category"] = train_df["category"].str.lower().eq("прочее").astype(int)

    train_df = train_df.sort_values(["sku_id", "date"]).reset_index(drop=True)
    train_df["day_of_week"] = train_df["date"].dt.dayofweek
    train_df["day_of_month"] = train_df["date"].dt.day
    train_df["month"] = train_df["date"].dt.month
    train_df["week_of_year"] = train_df["date"].dt.isocalendar().week.astype(int)
    train_df["quarter"] = train_df["date"].dt.quarter
    train_df["day_of_year"] = train_df["date"].dt.dayofyear
    train_df["is_weekend"] = train_df["day_of_week"].isin([5, 6]).astype(int)

    sale_group = train_df.groupby("sku_id")["sales_qty"]
    train_df["sales_prev_week_1"] = sale_group.shift(1).rolling(7).sum().reset_index(level=0, drop=True)
    train_df["sales_prev_week_2"] = sale_group.shift(8).rolling(7).sum().reset_index(level=0, drop=True)
    train_df["sales_prev_week_3"] = sale_group.shift(15).rolling(7).sum().reset_index(level=0, drop=True)
    train_df["sales_prev_week_4"] = sale_group.shift(22).rolling(7).sum().reset_index(level=0, drop=True)
    train_df["sales_7d"] = sale_group.shift(1).rolling(7).sum().reset_index(level=0, drop=True)
    train_df["sales_28d"] = sale_group.shift(1).rolling(28).sum().reset_index(level=0, drop=True)

    safe_last_week = train_df["sales_7d"].replace(0, np.nan)
    safe_avg_4w = (train_df["sales_28d"] / 4).replace(0, np.nan)
    train_df["sales_4w_to_last_week_ratio"] = train_df["sales_28d"] / safe_last_week
    train_df["sales_last_week_to_avg_4w_ratio"] = train_df["sales_7d"] / safe_avg_4w

    category_daily = (
        train_df.groupby(["date", "category"], as_index=False)
        .agg(category_sales_qty=("sales_qty", "sum"))
        .sort_values(["category", "date"])
        .reset_index(drop=True)
    )

    cat_group = category_daily.groupby("category")["category_sales_qty"]
    category_daily["category_sales_7d"] = cat_group.shift(1).rolling(7).sum().reset_index(level=0, drop=True)
    category_daily["category_sales_28d"] = cat_group.shift(1).rolling(28).sum().reset_index(level=0, drop=True)

    train_df = train_df.merge(
        category_daily[["date", "category", "category_sales_7d", "category_sales_28d"]],
        on=["date", "category"],
        how="left",
    )

    safe_category_sales_28d = train_df["category_sales_28d"].replace(0, np.nan)
    train_df["sku_share_in_category_28d"] = train_df["sales_28d"] / safe_category_sales_28d
    train_df.loc[train_df["is_other_category"] == 1, "sku_share_in_category_28d"] = np.nan

    years = sorted(train_df["date"].dt.year.unique().tolist())
    years = sorted(set(years + [year + 1 for year in years]))
    ru_holidays = holidays.country_holidays("RU", years=years)
    holiday_dates = set(ru_holidays.keys())

    train_df["date_only"] = train_df["date"].dt.date
    train_df["next_date_only"] = (train_df["date"] + pd.Timedelta(days=1)).dt.date
    train_df["is_holiday_ru"] = train_df["date_only"].isin(holiday_dates).astype(int)
    train_df["is_preholiday_ru"] = train_df["next_date_only"].isin(holiday_dates).astype(int)

    next_new_year = pd.to_datetime((train_df["date"].dt.year + 1).astype(str) + "-01-01")
    train_df["days_to_new_year"] = (next_new_year - train_df["date"]).dt.days
    train_df["date"] = train_df["date"].dt.strftime("%Y-%m-%d")

    out_cols = [
        "date",
        "sku_id",
        "sales_qty",
        "product_name",
        "measure_name",
        "product_code_from_catalog",
        "category",
        "is_other_category",
        "stock_on_day",
        "stock_available_flag",
        "day_of_week",
        "day_of_month",
        "month",
        "week_of_year",
        "quarter",
        "day_of_year",
        "is_weekend",
        "is_holiday_ru",
        "is_preholiday_ru",
        "days_to_new_year",
        "sales_prev_week_1",
        "sales_prev_week_2",
        "sales_prev_week_3",
        "sales_prev_week_4",
        "sales_7d",
        "sales_28d",
        "sales_4w_to_last_week_ratio",
        "sales_last_week_to_avg_4w_ratio",
        "category_sales_7d",
        "category_sales_28d",
        "sku_share_in_category_28d",
    ]

    for col in out_cols:
        if col not in train_df.columns:
            train_df[col] = np.nan

    train_df[out_cols].to_csv(params.output_file, index=False, encoding="utf-8-sig")

    return BuildTrainDatasetResult(
        output_file=params.output_file,
        rows_count=len(train_df),
        sku_count=train_df["sku_id"].nunique(),
    )
