#!/bin/bash
cd /root/nike-project || exit 1
source .venv/bin/activate
python3 fetch_nke.py       >> logs/refresh.log 2>&1
python3 build_dashboard.py >> logs/refresh.log 2>&1
python3 news.py            >> logs/refresh.log 2>&1
echo "--- done $(date -u) ---" >> logs/refresh.log
