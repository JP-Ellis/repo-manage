"""
Subcommand for updating repositories.
"""

import logging
import shutil
import subprocess
from typing import TYPE_CHECKING

import rich_click as click

from repo_manage.util import local_repositories

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

    if not (git_exec := shutil.which("git")):
        logger.error("Git executable not found.")
        ctx.exit(1)

    if not (gh_exec := shutil.which("gh")):
        logger.error("GitHub CLI (gh) executable not found.")
        ctx.exit(1)

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
            ).strip()
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to fetch default branch: %s", e)
            continue

        try:
            subprocess.check_call(  # noqa: S603
                [git_exec, "checkout", default_branch],
                cwd=repo_dir,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to checkout branch %s: %s", default_branch, e)
            continue

        try:
            subprocess.check_call(  # noqa: S603
                [git_exec, "pull"],
                cwd=repo_dir,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.warning(
                "Failed to pull updates for repository %s: %s", repo_dir.name, e
            )
            continue
