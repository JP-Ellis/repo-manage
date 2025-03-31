import logging
import shutil
from typing import TYPE_CHECKING

import pytest
import pytest_mock

from repo_manage.util import github_token

if TYPE_CHECKING:
    from unittest.mock import MagicMock


def test_github_token_from_env(caplog: pytest.LogCaptureFixture) -> None:
    """
    Test default when environment variable is set.

    The `conftext.py` file ensures that `GITHUB_TOKEN` is set, so this
    should
    """
    with caplog.at_level(logging.DEBUG):
        token = github_token()
        assert token

    assert "Using GitHub token from environment variable." in caplog.text


def test_github_token_from_cli(
    monkeypatch: pytest.MonkeyPatch,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """
    Test default when CLI is set.

    The `conftext.py` file ensures that `GH_TOKEN` is set, so this should
    be the only token used.
    """
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    mock: MagicMock = mocker.patch(
        "subprocess.check_output",
        return_value="cli-token\n",
    )

    token = github_token()
    assert token == "cli-token"  # noqa: S105
    mock.assert_called_once_with(
        [shutil.which("gh"), "auth", "token"],
        encoding="utf-8",
    )
