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
        self.simulate = simulate
        self.token_env = token_env
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copyfile(token_env, f"{token_env}.bak_{timestamp}")
        except Exception:
            pass
        load_dotenv(token_env, override=True)
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
        # Support Next Engine nested response
        # e.g., {'result':'success','response':{'access_token':...,'refresh_token':...}}
        if 'response' in resp_json:
            data = resp_json['response']
        else:
            data = resp_json
        access = data.get('access_token')
        refresh = data.get('refresh_token')
        if not access or not refresh:
            raise RuntimeError(f"Failed to refresh token, response: {resp_json}")
        lines = []
        try:
            with open(self.token_env, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            pass
        with open(self.token_env, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith('NE_ACCESS_TOKEN='):
                    f.write(f"NE_ACCESS_TOKEN={access}\n")
                elif line.startswith('NE_REFRESH_TOKEN='):
                    f.write(f"NE_REFRESH_TOKEN={refresh}\n")
                else:
                    f.write(line)
        self.ne_access_token = access
        self.ne_refresh_token = refresh

    # ... rest of class unchanged ...
