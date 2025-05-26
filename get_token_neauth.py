# --- ファイル: get_token_neauth.py ---
import os
import requests
from dotenv import load_dotenv

# テスト環境用の .env.test を読み込む
load_dotenv('.env.test')

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

if not CLIENT_ID or not CLIENT_SECRET:
    print('[ERROR] CLIENT_ID または CLIENT_SECRET が .env.test に設定されていません。')
    exit(1)

# ブラウザコールバックから取得した uid と state を入力
uid = input('uid を入力してください: ').strip()
state = input('state を入力してください: ').strip()

# Next Engine ネクストエンジンの neauth トークン取得エンドポイント
token_url = 'https://api.next-engine.org/api_v1_neauth/access_token'

payload = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'uid': uid,
    'state': state,
    'redirect_uri': REDIRECT_URI
}

response = requests.post(token_url, data=payload)

print('\n[DEBUG] レスポンス内容：')
try:
    data = response.json()
except ValueError:
    print(response.text)
    exit(1)

print(data)

if data.get('result') == 'success':
    # 成功時は .env.token に access/refresh を書き込み
    token_path = '.env.token'
    with open(token_path, 'w', encoding='utf-8') as f:
        f.write(f"ACCESS_TOKEN={data.get('access_token')}\n")
        f.write(f"REFRESH_TOKEN={data.get('refresh_token')}\n")
    print(f"\n[SUCCESS] アクセストークンを {token_path} に保存しました。")
else:
    print(f"\n[ERROR] トークン取得に失敗しました: {data.get('message')}")
