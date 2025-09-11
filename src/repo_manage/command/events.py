"""
Subcommand for listing events.
"""

import logging
import re
import sys
import typing
from datetime import UTC, datetime
from pathlib import Path

import rich_click as click
from click.core import ParameterSource
from github import UnknownObjectException
from github.AuthenticatedUser import AuthenticatedUser
from github.Event import Event
from isodate import parse_duration
from rich.console import Console
from rich.table import Table

from repo_manage.util import GITHUB

logger = logging.getLogger(__name__)


def get_explicit_arg(ctx: click.Context, param: str) -> str | None:
    """
    Get the explicit argument for a parameter in the context.
    """
    if ctx.get_parameter_source(param) is ParameterSource.COMMANDLINE:
        return ctx.params.get(param)
    return None


@click.command()
@click.option(
    "--newer-than",
    type=str,
    default="P7D",
    show_default=True,
    help="Filter PRs newer than the given ISO 8601 duration.",
)
@click.pass_context
def events(ctx: click.Context, newer_than: str) -> None:
    """
    List events for the current organization or repository.

    This command inspects the current directory to determine if it is in a
    repository, or an org/user directory containing multiple repositories.

    In this context, `--local` can be used to specify a local directory which
    will be used to find the or
    """
    parent_ctx = ctx.parent
    if parent_ctx is None:
        logger.error("Missing parent context")
        ctx.exit(1)

    org = get_explicit_arg(parent_ctx, "org")
    local = get_explicit_arg(parent_ctx, "local")
    cutoff_dt = typing.cast(
        "datetime", datetime.now(tz=UTC) - parse_duration(newer_than)
    )
    logger.debug("Using cutoff date %s for events", cutoff_dt.isoformat())

    if org and local:
        logger.error(
            "Both --org and --local cannot be provided as command line arguments"
        )

    if org:
        return list_org_events(org, cutoff_dt)

    local = local or Path.cwd()
    if (local / ".git").exists():
        # We are in a repo, so we need to get the org from the remote URL.
        org = local.resolve().parent.name
        return list_repo_events(org, local.name, cutoff_dt)
    return list_org_events(local.name, cutoff_dt)


def list_org_events(org_name: str, cutoff_dt: datetime) -> None:
    """
    List events from the organization.

    This uses the current auth token to list public and (accessible) private
    events from the organization.

    Args:
        org_name:
            The organization name to list events from.

        cutoff_dt:
            The cutoff datetime. Events older than this will not be shown.
    """
    console = Console()
    try:
        logger.debug("Getting organization %s", org_name)
        org = GITHUB.get_organization(org_name).name
    except UnknownObjectException:
        logger.debug("Getting user %s", org_name)
        org = GITHUB.get_user(org_name).name
    user = GITHUB.get_user()
    if not isinstance(user, AuthenticatedUser):
        logger.error("Not authenticated user")
        sys.exit(1)

    for event in user.get_organization_events(org):
        if event.created_at > cutoff_dt:
            console.print(event)
        else:
            return


