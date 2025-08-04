#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
parse_callback_auto.py

Next Engine の OAuth2 風認可フローを自動化するスクリプトです。

■使い方
    1) そのまま引数なしで実行すると、
       - 環境変数 .env に定義済みの NE_CLIENT_ID・NE_CLIENT_SECRET・NE_REDIRECT_URI を読み込む
       - /users/sign_in/?client_id=…&redirect_uri=… をブラウザで開く（uid/state 取得フェーズ）
       - ローカルでポート（8443）を立ててコールバック（/callback?uid=…&state=…）を待つ
       - コールバックを受けると自動的に POST /api_neauth を叩いて access_token/refresh_token を取得
       - 取得したトークンを .env に上書き保存
    2) 引数にコールバック URL を直接渡すと（手動コピー＆ペースト）、同じくトークン交換→.env 更新を行う

── 自動インストール
    requests と python-dotenv がなければ、自動で pip install します。
"""

import os
import sys
import threading
import importlib
import subprocess
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser

# 必要パッケージを自動インストール
for pkg, mod in [('requests', 'requests'), ('python-dotenv', 'dotenv')]:
    try:
        importlib.import_module(mod)
    except ImportError:
        print(f"Installing missing package: {pkg} …")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])

import requests
from dotenv import load_dotenv

# デフォルトのローカルポート（.env の REDIRECT_URI と合わせる）
DEFAULT_PORT = 8443


class CallbackHandler(BaseHTTPRequestHandler):
    """
    ローカルで /callback に飛んできたリクエストを受け取り、
    URL 中の uid, state, code（あるいは id）を取り出して
    /api_neauth に POST し、.env を更新する。
    """

    def do_GET(self):
        # まず path をパース
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != '/callback':
            self.send_error(404)
            return

        # クエリパラメータを辞書化
        params = urllib.parse.parse_qs(parsed.query)
        uid_list   = params.get('uid', [])
        state_list = params.get('state', [])
        # Next Engine 仕様では「id」ではなく「code」で返ることはないが念のため両方チェック
        code_list  = params.get('code', []) or params.get('id', [])

        uid   = uid_list[0]   if uid_list else None
        state = state_list[0] if state_list else None
        code  = code_list[0]  if code_list else None

        if not (uid and state):
            # code は使わず、実際は uid と state が正しく戻ってくる
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing parameters (uid/state)")
            return

        # .env から client_id, client_secret, redirect_uri を読み込む
        load_dotenv('.env', override=True)
        client_id     = os.getenv('NE_CLIENT_ID')
        client_secret = os.getenv('NE_CLIENT_SECRET')
        redirect_uri  = os.getenv('NE_REDIRECT_URI')

        if not (client_id and client_secret and redirect_uri):
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"NE_CLIENT_ID/NE_CLIENT_SECRET/NE_REDIRECT_URI missing in .env")
            return

        # Next Engine のトークン交換エンドポイント
        # （テスト環境のときは環境変数やコード中で調整してください）
        token_url = 'https://api.next-engine.org/api_neauth'

        # POST データを構築
        payload = {
            'uid':           uid,
            'state':         state,
            'client_id':     client_id,
            'client_secret': client_secret
        }

        try:
            resp = requests.post(token_url, data=payload)
            resp.raise_for_status()
            j = resp.json()
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Token exchange HTTP error: {e}".encode('utf-8'))
            return

        # Next Engine のレスポンス確認
        # 正常時は result が "success"、レスポンスボディに access_token/refresh_token が含まれる
        if j.get('result') != 'success':
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Token exchange failed: {j}".encode('utf-8'))
            return

        data = j.get('response', j)
        access_token  = data.get('access_token')
        refresh_token = data.get('refresh_token')

        if not (access_token and refresh_token):
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Invalid token response: {j}".encode('utf-8'))
            return

        # ------- ここで .env を更新 -------
        env_path = '.env'
        # 既存の .env 中身を行単位で読む
        existing_lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                existing_lines = f.readlines()

        # キー=値 ペアにパース
        env_dict = {}
        for line in existing_lines:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                env_dict[k] = v

        # 新しい値をセット（上書き）
        env_dict['NE_CLIENT_ID']     = client_id
        env_dict['NE_AUTH_STATE']    = state
        env_dict['NE_ACCESS_TOKEN']  = access_token
        env_dict['NE_REFRESH_TOKEN'] = refresh_token

        # ファイルに書き戻し
        with open(env_path, 'w', encoding='utf-8') as f:
            for k, v in env_dict.items():
                f.write(f"{k}={v}\n")

        # レスポンスを返してブラウザ側を閉じてもらう
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Tokens updated successfully. You may close this window.")

        # サーバをシャットダウンさせる
        threading.Thread(target=self.server.shutdown).start()


def start_server_flow():
    """
    ブラウザで /users/sign_in/?client_id=…&redirect_uri=… を開き、
    ローカルでコールバックを受け取って access/refresh を更新する流れ。
    """

    # .env から必要な情報を読み込む
    load_dotenv('.env', override=True)
    client_id    = os.getenv('NE_CLIENT_ID')
    redirect_uri = os.getenv('NE_REDIRECT_URI')

    if not (client_id and redirect_uri):
        print("Error: NE_CLIENT_ID および NE_REDIRECT_URI を .env に設定してください。")
        sys.exit(1)

    # state は一度だけ生成して .env に書き込んでおく
    existing_state = os.getenv('NE_AUTH_STATE')
    if existing_state:
        state = existing_state
    else:
        state = os.urandom(8).hex()
        with open('.env', 'a', encoding='utf-8') as f:
            f.write(f"NE_AUTH_STATE={state}\n")

    # Next Engine の「uid/state 取得用」のサインイン URL
    # 本番環境では base.next-engine.org、テスト環境では test-base.next-engine.org に置き換え
    base_signin = 'https://base.next-engine.org/users/sign_in/'  # ← 本番用
    #base_signin = 'https://test-base.next-engine.org/users/sign_in/'  # ← テスト用に書き換える

    urlencode_redirect = urllib.parse.quote(redirect_uri, safe='')
    auth_url = (
        f"{base_signin}"
        f"?client_id={client_id}"
        f"&redirect_uri={urlencode_redirect}"
    )

    print("Opening browser for authorization (uid/state 取得)…")
    webbrowser.open(auth_url)

    # ローカルでコールバックを待ち受ける
    local_port = urllib.parse.urlparse(redirect_uri).port or DEFAULT_PORT
    httpd = HTTPServer(('127.0.0.1', local_port), CallbackHandler)
    print(f"Waiting for callback on {redirect_uri} …")
    httpd.serve_forever()
    print("Auth flow complete.")


def update_from_url_flow(url: str):
    """
    手動でコピーしたコールバックURLを引数に渡す場合の処理。
    例:
        python parse_callback_auto.py "https://xxxx.ngrok.app/callback?uid=…&state=…"
    """
    handler = CallbackHandler(request=None, client_address=None, server=None)
    # Handler に URL を直接セットして GET 処理をシミュレート
    parsed = urllib.parse.urlparse(url)
    handler.path = parsed.path + '?' + parsed.query
    handler.server = type('DummyServer', (), {'shutdown': lambda self: None})()
    handler.do_GET()


def main():
    if len(sys.argv) == 1:
        start_server_flow()
    elif len(sys.argv) == 2:
        update_from_url_flow(sys.argv[1])
    else:
        print("Usage:")
        print("  python parse_callback_auto.py")
        print('  python parse_callback_auto.py "<callback_url>"')
        sys.exit(1)


if __name__ == '__main__':
    main()
