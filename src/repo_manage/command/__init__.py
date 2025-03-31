"""
Subcommands for repo_manage.

Each module in this package should contain a single subcommand for the
repo_manage command line interface (CLI). The subcommands should be implemented
as functions decorated with the `@click.command()` decorator and need to be
registered with the main command in the `src/repo_manage/cli.py` file.
"""

from repo_manage.command.list import list  # noqa: A004
from repo_manage.command.version import version

__all__ = [
    "list",
    "version",
]
