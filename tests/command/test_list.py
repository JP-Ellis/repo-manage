from pathlib import Path

import pytest
from click.testing import CliRunner

from repo_manage.cli import main


def test_cli_list_local() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--local", str(Path(__file__).parents[3]), "list", "--local"],
    )
    assert result.exit_code == 0
    assert "repo-manage" in result.output


def test_cli_list_remote() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--org", "JP-Ellis", "list", "--remote"])
    assert result.exit_code == 0
    assert "JP-Ellis/repo-manage" in result.output


def test_cli_list_all() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--org",
            "JP-Ellis",
            "--local",
            str(Path(__file__).parents[3]),
            "list",
            "--local",
            "--remote",
        ],
    )
    assert result.exit_code == 0
    assert "repo-manage" in result.output
    assert "JP-Ellis/repo-manage" in result.output


def test_cli_list_no_flag(caplog: pytest.LogCaptureFixture) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["list"])
    assert result.exit_code == 1
    assert "Please specify either --local or --remote." in caplog.text
