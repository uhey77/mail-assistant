"""外部境界で扱うデータ構造。"""

from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

type Category = Literal["reply", "action", "see", "skip"]
type Priority = Literal["high", "medium", "low"]


EmailData = TypedDict(
    "EmailData",
    {
        "account": str,
        "account_email": str,
        "gmail_message_id": str,
        "gmail_thread_id": str | None,
        "subject": str,
        "from": str,
        "to": str,
        "received_at_utc": str,
        "snippet": str,
        "is_unread": bool,
        "is_inbox": bool,
        "labels": list[str],
        "cc": NotRequired[str],
        "reply_to": NotRequired[str],
        "body": NotRequired[str],
        "body_source": NotRequired[str],
        "body_length": NotRequired[int],
    },
)


class ClassificationData(TypedDict):
    gmail_message_id: str
    account: str
    category: Category
    priority: Priority
    deadline: str | None
    summary: str
    required_action: str | None
    reason: str
    needs_review: bool
