"""
Claude API を使って記事を日本語要約するモジュール
"""

import os
import json
import time
import requests

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 300
BATCH_SIZE = 5  # 1回のAPI呼び出しでまとめて要約する記事数


SYSTEM_PROMPT = """あなたはAI技術情報のキュレーターです。
与えられた英語の記事タイトルと要約を、日本語で簡潔に要約してください。

【ルール】
- 2〜3文で簡潔にまとめる
- 技術的な固有名詞（Claude Code、SKILL.md等）はそのまま使う
- 重要度（高/中/低）を判定する
  - 高: 新モデルリリース、重大機能追加、セキュリティ問題
  - 中: 機能改善、新スキル、アップデート
  - 低: バグ修正、マイナー更新、コミュニティ話題
- JSONで返す（マークダウンコードブロック不要）

【出力形式（JSON配列）】
[
  {"index": 0, "summary": "日本語要約テキスト", "importance": "高|中|低"},
  ...
]"""


def summarize_batch(articles: list) -> list:
    """記事リストをバッチで要約（インデックス順を保持）"""
    if not articles:
        return []

    # バッチ処理
    results = [None] * len(articles)
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        batch_results = _summarize_single_batch(batch, offset=i)
        for j, r in enumerate(batch_results):
            results[i + j] = r
        if i + BATCH_SIZE < len(articles):
            time.sleep(1)  # レート制限対策

    return results


def _summarize_single_batch(batch: list, offset: int = 0) -> list:
    """1バッチ分を要約"""
    # プロンプト組み立て
    items_text = ""
    for idx, article in enumerate(batch):
        items_text += f"""
--- 記事 {idx} ---
ツール: {article['tool']}
タイトル: {article['title']}
概要: {article.get('raw_summary', '')[:300]}
URL: {article['url']}
"""

    user_message = f"以下の記事{len(batch)}件を要約してください:\n{items_text}"

    try:
        resp = requests.post(
            API_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": MAX_TOKENS * len(batch),
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_message}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()

        # JSON パース
        parsed = json.loads(text)
        results = []
        for item in parsed:
            idx = item.get("index", 0)
            if 0 <= idx < len(batch):
                article = batch[idx].copy()
                article["summary"] = item.get("summary", "")
                article["importance"] = item.get("importance", "中")
                results.append(article)
            
        # パース失敗時のフォールバック
        if len(results) != len(batch):
            results = _fallback_results(batch)
        return results

    except Exception as e:
        print(f"[Summarizer ERROR] {e}")
        return _fallback_results(batch)


def _fallback_results(batch: list) -> list:
    """要約失敗時のフォールバック"""
    results = []
    for article in batch:
        a = article.copy()
        a["summary"] = article.get("raw_summary", article["title"])[:200]
        a["importance"] = "中"
        results.append(a)
    return results
