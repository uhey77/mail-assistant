"""メール取得・分類・通知を順番に実行するコマンド。"""

from __future__ import annotations

import fcntl
import subprocess
import sys
from datetime import datetime

from mail_assistant.json_io import load_json_object
from mail_assistant.settings import DEFAULT_PATHS


def log(message: str) -> None:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"[{timestamp}] {message}", flush=True)


def run_command(command: list[str]) -> None:
    log(f"実行: {' '.join(command)}")
    completed = subprocess.run(
        command,
        cwd=DEFAULT_PATHS.root,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"コマンドが失敗しました。終了コード={completed.returncode}\n"
            f"コマンド: {' '.join(command)}"
        )


def get_selected_email_count() -> int:
    data = load_json_object(DEFAULT_PATHS.inbox_bodies)
    emails = data.get("emails")
    if not isinstance(emails, list):
        raise ValueError("inbox_bodies.jsonにemails配列がありません。")
    return len(emails)


def main() -> int:
    lock_path = DEFAULT_PATHS.pipeline_lock
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("別のメール処理が実行中のため、今回は終了します。")
            return 0

        try:
            log("メール処理を開始します。")
            run_command(
                [
                    sys.executable,
                    "-m",
                    "mail_assistant",
                    "fetch-bodies",
                    "--max-total",
                    "10",
                ]
            )
            email_count = get_selected_email_count()
            if email_count == 0:
                log("新しい未処理メールはありません。")
                return 0
            log(f"未処理メール数: {email_count}件")
            run_command([sys.executable, "-m", "mail_assistant", "classify"])
            run_command([sys.executable, "-m", "mail_assistant", "notify"])
            log("メール処理が正常に完了しました。")
            return 0
        except Exception as exc:
            log(f"メール処理に失敗しました: {exc}")
            return 1
