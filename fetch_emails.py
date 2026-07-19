"""互換用エントリーポイント。"""

from mail_assistant.cli.fetch_emails import fetch_account_emails, main, parse_args
from mail_assistant.gmail.client import GmailClient, load_credentials
from mail_assistant.gmail.mime import decode_mime_header, get_header
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


if __name__ == "__main__":
    raise SystemExit(main())
