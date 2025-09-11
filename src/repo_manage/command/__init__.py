"""
Subcommands for repo_manage.

Each module in this package should contain a single subcommand for the
repo_manage command line interface (CLI). The subcommands should be implemented
as functions decorated with the `@click.command()` decorator and need to be
registered with the main command in the `src/repo_manage/cli.py` file.
"""

from repo_manage.command.clone import clone
from repo_manage.command.events import events
from repo_manage.command.exec import exec_cmd
from repo_manage.command.list import list_cmd, list_prs
from repo_manage.command.update import update
from repo_manage.command.version import version

__all__ = [
    "clone",
    "events",
    "exec_cmd",
    "list_cmd",
    "list_prs",
    "update",
    "version",
]
