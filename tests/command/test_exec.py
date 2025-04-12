import shutil
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from repo_manage.cli import main


@pytest.fixture
def repos(tmp_path: Path) -> tuple[Path, Path]:
    """Fixture to create two temporary git repositories."""
    git = shutil.which("git")
    if not git:
        msg = "Git is not installed or not found in PATH."
        raise RuntimeError(msg)

    git_cmd = [
        git,
        "-c",
        "user.name=pytest-test",
        "-c",
        "user.email=pytest-test@localhost",
    ]

    def create_git_repo(path: Path, filename: str) -> None:
        path.mkdir(parents=True, exist_ok=True)
        (path / filename).write_text("test content")

        subprocess.check_output([*git_cmd, "init"], cwd=path)  # noqa: S603
        subprocess.check_output([*git_cmd, "add", filename], cwd=path)  # noqa: S603
        subprocess.check_output([*git_cmd, "commit", "-m", "Initial commit"], cwd=path)  # noqa: S603

    repo1 = tmp_path / "repo1"
    repo2 = tmp_path / "repo2"

    create_git_repo(repo1, "file1.txt")
    create_git_repo(repo2, "file2.txt")

    return repo1, repo2


def test_exec_command(repos: tuple[Path, Path]) -> None:
    """Test the `repo-manage exec` command."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--local", str(repos[0].parent), "exec", "--", "touch", "output.txt"],
    )

    assert result.exit_code == 0
    for repo in repos:
        assert (repo / "output.txt").exists()


def test_exec_capture(
    repos: tuple[Path, Path],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the `repo-manage exec` command with capture."""
    runner = CliRunner()
    with caplog.at_level("INFO"):
        result = runner.invoke(
            main,
            [
                "--local",
                str(repos[0].parent),
                "exec",
                "--capture",
                "--",
                "echo",
                "Hello, World!",
            ],
        )

    assert result.exit_code == 0
    assert "Hello, World!" in caplog.text


def test_exec_check(
    repos: tuple[Path, Path],
    caplog: pytest.LogCaptureFixture,
) -> None:
    runner = CliRunner()
    with caplog.at_level("INFO"):
        result = runner.invoke(
            main,
            [
                "--local",
                str(repos[0].parent),
                "exec",
                "--check",
                "--capture",
                "--",
                "touch",
                "output.txt",
                ";",
                "false",
            ],
        )

    assert result.exit_code != 0
    assert (repos[0] / "output.txt").exists()
    assert not (repos[1] / "output.txt").exists()


def test_exec_no_check(
    repos: tuple[Path, Path],
    caplog: pytest.LogCaptureFixture,
) -> None:
    runner = CliRunner()
    with caplog.at_level("INFO"):
        result = runner.invoke(
            main,
            [
                "--local",
                str(repos[0].parent),
                "exec",
                "--no-check",
                "--capture",
                "--",
                "touch",
                "output.txt",
                ";",
                "false",
            ],
        )

    assert result.exit_code == 0
    assert (repos[0] / "output.txt").exists()
    assert (repos[1] / "output.txt").exists()


def test_exec_and_or(
    repos: tuple[Path, Path],
    caplog: pytest.LogCaptureFixture,
) -> None:
    runner = CliRunner()
    with caplog.at_level("INFO"):
        result = runner.invoke(
            main,
            [
                "--local",
                str(repos[0].parent),
                "exec",
                "--capture",
                "--",
                "echo",
                "hello",
                "&&",
                "echo",
                "world",
                "||",
                "echo",
                "foo",
            ],
        )

    assert result.exit_code == 0
    assert "hello" in caplog.text
    assert "world" in caplog.text
    assert "foo" not in caplog.text
