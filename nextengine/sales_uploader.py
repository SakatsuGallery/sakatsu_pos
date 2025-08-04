import csv
import glob
import io
import os
import shutil
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from logger import get_logger
from utils.file_utils import load_json, ensure_dir

log = get_logger(__name__)

class SalesUploader:
    """Sales upload module for Next Engine."""

    API_PATH   = "/api_v1_receiveorder_base/upload"
    TOKEN_PATH = "/api_neauth"
    DOMAIN     = "api.next-engine.org"

    def __init__(self, token_env: str = ".env", pattern_id: int = 1, wait_flag: int = 1):
        self.token_env  = token_env
        self.pattern_id = pattern_id
        self.wait_flag  = wait_flag

        # --- .env のバックアップ（修正：f-string の引用符を正しく） ---
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.token_env}.bak_{timestamp}"
            shutil.copyfile(self.token_env, backup_file)
        except Exception:
            pass

        # 環境変数読み込み
        load_dotenv(self.token_env, override=True)
        self.access_token  = os.getenv("NE_ACCESS_TOKEN")
        self.refresh_token = os.getenv("NE_REFRESH_TOKEN")
        self.client_id     = os.getenv("NE_CLIENT_ID")
        self.client_secret = os.getenv("NE_CLIENT_SECRET")

        if not (self.access_token and self.refresh_token and self.client_id and self.client_secret):
            raise RuntimeError(f"Missing credentials in {self.token_env}")

        # エンドポイント設定
        self.api_url   = f"https://{self.DOMAIN}{self.API_PATH}"
        self.token_url = f"https://{self.DOMAIN}{self.TOKEN_PATH}"

    def refresh_access_token(self):
        """Refresh access token using refresh_token grant and overwrite .env."""
        payload = {
            "grant_type":    "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id":     self.client_id,
            "client_secret": self.client_secret
        }
        res = requests.post(self.token_url, data=payload)
        res.raise_for_status()
        data = res.json()
        if "access_token" not in data or "refresh_token" not in data:
            raise RuntimeError(f"Invalid token response: {data}")

        self.access_token  = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self._write_tokens_to_env()
        log.info("[SalesUploader] Tokens refreshed")

    def _write_tokens_to_env(self):
        lines = []
        try:
            with open(self.token_env, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            pass
        with open(self.token_env, "w", encoding="utf-8") as f:
            for line in lines:
                if line.startswith("NE_ACCESS_TOKEN="):
                    f.write(f"NE_ACCESS_TOKEN={self.access_token}\n")
                elif line.startswith("NE_REFRESH_TOKEN="):
                    f.write(f"NE_REFRESH_TOKEN={self.refresh_token}\n")
                else:
                    f.write(line)

    def build_csv(self, record: dict) -> str:
        """Convert a record dict to Next Engine CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        headers = [
            "店舗伝票番号", "受注日", "受注名",
            "支払方法",   "合計金額",
            "商品名",     "商品コード",
            "商品価格",   "受注数量",
        ]
        writer.writerow(headers)

        tx_id = record.get("transaction_id")
        dt = datetime.fromisoformat(record.get("timestamp"))
        dt_str = dt.strftime("%Y/%m/%d %H:%M:%S")

        payments = record.get("payments", [])
        method = payments[0].get("method", "") if payments else ""
        total = int(record.get("total_due", 0))

        for item in record.get("cart", []):
            writer.writerow([
                tx_id, dt_str, tx_id,
                method, total,
                item.get("name"),
                item.get("code", item.get("name")),
                int(item.get("price", 0)),
                item.get("quantity", 1),
            ])
        return output.getvalue()

    def upload_record(self, json_path: str) -> dict:
        """Upload a single JSON file and retry on token expiration."""
        log.debug(f"Uploading {json_path}")
        record = load_json(json_path)
        csv_data = self.build_csv(record)

        payload = {
            "access_token":  self.access_token,
            "refresh_token": self.refresh_token,
            "receive_order_upload_pattern_id": self.pattern_id,
            "wait_flag": self.wait_flag,
            "data_type_1": "csv",
            "data_1": csv_data,
        }

        for attempt in range(2):
            try:
                res = requests.post(self.api_url, data=payload)
                if res.status_code == 401:
                    log.info("[SalesUploader] 401 Unauthorized, refreshing token")
                    self.refresh_access_token()
                    continue
                res.raise_for_status()
                return res.json()
            except Exception as e:
                log.warning(f"[SalesUploader] Attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)

        raise RuntimeError("Max retries exceeded for upload_record")

    def upload_all(self, data_dir: str = "data") -> dict:
        """Upload all sales_*.json files under YYYYMM folders."""
        results = {}
        pattern = os.path.join(data_dir, "[0-9]"*6, "sales_*.json")
        for path in glob.glob(pattern):
            try:
                res = self.upload_record(path)
                results[path] = res
                log.info(f"Uploaded {path} => {res}")
                dest = os.path.join(data_dir, "success") if res.get("result") == "success" else os.path.join(data_dir, "pending")
                ensure_dir(dest)
                shutil.move(path, os.path.join(dest, os.path.basename(path)))
            except Exception as e:
                log.error(f"Error uploading {path}: {e}", exc_info=True)
                results[path] = {"error": str(e)}
        return results

if __name__ == "__main__":
    su = SalesUploader(token_env=".env.test", pattern_id=1, wait_flag=1)
    print(su.upload_all(data_dir="data"))
