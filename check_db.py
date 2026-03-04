"""
DBの中身を確認するスクリプト
実行方法: python check_db.py
"""

import sqlite3
import os

DB_PATH = os.path.join("data", "chatbot.db")
conn = sqlite3.connect(DB_PATH)

print("\n===== FAQに命中しなかった質問 =====")
rows = conn.execute("SELECT id, question, asked_at FROM unanswered ORDER BY asked_at DESC").fetchall()
if rows:
    for row in rows:
        print(f"[{row[0]}] {row[2]}  →  {row[1]}")
else:
    print("なし")