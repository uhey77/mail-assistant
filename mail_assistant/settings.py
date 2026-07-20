"""アプリケーション全体で共有するパスと定数。"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from mail_assistant.model_base import FrozenModel

SOURCE_ROOT = Path(__file__).resolve().parent.parent


def resolve_project_root(env: Mapping[str, str] | None = None) -> Path:
    """環境変数があれば実行データの基準ディレクトリとして採用する。"""
    source = os.environ if env is None else env
    configured_root = source.get("MAIL_ASSISTANT_HOME")
    if configured_root:
        return Path(configured_root).expanduser().resolve()
    return SOURCE_ROOT


PROJECT_ROOT = resolve_project_root()

GMAIL_SCOPES = ("https://www.googleapis.com/auth/gmail.readonly",)

ACCOUNT_NAMES = (
    "personal",
    "university",
    "job",
)


class AppPaths(FrozenModel):
    """プロジェクト内のファイル配置を一元管理する。"""

    root: Path

    def __init__(self, root: Path | str) -> None:
        super().__init__(root=root)

    @property
    def credentials(self) -> Path:
        return self.root / "credentials" / "credentials.json"

    @property
    def tokens(self) -> Path:
        return self.root / "tokens"

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def prompt(self) -> Path:
        return self.root / "prompts" / "classify_emails.md"

    @property
    def classification_schema(self) -> Path:
        return self.root / "schemas" / "email_classification.schema.json"

    @property
    def database(self) -> Path:
        return self.data / "mail_assistant.db"

    @property
    def inbox_bodies(self) -> Path:
        return self.data / "inbox_bodies.json"

    @property
    def inbox_summary(self) -> Path:
        return self.data / "inbox_summary.json"

    @property
    def classification(self) -> Path:
        return self.data / "classification.json"

    @property
    def slack_notification_state(self) -> Path:
        return self.data / "slack_notification_state.json"

    @property
    def pipeline_lock(self) -> Path:
        return self.data / "mail_pipeline.lock"

    @property
    def codex_config(self) -> Path:
        return self.root / ".codex" / "config.toml"

    def token_for(self, account: str) -> Path:
        """アカウント設定名に対応するOAuthトークンのパスを返す。"""
        if account not in ACCOUNT_NAMES:
            allowed = ", ".join(ACCOUNT_NAMES)
            raise ValueError(
                f"不正なアカウント名です: {account}\n使用可能な値: {allowed}"
            )
        return self.tokens / f"{account}.json"

    def account_tokens(self) -> dict[str, Path]:
        """定義順を維持したアカウントとトークンの対応を返す。"""
        return {account: self.token_for(account) for account in ACCOUNT_NAMES}


DEFAULT_PATHS = AppPaths(PROJECT_ROOT)


class AppConfig(FrozenModel):
    """実行時設定。グローバル環境をアプリケーション層から分離する。"""

    paths: AppPaths
    account_names: tuple[str, ...] = ACCOUNT_NAMES

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> AppConfig:
        return cls(paths=AppPaths(resolve_project_root(env)))


DEFAULT_CONFIG = AppConfig(paths=DEFAULT_PATHS)
