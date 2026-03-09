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
    # .env を読み込む
    # ANTHROPIC_API_KEY がなくてもアプリは起動できるが、
    # FAQに命中しない質問への AI回答が無効になる
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    # Limiter 初期化
    limiter.init_app(app)

    # routes（Blueprint）
    from .routes import bp
    app.register_blueprint(bp)

    # 429 handler（limiter 超過）
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"reply": "リクエストが多すぎます。しばらくしてから再度お試しください。"}), 429

    return app