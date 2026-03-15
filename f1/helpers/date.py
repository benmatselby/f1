"""Date utilities for F1 events."""

from datetime import UTC
from datetime import datetime

import pandas as pd


def get_race_utc(event: pd.Series) -> datetime | None:
    """Return the UTC datetime of the race session, or None if unavailable.

    Scans session slots 1-5 looking for one named "Race" and returns its
    UTC timestamp as a timezone-aware datetime.  Returns None when the
    event has no race session or the date is not yet confirmed (NaT).
    """
    for n in range(1, 6):
        if event.get(f"Session{n}") == "Race":
            utc = event.get(f"Session{n}DateUtc")

            if pd.notna(utc):
                return utc.to_pydatetime().replace(tzinfo=UTC)

            return None

    return None


def format_race_datetime(event: pd.Series) -> str:
    """Extract and format the race session date/time in the local timezone."""
    race_time = get_race_utc(event)
    if not race_time:
        return "TBC"

    local_dt = race_time.astimezone()
    return local_dt.strftime("%Y-%m-%d  %H:%M %Z")
