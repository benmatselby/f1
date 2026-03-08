from datetime import datetime, timezone

import pandas as pd


def get_race_utc(event: pd.Series) -> datetime | None:
    for n in range(1, 6):
        if event.get(f"Session{n}") == "Race":
            utc = event.get(f"Session{n}DateUtc")

            if pd.notna(utc):
                return utc.to_pydatetime().replace(tzinfo=timezone.utc)

            return None

    return None


def format_race_datetime(event: pd.Series) -> str:
    """Extract and format the race session date/time in the local timezone."""
    race_time = get_race_utc(event)
    if not race_time:
        return "TBC"

    local_dt = race_time.astimezone()
    return local_dt.strftime("%Y-%m-%d  %H:%M %Z")
