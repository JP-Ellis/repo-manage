"""
Subcommand for updating repositories.
"""

import logging
import subprocess
from typing import TYPE_CHECKING

import rich_click as click

from repo_manage.util import find_executable, local_repositories

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
def update(ctx: click.Context) -> None:
    """
    Update all local repositories.

    This command goes through all local repositories, checks out the default
    branch, and pulls the latest updates. If any step fails, it logs a warning
    and continues with the next repository.
    """
    local: Path = ctx.obj["local"]
    git_exec = find_executable("git")
    gh_exec = find_executable("gh")
    stream_output = logger.getEffectiveLevel() <= logging.DEBUG

    for repo_dir in local_repositories(local):
        logger.info("Updating repository: %s", repo_dir.name)

        try:
            default_branch = subprocess.check_output(  # noqa: S603
                [
                    gh_exec,
                    "repo",
                    "view",
                    "--json",
                    "defaultBranchRef",
                    "--jq",
                    ".defaultBranchRef.name",
                ],
                cwd=repo_dir,
                text=True,
                stderr=None if stream_output else subprocess.PIPE,
            ).strip()
        except subprocess.CalledProcessError as e:
            logger.warning(
                "Failed to fetch default branch for %s: %s",
                repo_dir.name,
                e,
            )
            if e.stderr:
                logger.exception("Error output: %s", e.stderr)
            continue

        try:
            subprocess.check_call(  # noqa: S603
                [git_exec, "checkout", default_branch],
                cwd=repo_dir,
                text=True,
                stdout=None if stream_output else subprocess.PIPE,
                stderr=None if stream_output else subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to checkout branch of %s: %s", repo_dir.name, e)
            if e.stderr:
                logger.exception("Error output: %s", e.stderr)
            continue

        try:
            subprocess.check_call(  # noqa: S603
                [git_exec, "pull"],
                cwd=repo_dir,
                text=True,
                stdout=None if stream_output else subprocess.PIPE,
                stderr=None if stream_output else subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            logger.warning(
                "Failed to pull updates for repository %s: %s",
                repo_dir.name,
                e,
            )
            if e.stderr:
                logger.exception("Error output: %s", e.stderr)
            continue
