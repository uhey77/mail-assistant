"""全機能を単一のコマンド名前空間へまとめるCLI dispatcher。"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Sequence

from mail_assistant.model_base import FrozenModel


class Command(FrozenModel):
    module: str
    summary: str


COMMANDS: dict[str, Command] = {
    "auth": Command(
        module="mail_assistant.cli.auth_gmail",
        summary="Gmail OAuth認証",
    ),
    "fetch": Command(
        module="mail_assistant.cli.fetch_emails",
        summary="メール概要の取得",
    ),
    "fetch-bodies": Command(
        module="mail_assistant.cli.fetch_email_bodies",
        summary="メール本文の取得",
    ),
    "classify": Command(
        module="mail_assistant.cli.classify",
        summary="メール分類",
    ),
    "notify": Command(
        module="mail_assistant.cli.notify_slack",
        summary="Slack通知",
    ),
    "state": Command(
        module="mail_assistant.cli.show_state",
        summary="処理状態の表示",
    ),
    "run": Command(
        module="mail_assistant.cli.pipeline",
        summary="パイプライン全体の実行",
    ),
}


def _print_help(*, stream: object = sys.stdout) -> None:
    print("usage: mail-assistant <command> [options]", file=stream)
    print("", file=stream)
    print("commands:", file=stream)
    width = max(len(name) for name in COMMANDS)
    for name, command in COMMANDS.items():
        print(f"  {name:<{width}}  {command.summary}", file=stream)
    print("", file=stream)
    print("各コマンドの詳細: mail-assistant <command> --help", file=stream)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] in {"-h", "--help"}:
        _print_help()
        return 0

    command_name, *command_arguments = arguments
    command = COMMANDS.get(command_name)
    if command is None:
        print(f"不明なコマンドです: {command_name}", file=sys.stderr)
        _print_help(stream=sys.stderr)
        return 2

    module = importlib.import_module(command.module)
    handler = getattr(module, "main", None)
    if not callable(handler):
        raise RuntimeError(f"CLIハンドラーがありません: {command.module}.main")

    original_argv = sys.argv
    sys.argv = [f"{original_argv[0]} {command_name}", *command_arguments]
    try:
        result = handler()
    finally:
        sys.argv = original_argv
    return result if isinstance(result, int) else 0
