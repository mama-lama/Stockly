import csv
import json
import os

from django.core.management.base import BaseCommand, CommandError

from integrations.easykassa_client import EasyKassaClient


class Command(BaseCommand):
    help = "Выгрузка движений товаров из EasyKassa в CSV"

    def add_arguments(self, parser):
        parser.add_argument("--token", type=str, required=False, help="Access token EasyKassa")
        parser.add_argument("--refresh-token", type=str, required=False, help="Refresh token EasyKassa")
        parser.add_argument("--store-uid", type=str, required=True, help="ID магазина")
        parser.add_argument("--from-dt", type=str, required=True, help="Дата начала")
        parser.add_argument("--till-dt", type=str, required=True, help="Дата конца")
        # parser.add_argument("--commodity-uuid", type=str, required=False, help="ID товара")
        parser.add_argument("--output", type=str, default="transactions_export.csv", help="Имя выходного CSV файла")
        parser.add_argument(
            "--tokens-output",
            type=str,
            default="easykassa_tokens.json",
            help="Файл для сохранения обновлённых токенов",
        )

    def handle(self, *args, **options):
        access_token = options.get("token") or os.getenv("EASYKASSA_TOKEN")
        refresh_token = options.get("refresh_token") or os.getenv("EASYKASSA_REFRESH_TOKEN")

        if not access_token and not refresh_token:
            raise CommandError(
                "Передайте --token или --refresh-token, либо задайте "
                "EASYKASSA_TOKEN / EASYKASSA_REFRESH_TOKEN"
            )

        store_uid = options["store_uid"]
        from_dt = options["from_dt"]
        till_dt = options["till_dt"]
        commodity_uuid = options.get("commodity_uuid")
        output = options["output"]
        tokens_output = options["tokens_output"]

        client = EasyKassaClient(
            access_token=access_token,
            refresh_token=refresh_token,
        )

        self.stdout.write(self.style.WARNING("Запрашиваю данные из EasyKassa..."))

        try:
            items = client.fetch_transactions(
                store_uid=store_uid,
                from_dt=from_dt,
                till_dt=till_dt,
                commodity_uuid=commodity_uuid,
            )
        except Exception as exc:
            raise CommandError(f"Ошибка при запросе к EasyKassa: {exc}")

        self.stdout.write(self.style.SUCCESS(f"Получено записей: {len(items)}"))

        rows = client.flatten_transactions(items)

        if not rows:
            self.stdout.write(self.style.WARNING("Нет данных для сохранения"))
        else:
            fieldnames = list(rows[0].keys())
            with open(output, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            self.stdout.write(self.style.SUCCESS(f"CSV сохранён: {output}"))

        if client.access_token or client.refresh_token:
            with open(tokens_output, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "access_token": client.access_token,
                        "refresh_token": client.refresh_token,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            self.stdout.write(self.style.SUCCESS(f"Токены сохранены: {tokens_output}"))