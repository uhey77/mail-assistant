# mail-assistant

複数のGmailアカウントから未処理の未読メールを取得し、Codex CLIで
`reply`・`action`・`see`・`skip` の4種類に分類してSlackへ通知する
ローカルアシスタントです。取得、分類、通知と処理状態を分離し、すべての操作を
単一の `mail-assistant` CLIから実行します。

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
`credentials/credentials.json` に配置します。

## 環境変数

プロジェクトルートの `.env` に必要な値を設定します。

```dotenv
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
MAIL_ASSISTANT_HOME=/absolute/path/to/mail-assistant
```

| 変数 | 必須条件 | 用途 |
| --- | --- | --- |
| `SLACK_WEBHOOK_URL` | Slack通知を行う場合 | Incoming WebhookのURL |
| `MAIL_ASSISTANT_HOME` | プロジェクト外やschedulerから実行する場合 | 認証情報、データ、プロンプト、`.env` を探索する基準ディレクトリ |

リポジトリのルートから実行する場合、`MAIL_ASSISTANT_HOME` は省略できます。
定期実行ではカレントディレクトリに依存しないよう、絶対パスで指定してください。

## Gmail認証

初回はアカウントごとにOAuth認証を行います。

```sh
uv run mail-assistant auth personal
uv run mail-assistant auth university
uv run mail-assistant auth job
```

## 実行方法

CLIのヘルプと利用可能なオプションは次のコマンドで確認できます。

```sh
uv run mail-assistant --help
uv run mail-assistant <subcommand> --help
```

インストールされたconsole scriptを使わず、Pythonモジュールとしても同じCLIを
実行できます。

```sh
uv run python -m mail_assistant <subcommand>
```

### サブコマンド

| サブコマンド | 役割 |
| --- | --- |
| `auth` | GmailアカウントのOAuth認証を行う |
| `fetch` | Gmailから対象メールの一覧を取得する |
| `fetch-bodies` | 取得済みメールの本文を取得する |
| `classify` | メールを4種類に分類して結果を保存する |
| `notify` | 未通知の分類結果をSlackへ通知する |
| `state` | 保存済みの処理状態を表示する |
| `run` | 取得から通知までのパイプライン全体を実行する |

パイプライン全体を実行する場合は `run` を使用します。

```sh
uv run mail-assistant run
```

各段階は独立して実行できます。

```sh
uv run mail-assistant fetch
uv run mail-assistant fetch-bodies
uv run mail-assistant classify
uv run mail-assistant notify
uv run mail-assistant state
```

## 定期実行

schedulerからは、実行環境の差異を吸収する正式なlauncherとして
`scripts/run_mail_pipeline.sh` を使用します。schedulerの設定内に個別の
サブコマンドを複製しないでください。

```sh
MAIL_ASSISTANT_HOME=/absolute/path/to/mail-assistant \
  /absolute/path/to/mail-assistant/scripts/run_mail_pipeline.sh
```

`cron` や `launchd` には上記と同じ絶対パスを登録し、OAuth認証を行ったユーザーで
実行してください。Codex CLIを利用できる実行環境を用意し、前回の処理が完了する
前に次の処理を開始しないようscheduler側で重複起動を防止してください。

## プロジェクト構成

```text
mail_assistant/
├── cli/             # 単一CLIの引数解析、コマンド振り分け、終了コード
├── clients/         # Codex CLI、Slack Webhookとの外部境界
├── gmail/           # Gmail APIとMIME本文処理
├── classification.py # 分類ユースケース
├── notifications.py  # 通知ユースケース
├── state.py          # SQLiteリポジトリ
├── json_io.py        # JSONの入出力
└── settings.py       # パスと環境設定
scripts/
└── run_mail_pipeline.sh # scheduler向けlauncher
```

`cli` は引数と終了コードだけを扱い、業務ロジックはパッケージ直下、外部サービス
との通信は `clients` と `gmail` に分離しています。この境界により、分類手段、
通知先、Gmail取得条件を他の層へ波及させずに変更できます。

## 開発

```sh
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest
```

認証トークン、取得データ、SQLiteデータベース、`.env` はGit管理対象外です。
