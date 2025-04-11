"""
Executes a command in all local repositories.
"""

import logging
import subprocess
from typing import TYPE_CHECKING, Any

import click

from repo_manage.util import local_repositories

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class DoubleDashCommand(click.Command):
    """
    Custom Click command to handle double dash arguments.

    This class is used to parse command-line arguments and handle the
    special case of double dash arguments. The double dash is used to
    separate arguments for the current command from any arguments to be passed
    to child commands.
    """

    def __init__(
        self,
        arg_name: str = "double_dash_args",
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """
        Initialize the command with a custom argument name.

        Args:
            arg_name:
                The name of the argument to store double dash arguments. This
                should be a keyword argument of the underlying function.

            *args:
                Positional arguments to pass to the parent class.

            **kwargs:
                Keyword arguments to pass to the parent class.
        """
        self.arg_name = arg_name
        super().__init__(*args, **kwargs)

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """
        Parse arguments after the double dash.
        """
        if "--" in args:
            index = args.index("--")
            args, command = args[:index], args[index + 1 :]
            ctx.params[self.arg_name] = tuple(command)

        return super().parse_args(ctx, args)


@click.command(cls=DoubleDashCommand, name="exec", arg_name="double_dash_args")
@click.option(
    "--capture",
    is_flag=True,
    help="Capture output of each command and print only if it fails.",
)
@click.option(
    "--check/--no-check",
    default=True,
    help="Check if each command exits successfully. If --no-check is given, "
    "the commands will be executed without checking the return code.",
)
@click.pass_context
def exec_cmd(
    ctx: click.Context,
    double_dash_args: tuple[str, ...],
    *,
    check: bool,
    capture: bool,
) -> None:
    r"""
    Run a command in all local repositories.

    This command will run the specified command (as specified after the double
    dash `--`) in all local repositories. Multiple commands can be executed by
    separating them with a `;` character (which will typically need to be
    escaped in the shell):

    ```console
    $ repo-manage exec -- ls -l \; pwd
    ```

    By default, all output is printed to the console. If you want to capture the
    output, you can use the `--capture` flag. This will capture the output of
    each command and only print the output if the command fails.

    The commands are executed from the root of each repository.
    """
    local: Path = ctx.obj.get("local")

    commands: list[tuple[str, ...]] = []
    while ";" in double_dash_args:
        idx = double_dash_args.index(";")
        command, double_dash_args = double_dash_args[:idx], double_dash_args[idx + 1 :]
        commands.append(command)
    commands.append(double_dash_args)

    for repo in local_repositories(local):
        logger.info("Executing in %s", repo)

        for command in commands:
            logger.info("Command: %s", " ".join(command))

            if capture:
                result = subprocess.run(  # noqa: S603
                    command,
                    cwd=repo,
                    check=check,
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    if check:
                        raise subprocess.CalledProcessError(
                            result.returncode,
                            command,
                            output=result.stdout,
                            stderr=result.stderr,
                        )
                    logger.error("Return code: %s", result.returncode)
                    logger.error("Stdout:\n%s", result.stdout)
                    logger.error("Stderr:\n%s", result.stderr)
                    continue

                logger.info("Stdout:\n%s", result.stdout)
                logger.info("Stderr:\n%s", result.stderr)

            else:
                subprocess.run(command, cwd=repo, check=check)  # noqa: S603
