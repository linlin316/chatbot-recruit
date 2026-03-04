import json
import time
from typing import Optional, Tuple

from .safety import normalize_text
from ..db import get_db


# ===== キャッシュ =====
_FAQ_CACHE: Optional[Tuple[dict, dict, dict]] = None
_FAQ_CACHE_AT: float = 0.0
_FAQ_CACHE_TTL_SEC: int = 10  # 10秒ごとにDB再読込


def _load_faq_from_db(force: bool = False) -> tuple[dict, dict, dict]:
    """
    DBからFAQデータを読み込んで3つの辞書を返す（キャッシュあり）
    戻り値: (FAQ, FAQ_SYNONYMS, FAQ_PRIORITY)
    force=True のときはキャッシュを無視して強制再読込
    """
    global _FAQ_CACHE, _FAQ_CACHE_AT

    now = time.time()
    if (not force) and _FAQ_CACHE is not None and (now - _FAQ_CACHE_AT) < _FAQ_CACHE_TTL_SEC:
        return _FAQ_CACHE

    faq = {}
    synonyms = {}
    priority = {}

    conn = get_db()

    try:
        rows = conn.execute('SELECT "key", synonyms, answer, priority FROM faq').fetchall()
        for row in rows:
            k = row["key"]
            faq[k] = row["answer"]
            priority[k] = int(row["priority"] or 1)
            raw = row["synonyms"]
            if not raw:
                synonyms[k] = []
                continue
            try:
                v = json.loads(raw)
                synonyms[k] = v if isinstance(v, list) else []
            except Exception:
                # データが壊れていても落とさない
                synonyms[k] = []
    finally:
        conn.close()

    _FAQ_CACHE = (faq, synonyms, priority)
    _FAQ_CACHE_AT = now
    return _FAQ_CACHE


def reload_faq_cache() -> None:
    """
    FAQ追加・編集・削除後にキャッシュを即時クリアし、DBから再読込する。
    ※ クリアだけでなく再読込まで行う（次のリクエストを待たずに最新化するため）
    将来管理画面を作ったときにここを呼ぶ
    例: from .faq import reload_faq_cache; reload_faq_cache()
    """
    global _FAQ_CACHE, _FAQ_CACHE_AT
    _FAQ_CACHE = None
    _FAQ_CACHE_AT = 0.0
    _load_faq_from_db(force=True)


def match_faq(text: str) -> str | None:
    """
    - DBからFAQを読み込む（キャッシュあり）
    - 部分一致 + 同義語でマッチング
    - 複数ヒットしたら priority で一番良いものを返す
    """
    t = normalize_text(text)
    if not t:
        return None

    faq, faq_synonyms, faq_priority = _load_faq_from_db()

    best_key = None
    best_score = 0.0
    MIN_TOKEN_LEN = 2  # 2文字未満は誤ヒットしやすいので除外

    for key in faq.keys():
        key_norm = normalize_text(key)
        if len(key_norm) < MIN_TOKEN_LEN:
            continue

        # キー自体の部分一致
        hit = key_norm in t

        # 同義語で探す
        if not hit:
            for syn in faq_synonyms.get(key, []):
                syn_norm = normalize_text(syn)
                if len(syn_norm) < MIN_TOKEN_LEN:
                    continue
                if syn_norm in t:
                    hit = True
                    break

        if not hit:
            continue

        # スコア計算（優先度 + キー長で同点対策）
        score = float(faq_priority.get(key, 1))
        score += len(key) * 0.1

        if score > best_score:
            best_score = score
            best_key = key

    return faq.get(best_key) if best_key else None