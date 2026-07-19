"""互換用エントリーポイント。"""

from mail_assistant.cli.notify_slack import main, parse_args
from mail_assistant.json_io import load_json_object as load_json
from mail_assistant.notifications import (
    CATEGORY_LABELS,
    NOTIFY_CATEGORIES,
    PRIORITY_LABELS,
    build_email_index,
    build_notification_text,
    calculate_notification_hash,
    filter_classifications,
    format_deadline,
    format_item,
    load_last_notification_hash,
    normalize_single_line,
    save_notification_state,
)
from mail_assistant.settings import DEFAULT_PATHS

BASE_DIR = DEFAULT_PATHS.root
DEFAULT_CLASSIFICATION_PATH = DEFAULT_PATHS.classification
DEFAULT_EMAILS_PATH = DEFAULT_PATHS.inbox_bodies
DEFAULT_STATE_PATH = DEFAULT_PATHS.slack_notification_state


if __name__ == "__main__":
    raise SystemExit(main())
