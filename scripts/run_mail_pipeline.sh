#!/bin/zsh

export HOME="/Users/yuhei"
export PATH="/Users/yuhei/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

cd "/Users/yuhei/Developer/mail-assistant" || exit 1

exec "/Users/yuhei/.local/bin/uv" run python run_mail_pipeline.py
