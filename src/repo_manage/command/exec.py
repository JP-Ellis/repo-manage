"""
Executes a command in all local repositories.
"""

from __future__ import annotations

import logging
import subprocess
from abc import ABC, abstractmethod
from itertools import groupby
from typing import TYPE_CHECKING, Any, NamedTuple

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


class CmdResult(NamedTuple):
    """
    Represents the result of a command execution.
    """

    exit_code: int
    """
    The exit code of the command, or group of commands.
    """
    stdout: str | None
    """
    The standard output of the command, or group of commands.

    If `capture` is set to `False`, this will be `None`.
    """
    stderr: str | None
    """
    The standard error output of the command, or group of commands.
    If `capture` is set to `False`, this will be `None`.
    """


class Cmd(ABC):
    """
    Base class for representing a command.
    """

    @abstractmethod
    def execute(self, cwd: Path, *, check: bool, capture: bool) -> CmdResult:
        """
        Execute the command in the given directory.

        Args:
            cwd:
                The directory to execute the command in.

            check:
                If True, check if the command exits successfully.

            capture:
                If True, capture the output of the command.

        Returns:
            The result of the command execution.
        """

    def append(self, other: Cmd) -> Cmd:
        """
        Append another command to this command.

        This will try and preserve the type of the command and returns a new
        command, unless it does not make sense to do so. A `CmdSequence` always
        takes precedence over any other type.
        """
        if isinstance(self, CmdSequence) or isinstance(other, CmdSequence):
            return CmdSequence(self, other)

        if isinstance(self, CmdSingle) and isinstance(other, CmdSingle):
            return CmdSequence(self, other)

        if isinstance(self, CmdSingle):
            return other.__class__(self, other)  # type: ignore[call-arg]

        return self.__class__(self, other)  # type: ignore[call-arg]

    @classmethod
    def parse(cls, args: list[str]) -> Cmd:  # noqa: C901, PLR0912, PLR0915
        """
        Parse the command line arguments and return a Cmd object.

        This method parses the list of arguments and creates a final `Cmd`
        object. It parses groups of commands separated by `;`, `&&`, or `||` and
        creates the appropriate `Cmd` object for each group.

        Just as with shells, commands can be grouped by either parentheses (`(` and
        `)`) or braces (`{` and `}`).

        Args:
            args:
                The command line arguments to parse.

        Returns:
            A Cmd object representing the command.
        """
        if not args:
            msg = "No command provided."
            raise ValueError(msg)

        idx = 0
        current_args: list[str] = []
        stack: list[Cmd] = []

        while idx < len(args):
            arg = args[idx]

            if arg == "(":
                if current_args:
                    msg = "Unexpected argument before opening parenthesis."
                    raise ValueError(msg)

                if ")" not in args[idx + 1 :]:
                    msg = "Unmatched opening parenthesis."
                    raise ValueError(msg)
                end_idx = args.index(")", idx + 1)
                stack.append(cls.parse(args[idx + 1 : end_idx]))
                idx = end_idx + 1

            elif arg == "{":
                if current_args:
                    msg = "Unexpected argument before opening brace."
                    raise ValueError(msg)

                if "}" not in args[idx + 1 :]:
                    msg = "Unmatched opening brace."
                    raise ValueError(msg)
                end_idx = args.index("}", idx + 1)
                stack.append(cls.parse(args[idx + 1 : end_idx]))
                idx = end_idx + 1

            elif arg in (")", "}"):
                msg = "Unmatched closing parenthesis or brace."
                raise ValueError(msg)

            elif arg == ";":
                if current_args:
                    stack.append(CmdSingle(*current_args))
                    current_args.clear()
                idx += 1
                stack.append(CmdSequence())

            elif arg == "||":
                if current_args:
                    stack.append(CmdSingle(*current_args))
                    current_args.clear()
                idx += 1
                stack.append(CmdOr())

            elif arg == "&&":
                if current_args:
                    stack.append(CmdSingle(*current_args))
                    current_args.clear()
                idx += 1
                stack.append(CmdAnd())

            else:
                current_args.append(arg)
                idx += 1

        if current_args:
            stack.append(CmdSingle(*current_args))
            current_args.clear()

        if len(stack) == 0:
            msg = "No command provided."
            raise ValueError(msg)

        # The 'CmdSequence' has the lowest precedence, so we split the stack at
        # the delimiters, and then join the result together.
        substacks = [
            list(substack)
            for _, substack in groupby(stack, key=lambda x: isinstance(x, CmdSequence))
        ]

        for substack in substacks:
            while len(substack) > 1:
                last = substack.pop()
                substack[-1] = substack[-1].append(last)

        if len(substacks) == 1:
            return substacks[0][0]

        return CmdSequence(*[substack[0] for substack in substacks])


