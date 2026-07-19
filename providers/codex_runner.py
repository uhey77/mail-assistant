"""旧importパスとの互換モジュール。"""

from mail_assistant.clients.codex import (
    CodexRunner,
    CodexRunnerError,
    CodexRunResult,
)

__all__ = ["CodexRunResult", "CodexRunner", "CodexRunnerError"]
