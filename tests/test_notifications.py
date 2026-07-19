from datetime import UTC, datetime

from mail_assistant.notifications import (
    build_email_index,
    build_notification_text,
    calculate_notification_hash,
    filter_classifications,
    normalize_single_line,
)

CLASSIFICATION = {
    "gmail_message_id": "m1",
    "account": "personal",
    "category": "reply",
    "priority": "high",
    "deadline": None,
    "summary": "返信が必要です",
    "required_action": "返信する",
    "reason": "質問があるため",
    "needs_review": False,
}


def test_filter_classifications_excludes_skip_by_default():
    data = {
        "classifications": [
            CLASSIFICATION,
            {**CLASSIFICATION, "gmail_message_id": "m2", "category": "skip"},
        ]
    }

    assert filter_classifications(data, include_skip=False) == [CLASSIFICATION]
    assert len(filter_classifications(data, include_skip=True)) == 2


def test_filter_classifications_excludes_github_pull_request_email():
    github_pr = CLASSIFICATION
    non_github_pr = {**CLASSIFICATION, "gmail_message_id": "m2"}
    data = {"classifications": [github_pr, non_github_pr]}
    email_index = build_email_index(
        {
            "emails": [
                {
                    "gmail_message_id": "m1",
                    "account": "personal",
                    "subject": (
                        "Re: [neoAI-inc/neo-smart-chat] Production リリース "
                        "2026-07-14 10:15:57 +0000 (PR #11891)"
                    ),
                    "from": "GitHub <notifications@github.com>",
                },
                {
                    "gmail_message_id": "m2",
                    "account": "personal",
                    "subject": "Pull requestについて #42",
                    "from": "担当者 <person@example.com>",
                },
            ]
        }
    )

    assert filter_classifications(
        data,
        include_skip=False,
        email_index=email_index,
    ) == [non_github_pr]


def test_build_notification_text_joins_email_metadata():
    emails = {
        "emails": [
            {
                "gmail_message_id": "m1",
                "account": "personal",
                "subject": "面談日程",
                "from": "担当者",
            }
        ]
    }
    text = build_notification_text(
        [CLASSIFICATION],
        build_email_index(emails),
        now=datetime(2026, 7, 15, 12, 30, tzinfo=UTC),
    )

    assert "実行日時: 2026-07-15 12:30" in text
    assert "*件名:* 面談日程" in text
    assert "返信: 1" in text


def test_notification_hash_ignores_reason_but_detects_summary_change():
    original = calculate_notification_hash([CLASSIFICATION])

    assert (
        calculate_notification_hash([{**CLASSIFICATION, "reason": "別の理由"}])
        == original
    )
    assert (
        calculate_notification_hash([{**CLASSIFICATION, "summary": "変更"}]) != original
    )


def test_normalize_single_line_handles_one_character_limit():
    assert normalize_single_line("long", max_length=1) == "…"