class CmdSingle(Cmd):
    """
    Represents a single command.
    """

    def __init__(self, *command: str) -> None:
        """
        Initialize the command.

        Args:
            command:
                The command to execute. This should be a sequence of strings
                representing the command and its arguments.
        """
        self.command = command

    def __repr__(self) -> str:
        """
        Return a string representation of the command.
        """
        return f"CmdSingle({' '.join(self.command)})"

    def __str__(self) -> str:
        """
        Return a string representation of the command.
        """
        return " ".join(self.command)

    def execute(self, cwd: Path, *, check: bool, capture: bool) -> CmdResult:  # noqa: D102
        logger.debug("Executing command: %s", self.command)
        result = subprocess.run(  # noqa: S603
            self.command,
            cwd=cwd,
            check=check,
            capture_output=capture,
            text=True,
        )
        return CmdResult(
            exit_code=result.returncode,
            stdout=result.stdout if capture else None,
            stderr=result.stderr if capture else None,
        )


class CmdSequence(Cmd):
    """
    Represents a sequence of commands separated by `;`.

    All commands in the sequence are executed in order, irrespective of the
    success of the previous commands. The final exit code is the exit code of
    the last command in the sequence.

    If output is captured, the combined standard output and standard error of all
    commands is returned.
    """

    def __init__(self, *command: Cmd) -> None:
        """
        Initialize the command.

        Args:
            command:
                The commands to execute. This should be a sequence of strings
                representing the command and its arguments.
        """
        self.command: list[Cmd] = []
        for cmd in command:
            if not isinstance(cmd, Cmd):
                msg = "Command sequence must contain only Cmd objects."
                raise TypeError(msg)

            if isinstance(cmd, CmdSequence):
                self.command.extend(cmd.command)

            else:
                self.command.append(cmd)

    def __repr__(self) -> str:
        """
        Return a string representation of the command.
        """
        return f"CmdSequence({', '.join(str(cmd) for cmd in self.command)})"

    def __str__(self) -> str:
        """
        Return a string representation of the command.
        """
        return " ; ".join(f"({cmd})" for cmd in self.command)

    def execute(self, cwd: Path, *, check: bool, capture: bool) -> CmdResult:  # noqa: D102
        results = [
            cmd.execute(cwd, check=check, capture=capture) for cmd in self.command
        ]

        return CmdResult(
            exit_code=results[-1].exit_code,
            stdout="\n######\n".join(result.stdout or "" for result in results)
            if capture
            else None,
            stderr="\n######\n".join(result.stderr or "" for result in results)
            if capture
            else None,
        )


