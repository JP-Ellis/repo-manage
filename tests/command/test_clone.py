"""
Tests for the `clone` CLI subcommand.
"""

from pathlib import Path

import pytest
import pytest_mock
from click.testing import CliRunner

from repo_manage.cli import main


def test_clone_success(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """
    Test the clone command with a successful clone operation.
    """
    (tmp_path / "repo-manage").mkdir()
    mock_check_call = mocker.patch("subprocess.check_call", return_value=0)
    mock_check_call.return_value = 0

    with caplog.at_level("INFO"):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--org", "JP-Ellis", "--local", str(tmp_path), "clone"],
        )
        assert result.exit_code == 0

    mock_check_call.assert_called()
    assert "Cloning repository" in caplog.text
    assert "Skipping existing repository" in caplog.text
