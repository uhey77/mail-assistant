"""Slack通知Adapter。"""

from __future__ import annotations

from mail_assistant.clients.slack import SlackResponse, SlackService


class SlackNotifier:
    def __init__(self, service: SlackService) -> None:
        self._service = service

    def send_text(self, text: str) -> SlackResponse:
        return self._service.send_text(text)
