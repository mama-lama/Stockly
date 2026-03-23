from typing import Any, Dict, List, Optional

import requests


DOC_TYPES = [
    "SELL",
    "WRITE_OFF",
    "PAYBACK",
    "RETURN",
    "BUY",
    "ACCEPT",
    "INVENTORY",
    "OPEN_TARE",
    "ACCEPT-GM",
    "ACCEPT-EDO-GM",
    "ACCEPT-TTN-GM",
    "RETURN-GM",
    "INVENTORY-GM",
    "WRITE_OFF-GM",
    "ASSEMBLY-GM",
    "DISASSEMBLY-GM",
    "MOVING-GM",
    "ADJUSTMENT-EP",
    "SELL-GM",
    "SELL-TECHCARD",
    "PAYBACK-TECHCARD",
    "SUPPLY_REQUEST-GM",
]


class EasyKassaClient:
    def __init__(
        self,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        timeout: int = 60,
    ) -> None:
        self.base_url = "https://api.easykassa.ru"
        self.token_url = (
            "https://auth.easykassa.ru/auth/realms/easykassa/"
            "protocol/openid-connect/token"
        )
        self.client_id = "app1"
        self.timeout = timeout

        self.access_token = access_token
        self.refresh_token = refresh_token

        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

        if self.access_token:
            self._set_auth_header(self.access_token)

    def _set_auth_header(self, access_token: str) -> None:
        self.session.headers["Authorization"] = f"Bearer {access_token}"

    def refresh_access_token(self) -> Dict[str, str]:
        if not self.refresh_token:
            raise ValueError("Нет refresh_token для обновления access_token")

        response = requests.post(
            self.token_url,
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "refresh_token": self.refresh_token,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        token_data = response.json()

        new_access_token = token_data.get("access_token")
        new_refresh_token = token_data.get("refresh_token", self.refresh_token)

        if not new_access_token:
            raise ValueError("Сервер не вернул новый access_token")

        self.access_token = new_access_token
        self.refresh_token = new_refresh_token
        self._set_auth_header(new_access_token)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
        }

    def _post_with_auto_refresh(self, url: str, payload: Dict[str, Any]) -> requests.Response:
        response = self.session.post(url, json=payload, timeout=self.timeout)

        if response.status_code != 401:
            response.raise_for_status()
            return response

        self.refresh_access_token()

        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response

    def fetch_transactions(
        self,
        store_uid: str,
        from_dt: str,
        till_dt: str,
        commodity_uuid: Optional[str] = None,
        doc_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/v2-analytics-backend/evotor/transactions"

        payload: Dict[str, Any] = {
            "storeUids": store_uid,
            "fromDt": from_dt,
            "tillDt": till_dt,
            "docTypes": doc_types or DOC_TYPES,
        }

        if commodity_uuid:
            payload["commodityUuids"] = commodity_uuid

        response = self._post_with_auto_refresh(url, payload)

        data = response.json()
        if not isinstance(data, list):
            raise ValueError(f"Ожидался список, но пришло: {type(data)}")

        return data

    @staticmethod
    def flatten_transactions(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []

        for item in items:
            transaction = item.get("transactions") or {}

            rows.append({
                "uuid": item.get("uuid"),
                "close_date": item.get("closeDate"),
                "doc_type": item.get("type"),
                "device_uuid": item.get("deviceUuid"),
                "close_user_uuid": item.get("closeUserUuid"),
                "number": item.get("number"),
                "counterparty": item.get("counterparty"),

                "commodity_uuid": transaction.get("commodityUuid"),
                "commodity_code": transaction.get("commodityCode"),
                "commodity_name": transaction.get("commodityName"),
                "commodity_type": transaction.get("commodityType"),
                "measure_name": transaction.get("measureName"),

                "quantity": transaction.get("quantity"),
                "cost_price": transaction.get("costPrice"),
                "price": transaction.get("price"),
                "result_price": transaction.get("resultPrice"),
                "result_sum": transaction.get("resultSum"),

                "barcodes": ",".join(transaction.get("barCodes", [])) if transaction.get("barCodes") else None,
            })

        return rows
    
    
    def fetch_products(self, store_uid: str, user_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/v2-products-service/qln3/graphql/"

        query = """
        query Products (
          $storeUuid: String!,
          $userId: String!
        )
        {
          allProducts
          (
            condition: { storeUuid: $storeUuid, userId: $userId }
            filter: { not: { isGroup: { isNull: false, equalTo: true } } }
          )
          {
            edges {
              node {
                nodeId
                data
                createdAt
                updatedAt
                images
                storeUuid
                extra
              }
            }
          }
          allEcwidCurrentProductReservationV1S
          (condition: { storeId: $storeUuid })
          {
            edges {
              node {
                productId
                quantity
              }
            }
          }
        }
        """

        payload = {
            "query": query,
            "variables": {
                "storeUuid": store_uid,
                "userId": user_id,
            },
        }

        response = self._post_with_auto_refresh(url, payload)
        data = response.json()

        if not isinstance(data, dict):
            raise ValueError(f"Ожидался dict, но пришло: {type(data)}")

        return data