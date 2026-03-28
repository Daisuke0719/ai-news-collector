"""
重複チェックモジュール
送信済み記事IDをJSONファイルで管理する
"""

import json
import os
import hashlib
from datetime import datetime, timedelta

DEDUP_FILE = os.path.join(os.path.dirname(__file__), "../data/sent_ids.json")
# 30日以上前のIDは自動削除（ファイル肥大化防止）
RETENTION_DAYS = 30


def _load() -> dict:
    if not os.path.exists(DEDUP_FILE):
        return {}
    try:
        with open(DEDUP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict):
    os.makedirs(os.path.dirname(DEDUP_FILE), exist_ok=True)
    with open(DEDUP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_id(url: str, title: str = "") -> str:
    """URLとタイトルからユニークIDを生成"""
    raw = f"{url}|{title}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def is_seen(article_id: str) -> bool:
    """既に送信済みかチェック"""
    data = _load()
    return article_id in data


def mark_seen(article_id: str):
    """送信済みとしてマーク"""
    data = _load()
    data[article_id] = datetime.utcnow().isoformat()
    # 古いエントリを削除
    cutoff = (datetime.utcnow() - timedelta(days=RETENTION_DAYS)).isoformat()
    data = {k: v for k, v in data.items() if v >= cutoff}
    _save(data)


def filter_new(articles: list) -> list:
    """未送信の記事だけ返す"""
    return [a for a in articles if not is_seen(a["id"])]


def mark_all_seen(articles: list):
    """記事リストをまとめて送信済みにする"""
    for a in articles:
        mark_seen(a["id"])
