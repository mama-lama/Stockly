import csv
import json
import os

from django.core.management.base import BaseCommand, CommandError

from integrations.easykassa_client import EasyKassaClient


class Command(BaseCommand):
    help = "Выгрузка списка товаров из EasyKassa в CSV"

    def add_arguments(self, parser):
        parser.add_argument("--token", type=str, required=False, help="Access token EasyKassa")
        parser.add_argument("--refresh-token", type=str, required=False, help="Refresh token EasyKassa")
        parser.add_argument("--tokens-file", type=str, default="easykassa_tokens.json", help="Путь к JSON-файлу с токенами")
        parser.add_argument("--store-uid", type=str, required=True, help="ID магазина")
        parser.add_argument("--user-id", type=str, required=True, help="ID пользователя")
        parser.add_argument("--output", type=str, default="data/exports/products.csv", help="Выходной CSV файл")
        parser.add_argument("--raw-output", type=str, default="data/raw/products_raw.json", help="Файл для сырого JSON")

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

    def handle(self, *args, **options):
        tokens_file = options["tokens_file"]
        file_access_token, file_refresh_token = self.load_tokens_from_file(tokens_file)

        access_token = options.get("token") or os.getenv("EASYKASSA_TOKEN") or file_access_token
        refresh_token = options.get("refresh_token") or os.getenv("EASYKASSA_REFRESH_TOKEN") or file_refresh_token

        if not access_token and not refresh_token:
            raise CommandError("Не найдены токены")

        store_uid = options["store_uid"]
        user_id = options["user_id"]
        output = options["output"]
        raw_output = options["raw_output"]

        os.makedirs(os.path.dirname(output), exist_ok=True)
        os.makedirs(os.path.dirname(raw_output), exist_ok=True)

        client = EasyKassaClient(
            access_token=access_token,
            refresh_token=refresh_token,
        )

        self.stdout.write(self.style.WARNING("Запрашиваю список товаров..."))

        try:
            result = client.fetch_products(store_uid=store_uid, user_id=user_id)
        except Exception as exc:
            raise CommandError(f"Ошибка при запросе товаров: {exc}")

        with open(raw_output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        data = result.get("data", {})
        all_products = data.get("allProducts", {})
        edges = all_products.get("edges", [])

        rows = []
        for edge in edges:
            node = (edge or {}).get("node", {}) or {}
            product_data = node.get("data", {}) or {}

            rows.append({
                "uuid": product_data.get("uuid"),
                "code": product_data.get("code"),
                "name": product_data.get("name"),
                "type": product_data.get("type"),
                "price": product_data.get("price"),
                "cost_price": product_data.get("costPrice"),
                "quantity": product_data.get("quantity"),
                "measure_name": product_data.get("measureName"),
                "parent_uuid": product_data.get("parentUuid"),
                "article_number": product_data.get("articleNumber"),
                "barcodes": ",".join(product_data.get("barCodes", [])) if product_data.get("barCodes") else None,
                "tax": product_data.get("tax"),
                "allow_to_sell": product_data.get("allowToSell"),
                "description": product_data.get("description"),
                "created_at": node.get("createdAt"),
                "updated_at": node.get("updatedAt"),
                "store_uuid": node.get("storeUuid"),
            })

        if not rows:
            self.stdout.write(self.style.WARNING("Товары не найдены"))
            return

        fieldnames = list(rows[0].keys())

        with open(output, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        self.save_tokens_to_file(tokens_file, client.access_token, client.refresh_token)

        self.stdout.write(self.style.SUCCESS(f"Сырой JSON сохранён: {raw_output}"))
        self.stdout.write(self.style.SUCCESS(f"CSV сохранён: {output}"))
        self.stdout.write(self.style.SUCCESS(f"Всего товаров: {len(rows)}"))