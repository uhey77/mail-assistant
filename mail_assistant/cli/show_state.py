"""処理履歴表示コマンド。"""

from __future__ import annotations

import argparse
from pathlib import Path

from mail_assistant.state import DEFAULT_DATABASE_PATH, StateStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="メール処理履歴を表示します。")
    parser.add_argument("--limit", type=int, default=20, help="表示件数。既定値: 20")
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="SQLiteデータベース",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit <= 0:
        raise ValueError("--limitは1以上にしてください。")

    store = StateStore(args.database)
    statistics = store.get_statistics()
    print("処理履歴")
    print(f"  合計: {statistics['total']}件")
    print("\nアカウント別")
    for account, count in statistics["by_account"].items():
        print(f"  {account}: {count}件")
    print("\n分類別")
    for category in ("reply", "action", "see", "skip"):
        count = statistics["by_category"].get(category, 0)
        print(f"  {category}: {count}件")

    print("\n最近の処理")
    rows = store.get_recent(limit=args.limit)
    if not rows:
        print("  処理履歴はありません。")
        return 0
    for index, row in enumerate(rows, start=1):
        print(f"{index}. [{row['account']}] {row['category']} / {row['priority']}")
        print(f"   件名: {row['subject']}")
        print(f"   送信者: {row['sender']}")
        print(f"   処理日時: {row['processed_at_utc']}\n")
    return 0
