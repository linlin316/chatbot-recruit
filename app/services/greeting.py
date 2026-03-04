import re
from .safety import normalize_text

# ===== あいさつ検知 =====
GREETING_MAP = {
    "ありがとう":       "こちらこそありがとうございます！他にご質問があればお気軽にどうぞ。",
    "はじめまして":     "はじめまして！採用に関するご質問があればお気軽にどうぞ。",
    "おはよう":         "おはようございます！採用に関するご質問があればお気軽にどうぞ。",
    "こんにちは":       "こんにちは！採用に関するご質問があればお気軽にどうぞ。",
    "こんばんは":       "こんばんは！採用に関するご質問があればお気軽にどうぞ。",
    "よろしく":         "よろしくお願いいたします！ご質問があればなんでもどうぞ。",
    "お世話になります": "お世話になります！採用に関するご質問があればお気軽にどうぞ。",
    "失礼します":       "いえいえ、お気軽にどうぞ！採用に関するご質問をお待ちしております。",
}


# モジュールロード時に一度だけ正規化
_NORMALIZED_GREETING_MAP = {normalize_text(k): v for k, v in GREETING_MAP.items()}


_QUESTION_HINTS = [normalize_text(h) for h in [
    "?", "？", "できますか", "ですか", "でしょうか",
    "教えて", "どこ", "勤務地", "勤務時間", "給与", "年収",
]]


# 長すぎる＝本題ありの可能性が高い
_GREETING_MAX_LEN = 12


def get_greeting_reply(text: str) -> str | None:
    """
    あいさつを検知したら対応する返答を返す。
    ただし「挨拶 + 本題」を誤って潰さないように、簡単なガードを入れる。
    """
    t = normalize_text(text)
    if not t:
        return None

    # 質問っぽいものは greeting 扱いしない（本題優先）
    if any(h in t for h in _QUESTION_HINTS):
        return None

    # 長すぎる文は greeting 扱いしない（本題ありの可能性が高い）
    if len(t) > _GREETING_MAX_LEN:
        return None

    # 末尾の記号だけ落とす
    t = re.sub(r"[!！。,.，、]+$", "", t)

    # 挨拶ワードが含まれていれば挨拶返し
    for key, reply in _NORMALIZED_GREETING_MAP.items():
        if key in t:
            return reply

    return None


def strip_greeting_prefix(text: str) -> str:
    """
    文頭の挨拶だけを取り除く（挨拶+本題をFAQ/LLMに流すため）
    例: 「こんにちは、募集したいです」→「募集したいです」
    """
    if not text:
        return ""
    t = text.strip()

    # 長い順に試す（「お世話になります」が「よろしく」より先にマッチするよう）
    keys_sorted = sorted(GREETING_MAP.keys(), key=len, reverse=True)

    for greeting_key in keys_sorted:
        # 元テキストの先頭が挨拶で始まるか確認（正規化せず直接比較）
        if t.startswith(greeting_key):
            remainder = t[len(greeting_key):]
            # 区切り文字（句読点・空白）を除去
            remainder = re.sub(r"^[\s　、,。.!！]+", "", remainder)
            return remainder.strip()

        # 全角→半角変換などで一致する場合も考慮（normalize同士で比較）
        norm_key = normalize_text(greeting_key)
        norm_t = normalize_text(t)
        if norm_t.startswith(norm_key):
            # 元テキストから近似的に残りを取り出す
            # normalize後の長さ分だけ元テキストを進める（保守的に文字数で推定）
            cut = len(greeting_key)
            remainder = t[cut:]
            remainder = re.sub(r"^[\s　、,。.!！]+", "", remainder)
            return remainder.strip()

    return t