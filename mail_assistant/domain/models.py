"""メール処理の内部で利用する検証済みドメインモデル。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any, Self

from pydantic import StrictBool, StrictInt

from mail_assistant.model_base import FrozenModel


class AccountName(StrEnum):
    PERSONAL = "personal"
    UNIVERSITY = "university"
    JOB = "job"


class ClassificationCategory(StrEnum):
    REPLY = "reply"
    ACTION = "action"
    SEE = "see"
    SKIP = "skip"


class ClassificationPriority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def _text(
    data: Mapping[str, object],
    key: str,
    *,
    default: str = "",
    required: bool = False,
) -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise TypeError(f"{key}は文字列で指定してください。")
    if required and not value:
        raise ValueError(f"{key}が空です。")
    return value


def _optional_text(data: Mapping[str, object], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{key}は文字列またはnullで指定してください。")
    return value


def _boolean(data: Mapping[str, object], key: str, *, default: bool = False) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise TypeError(f"{key}は真偽値で指定してください。")
    return value


class Email(FrozenModel):
    account: AccountName
    account_email: str
    gmail_message_id: str
    gmail_thread_id: str | None
    subject: str
    sender: str
    recipient: str
    received_at_utc: str
    snippet: str
    is_unread: StrictBool
    is_inbox: StrictBool
    labels: tuple[str, ...]
    cc: str = ""
    reply_to: str = ""
    body: str = ""
    body_source: str = ""
    body_length: StrictInt | None = None
    header_date: str = ""
    message_id_header: str = ""
    in_reply_to: str = ""
    references: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> Self:
        labels_value = data.get("labels", [])
        if not isinstance(labels_value, list) or not all(
            isinstance(label, str) for label in labels_value
        ):
            raise TypeError("labelsは文字列配列で指定してください。")

        thread_id = data.get("gmail_thread_id")
        if thread_id is not None and not isinstance(thread_id, str):
            raise TypeError("gmail_thread_idは文字列またはnullで指定してください。")

        body_length = data.get("body_length")
        if body_length is not None and (
            not isinstance(body_length, int) or isinstance(body_length, bool)
        ):
            raise TypeError("body_lengthは整数またはnullで指定してください。")

        return cls(
            account=AccountName(_text(data, "account", required=True)),
            account_email=_text(data, "account_email"),
            gmail_message_id=_text(data, "gmail_message_id", required=True),
            gmail_thread_id=thread_id,
            subject=_text(data, "subject"),
            sender=_text(data, "from"),
            recipient=_text(data, "to"),
            received_at_utc=_text(data, "received_at_utc"),
            snippet=_text(data, "snippet"),
            is_unread=_boolean(data, "is_unread"),
            is_inbox=_boolean(data, "is_inbox"),
            labels=tuple(labels_value),
            cc=_text(data, "cc"),
            reply_to=_text(data, "reply_to"),
            body=_text(data, "body"),
            body_source=_text(data, "body_source"),
            body_length=body_length,
            header_date=_text(data, "header_date"),
            message_id_header=_text(data, "message_id_header"),
            in_reply_to=_text(data, "in_reply_to"),
            references=_text(data, "references"),
        )

    def to_mapping(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "account": self.account.value,
            "account_email": self.account_email,
            "gmail_message_id": self.gmail_message_id,
            "gmail_thread_id": self.gmail_thread_id,
            "subject": self.subject,
            "from": self.sender,
            "to": self.recipient,
            "received_at_utc": self.received_at_utc,
            "snippet": self.snippet,
            "is_unread": self.is_unread,
            "is_inbox": self.is_inbox,
            "labels": list(self.labels),
        }
        optional_values: tuple[tuple[str, object], ...] = (
            ("cc", self.cc),
            ("reply_to", self.reply_to),
            ("body", self.body),
            ("body_source", self.body_source),
            ("body_length", self.body_length),
            ("header_date", self.header_date),
            ("message_id_header", self.message_id_header),
            ("in_reply_to", self.in_reply_to),
            ("references", self.references),
        )
        data.update(
            {key: value for key, value in optional_values if value not in ("", None)}
        )
        return data


class EmailClassification(FrozenModel):
    gmail_message_id: str
    account: AccountName
    category: ClassificationCategory
    priority: ClassificationPriority
    deadline: str | None
    summary: str
    required_action: str | None
    reason: str
    needs_review: StrictBool

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> Self:
        return cls(
            gmail_message_id=_text(data, "gmail_message_id", required=True),
            account=AccountName(_text(data, "account", required=True)),
            category=ClassificationCategory(_text(data, "category", required=True)),
            priority=ClassificationPriority(_text(data, "priority", required=True)),
            deadline=_optional_text(data, "deadline"),
            summary=_text(data, "summary", required=True),
            required_action=_optional_text(data, "required_action"),
            reason=_text(data, "reason", required=True),
            needs_review=_boolean(data, "needs_review"),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "gmail_message_id": self.gmail_message_id,
            "account": self.account.value,
            "category": self.category.value,
            "priority": self.priority.value,
            "deadline": self.deadline,
            "summary": self.summary,
            "required_action": self.required_action,
            "reason": self.reason,
            "needs_review": self.needs_review,
        }


class ClassificationBatch(FrozenModel):
    classifications: tuple[EmailClassification, ...]

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> Self:
        raw_items = data.get("classifications")
        if not isinstance(raw_items, list):
            raise ValueError("classifications配列がありません。")
        if not all(isinstance(item, dict) for item in raw_items):
            raise TypeError("classificationsにはオブジェクトだけを指定してください。")
        return cls(
            classifications=tuple(
                EmailClassification.from_mapping(item) for item in raw_items
            )
        )

    @classmethod
    def from_items(cls, items: Sequence[Mapping[str, object]]) -> Self:
        return cls(
            classifications=tuple(
                EmailClassification.from_mapping(item) for item in items
            )
        )

    def to_mapping(self) -> dict[str, Any]:
        return {"classifications": [item.to_mapping() for item in self.classifications]}

    def ensure_matches(self, emails: Sequence[Mapping[str, object]]) -> None:
        expected = [
            (str(email.get("gmail_message_id", "")), str(email.get("account", "")))
            for email in emails
        ]
        actual = [
            (item.gmail_message_id, item.account.value) for item in self.classifications
        ]
        if expected != actual:
            raise ValueError(
                "分類結果のメールID、アカウント、または順序が入力と一致しません。"
            )

    def counts(self) -> dict[ClassificationCategory, int]:
        counts = {category: 0 for category in ClassificationCategory}
        for item in self.classifications:
            counts[item.category] += 1
        return counts
