"""
収集ソース定義
AI最新情報収集ツール - sources.py
"""

# ========================================
# RSS フィード一覧
# ========================================
RSS_FEEDS = [
    # --- Claude / Anthropic ---
    {
        "id": "anthropic_news",
        "tool": "Claude",
        "label": "Anthropic公式ニュース",
        "url": "https://www.anthropic.com/news",
        "rss": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
    },
    {
        "id": "anthropic_engineering",
        "tool": "Claude",
        "label": "Anthropic Engineering Blog",
        "url": "https://www.anthropic.com/engineering",
        "rss": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
    },
    {
        "id": "anthropic_research",
        "tool": "Claude",
        "label": "Anthropic Research Blog",
        "url": "https://www.anthropic.com/research",
        "rss": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
    },
    {
        "id": "claude_code_changelog",
        "tool": "Claude Code",
        "label": "Claude Code Changelog",
        "url": "https://docs.anthropic.com/en/release-notes/claude-code",
        "rss": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_changelog_claude_code.xml",
        "latest_only": True,  # 最新バージョンのみ通知
    },
    {
        "id": "claude_blog",
        "tool": "Claude",
        "label": "Claude Blog",
        "url": "https://claude.com/blog",
        "rss": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_claude.xml",
    },
    # --- Gemini / Google DeepMind ---
    {
        "id": "deepmind_blog",
        "tool": "Gemini",
        "label": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/",
        "rss": "https://deepmind.google/blog/rss.xml",
    },
    {
        "id": "google_gemini_blog",
        "tool": "Gemini",
        "label": "Google Blog (Gemini)",
        "url": "https://blog.google/products-and-platforms/products/gemini/",
        "rss": "https://blog.google/products-and-platforms/products/gemini/rss/",
    },
    {
        "id": "google_research_blog",
        "tool": "Gemini",
        "label": "Google Research Blog",
        "url": "https://research.google/blog/",
        "rss": "https://feeds.feedburner.com/blogspot/gJZg",
    },
    # --- Codex / OpenAI ---
    {
        "id": "openai_blog",
        "tool": "Codex",
        "label": "OpenAI Blog",
        "url": "https://openai.com/blog",
        "rss": "https://openai.com/blog/rss.xml",
    },
    {
        "id": "openai_developer_changelog",
        "tool": "Codex",
        "label": "OpenAI Developer Changelog",
        "url": "https://developers.openai.com/changelog/",
        "rss": "https://developers.openai.com/changelog/rss.xml",
    },
    {
        "id": "codex_changelog",
        "tool": "Codex",
        "label": "Codex Changelog",
        "url": "https://developers.openai.com/codex/changelog",
        "rss": "https://developers.openai.com/codex/changelog/rss.xml",
    },
    # --- OpenClaw ---
    {
        "id": "openclaw_blog",
        "tool": "OpenClaw",
        "label": "OpenClaw Blog",
        "url": "https://openclaw.ai/blog",
        "rss": "https://openclaw.ai/blog/rss.xml",
    },
]

# ========================================
# Google News RSS（キーワード別）
# ========================================
GOOGLE_NEWS_KEYWORDS = []

def google_news_rss_url(keyword: str) -> str:
    import urllib.parse
    q = urllib.parse.quote(keyword)
    return f"https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"

# ========================================
# GitHub API 監視対象
# ========================================
GITHUB_REPOS = [
    {
        "id": "anthropic_skills_commits",
        "tool": "Skills",
        "label": "Anthropic公式Skills更新",
        "owner": "anthropics",
        "repo": "skills",
        "type": "commits",
        "path": "skills",  # skills/ ディレクトリの変更のみ追跡
    },
]

# GitHub Search API: 新着リポジトリ検索
GITHUB_SKILL_SEARCH_QUERIES = []

# ========================================
# HackerNews Algolia API キーワード
# ========================================
HACKERNEWS_KEYWORDS = []

# ========================================
# ツール別の色・絵文字マッピング（LINE通知用）
# ========================================
TOOL_EMOJI = {
    "Claude":      "🟣",
    "Claude Code": "💜",
    "Gemini":      "🟢",
    "Codex":       "🔵",
    "OpenClaw":    "🦞",
    "Skills":      "⚡",
}
