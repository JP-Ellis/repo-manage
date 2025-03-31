# Repo Manage

<!-- markdownlint-disable MD033 -->
<div align="center"><table>
    <tr>
        <td>CI/CD</td>
        <td>
            <a href="https://github.com/JP-Ellis/repo-manage/actions/workflows/test.yml"><img
                alt="Workflow status badge"
                src="https://github.com/JP-Ellis/repo-manage/actions/workflows/test.yml/badge.svg"></a>
    </tr>
    <tr>
        <td>Meta</td>
        <td>
            <a
                href="https://github.com/pypa/hatch"><img
                src="https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg"
                alt="Hatch project"></a>
            <a href="https://github.com/astral-sh/ruff"><img
                src="https://img.shields.io/badge/ruff-ruff?label=linting&color=%23261230"
                alt="linting - Ruff"></a>
            <a href="https://github.com/astral-sh/ruff"><img
                src="https://img.shields.io/badge/ruff-ruff?label=style&color=%23261230"
                alt="style - Ruff"></a>
            <a
                href="https://github.com/python/mypy"><img
                src="https://img.shields.io/badge/types-Mypy-blue.svg"
                alt="types - Mypy"></a>
            <a
                href="https://github.com/JP-Ellis/repo-manage/blob/main/LICENSE"><img
                src="https://img.shields.io/github/license/JP-Ellis/repo-manage"
                alt="License"></a>
        </td>
    </tr>
</table></div>
<!-- markdownlint-enable MD033 -->

Repo Manage is a Python package designed to simplify the management of multiple repositories within a GitHub organization. It provides functionality to clone, update, and perform certain operations on repositories.

## Development

This project uses [Hatch](https://github.com/pypa/hatch) for managing the development environment. If you have `direnv` installed, it should automatically discover the `.envrc` file and activate the virtual environment.

To run tests for all supported Python versions, use the following command:

```console
hatch run test:test
```

which executes the `test` script defined in the `pyproject.toml` file within all the environments defined in the `test` matrix.
