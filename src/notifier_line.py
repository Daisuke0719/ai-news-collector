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


def _build_message_blocks(articles: list, date_str: str) -> list:
    """記事リストをLINEメッセージブロックに変換"""
    # ツール別にグループ化
    grouped = {}
    for a in articles:
        tool = a.get("tool", "その他")
        grouped.setdefault(tool, []).append(a)

    # ヘッダー
    header = f"🤖 AI最新情報 - {date_str}\n合計 {len(articles)} 件\n{'━'*20}"
    blocks = [header]
    current = ""

    for tool, tool_articles in grouped.items():
        emoji = tool_articles[0].get("emoji", "📌")
        section = f"\n\n【{emoji} {tool}】"
        for a in tool_articles:
            imp_icon = _importance_icon(a.get("importance", "中"))
            entry = (
                f"\n{imp_icon} {a['title']}\n"
                f"🔗 {a['url']}\n"
                f"📝 {a.get('summary', '')}\n"
            )
            section += entry

        # メッセージサイズ管理
        if len(current) + len(section) > MAX_CHARS_PER_MESSAGE:
            blocks.append(current)
            current = section
        else:
            current += section

    if current:
        blocks.append(current)

    return blocks


def send_line(articles: list):
    """LINE にまとめて通知する"""
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("[LINE] 環境変数未設定のためスキップ")
        return

    if not articles:
        print("[LINE] 新着記事なし。通知スキップ")
        return

    date_str = datetime.now().strftime("%Y/%m/%d")
    blocks = _build_message_blocks(articles, date_str)

    # LINE は1回のpushで最大5メッセージ
    messages = [{"type": "text", "text": b} for b in blocks[:MAX_MESSAGES_PER_PUSH]]

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
        print(f"[LINE] ✅ 送信完了（{len(articles)}件、{len(messages)}メッセージ）")
    except Exception as e:
        print(f"[LINE ERROR] {e}")


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
