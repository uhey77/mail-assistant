"""Codex CLIを構造化出力モードで実行するクライアント。"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from mail_assistant.model_base import FrozenModel


class CodexRunnerError(RuntimeError):
    """Codex CLIの実行または出力処理に失敗した場合の例外。"""


class CodexRunResult(FrozenModel):
    data: dict[str, Any]
    stdout: str
    stderr: str


class CodexRunner:
    """プロジェクトの設定を利用してCodex CLIを実行する。"""

    def __init__(
        self,
        *,
        working_directory: Path,
        ephemeral: bool = True,
        timeout_seconds: int = 300,
        strict_config: bool = True,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_secondsは1以上にしてください。")
        self.working_directory = working_directory.resolve()
        self.ephemeral = ephemeral
        self.timeout_seconds = timeout_seconds
        self.strict_config = strict_config

    def validate_environment(self) -> None:
        if shutil.which("codex") is None:
            raise CodexRunnerError(
                "codexコマンドが見つかりません。\n"
                "Codex CLIがインストールされ、PATHが通っているか"
                "確認してください。"
            )
        if not self.working_directory.is_dir():
            raise CodexRunnerError(
                f"作業ディレクトリが存在しません: {self.working_directory}"
            )

        config_path = self.working_directory / ".codex" / "config.toml"
        if not config_path.is_file():
            raise CodexRunnerError(f"プロジェクト設定が見つかりません: {config_path}")

    def build_command(self, *, schema_path: Path, output_path: Path) -> list[str]:
        command = [
            "codex",
            "exec",
            "--cd",
            str(self.working_directory),
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
        ]
        if self.ephemeral:
            command.append("--ephemeral")
        if self.strict_config:
            command.append("--strict-config")
        command.append("-")
        return command

    def run_json(self, *, prompt: str, schema_path: Path) -> CodexRunResult:
        self.validate_environment()
        schema_path = schema_path.resolve()
        if not schema_path.is_file():
            raise FileNotFoundError(f"JSON Schemaが見つかりません: {schema_path}")

        with tempfile.TemporaryDirectory(
            prefix="mail-assistant-codex-"
        ) as temporary_directory:
            output_path = Path(temporary_directory) / "result.json"
            command = self.build_command(
                schema_path=schema_path, output_path=output_path
            )
            completed = self._execute(command, prompt=prompt)

            if not output_path.is_file():
                raise CodexRunnerError(
                    "Codexの最終出力ファイルが生成されませんでした。\n"
                    f"標準出力:\n{completed.stdout}\n"
                    f"標準エラー:\n{completed.stderr}"
                )

            raw_output = output_path.read_text(encoding="utf-8").strip()
            if not raw_output:
                raise CodexRunnerError("Codexの最終出力が空です。")
            try:
                data = json.loads(raw_output)
            except json.JSONDecodeError as exc:
                raise CodexRunnerError(
                    "Codexの最終出力をJSONとして解析できませんでした。\n"
                    f"出力:\n{raw_output}"
                ) from exc
            if not isinstance(data, dict):
                raise CodexRunnerError(
                    "CodexのJSON出力ルートがオブジェクトではありません。"
                )
            return CodexRunResult(
                data=data, stdout=completed.stdout, stderr=completed.stderr
            )

    def _execute(
        self, command: list[str], *, prompt: str
    ) -> subprocess.CompletedProcess[str]:
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                cwd=self.working_directory,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise CodexRunnerError(
                f"Codexの実行が{self.timeout_seconds}秒でタイムアウトしました。"
            ) from exc
        except OSError as exc:
            raise CodexRunnerError(f"Codex CLIを起動できませんでした: {exc}") from exc

        if completed.returncode != 0:
            raise CodexRunnerError(
                "Codexの実行に失敗しました。\n"
                f"終了コード: {completed.returncode}\n"
                f"実行コマンド: {' '.join(command)}\n"
                f"標準出力:\n{completed.stdout}\n"
                f"標準エラー:\n{completed.stderr}"
            )
        return completed
