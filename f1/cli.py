"""F1 CLI - View Formula 1 season schedules powered by Fast-F1."""

import sys
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

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

    local_tz = _get_local_timezone()

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

    date_header = "Date & Time"
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


@cli.command()
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
        raise click.ClickException(f"Failed to load race data: {e}")

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
        pts = _fmt_points(driver["Points"])

        is_first = False
        rows.append((pos, name, team, grid, time_str, status, laps, pts))

    headers = ("Pos", "Driver", "Team", "Grid", "Time/Gap", "Status", "Laps", "Pts")
    col_widths = []
    for i, header in enumerate(headers):
        max_data = max((len(r[i]) for r in rows), default=0)
        col_widths.append(max(len(header), max_data) + 2)
    # Last column doesn't need trailing padding
    col_widths[-1] = max(len(headers[-1]), max(len(r[-1]) for r in rows))

    total_width = sum(col_widths)
    header_line = "".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))

    click.echo(f"\n{event_name}\n")
    click.echo(header_line)
    click.echo("-" * total_width)

    for row in rows:
        click.echo("".join(f"{val:<{col_widths[i]}}" for i, val in enumerate(row)))

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


def _fmt_points(value) -> str:
    """Format points, showing integers where possible."""
    if pd.notna(value):
        pts = float(value)
        return str(int(pts)) if pts == int(pts) else str(pts)
    return "0"


def _format_location(event: pd.Series) -> str:
    """Build a location string from the event data."""
    location = event.get("Location", "")
    country = event.get("Country", "")
    if location and country:
        return f"{location}, {country}"
    return location or country or "TBC"


def _format_race_datetime(event: pd.Series, local_tz: ZoneInfo) -> str:
    """Extract and format the race session date/time in the local timezone.

    The timezone abbreviation shown reflects the offset in effect on the race
    date, so DST transitions are handled correctly (e.g. GMT vs BST).
    """
    for session_num in range(1, 6):
        if event.get(f"Session{session_num}") == "Race":
            date_utc = event.get(f"Session{session_num}DateUtc")
            if pd.notna(date_utc):
                utc_dt = date_utc.to_pydatetime().replace(tzinfo=timezone.utc)
                local_dt = utc_dt.astimezone(local_tz)
                tz_abbr = local_dt.strftime("%Z")
                return f"{local_dt.strftime('%Y-%m-%d  %H:%M')} {tz_abbr}"
            break

    # Fallback to EventDate
    event_date = event.get("EventDate")
    if pd.notna(event_date):
        return str(event_date.strftime("%Y-%m-%d"))

    return "TBC"


def _get_local_timezone() -> ZoneInfo:
    """Detect the system's IANA timezone for DST-aware conversions.

    Falls back to UTC if the local timezone cannot be determined.
    """
    if sys.platform == "win32":
        # On Windows, try tzdata via datetime
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation",
            )
            tz_keyname, _ = winreg.QueryValueEx(key, "TimeZoneKeyName")
            return ZoneInfo(tz_keyname)
        except Exception:
            return ZoneInfo("UTC")

    # On Unix-like systems, read /etc/localtime symlink or TZ env var
    import os

    tz_env = os.environ.get("TZ")
    if tz_env:
        # Handle TZ values like ":Europe/London" (leading colon)
        tz_env = tz_env.lstrip(":")
        try:
            return ZoneInfo(tz_env)
        except Exception:
            pass

    try:
        link = os.readlink("/etc/localtime")
        # Typical path: /usr/share/zoneinfo/Europe/London
        if "zoneinfo/" in link:
            tz_key = link.split("zoneinfo/", 1)[1]
            return ZoneInfo(tz_key)
    except (OSError, IndexError):
        pass

    return ZoneInfo("UTC")
