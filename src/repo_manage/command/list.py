"""
Subcommand for listing repositories and pull requests.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

import rich_click as click
from isodate import parse_duration
from rich.console import Console
from rich.table import Table

from repo_manage.util import local_repositories, remote_repositories

try:
    from datetime import UTC
except ImportError:
    from datetime import timezone

    UTC = timezone.utc

logger = logging.getLogger(__name__)


@click.command(name="list")
@click.option(
    "--local",
    is_flag=True,
    help="List local repositories.",
)
@click.option(
    "--remote",
    is_flag=True,
    help="List remote repositories.",
)
@click.pass_context
def list_cmd(
    ctx: click.Context,
    *,
    local: bool,
    remote: bool,
) -> None:
    """
    List repositories.

    This command lists all repositories in the specified organization or
    directory.
    """
    if not local and not remote:
        logger.error("Please specify either --local or --remote.")
        ctx.exit(1)

    if local:
        for repo_path in local_repositories(ctx.obj["local"]):
            click.echo(repo_path.relative_to(ctx.obj["local"]))

    if remote:
        for repo in remote_repositories(ctx.obj["org"]):
            if repo.fork:
                click.echo(repo.full_name + " (fork of: " + repo.parent.full_name + ")")
            else:
                click.echo(repo.full_name)


@click.command()
@click.option(
    "--include-forks/--exclude-forks",
    default=True,
    help="Include or exclude forked repositories (default: include).",
)
@click.option(
    "--include-archived/--exclude-archived",
    default=False,
    help="Include or exclude archived repositories (default: exclude).",
)
@click.option(
    "--exclude-author",
    multiple=True,
    help="Exclude authors matching the given regex pattern. Can be repeated.",
)
@click.option(
    "--include-drafts/--exclude-drafts",
    default=False,
    help="Include or exclude draft pull requests (default: exclude).",
)
@click.option(
    "--author",
    multiple=True,
    help="Include authors matching the given regex pattern. Can be repeated.",
)
@click.option(
    "--older-than",
    type=str,
    help="Filter PRs older than the given ISO 8601 duration.",
)
@click.option(
    "--newer-than",
    type=str,
    help="Filter PRs newer than the given ISO 8601 duration.",
)
@click.pass_context
def list_prs(  # noqa: PLR0913
    ctx: click.Context,
    *,
    include_forks: bool,
    include_archived: bool,
    author: tuple[str, ...],
    exclude_author: tuple[str, ...],
    include_drafts: bool,
    older_than: str | None,
    newer_than: str | None,
) -> None:
    """
    List all open pull requests for each repository in the organization.

    This command iterates over all repositories and gathers open PRs,
    displaying them in a Markdown-styled table.
    """
    org: str = ctx.obj["org"]
    console = Console()

    table = Table(
        title="Open Pull Requests",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("PR", no_wrap=True)
    table.add_column("Title", overflow="ellipsis")
    table.add_column("Author")
    table.add_column("Created")
    data: list[dict[str, Any]] = []

    exclude_patterns = [re.compile(pattern) for pattern in exclude_author]
    include_patterns = [re.compile(pattern) for pattern in author]

    older_than_date: datetime | None = (
        datetime.now(tz=UTC) - parse_duration(older_than) if older_than else None
    )
    newer_than_date: datetime | None = (
        datetime.now(tz=UTC) - parse_duration(newer_than) if newer_than else None
    )

    for repo in remote_repositories(
        org,
        forks=include_forks,
        archived=include_archived,
    ):
        logger.info("Fetching PRs for repository: %s", repo.name)

        for pr in repo.get_pulls(state="open", sort="created"):
            if not include_drafts and pr.draft:
                logger.info("Excluding draft PR #%s", pr.number)
                continue

            if any(pattern.search(pr.user.login) for pattern in exclude_patterns):
                logger.info("Excluding PR #%s by author: %s", pr.number, pr.user.login)
                continue

            if author and not any(
                pattern.search(pr.user.login) for pattern in include_patterns
            ):
                logger.info(
                    "Excluding PR #%s by author not matching: %s",
                    pr.number,
                    pr.user.login,
                )
                continue

            if older_than_date and pr.created_at > older_than_date:
                logger.info("Excluding PR #%s created after older-than date", pr.number)
                continue

            if newer_than_date and pr.created_at < newer_than_date:
                logger.info(
                    "Excluding PR #%s created before newer-than date", pr.number
                )
                continue

            data.append({
                "number": pr.number,
                "repo": pr.base.repo.full_name,
                "title": pr.title,
                "author": pr.user.login,
                "created_at": pr.created_at,
            })

    data.sort(key=lambda x: x["created_at"], reverse=True)
    for row in data:
        table.add_row(
            f"{row['repo']}#{row['number']}",
            row["title"],
            row["author"],
            row["created_at"].strftime("%Y-%m-%d"),
        )

    console.print(table)
