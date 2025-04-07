"""
Subcommand for cloning repositories.
"""

import logging
import subprocess
from pathlib import Path

import rich_click as click

from repo_manage.util import find_executable, remote_repositories

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--forks",
    is_flag=True,
    help="Include forked repositories.",
)
@click.option(
    "--archived",
    is_flag=True,
    help="Include archived repositories.",
)
@click.pass_context
def clone(
    ctx: click.Context,
    *,
    forks: bool,
    archived: bool,
) -> None:
    """
    Clone repositories.

    This command clones all repositories from the specified organization or
    user into the current directory. Existing repositories are skipped.
    """
    org = ctx.obj["org"]
    current_dir = Path.cwd()
    gh_exec = find_executable("gh")

    for repo in remote_repositories(org, forks=forks, archived=archived):
        repo_dir = current_dir / repo.name
        if repo_dir.exists():
            logger.info("Skipping existing repository: %s", repo.name)
            continue

        logger.info("Cloning repository: %s", repo.name)
        try:
            subprocess.check_call(  # noqa: S603
                [gh_exec, "repo", "clone", repo.full_name, str(repo_dir)],
                text=True,
            )
        except subprocess.SubprocessError:
            logger.exception("Failed to clone repository %s", repo.name)
            ctx.exit(1)
