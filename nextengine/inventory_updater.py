
import glob
import io
import os
import csv
import requests
import shutil
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from utils.file_utils import load_json, save_csv, ensure_dir

class InventoryUpdater:
    """Inventory update モジュール for Next Engine.
    ───────────────────────────────────────────────────────────
    ・在庫同期を JSON→CSV 変換して Next Engine に送信
    ・access_token/refresh_token が期限切れなら自動的に再認可フローを起動
    ・テストモード（simulate=True）では実際の POST は行わない
    """

    API_PATH   = "/api_v1_master_goods/upload"
    TOKEN_PATH = "/api_neauth"       # トークン交換用
    SIGNIN_URL = "https://base.next-engine.org/users/sign_in/"

    def __init__(self, token_env: str = ".env", simulate: bool = True):
        self.simulate   = simulate
        self.token_env  = token_env

        # .env のバックアップ（任意）
        try:
            timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{token_env}.bak_{timestamp}"
            shutil.copyfile(token_env, backup_path)
        except Exception:
            pass

        # 環境変数読み込み
        load_dotenv(token_env, override=True)
        self.access_token  = os.getenv("NE_ACCESS_TOKEN")
        self.refresh_token = os.getenv("NE_REFRESH_TOKEN")
        self.client_id     = os.getenv("NE_CLIENT_ID")
        self.client_secret = os.getenv("NE_CLIENT_SECRET")
        self.redirect_uri  = os.getenv("NE_REDIRECT_URI")

        if not all([self.access_token, self.refresh_token, self.client_id, self.client_secret, self.redirect_uri]):
            raise RuntimeError(f"Missing credentials in {token_env}")

        # エンドポイント設定
        domain = "api.next-engine.org"
        self.api_url   = f"https://{domain}{self.API_PATH}"
        self.token_url = f"https://{domain}{self.TOKEN_PATH}"

    def refresh_access_token(self):
        """Refresh access token using refresh_token grant."""
        payload = {
            "grant_type":    "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id":     self.client_id,
            "client_secret": self.client_secret
        }
        try:
            res = requests.post(self.token_url, data=payload)
            res.raise_for_status()
        except Exception as e:
            print(f"[InventoryUpdater] Token refresh HTTP error: {e}")
            self._invoke_interactive_auth()
            raise RuntimeError("Interactive auth required")

        data = res.json()
        if "access_token" not in data or "refresh_token" not in data:
            print(f"[InventoryUpdater] Unexpected token response: {data}")
            self._invoke_interactive_auth()
            raise RuntimeError("Invalid token response")

        self.access_token  = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self._write_tokens_to_env(self.access_token, self.refresh_token)
        print("[InventoryUpdater] Tokens refreshed.")

    def _invoke_interactive_auth(self):
        """Launch interactive auth flow (e.g., callback.php)."""
        try:
            # Open browser to initiate OAuth
            import webbrowser
            webbrowser.open(self.SIGNIN_URL + f"?client_id={self.client_id}")
        except Exception as e:
            print(f"[InventoryUpdater] Failed to start interactive auth: {e}")

    def _write_tokens_to_env(self, access, refresh):
        """Overwrite .env with new tokens."""
        lines = []
        try:
            with open(self.token_env, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            pass

        with open(self.token_env, "w", encoding="utf-8") as f:
            for line in lines:
                if line.startswith("NE_ACCESS_TOKEN="):
                    f.write(f"NE_ACCESS_TOKEN={access}\n")
                elif line.startswith("NE_REFRESH_TOKEN="):
                    f.write(f"NE_REFRESH_TOKEN={refresh}\n")
                else:
                    f.write(line)

    def build_csv(self, record):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["syohin_code", "zaiko_su"])
        valid = 0
        for item in record.get("cart", []):
            code = item.get("goods_id")
            qty  = item.get("quantity", 1)
            if code:
                writer.writerow([code, -qty])
                valid += 1
        return output.getvalue(), valid

    def update_from_record(self, json_path: str):
        # Load JSON
        try:
            record = load_json(json_path)
        except Exception as e:
            print(f"[InventoryUpdater] Fail load JSON {json_path}: {e}")
            pending = os.path.join("data", "pending")
            ensure_dir(pending)
            shutil.move(json_path, os.path.join(pending, os.path.basename(json_path)))
            return {"error": str(e)}

        csv_data, valid = self.build_csv(record)
        if valid == 0:
            print(f"[InventoryUpdater] No valid data in {json_path}")
            success = os.path.join("data", "success")
            ensure_dir(success)
            shutil.move(json_path, os.path.join(success, os.path.basename(json_path)))
            return {"skipped": True}

        # Save report
        report_dir = "reports"
        ensure_dir(report_dir)
        date_str = Path(json_path).stem.replace("sales_", "")
        report_path = os.path.join(report_dir, f"inventory_{date_str}.csv")
        rows = [line.split(",") for line in csv_data.strip().splitlines()]
        save_csv(report_path, rows)
        print(f"[InventoryUpdater] Report saved: {report_path}")

        if self.simulate:
            print(f"[InventoryUpdater] Simulation: POST to {self.api_url}")
            dest = os.path.join("data", "success")
            ensure_dir(dest)
            shutil.move(json_path, os.path.join(dest, os.path.basename(json_path)))
            return {"simulated": True}

        # Attempt API call with retry and token refresh
        payload = {
            "access_token":  self.access_token,
            "refresh_token": self.refresh_token,
            "data_type":     "csv",
            "data":          csv_data
        }
        result = None
        for i in range(2):
            try:
                resp = requests.post(self.api_url, data=payload)
                if resp.status_code == 401:
                    print("[InventoryUpdater] 401 Unauthorized, refreshing token")
                    self.refresh_access_token()
                    continue
                resp.raise_for_status()
                result = resp.json()
                break
            except Exception as e:
                print(f"[InventoryUpdater] Attempt {i+1} failed: {e}")
                time.sleep(2 ** i)

        # Move file based on result
        dest_dir = "data/success" if result and result.get("result")=="success" else "data/pending"
        ensure_dir(dest_dir)
        shutil.move(json_path, os.path.join(dest_dir, os.path.basename(json_path)))
        return result or {"error": "Max retries exceeded"}

    def update_all(self, data_dir="data"):
        results = {}
        pattern = os.path.join(data_dir, "*", "sales_*.json")
        for path in glob.glob(pattern):
            try:
                results[path] = self.update_from_record(path)
            except Exception as e:
                results[path] = {"error": str(e)}
        return results

if __name__ == "__main__":
    updater = InventoryUpdater(token_env=".env.test", simulate=True)
    print(updater.update_all())
