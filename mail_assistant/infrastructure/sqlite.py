"""SQLite状態管理Adapterの公開窓口。"""

from mail_assistant.state import StateStore, StateStoreError


class SqliteStateStore(StateStore):
    """インフラ層から利用するStateStoreの明示的な名前。"""


__all__ = ["SqliteStateStore", "StateStoreError"]
