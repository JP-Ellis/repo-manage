"""
CLI entry point for the repo_manage.
"""

import logging
from pathlib import Path

import rich_click as click
from rich.logging import RichHandler

logger = logging.getLogger(__name__)


def setup_logging(verbose: int, quiet: int) -> None:
    """
    Set up logging for the application.

    Args:
        verbose:
            The verbosity level. Higher values indicate more verbose output.

        quiet:
            The quietness level. Higher values indicate less output.
    """
    level = logging.WARNING - (verbose - quiet) * 10
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    logger.debug("Debug logging enabled.")


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Increase verbosity.")
@click.option("-q", "--quiet", is_flag=True, help="Decrease verbosity.")
@click.option(
    "--org",
    type=str,
    help="""
    The organization name to use for the repo.

    If not provided, this will assume that the current directory name is the
    organization name.
    """,
    default=Path.cwd().name,
)
@click.option(
    "--local",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="""
    The local directory to use for the org/collection of repos.

    If not provided, this will assume that the current directory contains the
    collection of repos.
    """,
    default=Path.cwd(),
)
@click.pass_context
def main(
    ctx: click.Context,
    *,
    verbose: int,
    quiet: int,
    org: str,
    local: Path,
) -> None:
    """
    repo-manage.

    A command line tool to manage your repositories.

    This tool is designed to help you manage your repositories more efficiently.
    It provides a set of commands to create, delete, and manage repositories on
    GitHub.
    """
    setup_logging(verbose, quiet)

    ctx.ensure_object(dict)
    ctx.obj["org"] = org
    ctx.obj["local"] = local


import repo_manage.command  # noqa: E402

main.add_command(repo_manage.command.version)
