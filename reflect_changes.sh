#!/usr/bin/env bash
set -euo pipefail

# 1. キャッシュ解除（もしまだなら）
git rm --cached -r utils/__pycache__ nextengine/__pycache__ || true

# 2. .gitignore に __pycache__／.env を無視設定（省略済みならコメントアウト）
cat << 'EOF' >> .gitignore
__pycache__/
*.pyc
.env
.env.test
EOF

# 3. ステージング
git add .gitignore \
        utils/file_utils.py \
        nextengine/inventory_updater.py

# 4. コミット
git commit -m "fix: apply final refactor of file_utils and inventory_updater"

# 5. プッシュ
git push origin main
