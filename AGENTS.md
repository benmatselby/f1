# AGENTS.md

## Project overview

This is a Python CLI tool for viewing Formula 1 data (season schedules, race results, driver standings). It uses the [Fast-F1](https://github.com/theOehrly/Fast-F1) library for data and [Click](https://click.palletsprojects.com/) for the CLI framework.

## Language and runtime

- Python >= 3.14
- Package manager: [uv](https://docs.astral.sh/uv/)
- Build backend: setuptools with setuptools-scm

## Repository layout

```
f1/                     # Application package
  cli.py                # Click command group and entrypoint
  commands/             # CLI subcommands (season, race, drivers)
  helpers/              # Shared utilities (date formatting, output formatting)
tests/                  # Test suite (mirrors f1/ structure)
.github/workflows/      # CI pipeline (GitHub Actions)
Makefile                # Task runner
pyproject.toml          # Project metadata, dependencies, tool config
```

## Common commands

All commands are run via Make:

```sh
make install        # Install dependencies (uv sync --locked)
make lint           # Lint with Ruff
make lint-fix       # Lint and auto-fix with Ruff
make test           # Run tests with pytest
make test-cov       # Run tests with coverage report
make clean          # Remove generated files
```

## Coding conventions

- No classes in application code; commands and helpers are plain functions.
- Private helpers are prefixed with underscore (e.g. `_format_location`).
- All functions have type hints for parameters and return values.
- All modules and functions have docstrings.
- CLI errors are raised via `click.ClickException`.
- Table output uses dynamic column-width computation, a header line, a dash separator, and data rows. This pattern is consistent across all commands.

## Linting

- **Ruff** is the sole linter and formatter, run with default configuration.
- Run `make lint` before committing. Pre-commit hooks enforce this automatically.

## Testing

- **pytest** with **pytest-cov** for coverage.
- Tests live in `tests/`, mirroring the source layout.
- Test classes group related tests with descriptive names (e.g. `TestProgressBar`, `test_returns_empty_string_when_total_is_zero`).
- External API calls (Fast-F1, Ergast) are always mocked using `unittest.mock.patch` and `MagicMock`.
- Click commands are tested via `click.testing.CliRunner`.
- Run `make test` to execute the full suite.

## CI

- GitHub Actions runs on every push: install, lint, test.
- Test results are posted as PR comments and written to the GitHub Step Summary.
- Coverage reports are uploaded as build artifacts.

## Pre-commit hooks

Two local hooks run before each commit:

1. `make lint`
2. `make test`
