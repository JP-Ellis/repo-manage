"""
Subcommand for cloning repositories.
"""

import logging
import subprocess
from typing import TYPE_CHECKING

import rich_click as click

from repo_manage.util import find_executable, remote_repositories

if TYPE_CHECKING:
    from pathlib import Path

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
    org: str = ctx.obj["org"]
    local: Path = ctx.obj["local"]
    gh_exec = find_executable("gh")
    stream_output = logger.getEffectiveLevel() <= logging.DEBUG

    for repo in remote_repositories(org, forks=forks, archived=archived):
        repo_dir = local / repo.name
        if repo_dir.exists():
            logger.info("Skipping existing repository: %s", repo.name)
            continue

        logger.info("Cloning repository: %s", repo.name)
        try:
            subprocess.check_call(  # noqa: S603
                [gh_exec, "repo", "clone", repo.full_name, str(repo_dir)],
                text=True,
                stdout=None if stream_output else subprocess.PIPE,
                stderr=None if stream_output else subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            if not stream_output:
                logger.exception("Error output: %s", e.stderr)
            logger.exception("Failed to clone repository %s", repo.name)
            ctx.exit(1)
