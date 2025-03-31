"""
Simple subcommand to display the current version of the application.
"""

import click

from repo_manage.__version__ import __version__
from repo_manage.cli import main


@main.command()
def version() -> None:
    """
    Display the current version of the application.
    """
    click.echo(f"Repo Manage version: {__version__}")
