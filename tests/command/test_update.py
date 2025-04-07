"""
Tests for the `update` CLI subcommand.
"""

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from repo_manage.cli import main
from repo_manage.util import find_executable


def test_update_success(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Test the update command with a successful update operation.
    """
    subprocess.check_call([  # noqa: S603
        find_executable("gh"),
        "repo",
        "clone",
        "JP-Ellis/repo-manage",
        str(tmp_path / "repo-manage"),
    ])

    with caplog.at_level("INFO"):
        runner = CliRunner()
        result = runner.invoke(
            main, ["--org", "JP-Ellis", "--local", str(tmp_path), "update"]
        )
        assert result.exit_code == 0

    assert "Updating repository" in caplog.text
