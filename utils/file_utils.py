import json
import csv
from pathlib import Path
import io

def ensure_dir(path: str):
    """指定したディレクトリを作成する（存在しなければ）。"""
    Path(path).mkdir(parents=True, exist_ok=True)

def load_json(path_or_file):
    """JSONファイルを読み込み、オブジェクトを返す。
    path_or_file: ファイルパス文字列またはファイルオブジェクトのいずれかを受け付ける。"""
    if hasattr(path_or_file, 'read'):
        return json.load(path_or_file)
    with open(path_or_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path: str, data):
    """オブジェクトをJSONファイルに保存する。"""
    ensure_dir(Path(path).parent)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_csv(path: str):
    """CSVファイルをリスト形式で読み込み、返す。"""
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        return list(reader)

def save_csv(path: str, rows):
    """リスト形式のデータをCSVファイルに保存する。"""
    ensure_dir(Path(path).parent)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
