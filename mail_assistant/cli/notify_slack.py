"""分類結果のSlack通知コマンド。"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from mail_assistant.clients.slack import SlackService, SlackServiceError
from mail_assistant.json_io import load_json_object
from mail_assistant.notifications import (
    build_email_index,
    build_notification_text,
    calculate_notification_hash,
    filter_classifications,
    load_last_notification_hash,
    save_notification_state,
)
from mail_assistant.settings import DEFAULT_PATHS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="メール分類結果をSlackへ通知します。")
    parser.add_argument(
        "--classification",
        type=Path,
        default=DEFAULT_PATHS.classification,
        help="分類結果JSON",
    )
    parser.add_argument(
        "--emails",
        type=Path,
        default=DEFAULT_PATHS.inbox_bodies,
        help="取得メールJSON",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=DEFAULT_PATHS.slack_notification_state,
        help="通知済み状態の保存先",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Slackへ送信せず、通知内容だけ表示します。",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="同一内容を通知済みでも強制的に再送します。",
    )
    parser.add_argument(
        "--include-skip",
        action="store_true",
        help="skip分類もSlackへ通知します。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        load_dotenv(DEFAULT_PATHS.root / ".env")
        classifications_data = load_json_object(args.classification)
        emails_data = load_json_object(args.emails)
        email_index = build_email_index(emails_data)
        classifications = filter_classifications(
            classifications_data,
            include_skip=args.include_skip,
            email_index=email_index,
        )
        if not classifications:
            print("Slack通知対象のメールはありません。")
            return 0

        notification_text = build_notification_text(classifications, email_index)
        notification_hash = calculate_notification_hash(classifications)
        if not args.force and notification_hash == load_last_notification_hash(
            args.state
        ):
            print("同一内容はすでにSlackへ通知済みです。")
            return 0

        if args.dry_run:
            print(f"Slack通知プレビュー\n\n{notification_text}\n")
            print("dry-runのためSlackには送信していません。")
            return 0

        webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        if not webhook_url:
            raise ValueError(".envにSLACK_WEBHOOK_URLが設定されていません。")
        response = SlackService(webhook_url=webhook_url).send_text(notification_text)
        save_notification_state(
            args.state,
            notification_hash=notification_hash,
            notification_count=len(classifications),
        )
        print("Slack通知が完了しました。")
        print(f"通知件数: {len(classifications)}")
        print(f"HTTPステータス: {response.status_code}")
        return 0
    except (FileNotFoundError, ValueError, SlackServiceError) as exc:
        print(f"Slack通知に失敗しました:\n{exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"予期しないエラーが発生しました:\n{exc}", file=sys.stderr)
        return 1
