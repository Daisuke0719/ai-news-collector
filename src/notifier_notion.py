"""
Notion DB 書き込みモジュール
"""

import os
import re
import requests
from datetime import datetime

NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")
NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_BLOCKS_URL = "https://api.notion.com/v1/blocks"
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

    # 日付フォーマット（ISO 8601形式のみ許可）
    date_prop = None
    if published and re.match(r"\d{4}-\d{2}-\d{2}", published):
        date_prop = {"start": published[:10]}

    return {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "タイトル": {
                "title": [{"text": {"content": article.get("title", "")[:2000]}}]
            },
            "ツール": {
                "select": {"name": tool}
            },
            "重要度": {
                "select": {"name": importance}
            },
            "日付": {
                "date": date_prop
            },
            "URL": {
                "url": article.get("url") or None
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


def _append_translation_blocks(page_id: str, text: str):
    """Notionページの本文に全文翻訳ブロックを追加"""
    # Notion APIは1ブロックあたり2000文字制限
    BLOCK_CHAR_LIMIT = 2000
    children = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "全文翻訳"}}]
            },
        }
    ]

    # テキストを2000文字ごとにチャンク分割
    for i in range(0, len(text), BLOCK_CHAR_LIMIT):
        chunk = text[i:i + BLOCK_CHAR_LIMIT]
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": chunk}}]
            },
        })

    # Notion Blocks APIは1回のリクエストで最大100ブロック
    for i in range(0, len(children), 100):
        batch = children[i:i + 100]
        try:
            resp = requests.patch(
                f"{NOTION_BLOCKS_URL}/{page_id}/children",
                headers=HEADERS,
                json={"children": batch},
                timeout=30,
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"[Notion Blocks ERROR] page={page_id[:8]}...: {e}")


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
            page_id = resp.json().get("id", "")

            # NotionページURLを記事に付与（LINE通知で使用）
            if page_id:
                clean_id = page_id.replace("-", "")
                article["notion_url"] = f"https://www.notion.so/{clean_id}"

            # 全文翻訳があればページ本文に追加
            full_translation = article.get("full_translation", "")
            if full_translation and page_id:
                _append_translation_blocks(page_id, full_translation)

            success += 1
        except requests.exceptions.HTTPError as e:
            body = e.response.text[:200] if e.response is not None else ""
            print(f"[Notion ERROR] {article.get('title', '')[:50]}: {e}\n  Detail: {body}")
            errors += 1
        except Exception as e:
            print(f"[Notion ERROR] {article.get('title', '')[:50]}: {e}")
            errors += 1

    print(f"[Notion] ✅ 保存完了: {success}件成功 / {errors}件失敗")
