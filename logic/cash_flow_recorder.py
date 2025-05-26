# logic/cash_flow_recorder.py
from pathlib import Path
import os
from utils.file_utils import save_json, ensure_dir
from utils.date_utils import get_current_timestamp
from logger import get_logger

log = get_logger(__name__)

class CashFlowRecorder:
    def __init__(self, data_dir="data"):
        """
        data_dir: 取引データ保存ルートディレクトリ。
        入金／出金は data/cashflow/YYYYMM/ に JSON ファイルで保存します。
        """
        self.data_dir = Path(data_dir)

    def _write(self, record: dict, prefix: str) -> str:
        """
        レコードを JSON ファイルとして保存し、ファイルパスを返します。
        """
        # タイムスタンプ（YYYYMMDD_HHMMSS）と年月ディレクトリ（YYYYMM）を取得
        ts = get_current_timestamp(fmt='%Y%m%d_%H%M%S')
        ym = get_current_timestamp(fmt='%Y%m')
        dir_path = self.data_dir / "cashflow" / ym

        # ディレクトリ作成
        ensure_dir(str(dir_path))

        # ファイル名生成と保存
        fname = f"{prefix}_{ts}.json"
        path = dir_path / fname
        save_json(str(path), record)
        log.info(f"Recorded {prefix}: {path}")
        return str(path)

    def record_deposit(self, amount: float) -> str:
        """現金入金を記録し、ファイルパスを返します。"""
        rec = {
            "type": "deposit",
            "timestamp": get_current_timestamp(fmt='%Y-%m-%dT%H:%M:%S'),
            "amount": amount
        }
        return self._write(rec, "deposit")

    def record_withdraw(self, amount: float) -> str:
        """現金出金を記録し、ファイルパスを返します。"""
        rec = {
            "type": "withdraw",
            "timestamp": get_current_timestamp(fmt='%Y-%m-%dT%H:%M:%S'),
            "amount": amount
        }
        return self._write(rec, "withdraw")
