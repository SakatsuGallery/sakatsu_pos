import logging
import os
import shutil
import sys
from pathlib import Path

# プロジェクトルートをパスに追加して nextengine モジュールを解決
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nextengine.inventory_updater import InventoryUpdater
from nextengine.sales_uploader import SalesUploader
from utils.date_utils import get_current_timestamp

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # シミュレーションモード判定
    sim_flag = os.getenv("IS_SIMULATION", "false").lower() in ("1", "true", "yes")
    token_env = ".env.test" if sim_flag else ".env"

    logging.info("=== 日次同期＆バックアップ開始 ===")

    # ① 在庫同期処理
    try:
        updater = InventoryUpdater(token_env=token_env, simulate=sim_flag)
        res_inv = updater.update_all(data_dir="data")
        logging.info(f"Inventory update results: {res_inv}")
    except Exception as e:
        logging.error(f"Inventory update failed: {e}", exc_info=True)

    # ② 売上アップロード処理
    try:
        uploader = SalesUploader(token_env=token_env, pattern_id=1, wait_flag=1)
        res_sales = uploader.upload_all(data_dir="data")
        logging.info(f"Sales upload results: {res_sales}")
    except Exception as e:
        logging.error(f"Sales upload failed: {e}", exc_info=True)

    # ③ 日次バックアップ処理
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
    if mode in ("daily", "monthly"):
        main()
    else:
        raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()
