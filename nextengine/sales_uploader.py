# nextengine/sales_uploader.py
# テスト実行時は .env.test を使い、本番では　.env　を使う。2か所書き換え必要

import csv
import glob
import io
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from logger import get_logger
from utils.file_utils import load_json

log = get_logger(__name__)


class SalesUploader:
    API_URL = "https://api.next-engine.org/api_v1_receiveorder_base/upload"

    def __init__(self, token_env=".env", pattern_id=1, wait_flag=1):
        """
        pattern_id: Next Engine 側の受注一括登録パターンID
        wait_flag: メイン機能過負荷時の挙動 (1:エラーにせず実行)
        """
        # Load only the specified env file, and override any existing vars
        load_dotenv(token_env, override=True)
        # Use Next Engine specific variable names
        self.access_token = os.getenv("NE_ACCESS_TOKEN") or os.getenv("ne_access_token")
        self.refresh_token = os.getenv("NE_REFRESH_TOKEN") or os.getenv("ne_refresh_token")
        if not self.access_token:
            raise RuntimeError(f"NE_ACCESS_TOKEN not found in {token_env}")
        if not self.refresh_token:
            raise RuntimeError(f"NE_REFRESH_TOKEN not found in {token_env}")

        self.pattern_id = pattern_id
        self.wait_flag = wait_flag

    def build_csv(self, record: dict) -> str:
        """
        Convert JSON record to CSV string for order upload.
        Headers: 店舗伝票番号,受注日,受注名,支払方法,合計金額,商品名,商品コード,商品価格,受注数量
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        headers = [
            "店舗伝票番号",
            "受注日",
            "受注名",
            "支払方法",
            "合計金額",
            "商品名",
            "商品コード",
            "商品価格",
            "受注数量",
        ]
        writer.writerow(headers)

        tx_id = record.get("transaction_id")
        dt_obj = datetime.fromisoformat(record.get("timestamp"))
        dt = dt_obj.strftime("%Y/%m/%d %H:%M:%S")

        payments = record.get("payments", [])
        payment_method = payments[0].get("method", "") if payments else ""
        total = int(record.get("total_due", 0))

        for item in record.get("cart", []):
            writer.writerow([
                tx_id,
                dt,
                tx_id,
                payment_method,
                total,
                item.get("name"),
                item.get("code", item.get("name")),
                int(item.get("price", 0)),
                item.get("quantity", 1),
            ])

        return output.getvalue()

    def upload_record(self, json_path: str) -> dict:
        """
        Upload a single JSON sales file.
        Returns response JSON on success.
        """
        record = load_json(json_path)
        csv_data = self.build_csv(record)

        payload = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "wait_flag": self.wait_flag,
            "receive_order_upload_pattern_id": self.pattern_id,
            "data_type_1": "csv",
            "data_1": csv_data,
        }
        resp = requests.post(self.API_URL, data=payload)
        resp.raise_for_status()
        return resp.json()

    def upload_all(self, data_dir="data") -> dict:
        """
        Execute upload_record for all JSON files under data_dir/YYYYMM.
        Returns dict mapping file paths to responses or errors.
        """
        results = {}
        pattern = os.path.join(data_dir, "*", "sales_*.json")
        log.debug(f"Searching for files with pattern: {pattern}")

        for jp in glob.glob(pattern):
            try:
                res = self.upload_record(jp)
                results[jp] = res
                log.info(f"Uploaded {jp} => {res}")
            except Exception as e:
                results[jp] = {"error": str(e)}
                log.error(f"Error uploading {jp} => {e}", exc_info=True)

        return results


if __name__ == "__main__":
    su = SalesUploader(token_env=".env", pattern_id=1)
    results = su.upload_all(data_dir="data")
    print(results)
