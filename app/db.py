import sqlite3
import os

# DBファイルの場所（プロジェクトルートの data/ フォルダ）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "chatbot.db")


def get_db():
    """DB接続を返す"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 結果を辞書形式で取得できるようにする
    return conn


def init_db():
    """テーブルを作成する（存在しない場合のみ）"""
    conn = get_db()
    cursor = conn.cursor()

    # FAQテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faq (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            key      TEXT NOT NULL,
            synonyms TEXT NOT NULL DEFAULT '[]',
            answer   TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 5
        )
    """)

    # FAQにヒットしなかった質問の記録テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unanswered (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            question  TEXT NOT NULL,
            asked_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("DBの初期化が完了しました")