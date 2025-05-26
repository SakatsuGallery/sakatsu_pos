# Sakatsu_POS – 開発者向け README  
**最終更新:** 2025‑05‑22 (JST)  

本リポジトリは *さかつうギャラリー* 実店舗向け POS システム **Sakatsu_POS** のソースコードを管理します。  
Next Engine API と連携し、会計・在庫・日次／月次バックオフィス処理を一貫して行います。  

## 主な機能
- 会計完了時に Next Engine 在庫を即時減算 (`InventoryUpdater.update_from_record`)  
- オフラインキューイングと自動リトライ  
- 日次・月次処理ボタン／売上4金額レシート印字  
- Tkinter GUI (Surface 7 タブレット最適化)  
- サーマルプリンタ ESC/POS 出力・キャッシュドロワ制御・カスタマーディスプレイ表示  

## ディレクトリ構成
```
sakatsu_pos/
  main.py               エントリポイント
  logic/                会計・在庫ロジック層
  nextengine/           NE API 連携層
  ui/                   GUI・周辺機器制御
  data/                 ローカルキャッシュ・ログ
  tests/                pytest 自動テスト
```
詳細はコード内 docstring を参照してください。

## セットアップ手順
1. Python 3.13.2 をインストール  
2. 仮想環境を作成しアクティブ化  
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows は .venv\Scripts\activate
   ```
3. 依存パッケージをインストール  
   ```bash
   pip install -r requirements.txt
   ```
4. `.env.token` と `.env.test` をプロジェクトルートに配置し、クライアント ID 等を設定  

## 実行
```bash
python main.py
```
コマンドライン引数 `--offline` で API 呼び出しを抑止し、ローカル CSV のみ更新できます。

## 日次／月次処理
- **日次**: UI の「日次処理実行」ボタンまたは `python main.py --daily`.  
- **月次**: `--monthly` オプション。  

## テスト
```bash
pytest -q
```

## ハードウェア
- レシートプリンタ: Epson TM‑T30III (USB)  
- キャッシュドロワ: USB‑Serial, ESC/POS kick 信号  
- カスタマーディスプレイ: USB‑HID LCD 2×20  

## 品質保証プロセス
変更時は README・仕様書同時更新、pytest・E2E、UI スクリーンショットを必須とします。

---
### 依存ライブラリ
`requirements.txt` を参照してください。
