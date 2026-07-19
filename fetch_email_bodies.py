"""互換用エントリーポイント。"""

from mail_assistant.cli.fetch_email_bodies import DEFAULT_QUERY, main, parse_args
from mail_assistant.gmail.client import GmailClient, load_credentials
from mail_assistant.gmail.mime import (
    decode_base64url,
    decode_mime_header,
    extract_message_body,
    get_header,
    html_to_text,
    normalize_text,
)
from mail_assistant.settings import DEFAULT_PATHS, GMAIL_SCOPES

BASE_DIR = DEFAULT_PATHS.root
TOKENS_DIR = DEFAULT_PATHS.tokens
DATA_DIR = DEFAULT_PATHS.data
SCOPES = list(GMAIL_SCOPES)
ACCOUNTS = DEFAULT_PATHS.account_tokens()


def build_gmail_service(token_path):
    return GmailClient.from_token(token_path).service


def get_account_email(service):
    return GmailClient(service).account_email()


def list_message_ids(service, query, max_results):
    return GmailClient(service).list_message_ids(query=query, max_results=max_results)


def fetch_message(service, account_name, account_email, message_id):
    return GmailClient(service).fetch_full_message(
        account_name=account_name,
        account_email=account_email,
        message_id=message_id,
    )


if __name__ == "__main__":
    raise SystemExit(main())