class CmdOr(Cmd):
    """
    Represents commands separated by `||`.

    The commands are executed in order, stopping at the first command that
    succeeds. The final exit code is the exit code of the last executed command.

    If output is captured, the combined standard output and standard error of
    all commands is returned.
    """

    def __init__(self, *command: Cmd) -> None:
        """
        Initialize the command.

        Args:
            command:
                The commands to execute. This should be a sequence of strings
                representing the command and its arguments.
        """
        self.command: list[Cmd] = []
        for cmd in command:
            if not isinstance(cmd, Cmd):
                msg = "Command sequence must contain only Cmd objects."
                raise TypeError(msg)

            if isinstance(cmd, CmdOr):
                self.command.extend(cmd.command)

            else:
                self.command.append(cmd)

    def __repr__(self) -> str:
        """
        Return a string representation of the command.
        """
        return f"CmdOr({', '.join(str(cmd) for cmd in self.command)})"

    def __str__(self) -> str:
        """
        Return a string representation of the command.
        """
        return " || ".join(f"({cmd})" for cmd in self.command)

    def execute(self, cwd: Path, *, check: bool, capture: bool) -> CmdResult:  # noqa: D102
        results: list[CmdResult] = []
        for cmd in self.command:
            result = cmd.execute(cwd, check=check, capture=capture)
            results.append(result)

            if result.exit_code == 0:
                break

        return CmdResult(
            exit_code=results[-1].exit_code,
            stdout="\n######\n".join(result.stdout or "" for result in results)
            if capture
            else None,
            stderr="\n######\n".join(result.stderr or "" for result in results)
            if capture
            else None,
        )


class CmdAnd(Cmd):
    """
    Represents commands separated by `&&`.

    The commands are executed in order, stopping at the first command that
    fails. The final exit code is the exit code of the last executed command.

    If output is captured, the combined standard output and standard error of
    all commands is returned.
    """

    def __init__(self, *command: Cmd) -> None:
        """
        Initialize the command.

        Args:
            command:
                The commands to execute. This should be a sequence of strings
                representing the command and its arguments.
        """
        self.command: list[Cmd] = []
        for cmd in command:
            if not isinstance(cmd, Cmd):
                msg = "Command sequence must contain only Cmd objects."
                raise TypeError(msg)

            if isinstance(cmd, CmdAnd):
                self.command.extend(cmd.command)

            else:
                self.command.append(cmd)

    def __repr__(self) -> str:
        """
        Return a string representation of the command.
        """
        return f"CmdAnd({', '.join(str(cmd) for cmd in self.command)})"

    def __str__(self) -> str:
        """
        Return a string representation of the command.
        """
        return " && ".join(f"({cmd})" for cmd in self.command)

    def execute(self, cwd: Path, *, check: bool, capture: bool) -> CmdResult:  # noqa: D102
        results: list[CmdResult] = []
        for cmd in self.command:
            result = cmd.execute(cwd, check=check, capture=capture)
            results.append(result)

            if result.exit_code != 0:
                break

        return CmdResult(
            exit_code=results[-1].exit_code,
            stdout="\n######\n".join(result.stdout or "" for result in results)
            if capture
            else None,
            stderr="\n######\n".join(result.stderr or "" for result in results)
            if capture
            else None,
        )


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
    dash `--`) in all local repositories.

    Multiple commands can be specified, separated by `;`, `&&`, or `||`
    (following the same rules as in shell commands). Commands can also be
    grouped using parentheses `(` and `)` or braces `{` and `}` (both are
    interpreted the same way and do not imply subshell execution or the like).

    By default, all output is printed to the console. If you want to capture the
    output, you can use the `--capture` flag. This will capture the output of
    each command and only print the output if the command fails.

    By default `--check` is enabled which will abort the execution in subsequent
    repositories if the exit code of a command (or group of commands) is not 0.

    Note that in this context, `;` is treated as a command separator and not as
    a logical operator and will execute all commands in the sequence, returning
    the exit code of the last command only. If you want to ensure that all
    commands in the sequence are executed successfully, use `&&` instead.
    """
    local: Path = ctx.obj.get("local")

    command = Cmd.parse(list(double_dash_args))

    for repo in local_repositories(local):
        logger.info("Executing in %s", repo)

        logger.debug("Command: %s", command)
        result = command.execute(repo, check=check, capture=capture)
        logger.info("Return code: %s", result.exit_code)
        if result.stdout:
            logger.info("Stdout:\n%s", result.stdout)
        if result.stderr:
            logger.info("Stderr:\n%s", result.stderr)

        if check and result.exit_code != 0:
            logger.error("Command failed, aborting.")
            break
