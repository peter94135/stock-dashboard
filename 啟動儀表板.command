#!/bin/bash
# 雙擊此檔即可啟動股票題材儀表板（會自動開啟瀏覽器）
cd "$(dirname "$0")"
echo "啟動股票題材儀表板…"
python3 server.py
