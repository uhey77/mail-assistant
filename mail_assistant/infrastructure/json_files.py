"""JSONファイル永続化Adapter。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from mail_assistant.json_io import load_json_object, write_json_object
from mail_assistant.model_base import FrozenArbitraryModel, FrozenModel
from mail_assistant.notifications import (
    load_last_notification_hash,
    save_notification_state,
)


class JsonFileRepository[T](FrozenArbitraryModel):
    path: Path
    decoder: Callable[[dict[str, Any]], T]
    encoder: Callable[[T], dict[str, Any]]

    def load(self) -> T:
        return self.decoder(load_json_object(self.path))

    def save(self, value: T) -> None:
        write_json_object(self.path, self.encoder(value))


class JsonNotificationState(FrozenModel):
    path: Path

    def last_notification_hash(self) -> str | None:
        return load_last_notification_hash(self.path)

    def save_notification(self, *, fingerprint: str, count: int) -> None:
        save_notification_state(
            self.path,
            notification_hash=fingerprint,
            notification_count=count,
        )
