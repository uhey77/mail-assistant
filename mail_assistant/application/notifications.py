"""通知計画と配信を分離したユースケース。"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from pydantic import NonNegativeInt

from mail_assistant.application.ports import NotificationState, TextNotifier
from mail_assistant.domain import ClassificationBatch, Email
from mail_assistant.model_base import FrozenModel
from mail_assistant.notifications import (
    build_email_index,
    build_notification_text,
    calculate_notification_hash,
    filter_classifications,
)


class NotificationPlan(FrozenModel):
    text: str
    fingerprint: str
    count: NonNegativeInt


class NotificationResult(FrozenModel):
    plan: NotificationPlan
    sent: bool
    reason: str


class Notify:
    def __init__(self, notifier: TextNotifier, state: NotificationState) -> None:
        self._notifier = notifier
        self._state = state

    def plan(
        self,
        batch: ClassificationBatch,
        emails: Sequence[Email],
        *,
        include_skip: bool = False,
        now: datetime | None = None,
    ) -> NotificationPlan:
        email_index = build_email_index(
            {"emails": [email.to_mapping() for email in emails]}
        )
        filtered = filter_classifications(
            batch.to_mapping(),
            include_skip=include_skip,
            email_index=email_index,
        )
        return NotificationPlan(
            text=build_notification_text(filtered, email_index, now=now),
            fingerprint=calculate_notification_hash(filtered),
            count=len(filtered),
        )

    def execute(
        self,
        batch: ClassificationBatch,
        emails: Sequence[Email],
        *,
        include_skip: bool = False,
        force: bool = False,
        now: datetime | None = None,
    ) -> NotificationResult:
        plan = self.plan(batch, emails, include_skip=include_skip, now=now)
        if plan.count == 0:
            return NotificationResult(plan=plan, sent=False, reason="no-targets")
        if not force and self._state.last_notification_hash() == plan.fingerprint:
            return NotificationResult(plan=plan, sent=False, reason="duplicate")

        self._notifier.send_text(plan.text)
        self._state.save_notification(
            fingerprint=plan.fingerprint,
            count=plan.count,
        )
        return NotificationResult(plan=plan, sent=True, reason="sent")
