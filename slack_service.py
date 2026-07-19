"""旧importパスとの互換モジュール。"""

from mail_assistant.clients.slack import (
    SlackResponse,
    SlackService,
    SlackServiceError,
)

__all__ = ["SlackResponse", "SlackService", "SlackServiceError"]
