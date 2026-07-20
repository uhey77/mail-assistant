"""複数メールボックスからの取得ユースケース。"""

from __future__ import annotations

from pydantic import PositiveInt

from mail_assistant.application.ports import MailGateway
from mail_assistant.domain import Email
from mail_assistant.model_base import FrozenModel


class FetchRequest(FrozenModel):
    query: str
    max_results: PositiveInt
    include_body: bool = False


class FetchEmails:
    def __init__(self, gateways: tuple[MailGateway, ...]) -> None:
        self._gateways = gateways

    def execute(self, request: FetchRequest) -> tuple[Email, ...]:
        emails: list[Email] = []
        for gateway in self._gateways:
            message_ids = gateway.list_message_ids(
                query=request.query,
                max_results=request.max_results,
            )
            fetch = (
                gateway.fetch_full_message
                if request.include_body
                else gateway.fetch_summary
            )
            emails.extend(fetch(message_id) for message_id in message_ids)
        return tuple(emails)
