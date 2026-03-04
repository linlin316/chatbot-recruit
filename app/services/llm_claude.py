import os
import threading
import anthropic
from ..config import Config

# ===== Claude API 呼叫計數 =====
_claude_call_lock = threading.Lock()
_call_count = 0


#API KEY
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


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


def claude_reply(user_text: str) -> str:
    global _call_count
    try:
        with _claude_call_lock:
            _call_count += 1
            current = _call_count
        print(f"[Claude CALL] total={current}") # ログ目的のみ（再起動でリセットされる）

        msg = client.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=Config.CLAUDE_MAX_TOKENS,
            temperature=Config.CLAUDE_TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_text}],
        )
        return msg.content[0].text
    except Exception as e:
        print("Claude error:", e)
        return "現在AIが混み合っています。時間をおいて再度お試しください。"