"""
AI最新情報収集ツール - メインエントリポイント
毎日 GitHub Actions から実行される
"""

import sys
import traceback

from collect import collect_all
from dedup import filter_new, mark_all_seen
from summarizer import summarize_batch
from notifier_line import send_line, send_line_error
from notifier_notion import save_to_notion


def main():
    print("=" * 50)
    print("🚀 AI最新情報収集ツール 起動")
    print("=" * 50)

    try:
        # Step 1: 収集
        all_articles = collect_all()

        # Step 2: 重複除去
        new_articles = filter_new(all_articles)
        print(f"\n🆕 新着記事（重複除去後）: {len(new_articles)}件")

        if not new_articles:
            print("新着情報なし。終了します。")
            return

        # Step 3: 重要度でソート（GitHub/公式を優先）
        priority_tools = ["Claude Code", "Claude", "Codex", "Gemini", "OpenClaw", "Skills"]
        new_articles.sort(key=lambda a: (
            priority_tools.index(a["tool"]) if a["tool"] in priority_tools else 99
        ))

        # Step 4: Claude API で日本語要約
        print("\n💬 Claude APIで日本語要約中...")
        summarized = summarize_batch(new_articles)
        print(f"  → {len(summarized)}件 要約完了")

        # 重要度でさらにソート
        importance_order = {"高": 0, "中": 1, "低": 2}
        summarized.sort(key=lambda a: importance_order.get(a.get("importance", "中"), 1))

        # Step 5: LINE 通知
        print("\n📲 LINE通知送信中...")
        send_line(summarized)

        # Step 6: Notion 保存
        print("\n📓 Notion保存中...")
        save_to_notion(summarized)

        # Step 7: 送信済みとしてマーク
        mark_all_seen(summarized)

        print("\n" + "=" * 50)
        print(f"✅ 完了! 処理件数: {len(summarized)}件")
        print("=" * 50)

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        print(f"\n❌ エラー発生:\n{error_msg}")
        send_line_error(error_msg[:500])
        sys.exit(1)


if __name__ == "__main__":
    main()
