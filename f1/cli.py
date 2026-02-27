"""F1 CLI - View Formula 1 season schedules powered by Fast-F1."""

from datetime import datetime, timezone

import click
import fastf1
import pandas as pd


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """A CLI tool for viewing Formula 1 season schedules."""


@cli.command()
@click.argument("year", type=int)
@click.option(
    "--include-testing",
    is_flag=True,
    default=False,
    help="Include pre-season testing events.",
)
def season(year: int, include_testing: bool):
    """Show all races in a given F1 season.

    Displays the race name, location, and date/time for each event.

    YEAR is the championship year (e.g. 2024).
    """
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=include_testing)
    except Exception as e:
        raise click.ClickException(f"Failed to fetch schedule for {year}: {e}")

    if schedule.empty:
        raise click.ClickException(f"No events found for {year}.")

    # Filter out testing events unless requested
    if not include_testing:
        schedule = schedule[~schedule.is_testing()]

    local_tz = datetime.now(timezone.utc).astimezone().tzinfo
    tz_name = datetime.now(timezone.utc).astimezone().strftime("%Z")

    # Pre-compute all rows so we can size columns to fit the data.
    rows = []
    for _, event in schedule.iterrows():
        rows.append(
            (
                str(event["RoundNumber"]),
                event["EventName"],
                _format_location(event),
                _format_race_datetime(event, local_tz),
            )
        )

    date_header = f"Date & Time ({tz_name})"
    col_rnd = max(len("Rnd"), max(len(r[0]) for r in rows)) + 2
    col_evt = max(len("Event"), max(len(r[1]) for r in rows)) + 2
    col_loc = max(len("Location"), max(len(r[2]) for r in rows)) + 2
    col_dt = max(len(date_header), max(len(r[3]) for r in rows))
    total = col_rnd + col_evt + col_loc + col_dt

    click.echo(f"\nFormula 1 {year} Season\n")
    click.echo(
        f"{'Rnd':<{col_rnd}}{'Event':<{col_evt}}{'Location':<{col_loc}}{date_header}"
    )
    click.echo("-" * total)

    for rnd, name, location, race_date in rows:
        click.echo(f"{rnd:<{col_rnd}}{name:<{col_evt}}{location:<{col_loc}}{race_date}")

    click.echo(f"\nTotal events: {len(rows)}")


def _format_location(event: pd.Series) -> str:
    """Build a location string from the event data."""
    location = event.get("Location", "")
    country = event.get("Country", "")
    if location and country:
        return f"{location}, {country}"
    return location or country or "TBC"


def _format_race_datetime(event: pd.Series, local_tz) -> str:
    """Extract and format the race session date/time in the local timezone."""
    # The race is always Session5 in the schedule
    for session_num in range(1, 6):
        if event.get(f"Session{session_num}") == "Race":
            date_utc = event.get(f"Session{session_num}DateUtc")
            if pd.notna(date_utc):
                utc_dt = date_utc.to_pydatetime().replace(tzinfo=timezone.utc)
                local_dt = utc_dt.astimezone(local_tz)
                return local_dt.strftime("%Y-%m-%d  %H:%M")
            break

    # Fallback to EventDate
    event_date = event.get("EventDate")
    if pd.notna(event_date):
        return str(event_date.strftime("%Y-%m-%d"))

    return "TBC"
