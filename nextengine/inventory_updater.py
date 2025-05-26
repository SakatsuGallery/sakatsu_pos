# --- ファイル: nextengine/inventory_updater.py ---
"""
Inventory update module for Next Engine.
After a sale, decrement stock quantities via the master goods upload API.
Supports simulation mode for development and real POST for production.
"""
import os
import glob
from utils.file_utils import load_json, save_json
import io
from utils.file_utils import load_csv, save_csv
import requests
from dotenv import load_dotenv

class InventoryUpdater:
    """
    - token_env: Path to the .env file (.env.test or .env.token)
    - simulate: If True, run in simulation mode (skip actual POST)
    """
    # エンドポイントパス
    API_PATH = '/api_v1_master_goods/upload'

    def __init__(self, token_env='.env.token', simulate=True):
        self.simulate = simulate
        domain = 'api.test.next-engine.org' if simulate else 'api.next-engine.org'
        self.api_url = f"https://{domain}{self.API_PATH}"

        load_dotenv(token_env)

        if not simulate:
            self.access_token = os.getenv('ACCESS_TOKEN') or os.getenv('access_token')
            self.refresh_token = os.getenv('REFRESH_TOKEN') or os.getenv('refresh_token')
            if not self.access_token:
                raise RuntimeError(f"ACCESS_TOKEN not found in {token_env}")
        else:
            self.access_token = os.getenv('ACCESS_TOKEN')
            self.refresh_token = os.getenv('REFRESH_TOKEN')

    def build_csv(self, record: dict) -> (str, int):
        output = io.StringIO()
        writer = save_csv(output)
        writer.writerow(['goods_id', 'stock_quantity'])
        valid_lines = 0
        for item in record.get('cart', []):
            gid = item.get('goods_id')
            qty = item.get('quantity', 1)
            if not gid:
                continue
            writer.writerow([gid, -qty])
            valid_lines += 1
        return output.getvalue(), valid_lines

    def update_from_record(self, json_path: str) -> dict:
        with open(json_path, 'r', encoding='utf-8') as f:
            record = load_json(f)

        csv_data, valid = self.build_csv(record)
        if valid == 0:
            print(f"[InventoryUpdater] No valid goods_id found in {json_path}, skipping.")
            return {'skipped': True}

        if self.simulate:
            print(f"[InventoryUpdater] Simulation mode: would POST to {self.api_url}")
            print(csv_data)
            return {'simulated': True, 'csv': csv_data}

        payload = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'data_type_1': 'csv',
            'data_1': csv_data
        }
        resp = requests.post(self.api_url, data=payload)
        resp.raise_for_status()
        return resp.json()

    def update_all(self, data_dir='data') -> dict:
        results = {}
        pattern = os.path.join(data_dir, '*', 'sales_*.json')
        for path in glob.glob(pattern):
            try:
                res = self.update_from_record(path)
                results[path] = res
                print(f"Processed {path} => {res}")
            except Exception as e:
                results[path] = {'error': str(e)}
                print(f"Error processing {path} => {e}")
        return results

if __name__ == '__main__':
    iu = InventoryUpdater(token_env='.env.test', simulate=True)
    result = iu.update_all(data_dir='data')
    print(result)