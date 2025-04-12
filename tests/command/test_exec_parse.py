import pytest

from repo_manage.command.exec import Cmd, CmdAnd, CmdOr, CmdSequence, CmdSingle


def test_parse_single() -> None:
    cmd = Cmd.parse(["echo", "hello"])
    assert isinstance(cmd, CmdSingle)
    assert cmd.command == ("echo", "hello")


def test_parse_sequence() -> None:
    cmd = Cmd.parse(["echo", "hello", ";", "echo", "world"])
    assert isinstance(cmd, CmdSequence)
    assert len(cmd.command) == 2
    assert isinstance(cmd.command[0], CmdSingle)
    assert cmd.command[0].command == ("echo", "hello")
    assert isinstance(cmd.command[1], CmdSingle)
    assert cmd.command[1].command == ("echo", "world")


def test_parse_and() -> None:
    cmd = Cmd.parse(["echo", "hello", "&&", "echo", "world"])
    assert isinstance(cmd, CmdAnd)
    assert len(cmd.command) == 2
    assert isinstance(cmd.command[0], CmdSingle)
    assert cmd.command[0].command == ("echo", "hello")
    assert isinstance(cmd.command[1], CmdSingle)
    assert cmd.command[1].command == ("echo", "world")


def test_parse_and_and() -> None:
    cmd = Cmd.parse(["echo", "hello", "&&", "echo", "world", "&&", "echo", "!"])
    assert isinstance(cmd, CmdAnd)
    assert len(cmd.command) == 3
    assert isinstance(cmd.command[0], CmdSingle)
    assert cmd.command[0].command == ("echo", "hello")
    assert isinstance(cmd.command[1], CmdSingle)
    assert cmd.command[1].command == ("echo", "world")
    assert isinstance(cmd.command[2], CmdSingle)
    assert cmd.command[2].command == ("echo", "!")


def test_parse_or() -> None:
    cmd = Cmd.parse(["echo", "hello", "||", "echo", "world"])
    assert isinstance(cmd, CmdOr)
    assert len(cmd.command) == 2
    assert isinstance(cmd.command[0], CmdSingle)
    assert cmd.command[0].command == ("echo", "hello")
    assert isinstance(cmd.command[1], CmdSingle)
    assert cmd.command[1].command == ("echo", "world")


def test_parse_or_or() -> None:
    cmd = Cmd.parse(["echo", "hello", "||", "echo", "world", "||", "echo", "!"])
    assert isinstance(cmd, CmdOr)
    assert len(cmd.command) == 3
    assert isinstance(cmd.command[0], CmdSingle)
    assert cmd.command[0].command == ("echo", "hello")
    assert isinstance(cmd.command[1], CmdSingle)
    assert cmd.command[1].command == ("echo", "world")
    assert isinstance(cmd.command[2], CmdSingle)
    assert cmd.command[2].command == ("echo", "!")


def test_parse_and_or() -> None:
    cmd = Cmd.parse(["echo", "hello", "&&", "echo", "world", "||", "echo", "!"])
    assert isinstance(cmd, CmdAnd)
    assert len(cmd.command) == 2
    assert isinstance(cmd.command[0], CmdSingle)
    assert cmd.command[0].command == ("echo", "hello")
    assert isinstance(cmd.command[1], CmdOr)
    assert len(cmd.command[1].command) == 2
    assert isinstance(cmd.command[1].command[0], CmdSingle)
    assert cmd.command[1].command[0].command == ("echo", "world")
    assert isinstance(cmd.command[1].command[1], CmdSingle)
    assert cmd.command[1].command[1].command == ("echo", "!")


def test_parse_or_and() -> None:
    cmd = Cmd.parse(["echo", "hello", "||", "echo", "world", "&&", "echo", "!"])
    assert isinstance(cmd, CmdOr)
    assert len(cmd.command) == 2
    assert isinstance(cmd.command[0], CmdSingle)
    assert cmd.command[0].command == ("echo", "hello")
    assert isinstance(cmd.command[1], CmdAnd)
    assert len(cmd.command[1].command) == 2
    assert isinstance(cmd.command[1].command[0], CmdSingle)
    assert cmd.command[1].command[0].command == ("echo", "world")
    assert isinstance(cmd.command[1].command[1], CmdSingle)
    assert cmd.command[1].command[1].command == ("echo", "!")


def test_parse_nested_parenthesis() -> None:
    cmd = Cmd.parse(["hello", "&&", "(", "foo", "||", "bar", ")", ";", "done"])

    assert isinstance(cmd, CmdSequence)
    assert len(cmd.command) == 2

    assert isinstance(cmd.command[0], CmdAnd)
    assert len(cmd.command[0].command) == 2

    assert isinstance(cmd.command[0].command[0], CmdSingle)
    assert cmd.command[0].command[0].command == ("hello",)

    assert isinstance(cmd.command[0].command[1], CmdOr)
    assert len(cmd.command[0].command[1].command) == 2

    assert isinstance(cmd.command[0].command[1].command[0], CmdSingle)
    assert cmd.command[0].command[1].command[0].command == ("foo",)

    assert isinstance(cmd.command[0].command[1].command[1], CmdSingle)
    assert cmd.command[0].command[1].command[1].command == ("bar",)

    assert isinstance(cmd.command[1], CmdSingle)
    assert cmd.command[1].command == ("done",)


def test_parse_nested_braces() -> None:
    cmd = Cmd.parse(["hello", "&&", "{", "foo", "||", "bar", "}", ";", "done"])

    assert isinstance(cmd, CmdSequence)
    assert len(cmd.command) == 2

    assert isinstance(cmd.command[0], CmdAnd)
    assert len(cmd.command[0].command) == 2

    assert isinstance(cmd.command[0].command[0], CmdSingle)
    assert cmd.command[0].command[0].command == ("hello",)

    assert isinstance(cmd.command[0].command[1], CmdOr)
    assert len(cmd.command[0].command[1].command) == 2

    assert isinstance(cmd.command[0].command[1].command[0], CmdSingle)
    assert cmd.command[0].command[1].command[0].command == ("foo",)

    assert isinstance(cmd.command[0].command[1].command[1], CmdSingle)
    assert cmd.command[0].command[1].command[1].command == ("bar",)

    assert isinstance(cmd.command[1], CmdSingle)
    assert cmd.command[1].command == ("done",)


def test_parse_empty_command() -> None:
    with pytest.raises(ValueError, match="No command provided."):
        Cmd.parse([])


def test_parse_unmatched_group() -> None:
    with pytest.raises(ValueError, match="Unmatched opening parenthesis."):
        Cmd.parse(["echo", "hello", ";", "("])

    with pytest.raises(ValueError, match="Unmatched opening brace."):
        Cmd.parse(["echo", "hello", ";", "{"])

    with pytest.raises(ValueError, match="Unmatched closing parenthesis or brace."):
        Cmd.parse(["echo", "hello", ")"])

    with pytest.raises(ValueError, match="Unmatched closing parenthesis or brace."):
        Cmd.parse(["echo", "hello", "}"])


def test_parse_arg_before_group() -> None:
    with pytest.raises(ValueError, match="Unexpected argument before opening brace."):
        Cmd.parse(["echo", "hello", "{"])

    with pytest.raises(
        ValueError, match="Unexpected argument before opening parenthesis."
    ):
        Cmd.parse(["echo", "hello", "("])
