"""F1 CLI - View Formula 1 data powered by Fast-F1."""

import logging

import click
import fastf1

from f1.commands.race import race
from f1.commands.season import season

fastf1.set_log_level(logging.ERROR)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """A CLI tool for viewing Formula 1 data."""


cli.add_command(race)
cli.add_command(season)
