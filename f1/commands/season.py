"""Show all races in a given F1 season."""

import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import click
import fastf1
import pandas as pd


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

    events = list(schedule.iterrows())
    with click.progressbar(
        events, length=len(events), label="Getting race details"
    ) as bar:
        for _, event in bar:
            row = [
                str(event["RoundNumber"]),
                event["EventName"],
                _format_location(event),
                _format_race_datetime(event, local_tz),
            ]
            if show_winners:
                row.append(_get_race_winner(year, event))
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

    completed = _count_completed(schedule)
    click.echo(f"\nProgress    : {_progress_bar(completed, len(rows))}")
    click.echo(f"Total events: {len(rows)}")


def _get_race_winner(year: int, event: pd.Series) -> str:
    """Return the full name of the race winner, or empty if not yet raced."""
    now = datetime.now(timezone.utc)
    for session_num in range(1, 6):
        if event.get(f"Session{session_num}") == "Race":
            date_utc = event.get(f"Session{session_num}DateUtc")
            if pd.notna(date_utc):
                race_dt = date_utc.to_pydatetime().replace(tzinfo=timezone.utc)
                if race_dt >= now:
                    return ""
            break

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


def _count_completed(schedule) -> int:
    """Count events whose race session is in the past."""
    now = datetime.now(timezone.utc)
    completed = 0
    for _, event in schedule.iterrows():
        for session_num in range(1, 6):
            if event.get(f"Session{session_num}") == "Race":
                date_utc = event.get(f"Session{session_num}DateUtc")
                if pd.notna(date_utc):
                    race_dt = date_utc.to_pydatetime().replace(tzinfo=timezone.utc)
                    if race_dt < now:
                        completed += 1
                break
    return completed


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
