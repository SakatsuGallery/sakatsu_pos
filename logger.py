# logger.py

import logging
import os
from logging.handlers import RotatingFileHandler

from config import Config

# ログ出力ディレクトリ
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """
    指定した名前のロガーを取得し、共通設定を適用する。
    コンソールとファイル（ローテート）へ出力します。
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # ログレベル
        level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)

        # フォーマット
        fmt = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
        formatter = logging.Formatter(fmt)

        # コンソール出力
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # ファイル出力（ローテーション）
        fh = RotatingFileHandler(
            filename=os.path.join(LOG_DIR, f"{name}.log"),
            maxBytes=10 * 1024 * 1024,  # 10MiB ごとにローテート
            backupCount=5,  # 古いログを 5 世代まで保持
            encoding="utf-8",
        )
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
