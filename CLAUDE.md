# CLAUDE.md — AI最新情報収集ツール

Claude Codeがこのプロジェクトを自律的に運用・保守するための完全ガイド。
作業前に必ずこのファイルを読むこと。

---

## 🎯 プロジェクト概要

**目的**: Claude / Claude Code / Gemini / Codex / OpenClaw の最新情報を毎日自動収集し、日本語要約してLINE通知 + Notion DBに保存する。

**オーナー**: 保険代理店 × AI事業を運営する日本のユーザー（Daisuke）。通知は日本語で、技術的な固有名詞は英語のまま残すこと。

**実行環境**: GitHub Actions（毎日 JST 10:00 = UTC 01:00）

---

## 📁 ファイル構成と各ファイルの責務

```
ai-news-collector/
├── CLAUDE.md                          ← 今読んでいるこのファイル
├── README.md                          ← セットアップ手順（人間向け）
├── requirements.txt                   ← Python依存ライブラリ
├── data/
│   └── sent_ids.json                  ← 送信済み記事IDの永続化ストア
├── src/
│   ├── main.py                        ← エントリポイント。Step1〜7を順番に呼ぶだけ
│   ├── sources.py                     ← 収集ソースの設定ファイル（ここだけ編集で収集先を変更可）
│   ├── collect.py                     ← RSS/GoogleNews/GitHub/HackerNewsの収集ロジック
│   ├── summarizer.py                  ← Claude APIで日本語要約・重要度判定
│   ├── notifier_line.py               ← LINE Messaging API送信
│   ├── notifier_notion.py             ← Notion DB書き込み
│   └── dedup.py                       ← 重複チェック（MD5ハッシュ + JSONファイル管理）
└── .github/
    └── workflows/
        └── daily-collect.yml          ← GitHub Actionsスケジュール定義
```

---

## 🔄 データフロー（main.pyの処理順）

```
Step 1: collect_all()         → 全ソースから記事を収集（生データ + 全文テキスト）
Step 2: filter_new()          → sent_ids.json と照合して新着だけ抽出
Step 3: ツール別優先度ソート   → Claude Code > Claude > Codex > Gemini > OpenClaw > Skills
Step 4: summarize_batch()     → Gemini API で日本語要約 + 重要度（高/中/低）判定
Step 4.5: translate_articles() → 重要度「高」「中」の記事を全文日本語翻訳
Step 5: 重要度ソート           → 高 > 中 > 低
Step 6: save_to_notion()      → Notion DB に1件ずつ保存（全文翻訳はページ本文に追加、notion_urlを記事に付与）
Step 7: send_line()           → LINE に記事単位で通知（要約全文 + 引用元URL + Notion全文リンク）
       mark_all_seen()        → sent_ids.json に記録
```

---

## 📦 記事オブジェクトの共通形式

プロジェクト全体で以下のdict形式を使う。**この形式を崩さないこと。**

```python
{
    "id":               str,   # make_id(url, title) で生成したMD5ハッシュ（重複チェックキー）
    "tool":             str,   # "Claude" | "Claude Code" | "Gemini" | "Codex" | "OpenClaw" | "Skills"
    "label":            str,   # 収集元の表示名（例: "Anthropic公式ニュース"）
    "title":            str,   # 記事タイトル
    "url":              str,   # 元記事URL
    "published":        str,   # ISO形式の日時文字列 or None
    "raw_summary":      str,   # 収集時の生テキスト（制限なし）
    "full_content":     str,   # 記事の全文テキスト（RSS content / 記事ページ取得）
    "emoji":            str,   # TOOL_EMOJI から取得した絵文字
    # summarize_batch() 実行後に追加される:
    "summary":          str,   # Gemini APIが生成した日本語要約（ポイント網羅）
    "importance":       str,   # "高" | "中" | "低"
    # translate_articles() 実行後に追加される:
    "full_translation": str,   # 全文日本語訳（重要度「高」「中」のみ）
}
```

---

## ⚙️ 環境変数（GitHub Secrets）

