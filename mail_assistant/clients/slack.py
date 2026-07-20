"""Slack Incoming Webhookクライアント。"""

from __future__ import annotations

from typing import Any

import requests

from mail_assistant.model_base import FrozenModel


class SlackServiceError(RuntimeError):
    """Slackへの通知に失敗した場合の例外。"""


class SlackResponse(FrozenModel):
    status_code: int
    response_text: str


class SlackService:
    """Slack Incoming WebhookへテキストまたはBlock Kitを送信する。"""

    def __init__(self, webhook_url: str, *, timeout_seconds: int = 15) -> None:
        webhook_url = webhook_url.strip()
        if not webhook_url:
            raise ValueError("Slack Webhook URLが空です。")
        if not webhook_url.startswith("https://hooks.slack.com/services/"):
            raise ValueError("Slack Webhook URLの形式が不正です。")
        if timeout_seconds <= 0:
            raise ValueError("timeout_secondsは1以上にしてください。")

        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def send_text(self, text: str) -> SlackResponse:
        text = text.strip()
        if not text:
            raise ValueError("Slackへ送信するテキストが空です。")
        return self._send(
            {
                "text": text,
                "unfurl_links": False,
                "unfurl_media": False,
            }
        )

    def send_blocks(self, *, text: str, blocks: list[dict[str, Any]]) -> SlackResponse:
        text = text.strip()
        if not text:
            raise ValueError("フォールバックテキストが空です。")
        if not blocks:
            raise ValueError("blocksが空です。")
        return self._send(
            {
                "text": text,
                "blocks": blocks,
                "unfurl_links": False,
                "unfurl_media": False,
            }
        )

    def _send(self, payload: dict[str, Any]) -> SlackResponse:
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as exc:
            raise SlackServiceError("Slackへの通知がタイムアウトしました。") from exc
        except requests.RequestException as exc:
            raise SlackServiceError(f"Slackへの接続に失敗しました: {exc}") from exc

        if not 200 <= response.status_code < 300:
            raise SlackServiceError(
                "Slackへの通知に失敗しました。\n"
                f"HTTPステータス: {response.status_code}\n"
                f"レスポンス: {response.text}"
            )
        return SlackResponse(
            status_code=response.status_code,
            response_text=response.text,
        )
