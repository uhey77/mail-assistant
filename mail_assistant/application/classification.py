"""型付きメール分類ユースケース。"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from mail_assistant.application.ports import StructuredOutputRunner
from mail_assistant.classification import build_prompt, validate_result
from mail_assistant.domain import ClassificationBatch
from mail_assistant.model_base import FrozenModel


class ClassificationOutcome(FrozenModel):
    batch: ClassificationBatch
    input_emails: tuple[dict[str, Any], ...]

    def to_mapping(self) -> dict[str, Any]:
        return self.batch.to_mapping()


class ClassifyEmails:
    """プロバイダー固有型をアプリケーション境界から排除して分類する。"""

    def __init__(self, runner: StructuredOutputRunner) -> None:
        self._runner = runner

    def execute(
        self,
        *,
        instruction: str,
        source_data: Mapping[str, object],
        schema_path: Path,
        max_body_chars: int,
    ) -> ClassificationOutcome:
        prompt, input_emails = build_prompt(
            instruction,
            dict(source_data),
            max_body_chars=max_body_chars,
        )
        result = self._runner.run_json(prompt=prompt, schema_path=schema_path)
        raw_data = dict(result.data)
        validate_result(raw_data, input_emails)
        batch = ClassificationBatch.from_mapping(raw_data)
        batch.ensure_matches(input_emails)
        return ClassificationOutcome(batch=batch, input_emails=tuple(input_emails))
