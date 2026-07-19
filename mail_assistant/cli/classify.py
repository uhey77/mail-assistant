"""Codexによるメール分類コマンド。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mail_assistant.classification import EmailClassifier, category_counts
from mail_assistant.clients.codex import CodexRunner, CodexRunnerError
from mail_assistant.json_io import load_json_object, write_json_object
from mail_assistant.settings import DEFAULT_PATHS
from mail_assistant.state import StateStore, StateStoreError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Codex CLIでメールを4分類します。")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_PATHS.inbox_bodies,
        help="入力メールJSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_PATHS.classification,
        help="分類結果JSON",
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        default=DEFAULT_PATHS.prompt,
        help="分類プロンプト",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_PATHS.classification_schema,
        help="Codex出力用JSON Schema",
    )
    parser.add_argument(
        "--max-body-chars",
        type=int,
        default=4000,
        help="メール1件あたりCodexへ渡す本文の最大文字数。既定値: 4000",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Codexのタイムアウト秒数。既定値: 300",
    )
    return parser.parse_args()


def _print_summary(data: dict[str, object]) -> None:
    counts = category_counts(data)
    print("\n分類結果")
    print(f"  reply : {counts['reply']}件")
    print(f"  action: {counts['action']}件")
    print(f"  see   : {counts['see']}件")
    print(f"  skip  : {counts['skip']}件")


def main() -> int:
    args = parse_args()
    try:
        if args.max_body_chars <= 0:
            raise ValueError("--max-body-charsは1以上にしてください。")
        if args.timeout <= 0:
            raise ValueError("--timeoutは1以上にしてください。")

        source_data = load_json_object(args.input)
        if not args.prompt.is_file():
            raise FileNotFoundError(f"プロンプトが見つかりません: {args.prompt}")
        instruction = args.prompt.read_text(encoding="utf-8")

        runner = CodexRunner(
            working_directory=DEFAULT_PATHS.root,
            ephemeral=True,
            timeout_seconds=args.timeout,
            strict_config=True,
        )
        classifier = EmailClassifier(runner)
        emails = source_data.get("emails")
        email_count = len(emails) if isinstance(emails, list) else 0
        print(f"{email_count}件をCodexで分類します。")
        result = classifier.classify(
            instruction=instruction,
            source_data=source_data,
            schema_path=args.schema,
            max_body_chars=args.max_body_chars,
        )
        write_json_object(args.output, result.data)

        classifications = result.data["classifications"]
        source_emails = source_data["emails"]
        if not isinstance(classifications, list) or not isinstance(source_emails, list):
            raise ValueError("分類結果または入力メールの形式が不正です。")
        saved_count = StateStore().save_classifications(
            source_emails=source_emails,
            classifications=classifications,
        )
        _print_summary(result.data)
        print("\n分類が完了しました。")
        print(f"出力先: {args.output}")
        print(f"SQLite保存件数: {saved_count}")
        return 0
    except (
        CodexRunnerError,
        StateStoreError,
        FileNotFoundError,
        ValueError,
    ) as exc:
        print(f"分類に失敗しました:\n{exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"予期しないエラーが発生しました:\n{exc}", file=sys.stderr)
        return 1