def list_repo_events(org: str, repo_name: str, cutoff_dt: datetime) -> None:
    """
    List events from the repository.

    This uses the current auth token to list public and (accessible) private
    events from the repository.

    Args:
        org:
            The organization name to list events from.

        repo_name:
            The repository name to list events from.

        cutoff_dt:
            The duration to filter events by.
    """
    console = Console()
    table = Table(
        title="Events",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Created At")
    table.add_column("Actor")
    table.add_column("Type")
    table.add_column("Description", overflow="ellipsis")

    repo = GITHUB.get_repo(f"{org}/{repo_name}")
    events = repo.get_events()
    prev_dt = None
    for event in events:
        if event.created_at < cutoff_dt:
            return
        logger.debug("Event %s", event.payload)
        dt, actor, type, description = parse_event(event)

        table.add_row(
            show_dt_diff(dt, prev_dt),
            actor,
            type,
            description,
        )
        prev_dt = dt

    console.print(table)


def parse_event(event: Event) -> tuple[datetime, str, str, str]:  # noqa: C901, PLR0911, PLR0912
    """
    Parse an event into a tuple of values.

    Args:
        event:
            The event to parse.

    Returns:
        A tuple of values.
    """
    if event.type == "CommitCommentEvent":
        body = convert_markdown_to_bbcode(
            event.payload["comment"]["body"].split("\n")[0]
        )
        return (
            event.created_at,
            event.actor.login,
            event.type,
            body,
        )

    if event.type == "CreateEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"Created {event.payload['ref_type']} {event.payload['ref']}: "
            f"{event.payload['description'][:100]}",
        )

    if event.type == "DeleteEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"Deleted {event.payload['ref_type']} {event.payload['ref']}",
        )

    if event.type == "ForkEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"Forked {event.payload['forkee']['name']}",
        )

    if event.type == "GollumEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"Edited {event.payload['pages'][0]['page_name']}",
        )

    if event.type == "IssueCommentEvent":
        body = convert_markdown_to_bbcode(
            event.payload["comment"]["body"].split("\n")[0]
        )
        return (
            event.created_at,
            event.actor.login,
            event.type,
            body,
        )

    if event.type == "IssuesEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"{event.payload['action']} {event.payload['issue']['title']}",
        )

    if event.type == "MemberEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"{event.payload['action']} {event.payload['member']['login']}",
        )

    if event.type == "PublicEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            "Repository made public",
        )

    if event.type == "PullRequestEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"{event.payload['action']} {event.payload['pull_request']['title']}",
        )

    if event.type == "PullRequestReviewEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"Reviewed {event.payload['pull_request']['title']}",
        )

    if event.type == "PullRequestReviewEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"{event.payload['action']} {event.payload['pull_request']['title']}",
        )

    if event.type == "PullRequestReviewCommentEvent":
        body = convert_markdown_to_bbcode(
            event.payload["comment"]["body"].split("\n")[0]
        )
        return (
            event.created_at,
            event.actor.login,
            event.type,
            body,
        )

    if event.type == "PullRequestReviewThreadEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"{event.payload['action']} {event.payload['pull_request']['title']}",
        )

    if event.type == "PushEvent":
        # Show branch, number of commits, and a summary of the first commit message
        ref = event.payload["ref"]
        branch = "/".join(ref.split("/")[2:])
        size = event.payload["size"]
        commits = event.payload["commits"]
        first_msg = commits[0]["message"].split("\n")[0] if commits else None
        desc = (
            f"Pushed {size} commit{'s' if size != 1 else ''} "
            f"to [i]{branch}[/i]{': ' + first_msg if first_msg else ''}"
        )
        return (
            event.created_at,
            event.actor.login,
            event.type,
            desc,
        )

    if event.type == "ReleaseEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"Released {event.payload['release']['name']}",
        )

    if event.type == "SponsorshipEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"{event.payload['action']} "
            f"{event.payload['sponsorship']['sponsor']['login']}",
        )

    if event.type == "WatchEvent":
        return (
            event.created_at,
            event.actor.login,
            event.type,
            f"{event.payload['action']}",
        )

    msg = f"Event type {event.type} not implemented"
    raise NotImplementedError(msg)


def convert_markdown_to_bbcode(markdown: str) -> str:
    """
    Convert Markdown to BBCode.

    This only supports the `[text](url)` format, which is converted to
    `[url=url]text[/url]`.

    Args:
        markdown:
            The Markdown string to convert.

    Returns:
        The converted BBCode string.
    """
    markdown = markdown.strip()

    url_re = re.compile(r"\[(?P<text>.*?)\]\((?P<url>.*?)\)")
    while match := url_re.search(markdown):
        markdown = (
            markdown[: match.start()]
            + f"[url={match.group('url')}]"
            + match.group("text")
            + "[/url]"
            + markdown[match.end() :]
        )

    return markdown


def show_dt_diff(
    dt: datetime,
    prev_dt: datetime | None,
) -> str:
    """
    Display the new portions of the datetime.

    When displaying consecutive events, most of the datetime is the same and
    only the new portions are shown:

    ```
    2023-10-01T12:00:00Z
              T13:01:10Z
                  05:25Z
         11-21T12:00:00Z
    ```

    Args:
        dt:
            The datetime to show.

        prev_dt:
            The previous datetime to compare to.

    Returns:
        The formatted string.
    """
    if prev_dt is None:
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    if dt.year != prev_dt.year:
        len = 4 + 1
    elif dt.month != prev_dt.month:
        len = 4 + 1 + 2 + 1
    elif dt.day != prev_dt.day:
        len = 4 + 1 + 2 + 1 + 2 + 1
    elif dt.hour != prev_dt.hour:
        len = 4 + 1 + 2 + 1 + 2 + 1 + 2 + 1
    elif dt.minute != prev_dt.minute:
        len = 4 + 1 + 2 + 1 + 2 + 1 + 2 + 1 + 2 + 1
    else:
        return ""

    return " " * len + dt.strftime("%Y-%m-%dT%H:%M:%SZ")[len:]
