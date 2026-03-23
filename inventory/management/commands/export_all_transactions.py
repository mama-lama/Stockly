import csv
import json
import os
import time

from django.core.management.base import BaseCommand, CommandError

from integrations.easykassa_client import EasyKassaClient


class Command(BaseCommand):
    help = "Выгрузка движений по всем товарам из EasyKassa в CSV"

    def add_arguments(self, parser):
        parser.add_argument("--token", type=str, required=False, help="Access token EasyKassa")
        parser.add_argument("--refresh-token", type=str, required=False, help="Refresh token EasyKassa")
        parser.add_argument("--tokens-file", type=str, default="easykassa_tokens.json", help="Путь к JSON-файлу с токенами")

        parser.add_argument("--store-uid", type=str, required=True, help="ID магазина")
        parser.add_argument("--from-dt", type=str, required=True, help="Дата начала")
        parser.add_argument("--till-dt", type=str, required=True, help="Дата конца")

        parser.add_argument("--products-file", type=str, default="data/exports/products.csv", help="CSV со списком товаров")
        parser.add_argument("--output", type=str, default="data/exports/all_transactions.csv", help="Итоговый CSV движений")
        parser.add_argument("--failed-file", type=str, default="data/logs/failed_products.csv", help="CSV с ошибками")
        parser.add_argument("--progress-file", type=str, default="data/logs/export_all_transactions_progress.json", help="Файл прогресса")

        parser.add_argument("--sleep", type=float, default=0.2, help="Пауза между запросами в секундах")
        parser.add_argument("--limit", type=int, required=False, help="Ограничить число товаров для теста")
        parser.add_argument("--resume", action="store_true", help="Продолжить с места последнего успешного товара")

    def load_tokens_from_file(self, tokens_file: str):
        if not os.path.exists(tokens_file):
            return None, None

        with open(tokens_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("access_token"), data.get("refresh_token")

    def save_tokens_to_file(self, tokens_file: str, access_token: str, refresh_token: str):
        with open(tokens_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def load_progress(self, progress_file: str):
        if not os.path.exists(progress_file):
            return {"last_index": -1, "last_uuid": None}

        with open(progress_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_progress(self, progress_file: str, last_index: int, last_uuid: str | None):
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "last_index": last_index,
                    "last_uuid": last_uuid,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def read_products(self, products_file: str):
        if not os.path.exists(products_file):
            raise CommandError(f"Файл товаров не найден: {products_file}")

        with open(products_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def ensure_parent_dir(self, path: str):
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def append_rows_to_csv(self, output_file: str, rows: list[dict]):
        if not rows:
            return

        file_exists = os.path.exists(output_file)
        fieldnames = list(rows[0].keys())

        with open(output_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists or os.path.getsize(output_file) == 0:
                writer.writeheader()

            writer.writerows(rows)

    def append_failed_row(self, failed_file: str, row: dict):
        file_exists = os.path.exists(failed_file)
        fieldnames = list(row.keys())

        with open(failed_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists or os.path.getsize(failed_file) == 0:
                writer.writeheader()

            writer.writerow(row)

    def handle(self, *args, **options):
        tokens_file = options["tokens_file"]
        file_access_token, file_refresh_token = self.load_tokens_from_file(tokens_file)

        access_token = options.get("token") or os.getenv("EASYKASSA_TOKEN") or file_access_token
        refresh_token = options.get("refresh_token") or os.getenv("EASYKASSA_REFRESH_TOKEN") or file_refresh_token

        if not access_token and not refresh_token:
            raise CommandError("Не найдены токены")

        store_uid = options["store_uid"]
        from_dt = options["from_dt"]
        till_dt = options["till_dt"]

        products_file = options["products_file"]
        output_file = options["output"]
        failed_file = options["failed_file"]
        progress_file = options["progress_file"]

        sleep_seconds = options["sleep"]
        limit = options.get("limit")
        resume = options["resume"]

        self.ensure_parent_dir(output_file)
        self.ensure_parent_dir(failed_file)
        self.ensure_parent_dir(progress_file)

        products = self.read_products(products_file)

        if not products:
            raise CommandError("В products.csv нет товаров")

        if limit:
            products = products[:limit]

        start_index = 0
        if resume:
            progress = self.load_progress(progress_file)
            start_index = progress.get("last_index", -1) + 1
            self.stdout.write(self.style.WARNING(f"Продолжаю с товара #{start_index + 1}"))

        client = EasyKassaClient(
            access_token=access_token,
            refresh_token=refresh_token,
        )

        total_products = len(products)
        total_rows_written = 0

        for idx, product in enumerate(products):
            if idx < start_index:
                continue

            commodity_uuid = product.get("uuid")
            commodity_name = product.get("name")
            commodity_code = product.get("code")

            self.stdout.write(f"[{idx + 1}/{total_products}] Товар: {commodity_name} ({commodity_uuid})")

            try:
                items = client.fetch_transactions(
                    store_uid=store_uid,
                    from_dt=from_dt,
                    till_dt=till_dt,
                    commodity_uuid=commodity_uuid,
                )

                rows = client.flatten_transactions(items)

                for row in rows:
                    row["product_name_from_catalog"] = commodity_name
                    row["product_code_from_catalog"] = commodity_code

                self.append_rows_to_csv(output_file, rows)
                total_rows_written += len(rows)

                self.save_progress(progress_file, idx, commodity_uuid)
                self.save_tokens_to_file(tokens_file, client.access_token, client.refresh_token)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  OK: движений {len(rows)}, всего записано {total_rows_written}"
                    )
                )

            except Exception as exc:
                self.append_failed_row(
                    failed_file,
                    {
                        "index": idx,
                        "commodity_uuid": commodity_uuid,
                        "commodity_name": commodity_name,
                        "commodity_code": commodity_code,
                        "error": str(exc),
                    },
                )

                self.stdout.write(
                    self.style.ERROR(f"  ERROR: {commodity_name} ({commodity_uuid}) -> {exc}")
                )

            time.sleep(sleep_seconds)

        self.save_tokens_to_file(tokens_file, client.access_token, client.refresh_token)

        self.stdout.write(self.style.SUCCESS("Выгрузка завершена"))
        self.stdout.write(self.style.SUCCESS(f"Итоговый файл: {output_file}"))
        self.stdout.write(self.style.SUCCESS(f"Ошибки: {failed_file}"))
        self.stdout.write(self.style.SUCCESS(f"Прогресс: {progress_file}"))
        self.stdout.write(self.style.SUCCESS(f"Всего товаров обработано: {total_products}"))
        self.stdout.write(self.style.SUCCESS(f"Всего строк движений записано: {total_rows_written}"))