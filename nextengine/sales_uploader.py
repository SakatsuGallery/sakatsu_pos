# nextengine/sales_uploader.py

import os
import glob
import io
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv
from utils.file_utils import load_json
from logger import get_logger

log = get_logger(__name__)

class SalesUploader:
    API_URL = 'https://api.next-engine.org/api_v1_receiveorder_base/upload'

    def __init__(self, token_env='.env.token', pattern_id=1, wait_flag=1):
        """
        pattern_id: Next Engine 側の受注一括登録パターンID
        wait_flag: メイン機能過負荷時の挙動 (1:エラーにせず実行)
        """
        # 環境変数の読み込み
        load_dotenv(token_env)
        # 大文字・小文字両対応でトークン取得
        self.access_token = os.getenv('ACCESS_TOKEN') or os.getenv('access_token')
        self.refresh_token = os.getenv('REFRESH_TOKEN') or os.getenv('refresh_token')
        if not self.access_token:
            raise RuntimeError(f"ACCESS_TOKEN not found in {token_env}")

        self.pattern_id = pattern_id
        self.wait_flag = wait_flag

    def build_csv(self, record: dict) -> str:
        """
        JSON record を受注CSV文字列に変換。
        必要なカラムを CSV ヘッダーとして定義し、その順序で出力します。
        ヘッダー例: 店舗伝票番号,受注日,受注名,支払方法,合計金額,商品名,商品コード,商品価格,受注数量
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー行
        headers = [
            '店舗伝票番号', '受注日', '受注名',
            '支払方法', '合計金額',
            '商品名', '商品コード', '商品価格', '受注数量'
        ]
        writer.writerow(headers)

        # データ行
        tx_id = record.get('transaction_id')
        # ISO 8601 ⽂字列→datetime→指定フォーマット文字列
        dt_obj = datetime.fromisoformat(record.get('timestamp'))
        dt = dt_obj.strftime('%Y/%m/%d %H:%M:%S')

        payments = record.get('payments', [])
        payment_method = payments[0]['method'] if payments else ''
        total = int(record.get('total_due', 0))

        for item in record.get('cart', []):
            writer.writerow([
                tx_id,
                dt,
                tx_id,
                payment_method,
                total,
                item.get('name'),
                item.get('code', item.get('name')),
                int(item.get('price', 0)),
                item.get('quantity', 1)
            ])

        return output.getvalue()

    def upload_record(self, json_path: str) -> dict:
        """
        単一の JSON 売上ファイルをアップロード。
        成功時はレスポンス JSON を返します。
        """
        # JSON 読み込みは load_json(path) を利用
        record = load_json(json_path)
        csv_data = self.build_csv(record)

        payload = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'wait_flag': self.wait_flag,
            'receive_order_upload_pattern_id': self.pattern_id,
            'data_type_1': 'csv',
            'data_1': csv_data
        }
        resp = requests.post(self.API_URL, data=payload)
        resp.raise_for_status()
        return resp.json()

    def upload_all(self, data_dir='data') -> dict:
        """
        data/YYYYMM/*.json を対象に upload_record を実行。
        返り値: ファイルパスをキー、レスポンスまたはエラーを値とした dict
        """
        results = {}
        pattern = os.path.join(data_dir, '*', 'sales_*.json')
        log.debug(f"Searching for files with pattern: {pattern}")

        for jp in glob.glob(pattern):
            try:
                res = self.upload_record(jp)
                results[jp] = res
                log.info(f"Uploaded {jp} => {res}")
            except Exception as e:
                results[jp] = {'error': str(e)}
                log.error(f"Error uploading {jp} => {e}", exc_info=True)

        return results

if __name__ == '__main__':
    su = SalesUploader(token_env='.env.token', pattern_id=1)
    results = su.upload_all(data_dir='data')
    print(results)
