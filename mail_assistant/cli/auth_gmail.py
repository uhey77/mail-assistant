"""Gmail OAuth認証コマンド。"""

from __future__ import annotations

import argparse
import sys

from googleapiclient.errors import HttpError

from mail_assistant.gmail.auth import authorize, verify_account
from mail_assistant.settings import ACCOUNT_NAMES, DEFAULT_PATHS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gmail APIのOAuth認証を行います。")
    parser.add_argument("account", choices=ACCOUNT_NAMES, help="認証設定名")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        credentials = authorize(args.account)
        email_address = verify_account(credentials)
        token_path = DEFAULT_PATHS.token_for(args.account)
        print("\n認証に成功しました。")
        print(f"設定名: {args.account}")
        print(f"Googleアカウント: {email_address}")
        print(f"トークン保存先: {token_path}")
        return 0
    except HttpError as exc:
        print(f"Gmail APIエラーが発生しました: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"認証に失敗しました: {exc}", file=sys.stderr)
        return 1
