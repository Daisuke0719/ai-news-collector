"""
Gemini API を使って記事を日本語要約するモジュール
"""

import os
import json
import time
import requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
MODEL = "gemini-2.5-flash"
# MAX_TOKENS = 500
BATCH_SIZE = 3  # 1回のAPI呼び出しでまとめて要約する記事数（全文入力のため小さめ）


SYSTEM_PROMPT = """あなたはAI技術情報のキュレーターです。
与えられた英語の記事タイトルと本文を、日本語で要約してください。

【ルール】
- 記事のポイントを漏らさず、しっかりとまとめる
  - 何が発表・変更されたか
  - どんな影響があるか、誰が対象か
  - 技術的な詳細や背景
- 読んだ人が元記事を読まなくても要点を把握できるレベルにする
- 短くまとめることより、ポイントを漏らさないことを優先する
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
        # full_content優先、なければraw_summaryを使用（制限なし）
        content = article.get("full_content") or article.get("raw_summary", "")
        items_text += f"""
--- 記事 {idx} ---
ツール: {article['tool']}
タイトル: {article['title']}
本文: {content}
URL: {article['url']}
"""

    user_message = f"以下の記事{len(batch)}件を要約してください:\n{items_text}"

    try:
        url = f"{API_URL}/{MODEL}:generateContent?key={GEMINI_API_KEY}"
        resp = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "systemInstruction": {
                    "parts": [{"text": SYSTEM_PROMPT}]
                },
                "contents": [
                    {"role": "user", "parts": [{"text": user_message}]}
                ],
                "generationConfig": {
                    # "maxOutputTokens": MAX_TOKENS * len(batch),
                    "temperature": 0,
                    "responseMimeType": "application/json",
                },
            },
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

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
        a["summary"] = article.get("raw_summary", article["title"])
        a["importance"] = "中"
        results.append(a)
    return results


# ========================================
# 全文翻訳機能
# ========================================

TRANSLATE_PROMPT = """以下の英語記事を日本語に全文翻訳してください。

【ルール】
- 技術用語（Claude Code, API, LLM, GitHub等）は英語のまま残す
- 段落構造を維持する
- マークダウン記法はそのまま保持する
- 翻訳のみを返す（説明やコメントは不要）"""


def translate_articles(articles: list) -> list:
    """重要度「高」「中」の記事に全文翻訳を追加"""
    if not articles:
        return []

    translated = 0
    for article in articles:
        importance = article.get("importance", "中")
        if importance == "低":
            article["full_translation"] = ""
            continue

        content = article.get("full_content") or article.get("raw_summary", "")
        if not content:
            article["full_translation"] = ""
            continue

        article["full_translation"] = _translate_single(content)
        if article["full_translation"]:
            translated += 1
        time.sleep(1)  # レート制限対策

    print(f"[Translate] {translated}件の記事を翻訳完了")
    return articles


def _translate_single(content: str) -> str:
    """1記事分の全文翻訳"""
    try:
        url = f"{API_URL}/{MODEL}:generateContent?key={GEMINI_API_KEY}"
        resp = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "systemInstruction": {
                    "parts": [{"text": TRANSLATE_PROMPT}]
                },
                "contents": [
                    {"role": "user", "parts": [{"text": content}]}
                ],
                "generationConfig": {
                    "temperature": 0,
                },
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[Translate ERROR] {e}")
        return ""
