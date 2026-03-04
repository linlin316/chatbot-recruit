import re
import unicodedata


def normalize_text(text: str) -> str:
    """ユーザー入力をFAQ判定しやすい形に正規化"""
    if not text:
        return ""

    # 全角は半角になる
    text = unicodedata.normalize("NFKC", text)

    # 小文字化
    text = text.lower()

    # 余分な空白除去
    text = re.sub(r"\s+", "", text)

    return text


# ===== 危険系キーワード（AI回答禁止）=====
BLOCK_KEYWORDS = [

    # ===== 個人情報系 =====
    "個人情報", "個人データ", "マイナンバー", "パスワード",
    "暗証番号", "ログイン情報", "認証情報", "銀行口座",
    "口座", "クレジット", "クレジットカード", "カード番号", "カード情報",

    # ===== 機密系 =====
    "社外秘", "機密", "内部資料", "訴訟", "裁判",

    # ===== 人事・内部評価 =====
    "人事評価", "評価情報", "解雇", "クビ", "降格", "内部告発",
]


# モジュールロード時に一度だけ正規化
_NORMALIZED_BLOCK_KEYWORDS = [normalize_text(k) for k in BLOCK_KEYWORDS]


def should_block(text: str) -> bool:
    """危険系の質問はAI回答しない"""
    t = normalize_text(text)
    return any(k in t for k in _NORMALIZED_BLOCK_KEYWORDS)