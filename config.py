# config.py

import json
import os
from pathlib import Path

from dotenv import load_dotenv

# プロジェクトのルートディレクトリを取得
BASE_DIR = Path(__file__).parent

# 環境変数ファイルのロード順
for env_file in [".env", ".env.token", ".env.test"]:
    dotenv_path = BASE_DIR / env_file
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)

# settings.json を読み込む
settings_path = BASE_DIR / "data" / "settings.json"
if settings_path.exists():
    with open(settings_path, "r", encoding="utf-8") as f:
        SETTINGS = json.load(f)
else:
    SETTINGS = {}


class Config:
    """アプリケーション設定を一元管理するクラス"""

    # ----- Next Engine API 設定 -----
    NE_CLIENT_ID = os.getenv("NE_CLIENT_ID")
    NE_CLIENT_SECRET = os.getenv("NE_CLIENT_SECRET")
    NE_API_TOKEN = os.getenv("NE_API_TOKEN")
    NE_REFRESH_TOKEN = os.getenv("NE_REFRESH_TOKEN")
    NE_API_BASE_URL = os.getenv("NE_API_BASE_URL", "https://api.next-engine.org/api_v1/")

    # ----- ハードウェア設定（settings.json 優先） -----
    _hw = SETTINGS.get("hardware", {})
    PRINTER_MODEL = _hw.get("printer_model", "Epson TM-T30III")
    PRINTER_PORT = _hw.get("printer_port", "/dev/usb/lp0")
    CASH_DRAWER_PORT = _hw.get("cash_drawer_port", "/dev/ttyUSB0")
    DISPLAY_TYPE = _hw.get("display_type", "USB-HID LCD")

    # ----- その他共通設定 -----
    # 例: ログレベル、タイムアウトなどをここに追加可能
    LOG_LEVEL = SETTINGS.get("log_level", "INFO")
    API_TIMEOUT = SETTINGS.get("api_timeout", 30)
