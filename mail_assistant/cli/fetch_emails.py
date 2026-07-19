"""メール概要取得コマンド。"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

from googleapiclient.errors import HttpError

from mail_assistant.gmail.client import GmailClient
from mail_assistant.json_io import write_json_object
from mail_assistant.settings import DEFAULT_PATHS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="複数のGmailアカウントからメール概要を取得します。"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="アカウントごとの最大取得件数。既定値: 10",
    )
    parser.add_argument(
        "--query",
        default="in:inbox newer_than:7d",
        help="Gmail検索クエリ。既定値: in:inbox newer_than:7d",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_PATHS.inbox_summary,
        help="出力JSONファイル",
    )
    return parser.parse_args()


def fetch_account_emails(
    account_name: str,
    token_path: Path,
    max_results: int,
    query: str,
) -> list[dict[str, Any]]:
    client = GmailClient.from_token(token_path)
    account_email = client.account_email()
    message_ids = client.list_message_ids(query=query, max_results=max_results)
    return [
        client.fetch_summary(
            account_name=account_name,
            account_email=account_email,
            message_id=message_id,
        )
        for message_id in message_ids
    ]


def main() -> int:
    args = parse_args()
    if args.max_results <= 0:
        print("--max-resultsは1以上を指定してください。", file=sys.stderr)
        return 1

    all_emails: list[dict[str, Any]] = []
    account_summaries: list[dict[str, Any]] = []
    try:
        for account_name, token_path in DEFAULT_PATHS.account_tokens().items():
            print(f"{account_name} のメールを取得しています...")
            emails = fetch_account_emails(
                account_name, token_path, args.max_results, args.query
            )
            all_emails.extend(emails)
            account_summaries.append({"account": account_name, "count": len(emails)})
            print(f"  {len(emails)}件取得しました。")

        all_emails.sort(key=lambda item: str(item["received_at_utc"]), reverse=True)
        output = {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "query": args.query,
            "max_results_per_account": args.max_results,
            "total_count": len(all_emails),
            "accounts": account_summaries,
            "emails": all_emails,
        }
        write_json_object(args.output, output)
        print("\n取得が完了しました。")
        print(f"合計件数: {len(all_emails)}")
        print(f"出力先: {args.output}")
        return 0
    except HttpError as exc:
        print(f"Gmail APIエラーが発生しました: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"取得に失敗しました: {exc}", file=sys.stderr)
        return 1
