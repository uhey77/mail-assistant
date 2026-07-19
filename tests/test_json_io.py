import json

import pytest

from mail_assistant.json_io import load_json_object, write_json_object


def test_json_object_round_trip(tmp_path):
    path = tmp_path / "nested" / "data.json"
    expected = {"message": "こんにちは", "count": 2}

    write_json_object(path, expected)

    assert load_json_object(path) == expected


def test_load_json_object_rejects_array(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps([1, 2]), encoding="utf-8")

    with pytest.raises(ValueError, match="ルートがオブジェクト"):
        load_json_object(path)
