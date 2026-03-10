import json
import time
from typing import Optional, Tuple

from .safety import normalize_text
from ..db import get_db


# ===== キャッシュ =====
_FAQ_CACHE: Optional[Tuple[dict, dict, dict]] = None
_FAQ_CACHE_AT: float = 0.0
_FAQ_CACHE_TTL_SEC: int = 10  # 10秒ごとにDB再読込


# 広すぎて誤ヒットしやすい語
# 一致しても弱く加点する
BROAD_WORDS = {
    "どこ",
    "場所",
    "制度",
    "方法",
    "いつ",
    "何",
    "なに",
}

MIN_TOKEN_LEN = 2
MIN_MATCH_SCORE = 4.0

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
    クリアだけでなく再読込まで行う（次のリクエストを待たずに最新化するため）
    """
    global _FAQ_CACHE, _FAQ_CACHE_AT
    _FAQ_CACHE = None
    _FAQ_CACHE_AT = 0.0
    _load_faq_from_db(force=True)


def _score_token_hit(token: str) -> float:
    """
    1つの語が一致した時の加点
    - 広すぎる語は弱く加点
    - それ以外は通常加点
    """
    if token in BROAD_WORDS:
        return 1.0
    return 3.0


def _calc_match_score(user_text: str, key: str, synonyms: list[str], priority: int) -> float:
    """
    FAQ候補1件ごとのスコアを計算する
    """
    score = 0.0
    hit_count = 0

    key_norm = normalize_text(key)
    if key_norm and len(key_norm) >= MIN_TOKEN_LEN and key_norm in user_text:
        # key一致は synonym より強くする
        if key_norm in BROAD_WORDS:
            score += 2.0
        else:
            score += 5.0
        hit_count += 1

    for syn in synonyms:
        syn_norm = normalize_text(syn)
        if not syn_norm or len(syn_norm) < MIN_TOKEN_LEN:
            continue
        if syn_norm in user_text:
            score += _score_token_hit(syn_norm)
            hit_count += 1

    # ヒットが0件なら即座に0を返す（priorityだけで通過しないように）
    if hit_count == 0:
        return 0.0

    # 2個以上ヒットしたら少し加点
    if hit_count >= 2:
        score += 1.5

    # priority は少しだけ加点
    score += float(priority) * 0.5

    # 同点対策として key の長さを少しだけ使う
    score += len(key_norm) * 0.05

    return score


def match_faq(text: str) -> str | None:
    """
    - DBからFAQを読み込む（キャッシュあり）
    - key / 同義語の一致をスコア化して判定する
    - 一番スコアの高いFAQを返す
    - スコアが低すぎる場合は FAQなし とする
    """
    t = normalize_text(text)
    if not t:
        return None

    faq, faq_synonyms, faq_priority = _load_faq_from_db()

    best_key = None
    best_score = 0.0

    for key in faq.keys():
        score = _calc_match_score(
            user_text=t,
            key=key,
            synonyms=faq_synonyms.get(key, []),
            priority=faq_priority.get(key, 1),
        )

        if score > best_score:
            best_score = score
            best_key = key

    if best_key is None:
        return None

    # 弱い一致しかない場合は FAQ 不一致にする
    if best_score < MIN_MATCH_SCORE:
        return None

    return faq.get(best_key)