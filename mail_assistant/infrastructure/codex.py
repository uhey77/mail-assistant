"""Codex構造化出力Adapter。"""

from __future__ import annotations

from pathlib import Path

from mail_assistant.clients.codex import CodexRunner, CodexRunResult


class CodexStructuredOutputRunner:
    def __init__(self, runner: CodexRunner) -> None:
        self._runner = runner

    def run_json(self, *, prompt: str, schema_path: Path) -> CodexRunResult:
        return self._runner.run_json(prompt=prompt, schema_path=schema_path)
