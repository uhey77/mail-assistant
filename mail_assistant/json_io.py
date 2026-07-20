"""JSONファイルの読み書き。"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

type JsonObject = dict[str, Any]
T = TypeVar("T")


def load_json_object(path: Path) -> JsonObject:
    """JSONオブジェクトを読み込み、利用者向けのエラーへ変換する。"""
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSONを解析できません: {path}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"JSONのルートがオブジェクトではありません: {path}")

    return data


def write_json_object(path: Path, data: JsonObject) -> None:
    """親ディレクトリを作成してJSONオブジェクトを保存する。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_decoded_json_object(
    path: Path,
    decoder: Callable[[JsonObject], T],
) -> T:
    """JSONオブジェクトを読み、境界で型付きオブジェクトへ変換する。"""
    return decoder(load_json_object(path))


def write_encoded_json_object(
    path: Path,
    value: T,
    encoder: Callable[[T], JsonObject],
) -> None:
    """型付きオブジェクトを境界でJSONへ変換して保存する。"""
    write_json_object(path, encoder(value))
