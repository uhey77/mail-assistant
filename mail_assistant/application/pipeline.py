"""パイプライン段階の実行制御。"""

from __future__ import annotations

from mail_assistant.application.ports import PipelineStep
from mail_assistant.model_base import FrozenArbitraryModel, FrozenModel


class StepResult(FrozenArbitraryModel):
    name: str
    value: object


class PipelineReport(FrozenModel):
    steps: tuple[StepResult, ...]


class Pipeline:
    """各段階をPortとして受け取り、実行順序だけを管理する。"""

    def __init__(self, steps: tuple[PipelineStep, ...]) -> None:
        self._steps = steps

    def execute(self) -> PipelineReport:
        return PipelineReport(
            steps=tuple(
                StepResult(name=step.name, value=step.execute())
                for step in self._steps
            )
        )
