"""
Notion DB 書き込みモジュール
"""

import os
import requests
from datetime import datetime

NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")
NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

# 重要度 → Notionのセレクトカラー
IMPORTANCE_COLOR = {
    "高": "red",
    "中": "yellow",
    "低": "gray",
}

# ツール → Notionのセレクトカラー
TOOL_COLOR = {
    "Claude":      "purple",
    "Claude Code": "pink",
    "Gemini":      "green",
    "Codex":       "blue",
    "OpenClaw":    "orange",
    "Skills":      "yellow",
}


def _build_page_payload(article: dict) -> dict:
    """記事1件のNotionページPayloadを生成"""
    tool = article.get("tool", "その他")
    importance = article.get("importance", "中")
    published = article.get("published")

    # 日付フォーマット
    date_prop = {}
    if published:
        date_str = published[:10]  # YYYY-MM-DD
        date_prop = {"start": date_str}

    return {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "タイトル": {
                "title": [{"text": {"content": article.get("title", "")[:2000]}}]
            },
            "ツール": {
                "select": {
                    "name": tool,
                    "color": TOOL_COLOR.get(tool, "default"),
                }
            },
            "重要度": {
                "select": {
                    "name": importance,
                    "color": IMPORTANCE_COLOR.get(importance, "default"),
                }
            },
            "日付": {
                "date": date_prop if date_prop else None
            },
            "URL": {
                "url": article.get("url", "")
            },
            "ソース": {
                "rich_text": [{"text": {"content": article.get("label", "")[:200]}}]
            },
            "要約": {
                "rich_text": [{"text": {"content": article.get("summary", "")[:2000]}}]
            },
            "収集日": {
                "date": {"start": datetime.now().strftime("%Y-%m-%d")}
            },
        },
    }


def save_to_notion(articles: list):
    """記事リストをNotion DBに保存"""
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        print("[Notion] 環境変数未設定のためスキップ")
        return

    if not articles:
        print("[Notion] 保存する記事なし")
        return

    success = 0
    errors = 0
    for article in articles:
        try:
            payload = _build_page_payload(article)
            resp = requests.post(
                NOTION_API_URL,
                headers=HEADERS,
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
            success += 1
        except Exception as e:
            print(f"[Notion ERROR] {article.get('title', '')[:50]}: {e}")
            errors += 1

    print(f"[Notion] ✅ 保存完了: {success}件成功 / {errors}件失敗")
