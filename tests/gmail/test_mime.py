import base64

from mail_assistant.gmail.mime import (
    decode_mime_header,
    extract_message_body,
    get_header,
    html_to_text,
)


def encode_body(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def test_decode_header_and_case_insensitive_lookup():
    headers = [
        {
            "name": "subject",
            "value": "=?UTF-8?B?44OG44K544OI?=",
        }
    ]

    assert get_header(headers, "Subject") == "テスト"
    assert decode_mime_header(None) == ""


def test_extract_message_body_prefers_plain_text():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {
                "mimeType": "text/html",
                "body": {"data": encode_body("<p>HTML</p>")},
            },
            {
                "mimeType": "text/plain",
                "body": {"data": encode_body(" Plain text \n\n\n End ")},
            },
        ],
    }

    assert extract_message_body(payload) == ("Plain text\n\nEnd", "text/plain")


def test_extract_message_body_falls_back_to_html():
    payload = {
        "mimeType": "text/html",
        "body": {"data": encode_body("<p>Hello<br>World</p>")},
    }

    assert extract_message_body(payload) == ("Hello\nWorld", "text/html")


def test_html_to_text_removes_scripts_and_decodes_entities():
    value = "<style>x</style><p>A &amp; B</p><script>bad()</script>"

    assert html_to_text(value) == "A & B"
