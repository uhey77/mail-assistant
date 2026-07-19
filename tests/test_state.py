from mail_assistant.state import StateStore


def test_state_store_saves_and_reads_classification(tmp_path):
    store = StateStore(tmp_path / "state.db")
    source = {
        "account": "personal",
        "gmail_message_id": "m1",
        "gmail_thread_id": "t1",
        "subject": "件名",
        "from": "sender@example.com",
        "received_at_utc": "2026-07-15T00:00:00+00:00",
    }
    classification = {
        "account": "personal",
        "gmail_message_id": "m1",
        "category": "reply",
        "priority": "high",
        "deadline": None,
        "summary": "要返信",
        "required_action": "返信する",
        "reason": "質問",
        "needs_review": False,
    }

    assert (
        store.save_classifications(
            source_emails=[source], classifications=[classification]
        )
        == 1
    )
    assert store.is_processed(account="personal", gmail_message_id="m1")
    assert store.get_processed_message_ids(
        account="personal", message_ids=["m1", "m2"]
    ) == {"m1"}
    assert store.get_statistics() == {
        "total": 1,
        "by_category": {"reply": 1},
        "by_account": {"personal": 1},
    }
    assert store.get_recent(limit=1)[0]["subject"] == "件名"


def test_state_store_upserts_same_message(tmp_path):
    store = StateStore(tmp_path / "state.db")
    source = {
        "account": "job",
        "gmail_message_id": "m1",
    }
    classification = {
        "account": "job",
        "gmail_message_id": "m1",
        "category": "see",
        "priority": "low",
        "deadline": None,
        "summary": "確認",
        "required_action": None,
        "reason": "通知",
        "needs_review": False,
    }

    store.save_classifications(source_emails=[source], classifications=[classification])
    store.save_classifications(
        source_emails=[source],
        classifications=[{**classification, "category": "action"}],
    )

    assert store.get_statistics()["by_category"] == {"action": 1}
