# 🤖 AI最新情報収集ツール

Claude / Claude Code / Gemini / Codex / OpenClaw の最新情報を毎日自動収集し、
**LINE通知 + Notion DB保存** するツールです。

## 📁 ファイル構成

```
.github/
  workflows/
    daily-collect.yml       # GitHub Actions（毎日10時JST実行）
src/
  main.py                   # エントリポイント
  sources.py                # 収集ソース定義
  collect.py                # RSS/GitHub/HN収集
  summarizer.py             # Claude API 日本語要約
  notifier_line.py          # LINE通知
  notifier_notion.py        # Notion DB保存
  dedup.py                  # 重複チェック
data/
  sent_ids.json             # 送信済み記事ID管理
requirements.txt
```

## 🔐 GitHub Secrets の設定

リポジトリの `Settings > Secrets and variables > Actions` に以下を登録：

| Secret名 | 取得方法 |
|----------|---------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| `LINE_CHANNEL_ACCESS_TOKEN` | [LINE Developers](https://developers.line.biz/) でMessaging APIチャンネル作成 |
| `LINE_USER_ID` | LINE Developersコンソール or Webhookで取得 |
| `NOTION_API_KEY` | [notion.so/my-integrations](https://www.notion.so/my-integrations) |
| `NOTION_DATABASE_ID` | NotionDBのURL末尾のID |

## 📓 Notion DB の準備

Notionで以下のプロパティを持つデータベースを作成：

| プロパティ名 | 型 |
|------------|-----|
| タイトル | タイトル |
| ツール | セレクト |
| 重要度 | セレクト |
| 日付 | 日付 |
| URL | URL |
| ソース | テキスト |
| 要約 | テキスト |
| 収集日 | 日付 |

作成後、IntegrationをDBに接続（Share → Invite）。

## 📲 LINE Messaging API の準備

1. [LINE Developers](https://developers.line.biz/) でプロバイダー作成
2. Messaging API チャンネル作成
3. チャンネルアクセストークン（長期）を発行 → `LINE_CHANNEL_ACCESS_TOKEN`
4. 自分のLINEアカウントのUser ID取得 → `LINE_USER_ID`

## 🚀 実行

### 手動実行（GitHub Actions）
`Actions > AI News Collector (Daily) > Run workflow`

### ローカルテスト
```bash
pip install -r requirements.txt

# 環境変数をセット
export ANTHROPIC_API_KEY="sk-..."
export LINE_CHANNEL_ACCESS_TOKEN="..."
export LINE_USER_ID="U..."
export NOTION_API_KEY="secret_..."
export NOTION_DATABASE_ID="..."

cd src
python main.py
```

## 📡 収集ソース

### Claude / Claude Code
- Anthropic公式ニュース RSS
- Claude Code Changelog RSS  
- Anthropic Engineering Blog RSS
- Anthropic Research Blog RSS
- Claude Blog RSS
- Releasebot（リリースノート）

### Gemini / Google DeepMind
- Google DeepMind Blog RSS
- Google Blog (Gemini) RSS
- Google Research Blog RSS
- Gemini Latest News

### Codex / OpenAI
- OpenAI Blog RSS
- OpenAI Developer Changelog RSS
- Codex Changelog RSS（直接）
- openai/codex GitHub Releases

### OpenClaw
- openclaw/openclaw GitHub Releases
- OpenClaw Blog RSS

### Skills（横断）
- anthropics/skills GitHub 新コミット
- awesome-claude-skills 更新監視
- GitHub Search API（filename:SKILL.md 新着）
- SkillsMP 新着RSS
- Medium / DEV.to タグRSS

### 横断メディア
- Google News RSS（ツール別キーワード）
- HackerNews Algolia API
- Reddit r/ClaudeAI, r/OpenAI RSS