| 変数名 | 用途 | 必須 |
|--------|------|------|
| `GEMINI_API_KEY` | Gemini API（要約生成・全文翻訳） | ✅ |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API | ✅ |
| `LINE_USER_ID` | LINE送信先ユーザーID | ✅ |
| `NOTION_API_KEY` | Notion Integration Token | ✅ |
| `NOTION_DATABASE_ID` | 保存先NotionデータベースID | ✅ |
| `GITHUB_TOKEN` | GitHub API（自動付与） | 自動 |
| `LOOKBACK_HOURS` | 収集対象の時間幅（デフォルト: 25） | ❌ |

環境変数が未設定の場合、LINE/Notionはスキップされるがエラーにはならない（graceful degradation）。
`GEMINI_API_KEY` のみ未設定でクラッシュする（summarizer.pyで `os.environ["GEMINI_API_KEY"]` と直接参照しているため）。

---

## 🛠️ よくある作業とその手順

### ① 収集ソースを追加する

**RSSフィードを追加する場合** → `src/sources.py` の `RSS_FEEDS` リストに追記する。

```python
# sources.py の RSS_FEEDS に追加
{
    "id":    "一意のID（snake_case）",
    "tool":  "Claude",  # TOOL_EMOJI のキーと一致させること
    "label": "表示名（日本語可）",
    "url":   "元サイトURL",
    "rss":   "RSSフィードの直接URL",
},
```

**GitHubリポジトリを監視する場合** → `GITHUB_REPOS` に追記する。

```python
{
    "id":    "一意のID",
    "tool":  "OpenClaw",
    "label": "表示名",
    "owner": "GitHubオーナー名",
    "repo":  "リポジトリ名",
    "type":  "releases",  # "releases" or "commits"
},
```

**新ツールを追加する場合** → `TOOL_EMOJI` にも必ず追記すること。

```python
TOOL_EMOJI = {
    ...,
    "NewTool": "🟠",  # 追加
}
```

また `notifier_notion.py` の `TOOL_COLOR` にも追記する。

---

### ② RSSフィードのURLが壊れている（収集0件）を診断する

```bash
cd src
python3 -c "
import feedparser
url = 'ここに疑わしいRSS URL'
feed = feedparser.parse(url)
print('status:', feed.get('status'))
print('entries:', len(feed.entries))
if feed.entries:
    print('最新:', feed.entries[0].get('title'))
"
```

修正方法は `sources.py` の該当エントリの `rss` URLを更新するだけ。

---

### ③ ローカルでテスト実行する

```bash
# 依存インストール
pip install -r requirements.txt

# 環境変数をセット（最低限これだけで動く）
export ANTHROPIC_API_KEY="sk-ant-..."

# 収集だけテスト（通知・保存なし）
cd src
python3 -c "
from collect import collect_all
from dedup import filter_new
articles = collect_all()
new = filter_new(articles)
print(f'新着: {len(new)}件')
for a in new[:3]:
    print(f'  [{a[\"tool\"]}] {a[\"title\"][:60]}')
"

# フル実行（全Secrets必要）
cd src
python3 main.py
```

---

### ④ 重複チェックをリセットする

`data/sent_ids.json` を空にすれば全記事が再送信対象になる。

```bash
echo "{}" > data/sent_ids.json
```

⚠️ リセット後に実行すると大量通知になるので注意。テスト後は必ず元に戻す。

---

### ⑤ 要約プロンプトを変更する

`src/summarizer.py` の `SYSTEM_PROMPT` を編集する。
変更後は必ず以下でプロンプトの動作を確認すること：

```bash
cd src
python3 -c "
import os
os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-...'
from summarizer import summarize_batch
test = [{
    'tool': 'Claude Code',
    'title': 'Claude Code 2.0 Released',
    'url': 'https://example.com',
    'raw_summary': 'Major update with new features...',
    'emoji': '💜',
    'id': 'test123',
    'label': 'Test',
    'published': None,
}]
result = summarize_batch(test)
print(result[0]['summary'])
print(result[0]['importance'])
"
```

---

### ⑥ GitHub Actionsのスケジュールを変更する

`.github/workflows/daily-collect.yml` の `cron` 行を編集する。

