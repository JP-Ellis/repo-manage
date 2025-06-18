import os
import subprocess

import pytest


def pytest_configure(config: pytest.Config) -> None:  # noqa: ARG001
    """
    Configure pytest.

    This function is called before any tests are run to configure Pytest.

    We use this to set up the GitHub token so that we don't rely on repeated
    calls to the GitHub CLI during the tests.
    """
    if not os.getenv("GH_TOKEN") or not os.getenv("GITHUB_TOKEN"):
        os.environ["GITHUB_TOKEN"] = subprocess.check_output(
            ["gh", "auth", "token"],  # noqa: S607
            encoding="utf-8",
        ).strip()
