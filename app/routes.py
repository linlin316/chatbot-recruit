from flask import Blueprint, render_template, request, jsonify, current_app
from . import limiter
from .services.chat_service import handle_chat

bp = Blueprint("main", __name__)

@bp.get("/")
def index():
    return render_template("index.html")

@bp.post("/chat")
@limiter.limit(lambda: current_app.config["CHAT_LIMIT"])
def chat_api():
    data = request.get_json(silent=True) or {}
    user_text = (data.get("message") or "").strip()

    result = handle_chat(user_text)

    print(f"[CHAT] source={result.get('source')}")

    return jsonify(result), 200