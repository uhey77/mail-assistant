# mail-assistant

複数のGmailアカウントから未処理の未読メールを取得し、Codex CLIで
`reply`・`action`・`see`・`skip` の4種類に分類してSlackへ通知する
ローカルパイプラインです。

## 必要なもの

- Python 3.12以上
- [uv](https://docs.astral.sh/uv/)
- Codex CLI
- Google OAuthクライアント認証情報
- Slack Incoming Webhook（通知する場合）

## セットアップ

```sh
uv sync --dev
mkdir -p credentials
```

Google OAuthクライアントのJSONを
`credentials/credentials.json` に配置します。Slack通知を利用する場合は
`.env` に次の値を設定します。

```dotenv
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

別の場所からインストール済みコマンドを実行する場合は、認証情報・データ・
プロンプトを置く基準ディレクトリを `MAIL_ASSISTANT_HOME` で指定できます。

```dotenv
MAIL_ASSISTANT_HOME=/path/to/mail-assistant
```

初回はアカウントごとにOAuth認証を行います。

```sh
uv run mail-assistant-auth personal
uv run mail-assistant-auth university
uv run mail-assistant-auth job
```

## 実行方法

パイプライン全体を実行します。

```sh
uv run mail-assistant
```

各段階は個別にも実行できます。

```sh
uv run mail-assistant-fetch --max-total 10
uv run mail-assistant-classify
uv run mail-assistant-notify --dry-run
uv run mail-assistant-state --limit 20
```

従来のスクリプト名も互換エントリーポイントとして利用できます。

```sh
uv run python fetch_email_bodies.py --max-total 10
uv run python classify_with_codex.py
uv run python notify_slack.py --dry-run
```

## 構成

```text
mail_assistant/
├── cli/             # 引数解析、表示、終了コード
├── clients/         # Codex CLI、Slack Webhookとの外部境界
├── gmail/           # Gmail APIとMIME本文処理
├── classification.py
├── notifications.py
├── state.py         # SQLiteリポジトリ
├── json_io.py
└── settings.py
```

CLIから業務ロジックと外部サービスを分離しているため、分類プロバイダーや
通知先の追加、Gmail取得条件の変更を局所的に実装できます。トップレベルの
Pythonファイルは既存ジョブとの互換性を保つ薄いラッパーです。

## 開発

```sh
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest
```

認証トークン、取得データ、SQLiteデータベース、`.env` はGit管理対象外です。
