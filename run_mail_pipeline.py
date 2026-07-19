"""互換用エントリーポイント。"""

from mail_assistant.cli.pipeline import (
    get_selected_email_count,
    log,
    main,
    run_command,
)

if __name__ == "__main__":
    raise SystemExit(main())
