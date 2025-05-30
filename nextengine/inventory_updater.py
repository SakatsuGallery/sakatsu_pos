import glob
import io
import os
import csv
import requests
import shutil
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from utils.file_utils import load_json, save_csv, ensure_dir

class InventoryUpdater:
    """Inventory update module for Next Engine."""
    API_PATH = "/api_v1_master_goods/upload"

    def __init__(self, token_env=".env", simulate=True):
        """Initialize the updater.
        token_env: Path to environment file (e.g. .env, .env.test)
        simulate: If True, skip actual POST and use test endpoint.
        """
        self.simulate = simulate
        self.token_env = token_env
        # Backup existing env file
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copyfile(token_env, f"{token_env}.bak_{timestamp}")
        except Exception:
            # If backup fails, proceed
            pass

        # Load environment variables, overriding existing
        load_dotenv(token_env, override=True)
        # Store tokens in attributes that won't clash with method names
        self.ne_access_token = os.getenv("NE_ACCESS_TOKEN")
        self.ne_refresh_token = os.getenv("NE_REFRESH_TOKEN")
        if not self.ne_access_token or not self.ne_refresh_token:
            raise RuntimeError(f"Missing NE_ACCESS_TOKEN or NE_REFRESH_TOKEN in {token_env}")
        self.api_url = f"https://api.next-engine.org{self.API_PATH}"

    def refresh_access_token(self):
        """Refresh expired access token using refresh token."""
        resp = requests.post(
            "https://api.next-engine.org/api_v1_auth/refresh_token",
            data={"refresh_token": self.ne_refresh_token}
        )
        resp.raise_for_status()
        resp_json = resp.json()
        # Handle nested response
        data = resp_json.get('response', resp_json)
        access = data.get('access_token')
        refresh = data.get('refresh_token')
        if not access or not refresh:
            raise RuntimeError(f"Failed to refresh token, response: {resp_json}")

        # Update .env file
        lines = []
        try:
            with open(self.token_env, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            # No existing file, will create new
            lines = []
        with open(self.token_env, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith('NE_ACCESS_TOKEN='):
                    f.write(f"NE_ACCESS_TOKEN={access}\n")
                elif line.startswith('NE_REFRESH_TOKEN='):
                    f.write(f"NE_REFRESH_TOKEN={refresh}\n")
                else:
                    f.write(line)
            # If tokens not in original, append
            if not any(l.startswith('NE_ACCESS_TOKEN=') for l in lines):
                f.write(f"NE_ACCESS_TOKEN={access}\n")
            if not any(l.startswith('NE_REFRESH_TOKEN=') for l in lines):
                f.write(f"NE_REFRESH_TOKEN={refresh}\n")

        # Update in-memory tokens
        self.ne_access_token = access
        self.ne_refresh_token = refresh

    def build_csv(self, record):
        """Build CSV data string from a record dict."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['syohin_code', 'zaiko_su'])
        valid_lines = 0
        for item in record.get('cart', []):
            code = item.get('goods_id')
            qty = item.get('quantity', 1)
            if code:
                writer.writerow([code, -qty])
                valid_lines += 1
        return output.getvalue(), valid_lines

    def update_from_record(self, json_path):
        """Process single JSON file: generate CSV, post to API, and move file."""
        if not os.path.isfile(json_path):
            print(f"[InventoryUpdater] Not a file, skipping: {json_path}")
            return {'skipped': True}

        record = load_json(json_path)
        if not isinstance(record, dict):
            print(f"[InventoryUpdater] Invalid JSON record, skipping: {json_path}")
            return {'skipped': True}

        csv_data, valid = self.build_csv(record)
        if valid == 0:
            print(f"[InventoryUpdater] No valid syohin_code in {json_path}, skipping.")
            dest = os.path.join('data', 'success')
            ensure_dir(dest)
            shutil.move(json_path, os.path.join(dest, os.path.basename(json_path)))
            return {'skipped': True}

        # Save report
        date_str = Path(json_path).stem.replace('sales_', '')
        report_dir = 'reports'
        ensure_dir(report_dir)
        report_path = os.path.join(report_dir, f"inventory_{date_str}.csv")
        rows = [line.split(',') for line in csv_data.strip().splitlines()]
        save_csv(report_path, rows)
        print(f"[InventoryUpdater] Report saved to {report_path}")

        if self.simulate:
            print(f"[InventoryUpdater] Simulation mode: POST to {self.api_url}")
            dest = os.path.join('data', 'success')
            ensure_dir(dest)
            shutil.move(json_path, os.path.join(dest, os.path.basename(json_path)))
            return {'simulated': True, 'csv': csv_data}

        payload = {
            'access_token': self.ne_access_token,
            'refresh_token': self.ne_refresh_token,
            'data_type_1': 'csv',
            'data_1': csv_data,
        }

        result = None
        for attempt in range(2):
            try:
                r = requests.post(self.api_url, data=payload)
                if r.status_code >= 500:
                    time.sleep(2 ** attempt)
                    continue
                result = r.json()
                if result.get('code') == '002004':
                    # Token expired, refresh and retry
                    self.refresh_access_token()
                    continue
                break
            except requests.RequestException:
                time.sleep(2 ** attempt)
                continue

        # Move file based on result
        success = result and result.get('result') == 'success'
        dest = os.path.join('data', 'success' if success else 'pending')
        ensure_dir(dest)
        shutil.move(json_path, os.path.join(dest, os.path.basename(json_path)))
        return result or {'error': 'Max retries exceeded'}

    def update_all(self, data_dir='data'):
        """Process all JSON records under data_dir."""
        results = {}
        pattern = os.path.join(data_dir, '*', 'sales_*.json')
        for path in glob.glob(pattern):
            parent = os.path.basename(os.path.dirname(path))
            if not (parent.isdigit() and len(parent) == 6):
                continue
            try:
                results[path] = self.update_from_record(path)
            except Exception as e:
                import traceback
                traceback.print_exc()
                results[path] = {'error': str(e)}
                print(f"[InventoryUpdater] Error processing {path}: {e}")
        return results

if __name__ == '__main__':
    updater = InventoryUpdater(token_env='.env', simulate=False)
    print(updater.update_all(data_dir='data'))
