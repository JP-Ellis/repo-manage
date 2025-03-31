from click.testing import CliRunner

from repo_manage.cli import main


def test_cli_version() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert "Repo Manage" in result.output
