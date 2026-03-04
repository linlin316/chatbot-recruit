class Config:
    # 多すぎ入力
    MAX_CHARS = 200

    # 短すぎ入力
    MIN_CHARS = 2  

    # Claude(API)
    CLAUDE_MODEL = "claude-haiku-4-5-20251001"
    CLAUDE_MAX_TOKENS = 180
    CLAUDE_TEMPERATURE = 0.3   # 応答のランダム性制御

    # 1分間あたり最大20リクエストまで
    CHAT_LIMIT = "20 per minute"

    # 会社情報
    COMPANY_NAME = "株式会社PREAI"
    COMPANY_SITE = "https://www.preai.co.jp/"
    COMPANY_LOCATION = "名古屋（詳細は募集要項をご確認ください）"
    CONTACT_TEXT = "採用担当へお問い合わせください（採用ページの問い合わせフォーム）。"