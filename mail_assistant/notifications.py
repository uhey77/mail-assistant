"""Slack通知対象の選択、整形、重複防止。"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

NOTIFY_CATEGORIES = frozenset({"reply", "action", "see"})
CATEGORY_LABELS = {
    "reply": "返信が必要",
    "action": "対応が必要",
    "see": "確認のみ",
    "skip": "通知不要",
}
PRIORITY_LABELS = {"high": "高", "medium": "中", "low": "低"}


def build_email_index(
    emails_data: dict[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    emails = emails_data.get("emails")
    if not isinstance(emails, list):
        raise ValueError("メールJSONにemails配列がありません。")

    index: dict[tuple[str, str], dict[str, Any]] = {}
    for email_data in emails:
        if not isinstance(email_data, dict):
            continue
        account = email_data.get("account")
        message_id = email_data.get("gmail_message_id")
        if account and message_id:
            index[(str(account), str(message_id))] = email_data
    return index


def filter_classifications(
    classifications_data: dict[str, Any], *, include_skip: bool
) -> list[dict[str, Any]]:
    classifications = classifications_data.get("classifications")
    if not isinstance(classifications, list):
        raise ValueError("分類結果JSONにclassifications配列がありません。")

    categories = set(NOTIFY_CATEGORIES)
    if include_skip:
        categories.add("skip")
    return [
        item
        for item in classifications
        if isinstance(item, dict) and item.get("category") in categories
    ]


def normalize_single_line(value: Any, *, max_length: int) -> str:
    if max_length <= 0:
        raise ValueError("max_lengthは1以上にしてください。")
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) <= max_length:
        return text
    if max_length == 1:
        return "…"
    return text[: max_length - 1] + "…"


def format_deadline(value: Any) -> str:
    if value is None:
        return "記載なし"
    return normalize_single_line(value, max_length=100) or "記載なし"


def format_item(
    classification: dict[str, Any],
    email_data: dict[str, Any] | None,
    *,
    index: int,
) -> str:
    category = str(classification.get("category", ""))
    priority = str(classification.get("priority", ""))
    account = str(classification.get("account", ""))
    subject = (
        normalize_single_line(
            email_data.get("subject") if email_data else None,
            max_length=180,
        )
        or "件名不明"
    )
    sender = (
        normalize_single_line(
            email_data.get("from") if email_data else None,
            max_length=180,
        )
        or "送信者不明"
    )

    lines = [
        (
            f"*{index}. {CATEGORY_LABELS.get(category, category)}*"
            f" / 優先度: {PRIORITY_LABELS.get(priority, priority)}"
        ),
        f"*アカウント:* `{account}`",
        f"*件名:* {subject}",
        f"*送信者:* {sender}",
        f"*期限:* {format_deadline(classification.get('deadline'))}",
    ]
    optional_lines = (
        (
            "要約",
            normalize_single_line(classification.get("summary"), max_length=350),
        ),
        (
            "必要な対応",
            normalize_single_line(
                classification.get("required_action"), max_length=350
            ),
        ),
        (
            "分類理由",
            normalize_single_line(classification.get("reason"), max_length=250),
        ),
    )
    lines.extend(f"*{label}:* {text}" for label, text in optional_lines if text)
    if bool(classification.get("needs_review")):
        lines.append("*要確認:* 本人による確認が必要です")
    return "\n".join(lines)


def build_notification_text(
    classifications: list[dict[str, Any]],
    email_index: dict[tuple[str, str], dict[str, Any]],
    *,
    now: datetime | None = None,
) -> str:
    """通知本文を生成する。nowを注入できるため決定的にテストできる。"""
    current_time = now or datetime.now(UTC).astimezone()
    counts = {"reply": 0, "action": 0, "see": 0, "skip": 0}
    for item in classifications:
        category = item.get("category")
        if category in counts:
            counts[str(category)] += 1

    header = [
        "*メール分類結果*",
        f"実行日時: {current_time.strftime('%Y-%m-%d %H:%M')}",
        " / ".join(
            (
                f"返信: {counts['reply']}",
                f"対応: {counts['action']}",
                f"確認: {counts['see']}",
                f"不要: {counts['skip']}",
            )
        ),
    ]
    sections = []
    for index, classification in enumerate(classifications, start=1):
        key = (
            str(classification.get("account", "")),
            str(classification.get("gmail_message_id", "")),
        )
        sections.append(
            format_item(
                classification,
                email_index.get(key),
                index=index,
            )
        )
    return "\n".join(header) + "\n\n" + "\n\n--------------------\n\n".join(sections)


def calculate_notification_hash(classifications: list[dict[str, Any]]) -> str:
    fields = (
        "account",
        "gmail_message_id",
        "category",
        "priority",
        "deadline",
        "summary",
        "required_action",
        "needs_review",
    )
    normalized = [
        {field: item.get(field) for field in fields} for item in classifications
    ]
    serialized = json.dumps(
        normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def load_last_notification_hash(state_path: Path) -> str | None:
    if not state_path.exists():
        return None
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(state, dict):
        return None
    value = state.get("last_notification_hash")
    return value if isinstance(value, str) else None


def save_notification_state(
    state_path: Path,
    *,
    notification_hash: str,
    notification_count: int,
) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "last_notification_hash": notification_hash,
        "notification_count": notification_count,
        "notified_at_utc": datetime.now(UTC).isoformat(),
    }
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
