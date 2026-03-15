"""Show the full breakdown of a race result."""

from datetime import timedelta

import click
import fastf1
import pandas as pd

from f1.helpers.formatting import fmt_points
from f1.helpers.formatting import print_table


@click.command()
@click.argument("year", type=int)
@click.argument("venue", type=str)
def race(year: int, venue: str):
    """Show the full breakdown of a race result.

    Displays finishing order, grid positions, time/gap, status, laps completed,
    and points for every driver.

    YEAR is the championship year (e.g. 2024).

    VENUE is the Grand Prix name, location, or country (e.g. 'monza',
    'British', 'Australia'). Fuzzy matching is applied.
    """
    try:
        session = fastf1.get_session(year, venue, "R")
        session.load(laps=False, telemetry=False, weather=False, messages=False)
    except Exception as e:
        raise click.ClickException(f"Failed to load race data: {e}") from e

    results = session.results
    if results.empty:
        raise click.ClickException(
            f"No results found for '{venue}' {year}. The race may not have "
            "taken place yet."
        )

    event = session.event
    event_name = event.get("OfficialEventName", event.get("EventName", venue))

    # Build rows: Pos, Driver, Team, Grid, Time/Gap, Status, Laps, Pts
    rows: list[tuple[str, str, str, str, str, str, str, str]] = []
    is_first = True

    for _, driver in results.iterrows():
        pos = _fmt_position(driver["Position"], driver["ClassifiedPosition"])
        name = str(driver["FullName"] or driver["Abbreviation"] or "?")
        team = str(driver["TeamName"] or "")
        grid = _fmt_grid(driver["GridPosition"])
        time_str = _fmt_time(driver, is_first)
        status = str(driver["Status"] or "")
        laps = _fmt_int(driver["Laps"])
        pts = fmt_points(driver["Points"])

        is_first = False
        rows.append((pos, name, team, grid, time_str, status, laps, pts))

    headers = ("Pos", "Driver", "Team", "Grid", "Time/Gap", "Status", "Laps", "Pts")
    print_table(event_name, headers, rows)

    click.echo(f"\nClassified: {sum(1 for r in rows if r[0].isdigit())}")


def _fmt_position(position, classified_position) -> str:
    """Format the finishing position."""
    if pd.notna(position):
        return str(int(position))

    if classified_position and str(classified_position) not in ("nan", ""):
        return str(classified_position)

    return "-"


def _fmt_grid(grid_position) -> str:
    """Format the grid position, handling pit-lane starts."""
    if pd.notna(grid_position):
        pos = int(grid_position)
        if pos < 0:
            return "-"

        return "PIT" if pos == 0 else str(pos)

    return "-"


def _fmt_time(driver: pd.Series, is_leader: bool) -> str:
    """Format the time or gap to leader.

    For the leader, Time is the absolute race duration.  For all other
    classified drivers, Time is already the gap to the leader.
    """
    driver_time = driver["Time"]
    if pd.notna(driver_time):
        t = timedelta(seconds=driver_time.total_seconds())  # type: ignore[union-attr]
        if is_leader:
            total_secs = int(t.total_seconds())
            hours, remainder = divmod(total_secs, 3600)
            minutes, seconds = divmod(remainder, 60)
            millis = t.microseconds // 1000
            if hours:
                return f"{hours}:{minutes:02d}:{seconds:02d}.{millis:03d}"

            return f"{minutes}:{seconds:02d}.{millis:03d}"
        else:
            gap_secs = t.total_seconds()
            if gap_secs < 60:
                return f"+{gap_secs:.3f}s"

            minutes, secs = divmod(gap_secs, 60)
            return f"+{int(minutes)}:{secs:06.3f}"

    status = driver.get("Status", "")
    if status and "Lap" in str(status):
        return str(status)

    return ""


def _fmt_int(value) -> str:
    """Format a numeric value as an integer string."""
    if pd.notna(value):
        return str(int(value))

    return "-"
