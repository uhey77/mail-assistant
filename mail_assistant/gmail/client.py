"""Gmail APIクライアント。"""

from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from mail_assistant.gmail.mime import extract_message_body, get_header
from mail_assistant.settings import GMAIL_SCOPES


def _save_credentials(credentials: Credentials, token_path: Path) -> None:
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    with suppress(OSError):
        token_path.chmod(0o600)


def load_credentials(token_path: Path) -> Credentials:
    """保存済みOAuthトークンを読み込み、期限切れなら更新する。"""
    if not token_path.exists():
        raise FileNotFoundError(
            f"トークンが見つかりません: {token_path}\n"
            "先にauth_gmail.pyで認証してください。"
        )

    credentials = Credentials.from_authorized_user_file(
        str(token_path), list(GMAIL_SCOPES)
    )
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        _save_credentials(credentials, token_path)

    if not credentials.valid:
        raise RuntimeError(
            f"トークンが無効です: {token_path}\nauth_gmail.pyを再実行してください。"
        )
    return credentials


class GmailClient:
    """動的なGoogle API Resourceを小さな型付き境界へ閉じ込める。"""

    def __init__(self, service: Any) -> None:
        self._service = service

    @property
    def service(self) -> Any:
        """互換処理や高度な用途向けにGoogle API Resourceを返す。"""
        return self._service

    @classmethod
    def from_token(cls, token_path: Path) -> Self:
        credentials = load_credentials(token_path)
        service = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )
        return cls(service)

    def account_email(self) -> str:
        profile = self._service.users().getProfile(userId="me").execute()
        email_address = profile.get("emailAddress")
        if not email_address:
            raise RuntimeError(
                "Gmailプロフィールからメールアドレスを取得できませんでした。"
            )
        return str(email_address)

    def list_message_ids(self, *, query: str, max_results: int) -> list[str]:
        response = (
            self._service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        messages = response.get("messages", [])
        return [
            str(item["id"])
            for item in messages
            if isinstance(item, dict) and item.get("id")
        ]

    def fetch_summary(
        self,
        *,
        account_name: str,
        account_email: str,
        message_id: str,
    ) -> dict[str, Any]:
        message = (
            self._service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="metadata",
                metadataHeaders=["Subject", "From", "To", "Date", "Message-ID"],
            )
            .execute()
        )
        return self._build_common_email(
            message,
            account_name=account_name,
            account_email=account_email,
        )

    def fetch_full_message(
        self,
        *,
        account_name: str,
        account_email: str,
        message_id: str,
    ) -> dict[str, Any]:
        message = (
            self._service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        email_data = self._build_common_email(
            message,
            account_name=account_name,
            account_email=account_email,
        )

        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        headers = self._headers(payload)
        body_text, body_source = extract_message_body(payload)
        email_data.update(
            {
                "cc": get_header(headers, "Cc"),
                "reply_to": get_header(headers, "Reply-To"),
                "message_id_header": get_header(headers, "Message-ID"),
                "in_reply_to": get_header(headers, "In-Reply-To"),
                "references": get_header(headers, "References"),
                "body": body_text,
                "body_source": body_source,
                "body_length": len(body_text),
            }
        )
        return email_data

    @staticmethod
    def _headers(payload: dict[str, Any]) -> list[dict[str, str]]:
        headers = payload.get("headers", [])
        if not isinstance(headers, list):
            return []
        return [item for item in headers if isinstance(item, dict)]

    @classmethod
    def _build_common_email(
        cls,
        message: dict[str, Any],
        *,
        account_name: str,
        account_email: str,
    ) -> dict[str, Any]:
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        headers = cls._headers(payload)
        label_ids = message.get("labelIds", [])
        if not isinstance(label_ids, list):
            label_ids = []

        internal_date_ms = int(message.get("internalDate", 0))
        received_at = datetime.fromtimestamp(internal_date_ms / 1000, tz=UTC)
        return {
            "account": account_name,
            "account_email": account_email,
            "gmail_message_id": str(message["id"]),
            "gmail_thread_id": message.get("threadId"),
            "subject": get_header(headers, "Subject"),
            "from": get_header(headers, "From"),
            "to": get_header(headers, "To"),
            "header_date": get_header(headers, "Date"),
            "received_at_utc": received_at.isoformat(),
            "snippet": message.get("snippet", ""),
            "is_unread": "UNREAD" in label_ids,
            "is_inbox": "INBOX" in label_ids,
            "labels": label_ids,
        }
