"""
Subcommand for listing repositories.
"""

import logging

import rich_click as click

from repo_manage.util import local_repositories, remote_repositories

logger = logging.getLogger(__name__)


@click.command(name="list")
@click.option(
    "--local",
    is_flag=True,
    help="List local repositories.",
)
@click.option(
    "--remote",
    is_flag=True,
    help="List remote repositories.",
)
@click.pass_context
def list_cmd(
    ctx: click.Context,
    *,
    local: bool,
    remote: bool,
) -> None:
    """
    List repositories.

    This command lists all repositories in the specified organization or
    directory.
    """
    if not local and not remote:
        logger.error("Please specify either --local or --remote.")
        ctx.exit(1)

    if local:
        for repo_path in local_repositories(ctx.obj["local"]):
            click.echo(repo_path.relative_to(ctx.obj["local"]))

    if remote:
        for repo in remote_repositories(ctx.obj["org"]):
            if repo.fork:
                click.echo(repo.full_name + " (fork of: " + repo.parent.full_name + ")")
            else:
                click.echo(repo.full_name)
