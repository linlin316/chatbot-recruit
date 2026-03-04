from flask import current_app

from .safety import should_block, normalize_text
from .faq import match_faq
from .llm_claude import claude_reply
from .greeting import get_greeting_reply, strip_greeting_prefix


def handle_chat(user_text: str) -> dict:
    """
    チャットの処理フロー
    戻り値: {"reply": "...", "source": "faq/ai", ...}
    """
    text = (user_text or "").strip()

    # 空チェック
    if not text:
        return {"reply": "質問を入力してください。", "source": "system"}
    
    # あいさつ検知
    greet = get_greeting_reply(text)
    if greet:
        return {"reply": greet, "source": "greeting"}
    
    # 文頭の挨拶を取り除く
    stripped = strip_greeting_prefix(text)
    if stripped:
        text = stripped

    # 短すぎる入力（正規化後で判定）
    if len(normalize_text(text)) < current_app.config["MIN_CHARS"]:
        return {"reply": "もう少し詳しく教えてください。", "source": "system"}

    # 長文制限（元の文字数で判定）
    if len(text) > current_app.config["MAX_CHARS"]:
        max_chars = current_app.config["MAX_CHARS"]
        return {"reply": f"文章が長すぎます。（{max_chars}文字以内で入力してください）", "source": "system"}

    # 危険系は人工へ
    if should_block(text):
        return {"reply": "その内容はAIでは回答できません。恐れ入りますが採用担当へお問い合わせください。", "source": "system"}

    # FAQ優先
    faq_reply = match_faq(text)
    if faq_reply:
        return {"reply": faq_reply, "source": "faq"}
    
    # それ以外はClaude
    reply = claude_reply(text)
    return {"reply": reply, "source": "ai"}