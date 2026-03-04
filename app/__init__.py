import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address



# Limiter は module-level で一つだけ作って init_app する
limiter = Limiter(
    get_remote_address,
    default_limits=["60 per hour"],
    storage_uri="memory://",
)


def create_app() -> Flask:
    load_dotenv()

    # 起動時に必須の環境変数チェック（最初のAPI呼び出しまで気づけない問題を防ぐ）
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "環境変数 ANTHROPIC_API_KEY が設定されていません。"
            ".env ファイルまたは環境変数を確認してください。"
        )

    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    # Limiter（全體デフォルト + memory storage）
    limiter.init_app(app)

    # routes（Blueprint）
    from .routes import bp
    app.register_blueprint(bp)

    # 429 handler（limiter 超過）
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"reply": "リクエストが多すぎます。しばらくしてから再度お試しください。"}), 429

    return app