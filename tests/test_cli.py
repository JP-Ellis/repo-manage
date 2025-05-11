from click.testing import CliRunner

from repo_manage.cli import main


def test_mutually_exclusive_verbose_and_quiet() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["-v", "-q", "version"])
    assert result.exit_code != 0
    assert "Mutually exclusive options" in result.stderr
