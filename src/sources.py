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
    # --- Skills ---
    {
        "id": "skillsmp_new",
        "tool": "Skills",
        "label": "SkillsMP 新着スキル",
        "url": "https://skillsmp.com",
        "rss": "https://skillsmp.com/rss/new.xml",
    },
    # --- コミュニティ / メディア ---
    {
        "id": "medium_claude_skills",
        "tool": "Skills",
        "label": "Medium - Claude Skills",
        "url": "https://medium.com/tag/claude-skills",
        "rss": "https://medium.com/feed/tag/claude-skills",
    },
    {
        "id": "devto_claudeskills",
        "tool": "Skills",
        "label": "DEV.to - claudeskills",
        "url": "https://dev.to/t/claudeskills",
        "rss": "https://dev.to/feed/tag/claudeskills",
    },
    {
        "id": "reddit_claudeai",
        "tool": "Claude",
        "label": "Reddit r/ClaudeAI",
        "url": "https://www.reddit.com/r/ClaudeAI/",
        "rss": "https://www.reddit.com/r/ClaudeAI/top/.rss?t=day",
    },
    {
        "id": "reddit_openai",
        "tool": "Codex",
        "label": "Reddit r/OpenAI",
        "url": "https://www.reddit.com/r/OpenAI/",
        "rss": "https://www.reddit.com/r/OpenAI/top/.rss?t=day",
    },
]

# ========================================
# Google News RSS（キーワード別）
# ========================================
GOOGLE_NEWS_KEYWORDS = [
    {"keyword": "Claude AI Anthropic",  "tool": "Claude",    "label": "Google News - Claude"},
    {"keyword": "Claude Code",          "tool": "Claude Code","label": "Google News - Claude Code"},
    {"keyword": "Gemini Google AI",     "tool": "Gemini",    "label": "Google News - Gemini"},
    {"keyword": "OpenAI Codex",         "tool": "Codex",     "label": "Google News - Codex"},
    {"keyword": "OpenClaw AI agent",    "tool": "OpenClaw",  "label": "Google News - OpenClaw"},
    {"keyword": "Claude Skills SKILL.md","tool": "Skills",   "label": "Google News - Skills"},
]

def google_news_rss_url(keyword: str) -> str:
    import urllib.parse
    q = urllib.parse.quote(keyword)
    return f"https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"

# ========================================
# GitHub API 監視対象
# ========================================
GITHUB_REPOS = [
    {
        "id": "openclaw_releases",
        "tool": "OpenClaw",
        "label": "OpenClaw GitHub Releases",
        "owner": "openclaw",
        "repo": "openclaw",
        "type": "releases",
    },
    {
        "id": "openai_codex_releases",
        "tool": "Codex",
        "label": "openai/codex GitHub Releases",
        "owner": "openai",
        "repo": "codex",
        "type": "releases",
    },
    {
        "id": "anthropic_skills_commits",
        "tool": "Skills",
        "label": "anthropics/skills 新コミット",
        "owner": "anthropics",
        "repo": "skills",
        "type": "commits",
    },
    {
        "id": "awesome_claude_skills_commits",
        "tool": "Skills",
        "label": "awesome-claude-skills 更新",
        "owner": "travisvn",
        "repo": "awesome-claude-skills",
        "type": "commits",
    },
]

# GitHub Search API: 新着 SKILL.md リポジトリ
GITHUB_SKILL_SEARCH_QUERIES = [
    "filename:SKILL.md",           # 新着スキルファイル
    "topic:claude-skills",         # Claude Skills タグ
    "topic:claude-code-skills",    # Claude Code Skills タグ
]

# ========================================
# HackerNews Algolia API キーワード
# ========================================
HACKERNEWS_KEYWORDS = [
    {"query": "Claude Code",   "tool": "Claude Code", "label": "HN - Claude Code"},
    {"query": "Anthropic",     "tool": "Claude",      "label": "HN - Anthropic"},
    {"query": "OpenClaw",      "tool": "OpenClaw",    "label": "HN - OpenClaw"},
    {"query": "Codex OpenAI",  "tool": "Codex",       "label": "HN - Codex"},
    {"query": "Gemini Google", "tool": "Gemini",      "label": "HN - Gemini"},
    {"query": "SKILL.md agent","tool": "Skills",      "label": "HN - Skills"},
]

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
