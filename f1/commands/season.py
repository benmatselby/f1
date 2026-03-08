"""Show all races in a given F1 season."""

from datetime import datetime, timezone

import click
import fastf1
import pandas as pd
from f1.helpers import date as date_helpers


@click.command()
@click.argument("year", type=int)
@click.option(
    "--include-testing",
    is_flag=True,
    default=False,
    help="Include pre-season testing events.",
)
@click.option(
    "--show-winners", is_flag=True, default=False, help="Show the face winners"
)
def season(year: int, include_testing: bool, show_winners: bool):
    """Show all races in a given F1 season.

    Displays the race name, location, and date/time for each event.

    YEAR is the championship year (e.g. 2024).
    """
    now = datetime.now(timezone.utc)
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=include_testing)
    except Exception as e:
        raise click.ClickException(f"Failed to fetch schedule for {year}: {e}")

    if schedule.empty:
        raise click.ClickException(f"No events found for {year}.")

    # Filter out testing events unless requested
    if not include_testing:
        schedule = schedule[~schedule.is_testing()]

    # Pre-compute all rows so we can size columns to fit the data.
    rows = []

    events = list(schedule.iterrows())
    completed = 0
    with click.progressbar(
        events,
        length=len(events),
        label="Getting race details",
        hidden=not show_winners,
    ) as bar:
        for _, event in bar:
            row = [
                str(event["RoundNumber"]),
                event["EventName"],
                _format_location(event),
                date_helpers.format_race_datetime(event),
            ]

            race_time = date_helpers.get_race_utc(event)
            if race_time and race_time < now:
                completed += 1

            if show_winners:
                row.append(_get_race_winner(now, year, event))

            rows.append(tuple(row))

    columns = [
        ("Rnd", 0),
        ("Event", 1),
        ("Location", 2),
        ("Date & Time", 3),
    ]
    if show_winners:
        columns.append(("Winner", 4))

    col_widths = [
        max(len(header), max(len(str(row[idx])) for row in rows)) + 2
        for header, idx in columns
    ]
    total = sum(col_widths)

    click.echo(f"\nFormula 1 {year} Season\n")
    header_row = "".join(
        f"{header:<{width}}" for (header, _), width in zip(columns, col_widths)
    )
    click.echo(header_row)
    click.echo("-" * total)

    for race in rows:
        row_str = "".join(
            f"{str(race[idx]):<{width}}" for (_, idx), width in zip(columns, col_widths)
        )
        click.echo(row_str)

    click.echo(f"\nProgress    : {_progress_bar(completed, len(rows))}")
    click.echo(f"Total events: {len(rows)}")


def _get_race_winner(now: datetime, year: int, event: pd.Series) -> str:
    """Return the full name of the race winner, or empty if not yet raced."""
    race_time = date_helpers.get_race_utc(event)
    if race_time and race_time >= now:
        return ""

    try:
        session = fastf1.get_session(year, event["RoundNumber"], "R")
        session.load(laps=False, telemetry=False, weather=False, messages=False)
        results = session.results
        if results.empty:
            return ""

        winner = results[results["Position"] == 1.0]
        if winner.empty:
            return ""

        return str(winner.iloc[0]["FullName"] or winner.iloc[0]["Abbreviation"] or "")
    except Exception:
        return ""


def _progress_bar(completed: int, total: int, width: int = 30) -> str:
    """Build an ASCII progress bar showing season completion."""
    if total == 0:
        return ""

    filled = round(width * completed / total)
    bar = "#" * filled + "-" * (width - filled)
    pct = 100 * completed / total
    return f"[{bar}] {completed}/{total} ({pct:.0f}%)"


def _format_location(event: pd.Series) -> str:
    """Build a location string from the event data."""
    location = event.get("Location", "")
    country = event.get("Country", "")

    if location and country:
        return f"{location}, {country}"

    return location or country or "TBC"
