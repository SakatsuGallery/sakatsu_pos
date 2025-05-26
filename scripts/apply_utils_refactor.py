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
    ("dt.strftime(", r"(\w+)\.strftime\(", "format_date("),
    ("timedelta\(", r"timedelta\(", "add_days("),
    ("len(text)>n", r"text\[:(\d+)\]\s*\+\s*['\u2026']", "truncate_text"),
    ("f"¥{int(x):,}"", r"f"¥\{int\(([^}]+)\):,\}"", r"format_currency(\1)")
]

# レガシーパターン: 置換後残っていると要確認
LEGACY_PATTERNS = [
    r"\bimport\s+json\b",
    r"\bjson\.",
    r"\bimport\s+csv\b",
    r"\bcsv\.",
    r"\bdatetime\.",
    r"\bstrptime\(",
    r"\.strftime\(",
    r"\btimedelta\(",
]

def process_file(path: Path):
    text = path.read_text(encoding='utf-8')
    original = text
    # Skip utils directory and special files
    if 'utils' in path.parts or path.name in ('config.py', 'logger.py'):
        return False, []

    changes = []
    for desc, pattern, repl in RULES:
        new_text, count = re.subn(pattern, repl, text, flags=re.MULTILINE)
        if count > 0:
            changes.append(f"{desc}: {count}件置換")
            text = new_text

    path.write_text(text, encoding='utf-8')

    # Check for legacy patterns
    warnings = []
    for pat in LEGACY_PATTERNS:
        if re.search(pat, text):
            warnings.append(f"注意: レガシーパターン '{pat}' が残存")

    return bool(changes), warnings

def main():
    parser = argparse.ArgumentParser(description="Apply utils refactoring rules.")
    parser.add_argument("--root", type=str, default=".", help="プロジェクトルート")
    args = parser.parse_args()

    root = Path(args.root)
    py_files = root.rglob("*.py")
    summary = {}
    for file in py_files:
        changed, warnings = process_file(file)
        if changed or warnings:
            summary[str(file)] = {"changed": changed, "warnings": warnings}

    # 出力
    for filepath, info in summary.items():
        print(f"ファイル: {filepath}")
        if info["changed"]:
            print("  置換実施")
        if info["warnings"]:
            for w in info["warnings"]:
                print(f"  {w}")
    print("リファクタリング完了")

if __name__ == "__main__":
    main()
