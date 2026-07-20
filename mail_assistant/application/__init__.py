"""メール処理のユースケース。"""

from mail_assistant.application.classification import (
    ClassificationOutcome,
    ClassifyEmails,
)
from mail_assistant.application.fetch import FetchEmails, FetchRequest
from mail_assistant.application.notifications import (
    NotificationPlan,
    NotificationResult,
    Notify,
)
from mail_assistant.application.pipeline import Pipeline, PipelineReport

__all__ = [
    "ClassificationOutcome",
    "ClassifyEmails",
    "FetchEmails",
    "FetchRequest",
    "NotificationPlan",
    "NotificationResult",
    "Notify",
    "Pipeline",
    "PipelineReport",
]
