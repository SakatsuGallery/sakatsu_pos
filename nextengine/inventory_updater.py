import glob
import io
import os
import csv
import requests
from pathlib import Path
from dotenv import load_dotenv
from utils.file_utils import load_json, save_csv, ensure_dir

class InventoryUpdater:
    """Inventory update module for Next Engine."""
    API_PATH = "/api_v1_master_goods/upload"

    def __init__(self, token_env=".env", simulate=True):
        """Initialize the updater.
        token_env: Path to environment file (e.g. .env, .env.test)
        simulate: If True, use test endpoint and skip actual POST.
        """
        self.simulate = simulate
        load_dotenv(token_env)
        self.access_token = os.getenv("NE_ACCESS_TOKEN")
        self.refresh_token = os.getenv("NE_REFRESH_TOKEN")
        if not self.access_token or not self.refresh_token:
            raise RuntimeError(f"Missing NE_ACCESS_TOKEN or NE_REFRESH_TOKEN in {token_env}")
        domain = "api.test.next-engine.org" if simulate else "api.next-engine.org"
        self.api_url = f"https://{domain}{self.API_PATH}"

    def build_csv(self, record):
        """Build CSV data string from a record dict."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["goods_id", "stock_quantity"])
        valid_lines = 0
        for item in record.get("cart", []):
            gid = item.get("goods_id")
            qty = item.get("quantity", 1)
            if gid:
                writer.writerow([gid, -qty])
                valid_lines += 1
        return output.getvalue(), valid_lines

    def update_from_record(self, json_path):
        """Update inventory from a single JSON record file and write audit CSV."""
        record = load_json(json_path)
        csv_data, valid = self.build_csv(record)
        if valid == 0:
            print(f"[InventoryUpdater] No valid goods_id in {json_path}, skipping.")
            return {"skipped": True}

        # Write audit CSV report
        date_str = Path(json_path).stem.replace("sales_", "")
        report_dir = "reports"
        ensure_dir(report_dir)
        report_path = os.path.join(report_dir, f"inventory_{date_str}.csv")
        # Convert CSV text to rows
        rows = [line.split(",") for line in csv_data.strip().splitlines()]
        save_csv(report_path, rows)
        print(f"[InventoryUpdater] Report saved to {report_path}")

        if self.simulate:
            print(f"[InventoryUpdater] Simulation mode: POST to {self.api_url}")
            return {"simulated": True, "csv": csv_data}

        payload = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "data_type_1": "csv",
            "data_1": csv_data,
        }
        response = requests.post(self.api_url, data=payload)
        response.raise_for_status()
        return response.json()

    def update_all(self, data_dir="data"):
        """Process all JSON records under data_dir."""
        results = {}
        pattern = os.path.join(data_dir, "*", "sales_*.json")
        for path in glob.glob(pattern):
            try:
                results[path] = self.update_from_record(path)
            except Exception as e:
                results[path] = {"error": str(e)}
                print(f"[InventoryUpdater] Error processing {path}: {e}")
        return results

if __name__ == "__main__":
    updater = InventoryUpdater(token_env=".env.test", simulate=True)
    result = updater.update_all(data_dir="data")
    print(result)
