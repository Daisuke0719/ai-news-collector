"""
情報収集メインモジュール
RSS / Google News / GitHub API / HackerNews を収集する
"""

import os
import re
import time
import requests
import feedparser
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from typing import Optional

from sources import (
    RSS_FEEDS,
    GOOGLE_NEWS_KEYWORDS,
    GITHUB_REPOS,
    GITHUB_SKILL_SEARCH_QUERIES,
    HACKERNEWS_KEYWORDS,
    TOOL_EMOJI,
    google_news_rss_url,
)
from dedup import make_id

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
LOOKBACK_HOURS = int(os.environ.get("LOOKBACK_HOURS", "25"))  # 収集対象期間（時間）

HEADERS_GITHUB = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    HEADERS_GITHUB["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_recent(dt: Optional[datetime]) -> bool:
    """LOOKBACK_HOURS 以内かどうか判定"""
    if dt is None:
        return True  # 日付不明は含める
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= _utcnow() - timedelta(hours=LOOKBACK_HOURS)


class _HTMLTextExtractor(HTMLParser):
    """HTMLからテキストを抽出するパーサー"""
    # スクリプト・スタイル等の非表示タグ
    _SKIP_TAGS = {"script", "style", "noscript", "header", "footer", "nav"}

    def __init__(self):
        super().__init__()
        self._pieces: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs):
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
        if tag in ("p", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
            self._pieces.append("\n")

    def handle_endtag(self, tag: str):
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str):
        if self._skip_depth == 0:
            self._pieces.append(data)

    def get_text(self) -> str:
        text = "".join(self._pieces)
        # 連続空白・改行を整理
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def _html_to_text(html: str) -> str:
    """HTMLからプレーンテキストを抽出"""
    parser = _HTMLTextExtractor()
    try:
        parser.feed(html)
        return parser.get_text()
    except Exception:
        # フォールバック: 正規表現でタグ除去
        return re.sub(r"<[^>]+>", "", html).strip()


def _fetch_article_text(url: str) -> str:
    """記事URLから本文テキストを取得"""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AINewsCollector/1.0)"},
            timeout=15,
        )
        resp.raise_for_status()
        return _html_to_text(resp.text)
    except Exception as e:
        print(f"[Fetch ERROR] {url[:80]}: {e}")
        return ""


def _parse_feed_entry(entry, source: dict) -> dict:
    """feedparser エントリを共通形式に変換"""
    url = entry.get("link", "")
    title = entry.get("title", "(タイトルなし)")

    # 日時パース
    published = None
    for field in ("published_parsed", "updated_parsed"):
        tp = entry.get(field)
        if tp:
            try:
                published = datetime(*tp[:6], tzinfo=timezone.utc)
                break
            except Exception:
                pass

    # フルコンテンツ取得: content > summary > description の優先順
    full_html = ""
    if hasattr(entry, "content") and entry.content:
        full_html = entry.content[0].get("value", "")
    if not full_html:
        full_html = entry.get("summary", "") or entry.get("description", "")

    full_content = _html_to_text(full_html)
    # raw_summaryもフルコンテンツから生成（制限なし）
    raw_summary = full_content

    return {
        "id": make_id(url, title),
        "tool": source["tool"],
        "label": source["label"],
        "title": title,
        "url": url,
        "published": published.isoformat() if published else None,
        "raw_summary": raw_summary,
        "full_content": full_content,
        "emoji": TOOL_EMOJI.get(source["tool"], "📌"),
    }


# ========================================
# RSS 収集
# ========================================
def collect_rss() -> list:
    articles = []
    for source in RSS_FEEDS:
        try:
            feed = feedparser.parse(source["rss"])
            latest_only = source.get("latest_only", False)
            for entry in feed.entries:
                article = _parse_feed_entry(entry, source)
                # 日付フィルタ
                published = None
                for field in ("published_parsed", "updated_parsed"):
                    tp = entry.get(field)
                    if tp:
                        try:
                            published = datetime(*tp[:6], tzinfo=timezone.utc)
                            break
                        except Exception:
                            pass
                if _is_recent(published):
                    articles.append(article)
                    if latest_only:
                        break  # 最新1件のみ取得
            time.sleep(0.5)
        except Exception as e:
            print(f"[RSS ERROR] {source['id']}: {e}")
    return articles


# ========================================
# Google News RSS 収集
# ========================================
def collect_google_news() -> list:
    articles = []
    for kw_config in GOOGLE_NEWS_KEYWORDS:
        source = {
            "tool": kw_config["tool"],
            "label": kw_config["label"],
        }
        rss_url = google_news_rss_url(kw_config["keyword"])
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:5]:  # 上位5件
                article = _parse_feed_entry(entry, source)
                published = None
                for field in ("published_parsed", "updated_parsed"):
                    tp = entry.get(field)
                    if tp:
                        try:
                            published = datetime(*tp[:6], tzinfo=timezone.utc)
                            break
                        except Exception:
                            pass
                if _is_recent(published):
                    articles.append(article)
            time.sleep(0.5)
        except Exception as e:
            print(f"[Google News ERROR] {kw_config['keyword']}: {e}")
    return articles