```yaml
# 現在: 毎日 01:00 UTC = JST 10:00
- cron: '0 1 * * *'

# 例: 毎日 00:00 UTC = JST 09:00 に変更
- cron: '0 0 * * *'
```

---

### ⑦ Notion DBにカラムを追加する

1. Notionで新しいプロパティを作成
2. `src/notifier_notion.py` の `_build_page_payload()` 内の `properties` dictに追記

```python
"新カラム名": {
    "rich_text": [{"text": {"content": article.get("新フィールド", "")}}]
},
```

3. 収集時にそのフィールドを埋めるよう `collect.py` か `summarizer.py` を修正する

---

## ⚠️ 修正時の注意事項

### やってはいけないこと
- `dedup.py` の `make_id()` のロジックを変更しない → sent_ids.json との整合性が壊れる
- `summarizer.py` の `BATCH_SIZE` を10より大きくしない → Gemini APIのコンテキスト上限に引っかかる（全文入力のため現在は3に設定）
- `notifier_line.py` の `MAX_MESSAGES_PER_PUSH` を5より大きくしない → LINE APIの制限
- `main.py` の Step7（`mark_all_seen`）をStep6より前に移動しない → 通知失敗時に再送できなくなる

### 修正後に必ず確認すること
- `python3 -c "import ast; ast.parse(open('src/XXX.py').read()); print('OK')"` で構文チェック
- 環境変数を設定してローカル実行し、エラーがないことを確認
- GitHub Actionsで `workflow_dispatch` による手動実行でE2Eテスト

---

## 🐛 よくあるエラーと対処法

| エラーメッセージ | 原因 | 対処 |
|----------------|------|------|
| `KeyError: 'ANTHROPIC_API_KEY'` | 環境変数未設定 | GitHub SecretsまたはローカルのexportでAPIキーをセット |
| `[RSS ERROR] xxx: ...` | RSSフィードURL変更 or サイト障害 | sources.pyのURLを最新に更新。一時的なら放置でOK |
| `[GitHub ERROR] xxx: 403` | GitHub APIレート制限 | GITHUB_TOKENが正しく設定されているか確認。未認証は60req/h |
| `[LINE ERROR] 400` | LINE_USER_IDが間違い | LINE DevelopersコンソールでUser IDを再確認 |
| `[Notion ERROR] xxx: 400` | Notionのプロパティ名が不一致 | Notion DBのプロパティ名とnotifier_notion.pyの定義を合わせる |
| `JSONDecodeError` in summarizer | Claude APIがJSON以外を返した | `_fallback_results()` が代替処理する。頻発するならSYSTEM_PROMPTを調整 |

---

## 📊 Notion DBスキーマ（参照用）

| プロパティ名 | 型 | 値の例 |
|------------|-----|------|
| タイトル | タイトル | "Claude Code 2.0 Released" |
| ツール | セレクト | Claude / Claude Code / Gemini / Codex / OpenClaw / Skills |
| 重要度 | セレクト | 高（赤）/ 中（黄）/ 低（グレー） |
| 日付 | 日付 | 記事公開日（YYYY-MM-DD） |
| URL | URL | 元記事URL |
| ソース | テキスト | "Anthropic公式ニュース" |
| 要約 | テキスト | Claude APIが生成した日本語要約 |
| 収集日 | 日付 | 収集実行日（YYYY-MM-DD） |

---

## 🔧 依存ライブラリ

```
feedparser==6.0.11   # RSSパース
requests==2.32.3     # HTTP通信（GitHub/LINE/Notion/HN API）
```

標準ライブラリのみで実装できる箇所は標準ライブラリを使い、依存を増やさないこと。

---

## 📝 コーディング規約

- **言語**: Python 3.12
- **型ヒント**: 関数シグネチャには必ず付ける（`def foo(articles: list) -> list:`）
- **エラー処理**: 外部API呼び出しは必ず `try/except` で囲む。エラーは `print` して継続（1ソースの失敗で全体を止めない）
- **ログ**: `print("[MODULE_NAME] メッセージ")` の形式を統一すること
- **コメント**: 日本語で書く
- **定数**: `sources.py` に集約する。他ファイルにマジックナンバーを散らばらせない