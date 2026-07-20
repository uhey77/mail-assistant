"""アプリケーション層が外部I/Oへ要求するPort。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from mail_assistant.domain import AccountName, Email


class StructuredOutput(Protocol):
    @property
    def data(self) -> dict[str, Any]: ...


class StructuredOutputRunner(Protocol):
    def run_json(self, *, prompt: str, schema_path: Path) -> StructuredOutput: ...


class MailGateway(Protocol):
    @property
    def account(self) -> AccountName: ...

    def list_message_ids(self, *, query: str, max_results: int) -> list[str]: ...

    def fetch_summary(self, message_id: str) -> Email: ...

    def fetch_full_message(self, message_id: str) -> Email: ...


class TextNotifier(Protocol):
    def send_text(self, text: str) -> object: ...


class NotificationState(Protocol):
    def last_notification_hash(self) -> str | None: ...

    def save_notification(self, *, fingerprint: str, count: int) -> None: ...


class PipelineStep(Protocol):
    @property
    def name(self) -> str: ...

    def execute(self) -> object: ...
