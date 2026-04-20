import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .exceptions import ValidationError


@dataclass
class PrepareSalesDataParams:
    transactions_file: str = "data/exports/all_transactions.csv"
    products_file: str = "data/exports/products.csv"
    output_dir: str = "data/processed"
    recent_days: int = 90
    include_payback_in_sales: bool = False


@dataclass
class PrepareSalesDataResult:
    daily_sales_path: str
    sku_status_path: str
    daily_stock_movements_path: str
    daily_stock_path: str
    daily_sales_rows: int
    sku_status_rows: int
    daily_stock_movements_rows: int
    daily_stock_rows: int


def normalize_doc_type(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.upper()


def to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def require_columns(df: pd.DataFrame, required_columns: set[str], source_name: str) -> None:
    missing = required_columns - set(df.columns)
    if missing:
        raise ValidationError(f"В источнике {source_name} отсутствуют колонки: {sorted(missing)}")


def prepare_sales_data(params: PrepareSalesDataParams) -> PrepareSalesDataResult:
    if not os.path.exists(params.transactions_file):
        raise ValidationError(f"Не найден файл транзакций: {params.transactions_file}")
    if not os.path.exists(params.products_file):
        raise ValidationError(f"Не найден файл товаров: {params.products_file}")

    os.makedirs(params.output_dir, exist_ok=True)

    tx = pd.read_csv(params.transactions_file, low_memory=False)
    products = pd.read_csv(params.products_file, low_memory=False)

    tx.columns = [column.strip() for column in tx.columns]
    products.columns = [column.strip() for column in products.columns]

    require_columns(tx, {"close_date", "doc_type", "commodity_uuid", "quantity"}, "transactions file")

    tx["close_date"] = pd.to_datetime(tx["close_date"], errors="coerce", format="mixed", utc=True)
    tx = tx.dropna(subset=["close_date"]).copy()
    tx["date"] = tx["close_date"].dt.tz_convert("Europe/Moscow").dt.floor("D")

    tx["doc_type"] = normalize_doc_type(tx["doc_type"])
    tx["sku_id"] = tx["commodity_uuid"].astype(str).str.strip()
    tx.loc[tx["sku_id"].isin(["", "nan", "None", "NONE"]), "sku_id"] = pd.NA
    tx = tx.dropna(subset=["sku_id"]).copy()

    tx["quantity"] = to_numeric(tx["quantity"])
    tx["result_sum"] = to_numeric(tx["result_sum"]) if "result_sum" in tx.columns else 0.0

    tx["commodity_code"] = tx.get("commodity_code", "").fillna("").astype(str)
    tx["product_code_from_catalog"] = tx.get("product_code_from_catalog", "").fillna("").astype(str)
    tx["product_name"] = tx.get("product_name_from_catalog", "").fillna("")
    tx["product_name"] = tx["product_name"].replace("", pd.NA).fillna(tx.get("commodity_name", "").fillna(""))
    tx["product_name"] = tx["product_name"].replace("", "Без названия").astype(str)
    tx["measure_name"] = tx.get("measure_name", "").fillna("").astype(str)

    sales = tx[tx["doc_type"].str.startswith("SELL")].copy()
    if params.include_payback_in_sales:
        payback = tx[tx["doc_type"] == "PAYBACK"].copy()
        if not payback.empty:
            payback["quantity"] = -payback["quantity"].abs()
            payback["result_sum"] = -payback["result_sum"].abs()
            sales = pd.concat([sales, payback], ignore_index=True)

    if sales.empty:
        raise ValidationError("После фильтрации не осталось продаж (SELL*)")

    sales["sales_qty"] = sales["quantity"]
    sales["sales_amount"] = sales["result_sum"]

    daily_sales = (
        sales.groupby(["date", "sku_id"], as_index=False)
        .agg(
            sales_qty=("sales_qty", "sum"),
            sales_amount=("sales_amount", "sum"),
            product_name=("product_name", "last"),
            measure_name=("measure_name", "last"),
            commodity_code=("commodity_code", "last"),
            product_code_from_catalog=("product_code_from_catalog", "last"),
        )
        .sort_values(["sku_id", "date"])
        .reset_index(drop=True)
    )

    products_meta = products.copy()
    products_meta["sku_id"] = products_meta.get("uuid", "").astype(str).str.strip()
    products_meta = products_meta[["sku_id", "code", "name", "measure_name"]].copy()
    products_meta = products_meta.rename(
        columns={
            "code": "product_code_from_catalog_products",
            "name": "product_name_from_products",
            "measure_name": "measure_name_from_products",
        }
    )
    products_meta = products_meta.drop_duplicates(subset=["sku_id"])

    daily_sales = daily_sales.merge(products_meta, on="sku_id", how="left")
    daily_sales["product_name"] = daily_sales["product_name"].replace("", pd.NA).fillna(daily_sales["product_name_from_products"])
    daily_sales["measure_name"] = daily_sales["measure_name"].replace("", pd.NA).fillna(daily_sales["measure_name_from_products"])
    daily_sales["product_code_from_catalog"] = daily_sales["product_code_from_catalog"].replace("", pd.NA).fillna(
        daily_sales["product_code_from_catalog_products"]
    )
    daily_sales = daily_sales.drop(columns=["product_name_from_products", "measure_name_from_products", "product_code_from_catalog_products"])

    movement = tx[["date", "sku_id", "doc_type", "quantity"]].copy()
    movement["quantity_abs"] = movement["quantity"].abs()
    movement["movement_qty"] = 0.0

    sell_mask = movement["doc_type"].str.startswith("SELL")
    payback_mask = movement["doc_type"] == "PAYBACK"
    accept_mask = movement["doc_type"].str.startswith("ACCEPT")
    write_off_mask = movement["doc_type"].str.startswith("WRITE_OFF")
    adjustment_mask = movement["doc_type"].str.startswith("ADJUSTMENT")
    inventory_mask = movement["doc_type"].str.startswith("INVENTORY")

    movement.loc[sell_mask, "movement_qty"] = -movement.loc[sell_mask, "quantity_abs"]
    movement.loc[payback_mask, "movement_qty"] = movement.loc[payback_mask, "quantity_abs"]
    movement.loc[accept_mask, "movement_qty"] = movement.loc[accept_mask, "quantity_abs"]
    movement.loc[write_off_mask, "movement_qty"] = -movement.loc[write_off_mask, "quantity_abs"]
    movement["is_ignored_for_stock"] = (adjustment_mask | inventory_mask).astype(int)

    daily_stock_movements = (
        movement.groupby(["date", "sku_id"], as_index=False)
        .agg(
            movement_qty=("movement_qty", "sum"),
            ignored_doc_count=("is_ignored_for_stock", "sum"),
        )
        .sort_values(["sku_id", "date"])
        .reset_index(drop=True)
    )

    daily_stock = daily_stock_movements.copy()
    daily_stock["stock_on_day"] = daily_stock.groupby("sku_id")["movement_qty"].cumsum()
    daily_stock["stock_available_flag"] = (daily_stock["stock_on_day"] > 0).astype(int)

    activity = tx.groupby("sku_id", as_index=False).agg(first_activity_date=("date", "min"), last_activity_date=("date", "max"))

    sales_status = daily_sales.groupby("sku_id", as_index=False).agg(
        first_sale_date=("date", "min"),
        last_sale_date=("date", "max"),
        sales_days=("date", "nunique"),
        total_sales_qty=("sales_qty", "sum"),
        product_name=("product_name", "last"),
        measure_name=("measure_name", "last"),
        commodity_code=("commodity_code", "last"),
        product_code_from_catalog=("product_code_from_catalog", "last"),
    )

    sku_status = activity.merge(sales_status, on="sku_id", how="left")
    max_date = tx["date"].max()
    sku_status["days_from_last_sale"] = (max_date - sku_status["last_sale_date"]).dt.days
    sku_status["is_active_now"] = (sku_status["days_from_last_sale"] <= int(params.recent_days)).fillna(False)

    for column in ["first_activity_date", "last_activity_date", "first_sale_date", "last_sale_date"]:
        sku_status[column] = pd.to_datetime(sku_status[column], errors="coerce").dt.strftime("%Y-%m-%d")

    daily_sales["date"] = pd.to_datetime(daily_sales["date"]).dt.strftime("%Y-%m-%d")
    daily_stock_movements["date"] = pd.to_datetime(daily_stock_movements["date"]).dt.strftime("%Y-%m-%d")
    daily_stock["date"] = pd.to_datetime(daily_stock["date"]).dt.strftime("%Y-%m-%d")

    daily_sales_path = str(Path(params.output_dir) / "daily_sales.csv")
    sku_status_path = str(Path(params.output_dir) / "sku_status.csv")
    daily_stock_movements_path = str(Path(params.output_dir) / "daily_stock_movements.csv")
    daily_stock_path = str(Path(params.output_dir) / "daily_stock.csv")

    daily_sales.to_csv(daily_sales_path, index=False, encoding="utf-8-sig")
    sku_status.to_csv(sku_status_path, index=False, encoding="utf-8-sig")
    daily_stock_movements.to_csv(daily_stock_movements_path, index=False, encoding="utf-8-sig")
    daily_stock.to_csv(daily_stock_path, index=False, encoding="utf-8-sig")

    return PrepareSalesDataResult(
        daily_sales_path=daily_sales_path,
        sku_status_path=sku_status_path,
        daily_stock_movements_path=daily_stock_movements_path,
        daily_stock_path=daily_stock_path,
        daily_sales_rows=len(daily_sales),
        sku_status_rows=len(sku_status),
        daily_stock_movements_rows=len(daily_stock_movements),
        daily_stock_rows=len(daily_stock),
    )
