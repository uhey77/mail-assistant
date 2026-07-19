"""未処理メール本文の取得コマンド。"""

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
from mail_assistant.state import StateStore, StateStoreError

DEFAULT_QUERY = "in:inbox is:unread newer_than:1d"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="3つのGmailアカウントから未読メール本文を取得します。"
    )
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
        help=f"Gmail検索クエリ。既定値: {DEFAULT_QUERY}",
    )
    parser.add_argument(
        "--max-total",
        type=int,
        default=30,
        help="3アカウント合計の最大件数。既定値: 30",
    )
    parser.add_argument(
        "--max-per-account",
        type=int,
        default=30,
        help="1アカウントあたりの取得候補数。既定値: 30",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_PATHS.inbox_bodies,
        help="出力先JSONファイル",
    )
    return parser.parse_args()


def _fetch_account(
    *,
    account_name: str,
    token_path: Path,
    query: str,
    max_results: int,
    state_store: StateStore,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    client = GmailClient.from_token(token_path)
    account_email = client.account_email()
    message_ids = client.list_message_ids(query=query, max_results=max_results)
    processed_ids = state_store.get_processed_message_ids(
        account=account_name, message_ids=message_ids
    )
    unprocessed_ids = [
        message_id for message_id in message_ids if message_id not in processed_ids
    ]
    print(
        f"  候補: {len(message_ids)}件 / "
        f"処理済み除外: {len(processed_ids)}件 / "
        f"未処理: {len(unprocessed_ids)}件"
    )

    emails: list[dict[str, Any]] = []
    for index, message_id in enumerate(unprocessed_ids, start=1):
        print(f"  本文取得中: {index}/{len(unprocessed_ids)}", end="\r")
        emails.append(
            client.fetch_full_message(
                account_name=account_name,
                account_email=account_email,
                message_id=message_id,
            )
        )
    if unprocessed_ids:
        print()

    summary = {
        "account": account_name,
        "account_email": account_email,
        "candidate_count": len(message_ids),
        "processed_excluded_count": len(processed_ids),
        "unprocessed_candidate_count": len(unprocessed_ids),
        "fetched_count": len(emails),
    }
    return emails, summary


def main() -> int:
    args = parse_args()
    if args.max_total <= 0:
        print("--max-totalは1以上を指定してください。", file=sys.stderr)
        return 1
    if args.max_per_account <= 0:
        print("--max-per-accountは1以上を指定してください。", file=sys.stderr)
        return 1

    try:
        state_store = StateStore()
        all_emails: list[dict[str, Any]] = []
        account_summaries: list[dict[str, Any]] = []
        for account_name, token_path in DEFAULT_PATHS.account_tokens().items():
            print(f"{account_name} のメールを確認しています...")
            emails, summary = _fetch_account(
                account_name=account_name,
                token_path=token_path,
                query=args.query,
                max_results=args.max_per_account,
                state_store=state_store,
            )
            all_emails.extend(emails)
            account_summaries.append(summary)
            print(f"  {len(emails)}件取得しました。")

        all_emails.sort(key=lambda item: str(item["received_at_utc"]), reverse=True)
        selected_emails = all_emails[: args.max_total]
        selected_counts = {account: 0 for account in DEFAULT_PATHS.account_tokens()}
        for email_data in selected_emails:
            selected_counts[str(email_data["account"])] += 1
        for summary in account_summaries:
            summary["selected_count"] = selected_counts[str(summary["account"])]

        output = {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "query": args.query,
            "max_total": args.max_total,
            "max_per_account": args.max_per_account,
            "total_candidate_count": len(all_emails),
            "total_selected_count": len(selected_emails),
            "accounts": account_summaries,
            "emails": selected_emails,
        }
        write_json_object(args.output, output)
        print("\n本文の取得が完了しました。")
        print(f"候補件数: {len(all_emails)}")
        print(f"保存件数: {len(selected_emails)}")
        print(f"出力先: {args.output}")
        return 0
    except HttpError as exc:
        print(f"Gmail APIエラーが発生しました: {exc}", file=sys.stderr)
        return 1
    except StateStoreError as exc:
        print(f"履歴管理エラーが発生しました: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"取得に失敗しました: {exc}", file=sys.stderr)
        return 1
