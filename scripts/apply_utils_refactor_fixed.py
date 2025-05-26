#!/usr/bin/env python3
"""
apply_utils_refactor.py

既存のコードを utils モジュール呼び出しに置き換えるリファクタリングスクリプト。
使用例:
  python apply_utils_refactor.py --root /path/to/sakatsu_pos

ルールに合わない呼び出し文が残った場合は警告を出力します。
"""
import re
import sys
import argparse
from pathlib import Path

# 置換ルール: (説明, パターン, 置換後)
RULES = [
    ("import json", r"^import\s+json", "from utils.file_utils import load_json, save_json"),
    ("json.load(", r"json\.load\(", "load_json("),
    ("json.dump(", r"json\.dump\(", "save_json("),
    ("import csv", r"^import\s+csv", "from utils.file_utils import load_csv, save_csv"),
    ("csv.reader(", r"csv\.reader\(", "load_csv("),
    ("csv.writer(", r"csv\.writer\(", "save_csv("),
    ("datetime.now()", r"datetime\.now\(\)", "get_current_timestamp()"),
    ("datetime.strptime(", r"datetime\.strptime\(", "parse_date("),
    ("strftime(", r"\.strftime\(", "format_date("),
    ("timedelta(", r"timedelta\(", "add_days("),
    # ↓ 追加: datetime のインポート行を置換
    ("datetime import", r"^from\s+datetime\s+import\s+datetime,?\s*timedelta?", 
     "from utils.date_utils import get_current_timestamp, parse_date, add_days"),
    ("import datetime", r"^import\s+datetime",
     "from utils.date_utils import get_current_timestamp, parse_date, format_date, add_days"),
    # 省略: 省略記号によるtruncateやcurrencyフォーマットは手動対応を推奨
]

# レガシーパターン: 置換後残っていると要確認
LEGACY_PATTERNS = [
    r"\bimport\s+json\b",
    r"\bjson\.",
    r"\bimport\s+csv\b",
    r"\bcsv\.",
    r"\bdatetime\b",
    r"strftime\(",
    r"timedelta\(",
]

def process_file(path: Path):
    text = path.read_text(encoding='utf-8')
    # 対象外パス（utils、設定ファイル、スクリプト自身、仮想環境、site-packages）はスキップ
    p = str(path)
    if (
        'utils' in p or
        path.name in ('config.py', 'logger.py', 'apply_utils_refactor_fixed.py') or
        # Windows仮想環境・Unix venv ディレクトリを除外
        any(part in ('venv', '.venv', 'env', '.env') for part in path.parts) or
        'site-packages' in p or
        'pip\\_internal' in p.replace('/', '\\')  # pip内モジュール除外
    ):
        return False, []

    changes_made = False
    warnings = []

    for desc, pattern, repl in RULES:
        new_text, count = re.subn(pattern, repl, text, flags=re.MULTILINE)
        if count > 0:
            changes_made = True
            text = new_text

    # 置換結果を書き戻し
    if changes_made:
        path.write_text(text, encoding='utf-8')

    # レガシーパターンチェック
    for pat in LEGACY_PATTERNS:
        if re.search(pat, text):
            warnings.append(f"レガシーパターン残存: {pat}")

    return changes_made, warnings

def main():
    parser = argparse.ArgumentParser(description="Apply utils refactoring rules.")
    parser.add_argument("--root", type=str, default=".", help="プロジェクトルート")
    args = parser.parse_args()

    project_root = Path(args.root)
    summary = {}

    for file in project_root.rglob("*.py"):
        changed, warnings = process_file(file)
        if changed or warnings:
            summary[str(file)] = {
                "changed": changed,
                "warnings": warnings
            }

    # 結果出力
    for filepath, info in summary.items():
        print(f"ファイル: {filepath}")
        if info["changed"]:
            print("  置換実施")
        for w in info["warnings"]:
            print(f"  警告: {w}")
    print("リファクタリング完了")

if __name__ == "__main__":
    main()
