"""
FAQ管理スクリプト
実行方法: python manage_faq.py

目的：
- 未命中の質問（unanswered）を見ながら
- 既存FAQの同義語（synonyms）を増やしてFAQ命中率を上げる
- 結果として Claude/AI の呼び出し回数を減らす

=== (使い方の流れ) ===
1) 未命中質問一覧が表示される
2) 処理したい質問のIDを選ぶ
3) a を選ぶ → どのFAQキーに紐付けるか選ぶ
4) 同義語（短い言葉）を追加する
   例：「社長は誰ですか？」 → 同義語: "社長 代表 CEO"
5) その質問は unanswered から削除される（処理済み扱い）
"""

import json
import sqlite3
import os
from typing import List, Tuple

DB_PATH = os.path.join("data", "chatbot.db")


# DB接続
def get_conn() -> sqlite3.Connection:
    """SQLite接続を返す（毎回新規接続）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 文字の簡易正規化（おすすめ候補計算用）
def _norm(s: str) -> str:
    """
    文字列を比べやすくするための簡易正規化
    - 前後の空白を削除
    - 小文字にする
    """
    return (s or "").strip().lower()


def _bigrams(s: str) -> set[str]:
    """
    ざっくり「文字の似ている度合い」を見るための2文字セット（2-gram）
    例: "shacho" → {"sh","ha","ac","ch","ho"}
    """
    s = _norm(s)
    if len(s) < 2:
        return set()
    return {s[i : i + 2] for i in range(len(s) - 1)}


def _safe_load_list(raw: str) -> List[str]:
    """
    synonyms は DB に JSON（文字列）で入っているので list に戻す
    DB内のデータが壊れていても、ここで落ちないようにする
    """
    if not raw:
        return []
    try:
        v = json.loads(raw)
        return v if isinstance(v, list) else []
    except Exception:
        return []


# 表示：未命中質問
def show_unanswered(conn: sqlite3.Connection):
    """
    unanswered テーブルから未命中質問を表示する
    """
    rows = conn.execute(
        "SELECT id, question, asked_at FROM unanswered ORDER BY asked_at DESC"
    ).fetchall()

    if not rows:
        print("\n📭 未命中の質問はありません。\n")
        return []

    print("\n📋 未命中の質問一覧：")
    print("-" * 70)
    for row in rows:
        print(f"  [{row['id']}] {row['question']}  （{row['asked_at']}）")
    print("-" * 70)
    return rows


# 表示：FAQキー一覧
def show_faq_keys(conn: sqlite3.Connection):
    """
    FAQのキー一覧を表示する
    priority が高い順に並べる（重要なFAQが上に来る）
    """
    rows = conn.execute(
        'SELECT id, "key", priority FROM faq ORDER BY priority DESC, id ASC'
    ).fetchall()

    print("\n📚 FAQキー一覧：")
    print("-" * 50)
    for row in rows:
        print(f"  [{row['id']}] {row['key']}  （優先度{row['priority']}）")
    print("-" * 50)
    return rows


# おすすめFAQ候補（Top5）を計算
def suggest_faq_keys(conn: sqlite3.Connection, question: str, top_k: int = 5) -> List[Tuple[float, int, str, int]]:
    """
    ユーザーの未命中質問に対して「どのFAQキーが近そうか」をTop5で提案する。

    - unanswered が増えると、毎回どのFAQに紐付けるか迷って時間がかかる
    - そこで「候補」を出して、作業を早くする（運用が楽になる）

    考え方：
     質問文にFAQのキーが入っていたら → かなり近いので高得点
     例: "社長は誰？" に "社長" が含まれる
     質問文に既存の同義語が入っていたら → そこそこ近いので加点

     完全一致しない場合でも「文字の似ている感じ」を少しだけ参考にする
    （あくまで補助。強すぎると誤推薦が増える）
    
     同義語も少しだけ反映する
    （重要FAQを多少優先するため）
    """
    qn = _norm(question)
    qbg = _bigrams(question)

    rows = conn.execute('SELECT id, "key", priority, synonyms FROM faq').fetchall()
    scored: List[Tuple[float, int, str, int]] = []

    for r in rows:
        fid = int(r["id"])
        key = r["key"]
        pr = int(r["priority"] or 1)

        keyn = _norm(key)
        syns = _safe_load_list(r["synonyms"])

        evidence = 0.0

        # key が質問文に含まれるか
        if keyn and keyn in qn:
            evidence += 10.0

        # 既存同義語が質問文に含まれるか
        for syn in syns:
            sn = _norm(syn)
            if sn and sn in qn:
                evidence += 6.0
                break

        # 文字の似ている度合いを少しだけ反映
        kbg = _bigrams(key)
        if qbg and kbg:
            jacc = len(qbg & kbg) / max(1, len(qbg | kbg))
            evidence += jacc * 3.0

        # 証拠が0なら候補にしない
        if evidence <= 0.0:
            continue

        # 証拠がある時だけ同義語を加点
        score = evidence + pr * 0.2

        scored.append((score, fid, key, pr))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


# 紐付け処理（未命中 → FAQへ）
def link_to_faq(conn: sqlite3.Connection, unanswered_id: int, question: str):
    """
    未命中の質問を、既存FAQの同義語に追加する。

    ポイント：
    - 同義語は「短い言葉」の方が命中しやすい
      例: "社長" / "代表" / "CEO"
      ※長文そのままだと別の言い方に弱くなりがち
    """

    # おすすめ候補を表示（Top5）
    print("\n🔎 おすすめFAQ候補（Top5）:")
    recs = suggest_faq_keys(conn, question, top_k=5)
    if recs:
        for score, fid, key, pr in recs:
            print(f"  [{fid}] {key}（優先度{pr} / score={score:.2f}）")
    else:
        print("  （候補なし）")

    # FAQキー一覧を表示（全体）
    faq_rows = show_faq_keys(conn)

    # 紐付け先FAQを選ぶ
    id_str = input("紐付けるFAQのIDを入力: ").strip()
    if not id_str.isdigit():
        print("⚠️  数字を入力してください。")
        return

    target = next((r for r in faq_rows if r["id"] == int(id_str)), None)
    if not target:
        print("⚠️  そのIDは存在しません。")
        return

    # 追加する同義語を入力
    print(f"\n未命中質問: {question}")
    print("同義語は短い方が命中しやすいです。例: 社長 代表 CEO")
    custom = input("追加する同義語（空白区切り / Enterなら原文を追加）: ").strip()

    if custom:
        add_words = [w.strip() for w in custom.split() if w.strip()]
    else:
        # 従来互換：入力がなければ原文をそのまま同義語にする
        add_words = [question]

    # 既存のsynonymsを取り出して、追加して、DBへ保存
    row = conn.execute('SELECT synonyms FROM faq WHERE id = ?', (target["id"],)).fetchone()
    current = _safe_load_list(row["synonyms"] if row else "")

    changed = False
    for w in add_words:
        if w not in current:
            current.append(w)
            changed = True

    if not changed:
        print("ℹ️  追加する同義語はすべて既に登録済みでした。")
    else:
        conn.execute(
            'UPDATE faq SET synonyms = ? WHERE id = ?',
            (json.dumps(current, ensure_ascii=False), target["id"])
        )

    # unanswered から削除（今まで通り）
    conn.execute("DELETE FROM unanswered WHERE id = ?", (unanswered_id,))
    conn.commit()

    print(f"✅ 「{question}」を「{target['key']}」に紐付け、同義語に追加しました。")
    if custom:
        print(f"   追加した同義語: {add_words}")
    else:
        print("   追加した同義語: （原文）")


def delete_unanswered(conn: sqlite3.Connection, unanswered_id: int):
    """
    FAQには追加しないで、未命中質問を削除する
    例: いたずら/関係ない質問/機密質問など
    """
    conn.execute("DELETE FROM unanswered WHERE id = ?", (unanswered_id,))
    conn.commit()
    print("🗑  削除しました。")


# メイン処理
def main():
    """
    対話式で未命中質問を処理する
    """
    conn = get_conn()
    print("\n===== FAQ管理スクリプト =====")

    try:
        while True:
            rows = show_unanswered(conn)
            if not rows:
                break

            id_str = input("処理したい質問のIDを入力（qで終了）: ").strip()
            if id_str.lower() == "q":
                break
            if not id_str.isdigit():
                print("⚠️  数字を入力してください。")
                continue

            target = next((r for r in rows if r["id"] == int(id_str)), None)
            if not target:
                print("⚠️  そのIDは存在しません。")
                continue

            print(f"\n質問：「{target['question']}」")
            print("  a: FAQに紐付ける（同義語追加）")
            print("  d: 削除（FAQには追加しない）")
            print("  s: スキップ")
            action = input("選択: ").strip().lower()

            if action == "a":
                link_to_faq(conn, target["id"], target["question"])
            elif action == "d":
                delete_unanswered(conn, target["id"])
            elif action == "s":
                continue
            else:
                print("⚠️  a / d / s を入力してください。")

    finally:
        conn.close()

    print("終了します。")


if __name__ == "__main__":
    main()