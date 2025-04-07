"""
Utility functions for the repo_manage package.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload

from github import Auth, Github, UnknownObjectException

if TYPE_CHECKING:
    from collections.abc import Generator

    from github.Repository import Repository

logger = logging.getLogger(__name__)


def github_token() -> str:
    """
    Get a GitHub token.

    This will try, in the following order:

    1.  The `GITHUB_TOKEN` environment variable,
    2.  The `GH_TOKEN` environment variable,
    3.  Generating a new token using the GitHub CLI.

    Returns:
        The GitHub token.
    """
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        logger.debug("Using GitHub token from environment variable.")
        return token

    # Generate a new token using the GitHub CLI
    if gh_cli := shutil.which("gh"):
        logger.debug("Generating a new GitHub token using the GitHub CLI.")
        return subprocess.check_output(  # noqa: S603
            [gh_cli, "auth", "token"], encoding="utf-8"
        ).strip()

    msg = (
        "No GitHub token found. "
        "Please set the GITHUB_TOKEN or GH_TOKEN environment variable."
    )
    raise ValueError(msg)


GITHUB = Github(auth=Auth.Token(github_token()))


def local_repositories(path: Path) -> Generator[Path]:
    """
    List all local repositories in the given path.

    This function searches for directories that contain a `.git` subdirectory,
    indicating that they are local Git repositories.

    Args:
        path:
            The path to search for local repositories.

    Yields:
        Paths to local repositories.
    """
    path = Path(path)
    if not path.is_dir():
        msg = f"Path {path} is not a directory."
        raise ValueError(msg)

    for item in sorted(path.iterdir()):
        if item.is_dir() and (item / ".git").exists():
            yield item


def remote_repositories(
    org: str,
    *,
    forks: bool = True,
    archived: bool = False,
) -> Generator[Repository]:
    """
    List all remote repositories in the given organization.

    This function uses the GitHub API to list all repositories in the
    specified organization.

    Args:
        org:
            The name of the organization.

        forks:
            Whether to include forked repositories.

        archived:
            Whether to include archived repositories.

    Yields:
        The repositories in the organization.
    """
    try:
        repos = GITHUB.get_organization(org).get_repos(type="all", sort="full_name")
    except UnknownObjectException:
        logger.debug("Organization %r not found, check if user.", org)
        try:
            repos = GITHUB.get_user(org).get_repos(type="all", sort="full_name")
        except UnknownObjectException:
            logger.error("Unable to find %r as user or organization.", org)  # noqa: TRY400
            sys.exit(1)

    # If we want both forks and archived, we can skip the check and yield all
    # repositories.
    if forks and archived:
        yield from repos
        return

    for repo in repos:
        if (not forks and repo.fork) or (not archived and repo.archived):
            continue

        yield repo


@overload
def find_executable(executable_name: str, *, raises: Literal[True] = True) -> str: ...
@overload
def find_executable(executable_name: str, *, raises: Literal[False]) -> str | None: ...
def find_executable(executable_name: str, *, raises: bool = True) -> str | None:
    """
    Locate an executable in the system PATH.

    Args:
        executable_name:
            The name of the executable to locate.

        raises:
            Whether to raise an exception if the executable is not found.
            If False, return None instead.

    Returns:
        The path to the executable.

    Raises:
        FileNotFoundError: If the executable is not found.
    """
    if path := shutil.which(executable_name):
        return path

    if raises:
        msg = f"Unable to find executable {executable_name!r}."
        raise FileNotFoundError(msg)
    return None
