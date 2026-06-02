#!/bin/bash
# 推送脚本：本地保持 /home/xiaoxin，GitHub 使用 /home/user

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
TEMP_README="$REPO_DIR/README.md.github"

echo "📦 准备推送到 GitHub..."

# 备份并替换 README.md 中的路径
cp "$REPO_DIR/README.md" "$TEMP_README"
sed -i 's|/home/xiaoxin|/home/user|g' "$REPO_DIR/README.md"

echo "✅ 已替换路径：/home/xiaoxin -> /home/user"

# 提交并推送
cd "$REPO_DIR"
git add README.md
git commit -m "docs: 示例路径使用通用用户名 /home/user" || echo "无变更"
git push origin main

echo "✅ 已推送到 GitHub"

# 恢复本地文件
mv "$TEMP_README" "$REPO_DIR/README.md"
git checkout README.md

echo "✅ 已恢复本地路径：/home/xiaoxin"
echo "🎉 完成！"
