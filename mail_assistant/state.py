"""処理済みメールと分類結果を管理するSQLiteリポジトリ。"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mail_assistant.settings import DEFAULT_PATHS

DEFAULT_DATABASE_PATH = DEFAULT_PATHS.database


class StateStoreError(RuntimeError):
    """SQLiteの読み書きに失敗した場合の例外。"""


class StateStore:
    """処理状態をSQLiteへ永続化するリポジトリ。"""

    def __init__(self, database_path: Path = DEFAULT_DATABASE_PATH) -> None:
        self.database_path = database_path.resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=30)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        try:
            with self.connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS processed_emails (
                        account TEXT NOT NULL,
                        gmail_message_id TEXT NOT NULL,
                        gmail_thread_id TEXT,
                        subject TEXT,
                        sender TEXT,
                        received_at_utc TEXT,
                        category TEXT NOT NULL CHECK (
                            category IN ('reply', 'action', 'see', 'skip')
                        ),
                        priority TEXT NOT NULL CHECK (
                            priority IN ('high', 'medium', 'low')
                        ),
                        deadline TEXT,
                        summary TEXT NOT NULL,
                        required_action TEXT,
                        reason TEXT NOT NULL,
                        needs_review INTEGER NOT NULL CHECK (
                            needs_review IN (0, 1)
                        ),
                        classification_json TEXT NOT NULL,
                        processed_at_utc TEXT NOT NULL,
                        PRIMARY KEY (account, gmail_message_id)
                    );

                    CREATE INDEX IF NOT EXISTS idx_processed_emails_processed_at
                    ON processed_emails (processed_at_utc);

                    CREATE INDEX IF NOT EXISTS idx_processed_emails_category
                    ON processed_emails (category);

                    CREATE INDEX IF NOT EXISTS idx_processed_emails_thread
                    ON processed_emails (account, gmail_thread_id);
                    """
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise StateStoreError(f"SQLiteの初期化に失敗しました: {exc}") from exc

    def is_processed(self, *, account: str, gmail_message_id: str) -> bool:
        try:
            with self.connect() as connection:
                row = connection.execute(
                    """
                    SELECT 1 FROM processed_emails
                    WHERE account = ? AND gmail_message_id = ?
                    LIMIT 1
                    """,
                    (account, gmail_message_id),
                ).fetchone()
            return row is not None
        except sqlite3.Error as exc:
            raise StateStoreError(f"処理済み確認に失敗しました: {exc}") from exc

    def get_processed_message_ids(
        self, *, account: str, message_ids: Sequence[str]
    ) -> set[str]:
        """候補IDのうち処理済みのIDを500件ずつまとめて取得する。"""
        if not message_ids:
            return set()

        processed_ids: set[str] = set()
        try:
            with self.connect() as connection:
                for start in range(0, len(message_ids), 500):
                    chunk = message_ids[start : start + 500]
                    placeholders = ",".join("?" for _ in chunk)
                    rows = connection.execute(
                        f"""
                        SELECT gmail_message_id
                        FROM processed_emails
                        WHERE account = ?
                          AND gmail_message_id IN ({placeholders})
                        """,
                        (account, *chunk),
                    ).fetchall()
                    processed_ids.update(str(row["gmail_message_id"]) for row in rows)
            return processed_ids
        except sqlite3.Error as exc:
            raise StateStoreError(f"処理済みIDの取得に失敗しました: {exc}") from exc

    def save_classifications(
        self,
        *,
        source_emails: list[dict[str, Any]],
        classifications: list[dict[str, Any]],
    ) -> int:
        """検証済みの分類結果を1トランザクションでupsertする。"""
        if len(source_emails) != len(classifications):
            raise ValueError(
                "入力メール数と分類結果数が一致しません。"
                f" 入力={len(source_emails)}, 分類={len(classifications)}"
            )

        source_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        for email_data in source_emails:
            account = email_data.get("account")
            message_id = email_data.get("gmail_message_id")
            if not account or not message_id:
                raise ValueError(
                    "入力メールにaccountまたはgmail_message_idがありません。"
                )
            source_by_key[(str(account), str(message_id))] = email_data

        processed_at = datetime.now(UTC).isoformat()
        rows = [
            self._classification_row(
                classification,
                source_by_key=source_by_key,
                processed_at=processed_at,
            )
            for classification in classifications
        ]

        try:
            with self.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.executemany(
                    """
                    INSERT INTO processed_emails (
                        account, gmail_message_id, gmail_thread_id, subject,
                        sender, received_at_utc, category, priority, deadline,
                        summary, required_action, reason, needs_review,
                        classification_json, processed_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (account, gmail_message_id) DO UPDATE SET
                        gmail_thread_id = excluded.gmail_thread_id,
                        subject = excluded.subject,
                        sender = excluded.sender,
                        received_at_utc = excluded.received_at_utc,
                        category = excluded.category,
                        priority = excluded.priority,
                        deadline = excluded.deadline,
                        summary = excluded.summary,
                        required_action = excluded.required_action,
                        reason = excluded.reason,
                        needs_review = excluded.needs_review,
                        classification_json = excluded.classification_json,
                        processed_at_utc = excluded.processed_at_utc
                    """,
                    rows,
                )
                connection.commit()
            return len(rows)
        except sqlite3.Error as exc:
            raise StateStoreError(f"分類結果の保存に失敗しました: {exc}") from exc

    @staticmethod
    def _classification_row(
        classification: dict[str, Any],
        *,
        source_by_key: dict[tuple[str, str], dict[str, Any]],
        processed_at: str,
    ) -> tuple[Any, ...]:
        account = classification.get("account")
        message_id = classification.get("gmail_message_id")
        source_email = source_by_key.get((str(account), str(message_id)))
        if source_email is None:
            raise ValueError(
                f"分類結果に対応する入力メールが見つかりません: {account}/{message_id}"
            )

        return (
            account,
            message_id,
            source_email.get("gmail_thread_id"),
            source_email.get("subject"),
            source_email.get("from"),
            source_email.get("received_at_utc"),
            classification["category"],
            classification["priority"],
            classification.get("deadline"),
            classification["summary"],
            classification.get("required_action"),
            classification["reason"],
            int(bool(classification["needs_review"])),
            json.dumps(
                classification,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            processed_at,
        )

    def get_statistics(self) -> dict[str, Any]:
        try:
            with self.connect() as connection:
                total_row = connection.execute(
                    "SELECT COUNT(*) AS count FROM processed_emails"
                ).fetchone()
                category_rows = connection.execute(
                    """
                    SELECT category, COUNT(*) AS count
                    FROM processed_emails GROUP BY category ORDER BY category
                    """
                ).fetchall()
                account_rows = connection.execute(
                    """
                    SELECT account, COUNT(*) AS count
                    FROM processed_emails GROUP BY account ORDER BY account
                    """
                ).fetchall()
            return {
                "total": int(total_row["count"]) if total_row else 0,
                "by_category": {
                    str(row["category"]): int(row["count"]) for row in category_rows
                },
                "by_account": {
                    str(row["account"]): int(row["count"]) for row in account_rows
                },
            }
        except sqlite3.Error as exc:
            raise StateStoreError(f"統計情報の取得に失敗しました: {exc}") from exc

    def get_recent(self, *, limit: int) -> list[dict[str, Any]]:
        """最近の処理履歴を表示層向けの辞書として返す。"""
        if limit <= 0:
            raise ValueError("limitは1以上にしてください。")
        try:
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT account, subject, sender, category, priority,
                           processed_at_utc
                    FROM processed_emails
                    ORDER BY processed_at_utc DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as exc:
            raise StateStoreError(f"処理履歴の取得に失敗しました: {exc}") from exc
