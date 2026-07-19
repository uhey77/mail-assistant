"""互換用エントリーポイント。"""

from mail_assistant.classification import (
    build_prompt,
    category_counts,
    compact_email,
    validate_result,
)
from mail_assistant.cli.classify import main, parse_args
from mail_assistant.json_io import load_json_object as load_json
from mail_assistant.settings import DEFAULT_PATHS

BASE_DIR = DEFAULT_PATHS.root
DEFAULT_INPUT_PATH = DEFAULT_PATHS.inbox_bodies
DEFAULT_OUTPUT_PATH = DEFAULT_PATHS.classification
DEFAULT_PROMPT_PATH = DEFAULT_PATHS.prompt
DEFAULT_SCHEMA_PATH = DEFAULT_PATHS.classification_schema


def print_summary(result):
    counts = category_counts(result)
    print("\n分類結果")
    print(f"  reply : {counts['reply']}件")
    print(f"  action: {counts['action']}件")
    print(f"  see   : {counts['see']}件")
    print(f"  skip  : {counts['skip']}件")


if __name__ == "__main__":
    raise SystemExit(main())
