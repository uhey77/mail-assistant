from mail_assistant.settings import AppPaths, resolve_project_root


def test_app_paths_builds_account_token_paths(tmp_path):
    paths = AppPaths(tmp_path)

    assert paths.token_for("personal") == tmp_path / "tokens" / "personal.json"
    assert list(paths.account_tokens()) == ["personal", "university", "job"]


def test_project_root_can_be_overridden(monkeypatch, tmp_path):
    monkeypatch.setenv("MAIL_ASSISTANT_HOME", str(tmp_path))

    assert resolve_project_root() == tmp_path.resolve()
