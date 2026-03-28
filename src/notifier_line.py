"""
LINE Messaging API 通知モジュール
"""

import os
import requests
from datetime import datetime

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.environ.get("LINE_USER_ID", "")
LINE_API_URL = "https://api.line.me/v2/bot/message/push"

MAX_CHARS_PER_MESSAGE = 4900  # LINEのメッセージ上限（5000文字）
MAX_MESSAGES_PER_PUSH = 5     # 1回のpushで送れるメッセージ数上限


def _importance_icon(importance: str) -> str:
    return {"高": "🔴", "中": "🟡", "低": "⚪"}.get(importance, "🟡")


def _build_article_message(article: dict) -> str:
    """記事1件をLINEメッセージ文字列に変換"""
    imp_icon = _importance_icon(article.get("importance", "中"))
    emoji = article.get("emoji", "📌")
    tool = article.get("tool", "その他")
    title = article.get("title", "")[:80]
    summary = article.get("summary", "") or ""
    url = article.get("url", "")
    notion_url = article.get("notion_url", "")

    lines = [
        f"{imp_icon}【{emoji} {tool}】{title}",
        "",
        summary,
        "",
        f"🔗 引用元: {url}",
    ]

    if notion_url:
        lines.append(f"📓 Notion全文: {notion_url}")

    text = "\n".join(lines)

    # メッセージ上限を超える場合は要約を切り詰め
    if len(text) > MAX_CHARS_PER_MESSAGE:
        overhead = len(text) - len(summary)
        max_summary = MAX_CHARS_PER_MESSAGE - overhead - 3
        summary = summary[:max_summary] + "..."
        lines[2] = summary
        text = "\n".join(lines)

    return text


def _push_messages(messages: list):
    """LINE push APIでメッセージリストを送信"""
    try:
        resp = requests.post(
            LINE_API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            },
            json={
                "to": LINE_USER_ID,
                "messages": messages,
            },
            timeout=15,
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        body = e.response.text[:200] if e.response is not None else ""
        print(f"[LINE ERROR] {e}\n  Detail: {body}")
    except Exception as e:
        print(f"[LINE ERROR] {e}")


def send_line(articles: list):
    """LINE に記事単位で通知する"""
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("[LINE] 環境変数未設定のためスキップ")
        return

    if not articles:
        print("[LINE] 新着記事なし。通知スキップ")
        return

    # 記事ごとにメッセージを生成
    text_messages = [{"type": "text", "text": _build_article_message(a)} for a in articles]

    # 5件ずつpushを分けて送信
    sent = 0
    for i in range(0, len(text_messages), MAX_MESSAGES_PER_PUSH):
        batch = text_messages[i:i + MAX_MESSAGES_PER_PUSH]
        _push_messages(batch)
        sent += len(batch)

    print(f"[LINE] ✅ 送信完了（{len(articles)}件、{(len(articles) - 1) // MAX_MESSAGES_PER_PUSH + 1}回push）")


def send_line_error(error_msg: str):
    """エラー通知"""
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        return
    try:
        requests.post(
            LINE_API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            },
            json={
                "to": LINE_USER_ID,
                "messages": [{"type": "text", "text": f"⚠️ AI情報収集エラー\n{error_msg}"}],
            },
            timeout=15,
        )
    except Exception:
        pass
