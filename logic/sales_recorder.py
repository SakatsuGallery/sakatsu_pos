# logic/sales_recorder.py
import os
from pathlib import Path

from logger import get_logger
from nextengine.inventory_updater import InventoryUpdater
from utils.date_utils import get_current_timestamp
from utils.file_utils import ensure_dir, save_json

log = get_logger(__name__)


class SalesRecorder:
    def __init__(self, data_dir="data"):
        """
        data_dir: ルートの保存ディレクトリ (例: C:\\sakatsu_pos\\data)
        """
        self.data_dir = Path(data_dir)

    def record_sale(self, cart, total_due, payments, change, transaction_id=None, timestamp=None):
        """
        1取引分の売上データを保存し、その JSON パスを返します。
        - cart: list of dicts, each with keys 'goods_id', 'name', 'price', 'quantity'
        - total_due: 合計金額
        - payments: list of dicts, each with 'method' and 'amount'
        - change: お釣り
        - transaction_id: 任意の取引ID (Noneならタイムスタンプを使用)
        - timestamp: datetime オブジェクト (Noneなら現在時刻)
        """
        # タイムスタンプの準備
        if timestamp:
            # datetime オブジェクトの場合
            ts_str = timestamp.isoformat()
            file_ts = timestamp.strftime("%Y%m%d_%H%M%S")
            ym = timestamp.strftime("%Y%m")
        else:
            ts_str = get_current_timestamp(fmt="%Y-%m-%dT%H:%M:%S")
            file_ts = get_current_timestamp(fmt="%Y%m%d_%H%M%S")
            ym = get_current_timestamp(fmt="%Y%m")

        # 保存ディレクトリ準備
        dir_path = Path(self.data_dir) / ym
        ensure_dir(str(dir_path))

        # ファイル名生成
        fname = f"sales_{file_ts}.json"
        file_path = dir_path / fname

        # レコード作成
        record = {
            "transaction_id": transaction_id or file_ts,
            "timestamp": ts_str,
            "cart": [
                {
                    "goods_id": item.get("goods_id"),
                    "name": item.get("name"),
                    "price": item.get("price"),
                    "quantity": item.get("quantity", 1),
                }
                for item in cart
            ],
            "total_due": total_due,
            "payments": [{"method": pay["method"], "amount": pay["amount"]} for pay in payments],
            "change": change,
        }

        # JSON 保存
        save_json(str(file_path), record)
        log.info(f"Recorded sale: {file_path}")

        # 即時在庫同期
        try:
            sim_flag = os.getenv("IS_SIMULATION", "true").lower() in ("1", "true", "yes")
            token_env = ".env.test" if sim_flag else ".env.token"
            updater = InventoryUpdater(token_env=token_env, simulate=sim_flag)
            res = updater.update_from_record(str(file_path))
            log.info(f"Inventory update successful (simulate={sim_flag}): {res}")
        except Exception as e:
            log.error(f"Inventory update failed: {e}", exc_info=True)

        return str(file_path)
