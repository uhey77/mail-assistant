"""旧importパスとの互換モジュール。"""

from mail_assistant.state import (
    DEFAULT_DATABASE_PATH,
    StateStore,
    StateStoreError,
)

__all__ = ["DEFAULT_DATABASE_PATH", "StateStore", "StateStoreError"]
