from datetime import timedelta
from pathlib import Path

import pytest
import pytest_mock
from click.testing import CliRunner

from repo_manage.cli import main

try:
    from datetime import UTC, datetime
except ImportError:
    from datetime import datetime, timezone

    UTC = timezone.utc


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


def test_cli_list_prs(mocker: pytest_mock.MockerFixture) -> None:
    runner = CliRunner()

    mock_repo = mocker.MagicMock()
    mock_repo.name = "repo-manage"
    mock_repo.get_pulls.return_value = [
        mocker.Mock(
            number=1,
            base=mocker.Mock(repo=mocker.Mock(full_name="JP-Ellis/repo-manage")),
            title="Fix bug",
            user=mocker.Mock(login="contributor"),
            created_at=datetime(2025, 4, 1, 12, 0, 0, tzinfo=UTC),
            draft=False,
        )
    ]

    mock_remote_repositories = mocker.patch(
        "repo_manage.command.list.remote_repositories", return_value=[mock_repo]
    )

    result = runner.invoke(
        main,
        ["--org", "JP-Ellis", "list-prs"],
    )

    mock_remote_repositories.assert_called_once()

    assert result.exit_code == 0
    assert "Open Pull Requests" in result.output
    assert "JP-Ellis/repo-manage#1" in result.output


def test_cli_list_prs_with_author(mocker: pytest_mock.MockerFixture) -> None:
    runner = CliRunner()

    mock_repo = mocker.MagicMock()
    mock_repo.name = "repo-manage"
    mock_repo.get_pulls.return_value = [
        mocker.Mock(
            number=1,
            base=mocker.Mock(repo=mocker.Mock(full_name="JP-Ellis/repo-manage")),
            title="Fix bug",
            user=mocker.Mock(login="test-author"),
            created_at=datetime(2025, 4, 1, 12, 0, 0, tzinfo=UTC),
            draft=False,
        ),
        mocker.Mock(
            number=2,
            base=mocker.Mock(repo=mocker.Mock(full_name="JP-Ellis/repo-manage")),
            title="Another PR",
            user=mocker.Mock(login="another-author"),
            created_at=datetime(2025, 4, 2, 12, 0, 0, tzinfo=UTC),
            draft=False,
        ),
    ]

    mock_remote_repositories = mocker.patch(
        "repo_manage.command.list.remote_repositories", return_value=[mock_repo]
    )

    result = runner.invoke(
        main,
        ["--org", "JP-Ellis", "list-prs", "--author", "test-author"],
    )

    mock_remote_repositories.assert_called_once()
    mock_repo.get_pulls.assert_called_once()

    assert result.exit_code == 0
    assert "Open Pull Requests" in result.output
    assert "JP-Ellis/repo-manage#1" in result.output
    assert "Fix bug" in result.output
    assert "test-author" in result.output
    assert "JP-Ellis/repo-manage#2" not in result.output
    assert "Another PR" not in result.output
    assert "another-author" not in result.output


def test_cli_list_prs_with_date_range(mocker: pytest_mock.MockerFixture) -> None:
    runner = CliRunner()

    mock_repo = mocker.MagicMock()
    mock_repo.name = "repo-manage"
    mock_repo.get_pulls.return_value = [
        mocker.Mock(
            number=1,
            base=mocker.Mock(repo=mocker.Mock(full_name="JP-Ellis/repo-manage")),
            title="Too new",
            user=mocker.Mock(login="new-author"),
            created_at=datetime.now(tz=UTC) - timedelta(days=1),
            draft=False,
        ),
        mocker.Mock(
            number=2,
            base=mocker.Mock(repo=mocker.Mock(full_name="JP-Ellis/repo-manage")),
            title="Just right",
            user=mocker.Mock(login="right-author"),
            created_at=datetime.now(tz=UTC) - timedelta(days=60),
            draft=False,
        ),
        mocker.Mock(
            number=3,
            base=mocker.Mock(repo=mocker.Mock(full_name="JP-Ellis/repo-manage")),
            title="Too old",
            user=mocker.Mock(login="old-author"),
            created_at=datetime.now(tz=UTC) - timedelta(days=366),
            draft=False,
        ),
    ]

    mock_remote_repositories = mocker.patch(
        "repo_manage.command.list.remote_repositories", return_value=[mock_repo]
    )

    result = runner.invoke(
        main,
        [
            "--org",
            "JP-Ellis",
            "list-prs",
            "--older-than",
            "P30D",
            "--newer-than",
            "P90D",
        ],
    )

    mock_remote_repositories.assert_called_once()
    mock_repo.get_pulls.assert_called_once()

    assert result.exit_code == 0
    assert "Open Pull Requests" in result.output

    assert "JP-Ellis/repo-manage#1" not in result.output
    assert "Too new" not in result.output
    assert "new-author" not in result.output

    assert "JP-Ellis/repo-manage#2" in result.output
    assert "Just right" in result.output
    assert "right-author" in result.output

    assert "JP-Ellis/repo-manage#3" not in result.output
    assert "Too old" not in result.output
    assert "old-author" not in result.output
