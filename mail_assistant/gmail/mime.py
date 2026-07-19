"""Gmailメッセージのヘッダーと本文を整形する純粋関数。"""

from __future__ import annotations

import base64
import html
import re
from email.header import decode_header, make_header
from typing import Any


def decode_mime_header(value: str | None) -> str:
    """MIMEエンコードされたメールヘッダーをデコードする。"""
    if not value:
        return ""

    try:
        return str(make_header(decode_header(value)))
    except (LookupError, UnicodeError):
        return value


def get_header(headers: list[dict[str, str]], name: str) -> str:
    """大文字小文字を区別せず、指定したヘッダーの値を取得する。"""
    target = name.casefold()
    for header in headers:
        if header.get("name", "").casefold() == target:
            return decode_mime_header(header.get("value"))
    return ""


def decode_base64url(data: str | None) -> str:
    """Gmail APIのBase64URL文字列をUTF-8テキストへ変換する。"""
    if not data:
        return ""

    try:
        padding = "=" * (-len(data) % 4)
        decoded = base64.urlsafe_b64decode(data + padding)
        return decoded.decode("utf-8", errors="replace")
    except (ValueError, UnicodeError):
        return ""


def html_to_text(value: str) -> str:
    """HTMLメールを依存ライブラリなしでプレーンテキストへ変換する。"""
    if not value:
        return ""

    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", value)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n\n", text)
    text = re.sub(r"(?i)</div\s*>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", "", text)
    text = html.unescape(text).replace("\r\n", "\n").replace("\r", "\n")

    cleaned_lines: list[str] = []
    previous_blank = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        is_blank = not line
        if is_blank and previous_blank:
            continue
        cleaned_lines.append(line)
        previous_blank = is_blank

    return "\n".join(cleaned_lines).strip()


def _extract_parts(part: dict[str, Any]) -> tuple[list[str], list[str]]:
    mime_type = part.get("mimeType", "")
    body = part.get("body", {})
    data = body.get("data") if isinstance(body, dict) else None

    plain_chunks: list[str] = []
    html_chunks: list[str] = []
    if isinstance(data, str):
        decoded = decode_base64url(data)
        if mime_type == "text/plain":
            plain_chunks.append(decoded)
        elif mime_type == "text/html":
            html_chunks.append(decoded)

    parts = part.get("parts", [])
    if isinstance(parts, list):
        for child in parts:
            if not isinstance(child, dict):
                continue
            child_plain, child_html = _extract_parts(child)
            plain_chunks.extend(child_plain)
            html_chunks.extend(child_html)

    return plain_chunks, html_chunks


def normalize_text(value: str) -> str:
    """本文中のNUL、行末空白、連続空行を正規化する。"""
    value = value.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    normalized: list[str] = []
    previous_blank = False

    for raw_line in value.splitlines():
        line = raw_line.strip()
        is_blank = not line
        if is_blank and previous_blank:
            continue
        normalized.append(line)
        previous_blank = is_blank

    return "\n".join(normalized).strip()


def extract_message_body(payload: dict[str, Any]) -> tuple[str, str]:
    """text/plainを優先して本文と採用したMIME種別を返す。"""
    plain_chunks, html_chunks = _extract_parts(payload)
    plain_body = "\n".join(plain_chunks).strip()
    html_body = "\n".join(html_chunks).strip()

    if plain_body:
        return normalize_text(plain_body), "text/plain"
    if html_body:
        return normalize_text(html_to_text(html_body)), "text/html"

    body = payload.get("body", {})
    fallback_data = body.get("data") if isinstance(body, dict) else None
    fallback_body = decode_base64url(
        fallback_data if isinstance(fallback_data, str) else None
    )
    if fallback_body:
        return normalize_text(fallback_body), "unknown"
    return "", "none"
