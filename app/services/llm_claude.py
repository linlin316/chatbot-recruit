import os
import threading
import anthropic

from ..config import Config

# ===== Claude API 呼び出し回数カウンター =====
# ログ出力専用。制限には使用していない
# サーバー再起動でリセットされる
_claude_call_lock = threading.Lock()
_call_count = 0


# ===== システムプロンプト（モジュールレベル定数・毎回生成しない）=====
SYSTEM_PROMPT = f"""
あなたは{Config.COMPANY_NAME}の採用向けAIチャットボットです。
求職者向けに、丁寧で簡潔な日本語で回答してください。
会社情報は以下を最優先で参照し、推測で断定しないでください。

[会社情報]
- 会社名: {Config.COMPANY_NAME}
- 公式サイト: {Config.COMPANY_SITE}
- 勤務地: {Config.COMPANY_LOCATION}
- 問い合わせ: {Config.CONTACT_TEXT}

ルール:
- 回答は最大2文（各文60文字以内目安）。
- 分かる範囲は具体的に答える（例：制度の有無/基本方針）。
- 断定できない内容は「募集要項をご確認ください」で止める（推測しない）。
- 箇条書きは禁止（短文で）。
- 同じ案内文を毎回繰り返さない（必要なときだけ）。
- URLは原則出さない（必要なら「採用ページ」まで）。
""".strip()


def _build_client() -> anthropic.Anthropic | None:
    """
    APIキーがある時だけ Claude client を作る。
    キーがない場合は None を返し、claude_reply がエラーメッセージを返す。
    FAQだけで返せるケースでは、キーなしでもアプリは起動・動作できる。
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


# ===== クライアントを起動時に1回だけ作る =====
_client: anthropic.Anthropic | None = _build_client()


def claude_reply(user_text: str) -> str:
    global _call_count

    if _client is None:
        return "現在AI応答は利用できません。募集要項または採用担当へご確認ください。"
    
    try:
        with _claude_call_lock:
            _call_count += 1
            current = _call_count
        print(f"[Claude CALL] total={current}") # ログ出力のみ（再起動でリセットされる）

        msg = _client.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=Config.CLAUDE_MAX_TOKENS,
            temperature=Config.CLAUDE_TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_text}],
        )

        if not msg.content:
            return "現在AIが混み合っています。時間をおいて再度お試しください。"
        
        return msg.content[0].text
    
    except Exception as e:
        print("Claude error:", e)
        return "現在AIが混み合っています。時間をおいて再度お試しください。"