# ========================================
# GitHub Releases / Commits 収集
# ========================================
def collect_github() -> list:
    articles = []
    for repo_config in GITHUB_REPOS:
        owner = repo_config["owner"]
        repo = repo_config["repo"]
        rtype = repo_config["type"]
        source = {
            "tool": repo_config["tool"],
            "label": repo_config["label"],
        }
        try:
            if rtype == "releases":
                url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=5"
                resp = requests.get(url, headers=HEADERS_GITHUB, timeout=10)
                resp.raise_for_status()
                for item in resp.json():
                    published_str = item.get("published_at") or item.get("created_at")
                    published = datetime.fromisoformat(published_str.replace("Z", "+00:00")) if published_str else None
                    if not _is_recent(published):
                        continue
                    body = item.get("body", "") or ""
                    articles.append({
                        "id": make_id(item.get("html_url", ""), item.get("name", "")),
                        "tool": source["tool"],
                        "label": source["label"],
                        "title": f"{repo} {item.get('tag_name', '')} - {item.get('name', '')}",
                        "url": item.get("html_url", ""),
                        "published": published.isoformat() if published else None,
                        "raw_summary": body,
                        "full_content": body,
                        "emoji": TOOL_EMOJI.get(source["tool"], "📌"),
                    })

            elif rtype == "commits":
                since = (_utcnow() - timedelta(hours=LOOKBACK_HOURS)).isoformat()
                path_filter = repo_config.get("path", "")
                url = f"https://api.github.com/repos/{owner}/{repo}/commits?since={since}&per_page=10"
                if path_filter:
                    url += f"&path={path_filter}"
                resp = requests.get(url, headers=HEADERS_GITHUB, timeout=10)
                resp.raise_for_status()
                for item in resp.json():
                    commit = item.get("commit", {})
                    message = commit.get("message", "").split("\n")[0][:200]
                    html_url = item.get("html_url", "")
                    published_str = (commit.get("author") or {}).get("date")
                    published = datetime.fromisoformat(published_str.replace("Z", "+00:00")) if published_str else None
                    full_message = commit.get("message", "")
                    articles.append({
                        "id": make_id(html_url, message),
                        "tool": source["tool"],
                        "label": source["label"],
                        "title": f"[{owner}/{repo}] {message}",
                        "url": html_url,
                        "published": published.isoformat() if published else None,
                        "raw_summary": full_message,
                        "full_content": full_message,
                        "emoji": TOOL_EMOJI.get(source["tool"], "📌"),
                    })
            time.sleep(0.5)
        except Exception as e:
            print(f"[GitHub ERROR] {repo_config['id']}: {e}")

    # Skills 新着検索
    articles += _collect_github_skill_search()
    return articles


def _collect_github_skill_search() -> list:
    """GitHub Search APIでSKILL.md新着リポジトリを取得"""
    articles = []
    source = {"tool": "Skills", "label": "GitHub新着スキル"}
    since_date = (_utcnow() - timedelta(hours=LOOKBACK_HOURS)).strftime("%Y-%m-%d")
    for query_base in GITHUB_SKILL_SEARCH_QUERIES:
        query = f"{query_base} pushed:>{since_date}"
        try:
            url = "https://api.github.com/search/repositories"
            resp = requests.get(
                url,
                headers=HEADERS_GITHUB,
                params={"q": query, "sort": "updated", "order": "desc", "per_page": 5},
                timeout=10,
            )
            resp.raise_for_status()
            for item in resp.json().get("items", []):
                html_url = item.get("html_url", "")
                name = item.get("full_name", "")
                description = item.get("description", "") or ""
                stars = item.get("stargazers_count", 0)
                articles.append({
                    "id": make_id(html_url, name),
                    "tool": "Skills",
                    "label": f"GitHub Skills検索: {query_base}",
                    "title": f"⭐{stars} {name} - {description[:100]}",
                    "url": html_url,
                    "published": None,
                    "raw_summary": description,
                    "full_content": description,
                    "emoji": "⚡",
                })
            time.sleep(1.0)  # GitHub Search API レート制限対策
        except Exception as e:
            print(f"[GitHub Search ERROR] {query_base}: {e}")
    return articles


# ========================================
# HackerNews Algolia API 収集
# ========================================
def collect_hackernews() -> list:
    articles = []
    since_ts = int((_utcnow() - timedelta(hours=LOOKBACK_HOURS)).timestamp())
    for kw_config in HACKERNEWS_KEYWORDS:
        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search_by_date",
                params={
                    "query": kw_config["query"],
                    "numericFilters": f"created_at_i>{since_ts}",
                    "tags": "story",
                    "hitsPerPage": 5,
                },
                timeout=10,
            )
            resp.raise_for_status()
            for hit in resp.json().get("hits", []):
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                title = hit.get("title", "")
                hn_meta = f"HN Score: {hit.get('points', 0)} | Comments: {hit.get('num_comments', 0)}"
                # 元記事URLから本文を取得
                full_content = ""
                if hit.get("url"):
                    full_content = _fetch_article_text(hit["url"])
                articles.append({
                    "id": make_id(url, title),
                    "tool": kw_config["tool"],
                    "label": kw_config["label"],
                    "title": title,
                    "url": url,
                    "published": None,
                    "raw_summary": full_content if full_content else hn_meta,
                    "full_content": full_content if full_content else hn_meta,
                    "emoji": TOOL_EMOJI.get(kw_config["tool"], "📌"),
                })
            time.sleep(0.3)
        except Exception as e:
            print(f"[HN ERROR] {kw_config['query']}: {e}")
    return articles


# ========================================
# メイン収集関数
# ========================================
def collect_all() -> list:
    print("📡 RSS収集中...")
    rss = collect_rss()
    print(f"  → {len(rss)}件")

    print("🗞️ Google News収集中...")
    gnews = collect_google_news()
    print(f"  → {len(gnews)}件")

    print("🐙 GitHub収集中...")
    github = collect_github()
    print(f"  → {len(github)}件")

    print("🔶 HackerNews収集中...")
    hn = collect_hackernews()
    print(f"  → {len(hn)}件")

    all_articles = rss + gnews + github + hn
    print(f"\n✅ 合計収集: {len(all_articles)}件")
    return all_articles
