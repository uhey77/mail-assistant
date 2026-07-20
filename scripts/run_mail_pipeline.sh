#!/bin/sh
set -eu

PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"
export PATH

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_root"

if command -v uv >/dev/null 2>&1; then
    uv_bin=$(command -v uv)
elif [ -x "${HOME}/.local/bin/uv" ]; then
    uv_bin="${HOME}/.local/bin/uv"
elif [ -x /opt/homebrew/bin/uv ]; then
    uv_bin=/opt/homebrew/bin/uv
elif [ -x /usr/local/bin/uv ]; then
    uv_bin=/usr/local/bin/uv
else
    echo "uvが見つかりません。UVをインストールするかPATHを設定してください。" >&2
    exit 127
fi

exec "$uv_bin" run --locked python -m mail_assistant run
