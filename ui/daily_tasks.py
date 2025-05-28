# daily_tasks.py

import logging
import os
import shutil

from nextengine.inventory_updater import InventoryUpdater
from nextengine.sales_uploader import SalesUploader
from utils.date_utils import get_current_timestamp


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sim_flag = os.getenv("IS_SIMULATION", "true").lower() in ("1", "true", "yes")
    token_env = ".env.test" if sim_flag else ".env.token"

    logging.info("=== 日次同期＆バックアップ開始 ===")

    try:
        uploader = SalesUploader(token_env=token_env, simulate=sim_flag)
        res_sales = uploader.upload_all(data_dir="data")
        logging.info(f"Sales upload results: {res_sales}")
    except Exception as e:
        logging.error(f"Sales upload failed: {e}", exc_info=True)

    try:
        updater = InventoryUpdater(token_env=token_env, simulate=sim_flag)
        res_inv = updater.update_all(data_dir="data")
        logging.info(f"Inventory update results: {res_inv}")
    except Exception as e:
        logging.error(f"Inventory update failed: {e}", exc_info=True)

    # ── 修正済み ──
    # YYYYMM 形式のフォルダ名を取得
    yyyymm = get_current_timestamp(fmt="%Y%m")
    src_dir = os.path.join("data", yyyymm)
    dst_dir = os.path.join(r"Z:\backup\pos", yyyymm)
    try:
        if os.path.isdir(src_dir):
            os.makedirs(dst_dir, exist_ok=True)
            for fname in os.listdir(src_dir):
                shutil.copy2(os.path.join(src_dir, fname), dst_dir)
            logging.info(f"Backed up {src_dir} → {dst_dir}")
        else:
            logging.warning(f"Source directory not found: {src_dir}")
    except Exception as e:
        logging.error(f"Backup failed: {e}", exc_info=True)

    logging.info("=== 日次同期＆バックアップ完了 ===")


def run_daily_tasks(mode: str = "daily"):
    """日次／月次処理を GUI から呼び出すラッパー関数"""
    if mode == "daily":
        main()
    elif mode == "monthly":
        # 月次処理も日次と同じフローを実行
        main()
    else:
        raise ValueError(f"Unknown mode: {mode}")
