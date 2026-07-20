"""外部サービスに依存しないドメイン型。"""

from mail_assistant.domain.models import (
    AccountName,
    ClassificationBatch,
    ClassificationCategory,
    ClassificationPriority,
    Email,
    EmailClassification,
)

__all__ = [
    "AccountName",
    "ClassificationBatch",
    "ClassificationCategory",
    "ClassificationPriority",
    "Email",
    "EmailClassification",
]
