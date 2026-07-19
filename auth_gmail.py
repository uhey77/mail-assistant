"""互換用エントリーポイント。実装はmail_assistantパッケージにあります。"""

from mail_assistant.cli.auth_gmail import main
from mail_assistant.gmail.auth import (
    authorize,
    verify_account,
)
from mail_assistant.gmail.auth import (
    load_saved_credentials as load_credentials,
)
from mail_assistant.settings import ACCOUNT_NAMES, DEFAULT_PATHS, GMAIL_SCOPES

CREDENTIALS_PATH = DEFAULT_PATHS.credentials
TOKENS_DIR = DEFAULT_PATHS.tokens
SCOPES = list(GMAIL_SCOPES)


def validate_files(account: str):
    token_path = DEFAULT_PATHS.token_for(account)
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            "OAuth認証情報が見つかりません。\n"
            f"次の場所に配置してください:\n{CREDENTIALS_PATH}"
        )
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    return token_path


if __name__ == "__main__":
    raise SystemExit(main())
