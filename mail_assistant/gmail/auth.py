"""Google OAuth認証フロー。"""

from __future__ import annotations

import sys
from contextlib import suppress
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from mail_assistant.settings import DEFAULT_PATHS, GMAIL_SCOPES, AppPaths


def load_saved_credentials(token_path: Path) -> Credentials | None:
    if not token_path.exists():
        return None
    return Credentials.from_authorized_user_file(str(token_path), list(GMAIL_SCOPES))


def authorize(account: str, *, paths: AppPaths = DEFAULT_PATHS) -> Credentials:
    """指定した設定名のGoogleアカウントをOAuth認証する。"""
    token_path = paths.token_for(account)
    if not paths.credentials.exists():
        raise FileNotFoundError(
            "OAuth認証情報が見つかりません。\n"
            f"次の場所に配置してください:\n{paths.credentials}"
        )

    paths.tokens.mkdir(parents=True, exist_ok=True)
    credentials = load_saved_credentials(token_path)
    if credentials and credentials.valid:
        return credentials

    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception:  # Google認証ライブラリは複数の例外型を送出する。
            print(
                "保存済みトークンを更新できませんでした。ブラウザ認証をやり直します。",
                file=sys.stderr,
            )
            credentials = None

    if not credentials:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(paths.credentials), list(GMAIL_SCOPES)
        )
        print(f"\n認証対象: {account}")
        print(
            "ブラウザが開いたら、必ずこの用途に対応する"
            "Googleアカウントを選択してください。\n"
        )
        credentials = flow.run_local_server(
            host="localhost",
            port=0,
            authorization_prompt_message=(
                "ブラウザでGoogleアカウントを認証してください。"
            ),
            success_message=(
                "認証が完了しました。このブラウザタブを閉じて構いません。"
            ),
            open_browser=True,
        )

    token_path.write_text(credentials.to_json(), encoding="utf-8")
    with suppress(OSError):
        token_path.chmod(0o600)
    return credentials


def verify_account(credentials: Credentials) -> str:
    """Gmail APIへ接続し、認証されたメールアドレスを返す。"""
    service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    email_address = profile.get("emailAddress")
    if not email_address:
        raise RuntimeError(
            "Gmailプロフィールからメールアドレスを取得できませんでした。"
        )
    return str(email_address)
