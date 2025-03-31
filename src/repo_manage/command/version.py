"""
Subcommand to display the current version of the application.
"""

import rich_click as click

from repo_manage.__version__ import __version__


@click.command()
def version() -> None:
    """
    Display the current version of the application.
    """
    click.echo(f"Repo Manage version: {__version__}")
