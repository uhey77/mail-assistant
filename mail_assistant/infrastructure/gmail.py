"""GmailClientを型付きMailGatewayへ変換するAdapter。"""

from __future__ import annotations

from pathlib import Path
from typing import Self

from mail_assistant.domain import AccountName, Email
from mail_assistant.gmail.client import GmailClient
from mail_assistant.model_base import FrozenArbitraryModel


class GmailMailbox(FrozenArbitraryModel):
    account: AccountName
    account_email: str
    client: GmailClient

    @classmethod
    def from_token(
        cls,
        *,
        account: AccountName | str,
        token_path: Path,
    ) -> Self:
        client = GmailClient.from_token(token_path)
        return cls(
            account=AccountName(account),
            account_email=client.account_email(),
            client=client,
        )

    def list_message_ids(self, *, query: str, max_results: int) -> list[str]:
        return self.client.list_message_ids(query=query, max_results=max_results)

    def fetch_summary(self, message_id: str) -> Email:
        return Email.from_mapping(
            self.client.fetch_summary(
                account_name=self.account.value,
                account_email=self.account_email,
                message_id=message_id,
            )
        )

    def fetch_full_message(self, message_id: str) -> Email:
        return Email.from_mapping(
            self.client.fetch_full_message(
                account_name=self.account.value,
                account_email=self.account_email,
                message_id=message_id,
            )
        )
